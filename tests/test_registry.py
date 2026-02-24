"""Tests for supervisory_procedures.core.registry."""

from pathlib import Path

import pytest
import yaml

from supervisory_procedures.core.access_control import (
    AgentNotAuthorisedError,
    SkillNotApprovedError,
    SkillNotFoundError,
)
from supervisory_procedures.core.registry import SkillRegistry

FIXTURES = Path(__file__).parent / "fixtures"
REGISTRY = Path(__file__).parent.parent / "registry"


class TestSkillRegistryLoad:
    def test_loads_production_registry(self):
        reg = SkillRegistry()
        reg.load()
        assert len(reg) > 0

    def test_loads_from_custom_path(self, tmp_path):
        # Skills must be directory-based (skill.yml inside a named directory)
        dest = tmp_path / "test_area" / "test-skill" / "skill.yml"
        dest.parent.mkdir(parents=True)
        dest.write_text((FIXTURES / "valid_skill.yml").read_text())
        reg = SkillRegistry(registry_path=tmp_path)
        reg.load()
        assert len(reg) == 1

    def test_skips_invalid_skills(self, tmp_path):
        valid_dir = tmp_path / "test_area" / "valid-skill"
        valid_dir.mkdir(parents=True)
        (valid_dir / "skill.yml").write_text((FIXTURES / "valid_skill.yml").read_text())

        invalid_dir = tmp_path / "test_area" / "invalid-skill"
        invalid_dir.mkdir(parents=True)
        (invalid_dir / "skill.yml").write_text((FIXTURES / "invalid_skill_missing_fields.yml").read_text())

        reg = SkillRegistry(registry_path=tmp_path)
        reg.load()
        assert len(reg) == 1

    def test_load_is_cached(self):
        reg = SkillRegistry()
        reg.load()
        first_count = len(reg)
        reg.load()  # should not re-scan
        assert len(reg) == first_count

    def test_force_reload(self):
        reg = SkillRegistry()
        reg.load()
        reg.load(force_reload=True)  # should not error
        assert len(reg) > 0

    def test_contains(self):
        reg = SkillRegistry()
        assert "retail_banking/loan-application-processing" in reg


class TestSkillRegistryGetSkill:
    def test_get_approved_skill_without_agent_id(self):
        reg = SkillRegistry()
        skill = reg.get_skill("retail_banking/loan-application-processing")
        assert skill["metadata"]["id"] == "retail_banking/loan-application-processing"

    def test_get_approved_skill_with_authorised_agent(self):
        reg = SkillRegistry()
        skill = reg.get_skill(
            "retail_banking/loan-application-processing",
            agent_id="loan-processor-agent-prod",
        )
        assert skill is not None

    def test_get_skill_with_unauthorised_agent_raises(self):
        reg = SkillRegistry()
        with pytest.raises(AgentNotAuthorisedError):
            reg.get_skill(
                "retail_banking/loan-application-processing",
                agent_id="rogue-agent",
            )

    def test_get_nonexistent_skill_raises(self):
        reg = SkillRegistry()
        with pytest.raises(SkillNotFoundError):
            reg.get_skill("nonexistent/skill")

    def test_draft_skill_blocked_by_agent_id(self, tmp_path):
        skill_dir = tmp_path / "test_area" / "draft-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "skill.yml").write_text((FIXTURES / "draft_skill.yml").read_text())
        reg = SkillRegistry(registry_path=tmp_path)
        with pytest.raises(SkillNotApprovedError):
            reg.get_skill("test_area/draft-skill", agent_id="test-agent-dev")

    def test_get_skill_returns_full_dict(self):
        reg = SkillRegistry()
        skill = reg.get_skill("retail_banking/loan-application-processing")
        assert "context" in skill
        assert "scope" in skill
        assert "constraints" in skill
        assert "control_points" in skill


class TestSkillRegistryListSkills:
    def test_list_all_skills(self):
        reg = SkillRegistry()
        skills = reg.list_skills()
        assert len(skills) > 0

    def test_list_by_business_area(self):
        reg = SkillRegistry()
        skills = reg.list_skills(business_area="retail_banking")
        assert all(s["business_area"] == "retail_banking" for s in skills)

    def test_list_by_status(self):
        reg = SkillRegistry()
        skills = reg.list_skills(status="approved")
        assert all(s["status"] == "approved" for s in skills)

    def test_list_nonexistent_area_returns_empty(self):
        reg = SkillRegistry()
        skills = reg.list_skills(business_area="nonexistent_area")
        assert skills == []

    def test_list_includes_risk_classification(self):
        reg = SkillRegistry()
        skills = reg.list_skills()
        for s in skills:
            assert "risk_classification" in s

    def test_list_results_are_sorted(self):
        reg = SkillRegistry()
        skills = reg.list_skills()
        ids = [s["id"] for s in skills]
        assert ids == sorted(ids)
