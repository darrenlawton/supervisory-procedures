"""Tests for supervisory_procedures.core.access_control."""

import pytest
import yaml
from pathlib import Path

from supervisory_procedures.core.access_control import (
    AgentNotAuthorisedError,
    AuthorisedAgentsGuard,
    SkillNotApprovedError,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load(filename: str) -> dict:
    return yaml.safe_load((FIXTURES / filename).read_text())


class TestAuthorisedAgentsGuard:
    def test_approved_named_agent_passes(self):
        data = _load("valid_skill.yml")
        guard = AuthorisedAgentsGuard(data)
        guard.check("test-agent-prod")  # should not raise

    def test_approved_named_agent_is_permitted(self):
        data = _load("valid_skill.yml")
        guard = AuthorisedAgentsGuard(data)
        assert guard.is_permitted("test-agent-prod") is True

    def test_unknown_agent_raises(self):
        data = _load("valid_skill.yml")
        guard = AuthorisedAgentsGuard(data)
        with pytest.raises(AgentNotAuthorisedError) as exc_info:
            guard.check("unknown-agent")
        assert exc_info.value.agent_id == "unknown-agent"
        assert "test_area/test-skill" in exc_info.value.skill_id

    def test_unknown_agent_not_permitted(self):
        data = _load("valid_skill.yml")
        guard = AuthorisedAgentsGuard(data)
        assert guard.is_permitted("unknown-agent") is False

    def test_draft_skill_raises_not_approved(self):
        data = _load("draft_skill.yml")
        guard = AuthorisedAgentsGuard(data)
        with pytest.raises(SkillNotApprovedError) as exc_info:
            guard.check("test-agent-dev")
        assert exc_info.value.status == "draft"

    def test_draft_skill_not_permitted(self):
        data = _load("draft_skill.yml")
        guard = AuthorisedAgentsGuard(data)
        assert guard.is_permitted("test-agent-dev") is False

    def test_wildcard_agent_allows_any(self):
        data = _load("wildcard_agents_skill.yml")
        guard = AuthorisedAgentsGuard(data)
        guard.check("any-random-agent")  # should not raise
        assert guard.is_permitted("another-agent") is True

    def test_wildcard_still_blocks_draft(self):
        """Even wildcard agents are blocked if skill is not approved."""
        data = _load("wildcard_agents_skill.yml")
        # Manually set to draft for this test
        data["metadata"]["status"] = "draft"
        guard = AuthorisedAgentsGuard(data)
        with pytest.raises(SkillNotApprovedError):
            guard.check("any-agent")

    def test_skill_id_property(self):
        data = _load("valid_skill.yml")
        guard = AuthorisedAgentsGuard(data)
        assert guard.skill_id == "test_area/test-skill"

    def test_not_approved_error_message(self):
        data = _load("draft_skill.yml")
        guard = AuthorisedAgentsGuard(data)
        with pytest.raises(SkillNotApprovedError) as exc_info:
            guard.check("any-agent")
        assert "draft" in str(exc_info.value)

    def test_not_authorised_error_message(self):
        data = _load("valid_skill.yml")
        guard = AuthorisedAgentsGuard(data)
        with pytest.raises(AgentNotAuthorisedError) as exc_info:
            guard.check("intruder-agent")
        assert "intruder-agent" in str(exc_info.value)
        assert "test_area/test-skill" in str(exc_info.value)
