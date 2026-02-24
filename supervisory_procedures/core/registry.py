"""SkillRegistry — loads, caches, and serves skills with access control."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .access_control import (
    AgentNotAuthorisedError,
    SkillNotApprovedError,
    SkillNotFoundError,
    check_access,
)
from .validator import ValidationError, load_yaml, validate_skill

logger = logging.getLogger(__name__)

# Default registry location relative to the project root
_DEFAULT_REGISTRY = Path(__file__).parent.parent.parent / "registry"


class SkillRegistry:
    """Load and serve skills from the Git registry directory.

    Skills are validated and cached at first load. Invalid or non-existent
    skills are excluded from the cache (Layer 3).

    Usage:
        registry = SkillRegistry()
        skill = registry.get_skill(
            "retail_banking/loan-application-processing",
            agent_id="loan-processor-agent-prod",
        )
    """

    def __init__(self, registry_path: Path | str | None = None) -> None:
        self._registry_path = Path(registry_path) if registry_path else _DEFAULT_REGISTRY
        self._cache: dict[str, dict[str, Any]] = {}
        self._loaded = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, force_reload: bool = False) -> None:
        """Scan the registry directory and populate the cache.

        Only directory-based skills (skill.yml inside a named directory) are
        loaded. Invalid skill files are skipped with a warning; they do not
        prevent other skills from loading.
        """
        if self._loaded and not force_reload:
            return

        self._cache.clear()

        for path in sorted(self._registry_path.rglob("skill.yml")):
            self._load_skill_file(path)

        self._loaded = True
        logger.info("Registry loaded: %d valid skills", len(self._cache))

    def _load_skill_file(self, path: Path) -> None:
        """Validate and load a single skill file into the cache."""
        try:
            validate_skill(path)
            data = load_yaml(path)
            skill_id: str = data["metadata"]["id"]
            data["_skill_dir"] = str(path.parent)
            self._cache[skill_id] = data
            logger.debug("Loaded skill %s from %s", skill_id, path)
        except ValidationError as exc:
            logger.warning("Skipping invalid skill %s: %s", path, exc)
        except (KeyError, ValueError) as exc:
            logger.warning("Skipping malformed skill %s: %s", path, exc)

    def get_skill(
        self,
        skill_id: str,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        """Return the skill data dict for skill_id.

        If agent_id is provided, all three access-control layers are enforced:
        - Layer 1: skill must be approved
        - Layer 2: agent_id must be in authorised_agents
        - Layer 3: skill must have passed schema validation (enforced at load time)

        Raises:
            SkillNotFoundError: if the skill_id is not in the registry
            SkillNotApprovedError: if the skill is draft/deprecated
            AgentNotAuthorisedError: if the agent is not on the allowlist
        """
        self.load()

        if skill_id not in self._cache:
            raise SkillNotFoundError(
                f"Skill '{skill_id}' not found in registry at {self._registry_path}"
            )

        skill_data = self._cache[skill_id]

        if agent_id is not None:
            check_access(skill_data, agent_id)

        return skill_data

    def list_skills(
        self,
        business_area: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return summary dicts for all (filtered) skills in the registry.

        Each summary dict merges the top-level ``metadata`` block with a
        ``risk_classification`` key pulled from the ``context`` block, so
        callers don't need to know the internal structure.

        Args:
            business_area: if set, only return skills in this business area slug
            status: if set, only return skills with this status
        """
        self.load()

        results = []
        for skill_data in self._cache.values():
            meta = skill_data.get("metadata", {})
            if business_area and meta.get("business_area") != business_area:
                continue
            if status and meta.get("status") != status:
                continue
            summary = dict(meta)
            summary["risk_classification"] = skill_data.get("context", {}).get(
                "risk_classification", ""
            )
            results.append(summary)

        return sorted(results, key=lambda m: m.get("id", ""))

    def __len__(self) -> int:
        self.load()
        return len(self._cache)

    def __contains__(self, skill_id: str) -> bool:
        self.load()
        return skill_id in self._cache


__all__ = ["SkillRegistry"]
