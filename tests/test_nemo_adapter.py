"""Tests for supervisory_procedures.adapters.nemo_guardrails."""

import json
from pathlib import Path

import pytest
import yaml

from supervisory_procedures.adapters.generic_json import GenericJsonAdapter
from supervisory_procedures.adapters.nemo_guardrails import NeMoGuardrailsAdapter

FIXTURES = Path(__file__).parent / "fixtures"
REGISTRY = Path(__file__).parent.parent / "registry"


def _load_skill(filename: str) -> dict:
    return yaml.safe_load((FIXTURES / filename).read_text())


def _load_registry_skill(path: str) -> dict:
    return yaml.safe_load((REGISTRY / path).read_text())


class TestNeMoGuardrailsAdapter:
    def test_export_returns_dict_with_required_keys(self):
        skill = _load_skill("valid_skill.yml")
        adapter = NeMoGuardrailsAdapter()
        result = adapter.export(skill)
        assert "config_yml" in result
        assert "skill_rails_co" in result

    def test_config_yml_is_valid_yaml(self):
        skill = _load_skill("valid_skill.yml")
        adapter = NeMoGuardrailsAdapter()
        result = adapter.export(skill)
        parsed = yaml.safe_load(result["config_yml"])
        assert isinstance(parsed, dict)

    def test_config_yml_has_instructions(self):
        skill = _load_skill("valid_skill.yml")
        adapter = NeMoGuardrailsAdapter()
        result = adapter.export(skill)
        config = yaml.safe_load(result["config_yml"])
        assert "instructions" in config
        assert len(config["instructions"]) > 0

    def test_config_yml_instructions_contain_skill_id(self):
        skill = _load_skill("valid_skill.yml")
        adapter = NeMoGuardrailsAdapter()
        result = adapter.export(skill)
        config = yaml.safe_load(result["config_yml"])
        instructions_content = config["instructions"][0]["content"]
        assert "test_area/test-skill" in instructions_content

    def test_config_yml_has_rails(self):
        skill = _load_skill("valid_skill.yml")
        adapter = NeMoGuardrailsAdapter()
        result = adapter.export(skill)
        config = yaml.safe_load(result["config_yml"])
        assert "rails" in config
        assert "input" in config["rails"]
        assert "output" in config["rails"]

    def test_input_rails_include_veto_flows(self):
        skill = _load_skill("valid_skill.yml")
        adapter = NeMoGuardrailsAdapter()
        result = adapter.export(skill)
        config = yaml.safe_load(result["config_yml"])
        input_flows = config["rails"]["input"]["flows"]
        assert len(input_flows) > 0
        assert any("error_threshold_exceeded" in f or "error" in f for f in input_flows)

    def test_colang_file_contains_veto_flows(self):
        skill = _load_skill("valid_skill.yml")
        adapter = NeMoGuardrailsAdapter()
        result = adapter.export(skill)
        co = result["skill_rails_co"]
        assert "flow check" in co

    def test_colang_file_has_stop_statement(self):
        skill = _load_skill("valid_skill.yml")
        adapter = NeMoGuardrailsAdapter()
        result = adapter.export(skill)
        assert "stop" in result["skill_rails_co"]

    def test_loan_application_export(self):
        skill = _load_registry_skill("retail_banking/loan_application_processing.yml")
        adapter = NeMoGuardrailsAdapter()
        result = adapter.export(skill)
        # Should have all 4 veto triggers as input rail flows
        config = yaml.safe_load(result["config_yml"])
        assert len(config["rails"]["input"]["flows"]) == 4
        # Should mention halt_and_escalate action
        assert "escalate" in result["skill_rails_co"].lower()

    def test_required_checkpoints_in_output_rails(self):
        skill = _load_registry_skill("retail_banking/loan_application_processing.yml")
        adapter = NeMoGuardrailsAdapter()
        result = adapter.export(skill)
        config = yaml.safe_load(result["config_yml"])
        output_flows = config["rails"]["output"]["flows"]
        # All 3 workflow checkpoints in loan_application_processing are required
        assert len(output_flows) == 3

    def test_config_contains_prohibited_actions(self):
        skill = _load_skill("valid_skill.yml")
        adapter = NeMoGuardrailsAdapter()
        result = adapter.export(skill)
        config = yaml.safe_load(result["config_yml"])
        content = config["instructions"][0]["content"]
        assert "PROHIBITED" in content or "NEVER" in content.upper()


class TestGenericJsonAdapter:
    def test_export_returns_json_string(self):
        skill = _load_skill("valid_skill.yml")
        adapter = GenericJsonAdapter()
        result = adapter.export(skill)
        assert isinstance(result, str)

    def test_export_is_valid_json(self):
        skill = _load_skill("valid_skill.yml")
        adapter = GenericJsonAdapter()
        result = adapter.export(skill)
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_envelope_has_required_keys(self):
        skill = _load_skill("valid_skill.yml")
        adapter = GenericJsonAdapter()
        result = json.loads(adapter.export(skill))
        assert result["export_format"] == "supervisory-skill-v1"
        assert "skill_id" in result
        assert "skill" in result

    def test_skill_id_in_envelope(self):
        skill = _load_skill("valid_skill.yml")
        adapter = GenericJsonAdapter()
        result = json.loads(adapter.export(skill))
        assert result["skill_id"] == "test_area/test-skill"

    def test_full_skill_preserved(self):
        skill = _load_skill("valid_skill.yml")
        adapter = GenericJsonAdapter()
        result = json.loads(adapter.export(skill))
        assert result["skill"]["metadata"]["id"] == "test_area/test-skill"
        assert "context" in result["skill"]
        assert "scope" in result["skill"]
        assert "hard_veto_triggers" in result["skill"]

    def test_loan_application_export(self):
        skill = _load_registry_skill("retail_banking/loan_application_processing.yml")
        adapter = GenericJsonAdapter()
        result = json.loads(adapter.export(skill))
        assert result["skill_id"] == "retail_banking/loan-application-processing"
        assert len(result["skill"]["hard_veto_triggers"]) == 4
