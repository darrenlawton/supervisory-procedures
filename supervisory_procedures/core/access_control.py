"""Three-layer runtime access control for agent skill loading.

Layer 1 — Status gate: only approved skills load.
Layer 2 — Allowlist gate: agent_id must be in authorised_agents.
Layer 3 — Schema validity gate: invalid skills excluded at registry load time.
"""

from __future__ import annotations

from typing import Any


_WILDCARD = "*"


class SkillNotFoundError(Exception):
    """Raised when the requested skill ID does not exist in the registry."""


class SkillNotApprovedError(PermissionError):
    """Raised when the skill exists but is not in approved status."""

    def __init__(self, skill_id: str, status: str) -> None:
        self.skill_id = skill_id
        self.status = status
        super().__init__(
            f"Skill '{skill_id}' has status '{status}' — only approved skills may be loaded"
        )


class AgentNotAuthorisedError(PermissionError):
    """Raised when the requesting agent ID is not in the skill's authorised_agents list."""

    def __init__(self, agent_id: str, skill_id: str) -> None:
        self.agent_id = agent_id
        self.skill_id = skill_id
        super().__init__(
            f"Agent '{agent_id}' is not authorised to load skill '{skill_id}'"
        )


class AuthorisedAgentsGuard:
    """Enforces the three access-control layers for a single skill."""

    def __init__(self, skill_data: dict[str, Any]) -> None:
        self._data = skill_data
        meta = skill_data.get("metadata", {})
        self._skill_id: str = meta.get("id", "<unknown>")
        self._status: str = meta.get("status", "draft")
        self._authorised_agents: list[str] = meta.get("authorised_agents", [])

    @property
    def skill_id(self) -> str:
        return self._skill_id

    def check(self, agent_id: str) -> None:
        """Raise the appropriate error if the agent is not permitted to use this skill.

        Call this before handing the skill data to an agent.
        """
        # Layer 1 — status gate
        if self._status != "approved":
            raise SkillNotApprovedError(self._skill_id, self._status)

        # Layer 2 — allowlist gate
        if _WILDCARD not in self._authorised_agents and agent_id not in self._authorised_agents:
            raise AgentNotAuthorisedError(agent_id, self._skill_id)

    def is_permitted(self, agent_id: str) -> bool:
        """Return True if the agent is permitted; False otherwise (no exception)."""
        try:
            self.check(agent_id)
            return True
        except PermissionError:
            return False
