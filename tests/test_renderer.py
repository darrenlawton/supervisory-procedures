"""Tests for supervisory_procedures.core.renderer — Option A frontmatter alignment."""

from pathlib import Path

import pytest
import yaml

from supervisory_procedures.core.renderer import render_skill_md

FIXTURES = Path(__file__).parent / "fixtures"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _frontmatter(md: str) -> dict:
    """Extract and parse the YAML frontmatter block from a SKILL.md string."""
    assert md.startswith("---\n"), "SKILL.md must open with '---'"
    end = md.index("\n---\n", 4)
    return yaml.safe_load(md[4:end])


class TestFrontmatterFields:
    def setup_method(self):
        self.skill = _load(FIXTURES / "valid_skill.yml")
        self.md = render_skill_md(self.skill)
        self.fm = _frontmatter(self.md)

    def test_name_field_present(self):
        assert "name" in self.fm

    def test_name_is_kebab_case_skill_slug(self):
        # name must be the last segment of the skill id, in kebab-case
        expected = self.skill["metadata"]["id"].split("/")[-1]
        assert self.fm["name"] == expected

    def test_description_field_present(self):
        assert "description" in self.fm

    def test_description_under_1024_chars(self):
        assert len(self.fm["description"]) <= 1024

    def test_description_contains_use_when(self):
        assert "Use when" in self.fm["description"]

    def test_description_does_not_contain_authorised_agents(self):
        # Agent list is internal access-control data, not triggering metadata
        assert "Authorised agents" not in self.fm["description"]
        assert "authorised_agents" not in self.fm["description"]

    def test_allowed_tools_field_present(self):
        assert "allowed-tools" in self.fm

    def test_allowed_tools_default_value(self):
        # Default when metadata.allowed_tools is not set in skill.yml
        assert self.fm["allowed-tools"] == "Bash(python:*)"

    def test_compatibility_field_present(self):
        assert "compatibility" in self.fm

    def test_compatibility_under_500_chars(self):
        assert len(self.fm["compatibility"]) <= 500

    def test_compatibility_mentions_python(self):
        assert "Python" in self.fm["compatibility"]

    def test_compatibility_mentions_risk(self):
        risk = self.skill["context"]["risk_classification"]
        assert risk in self.fm["compatibility"]

    def test_metadata_block_present(self):
        assert "metadata" in self.fm

    def test_metadata_author_matches_supervisor(self):
        expected = self.skill["metadata"]["supervisor"]["name"]
        assert self.fm["metadata"]["author"] == expected

    def test_metadata_version_matches_skill_version(self):
        expected = self.skill["metadata"]["version"]
        assert self.fm["metadata"]["version"] == expected

    def test_metadata_category_matches_business_area(self):
        # business_area slug with underscores → human-readable with spaces
        expected = self.skill["metadata"]["business_area"].replace("_", " ")
        assert self.fm["metadata"]["category"] == expected


class TestAllowedToolsOverride:
    def test_custom_allowed_tools_respected(self, tmp_path):
        skill = yaml.safe_load((FIXTURES / "valid_skill.yml").read_text())
        skill["metadata"]["allowed_tools"] = "Bash(python:*) Read"
        path = tmp_path / "skill.yml"
        path.write_text(yaml.dump(skill))
        md = render_skill_md(skill)
        fm = _frontmatter(md)
        assert fm["allowed-tools"] == "Bash(python:*) Read"


class TestCompatibilityRegulationCount:
    def test_regulation_count_in_compatibility(self, tmp_path):
        skill = yaml.safe_load((FIXTURES / "valid_skill.yml").read_text())
        skill["context"]["applicable_regulations"] = ["Reg A", "Reg B", "Reg C"]
        md = render_skill_md(skill)
        fm = _frontmatter(md)
        assert "3 regulation(s)" in fm["compatibility"]

    def test_no_regulations_omits_count(self):
        skill = yaml.safe_load((FIXTURES / "valid_skill.yml").read_text())
        assert skill["context"]["applicable_regulations"] == []
        md = render_skill_md(skill)
        fm = _frontmatter(md)
        assert "regulation(s)" not in fm["compatibility"]


class TestFrontmatterFormat:
    def test_skill_md_opens_with_frontmatter(self):
        skill = _load(FIXTURES / "valid_skill.yml")
        md = render_skill_md(skill)
        assert md.startswith("---\n")

    def test_frontmatter_closes_before_body(self):
        skill = _load(FIXTURES / "valid_skill.yml")
        md = render_skill_md(skill)
        # There must be a closing '---' after the opening one
        assert "\n---\n" in md[4:]

    def test_loan_skill_frontmatter_complete(self):
        registry = Path(__file__).parent.parent / "registry"
        skill_path = registry / "retail_banking" / "loan-application-processing" / "skill.yml"
        skill = yaml.safe_load(skill_path.read_text())
        md = render_skill_md(skill)
        fm = _frontmatter(md)
        for field in ("name", "description", "allowed-tools", "compatibility", "metadata"):
            assert field in fm, f"Missing frontmatter field: {field}"
