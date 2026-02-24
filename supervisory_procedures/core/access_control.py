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


def check_access(skill_data: dict[str, Any], agent_id: str) -> None:
    """Raise an appropriate error if agent_id is not permitted to use the skill.

    Enforces access-control layers:
    - Layer 1: skill must be approved
    - Layer 2: agent_id must be in authorised_agents
    - Layer 3: schema validity is enforced at registry load time
    """
    meta = skill_data.get("metadata", {})
    skill_id: str = meta.get("id", "<unknown>")
    status: str = meta.get("status", "draft")
    authorised_agents: list[str] = meta.get("authorised_agents", [])

    if status != "approved":
        raise SkillNotApprovedError(skill_id, status)

    if _WILDCARD not in authorised_agents and agent_id not in authorised_agents:
        raise AgentNotAuthorisedError(agent_id, skill_id)


def is_permitted(skill_data: dict[str, Any], agent_id: str) -> bool:
    """Return True if the agent is permitted; False otherwise (no exception)."""
    try:
        check_access(skill_data, agent_id)
        return True
    except PermissionError:
        return False
