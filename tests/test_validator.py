"""Tests for supervisory_procedures.core.validator."""

from pathlib import Path

import pytest
import yaml

from supervisory_procedures.core.validator import (
    ValidationError,
    ValidationWarning,
    validate_directory,
    validate_skill,
)

FIXTURES = Path(__file__).parent / "fixtures"


class TestValidateSkill:
    def test_valid_skill_passes(self):
        warnings = validate_skill(FIXTURES / "valid_skill.yml")
        assert isinstance(warnings, list)

    def test_invalid_skill_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_skill(FIXTURES / "invalid_skill_missing_fields.yml")
        assert exc_info.value.path == FIXTURES / "invalid_skill_missing_fields.yml"
        assert len(exc_info.value.errors) > 0

    def test_wildcard_agents_produces_warning(self):
        warnings = validate_skill(FIXTURES / "wildcard_agents_skill.yml")
        assert any("wildcard" in w.message.lower() or "*" in w.message for w in warnings)

    def test_wildcard_agents_strict_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_skill(FIXTURES / "wildcard_agents_skill.yml", strict=True)
        assert len(exc_info.value.errors) > 0

    def test_valid_skill_no_warnings(self):
        warnings = validate_skill(FIXTURES / "valid_skill.yml")
        # valid_skill.yml uses named agents so no wildcard warning
        wildcard_warnings = [w for w in warnings if "*" in w.message]
        assert len(wildcard_warnings) == 0

    def test_draft_skill_validates_schema(self):
        # Draft skills should still pass schema validation
        warnings = validate_skill(FIXTURES / "draft_skill.yml")
        assert isinstance(warnings, list)

    def test_loan_application_processing_valid(self):
        registry = Path(__file__).parent.parent / "registry"
        skill_path = registry / "retail_banking" / "loan-application-processing" / "skill.yml"
        warnings = validate_skill(skill_path)
        assert isinstance(warnings, list)

    def test_missing_file_raises_error(self):
        with pytest.raises((FileNotFoundError, ValueError)):
            validate_skill(Path("/nonexistent/path/skill.yml"))


class TestValidateDirectory:
    def test_validates_all_files(self):
        successes, failures = validate_directory(FIXTURES)
        # Should find valid fixtures and invalid ones
        assert len(successes) + len(failures) > 0

    def test_invalid_fixture_in_failures(self):
        _, failures = validate_directory(FIXTURES)
        failure_paths = [f.path for f in failures]
        assert any("invalid" in p.name for p in failure_paths)

    def test_valid_fixture_in_successes(self):
        successes, _ = validate_directory(FIXTURES)
        success_paths = [p for p, _ in successes]
        assert any("valid_skill" in p.name for p in success_paths)

    def test_registry_validates_cleanly(self):
        registry = Path(__file__).parent.parent / "registry"
        successes, failures = validate_directory(registry)
        # The production registry should have no validation failures
        assert failures == [], f"Registry validation failures: {failures}"

    def test_empty_directory_returns_empty(self, tmp_path):
        successes, failures = validate_directory(tmp_path)
        assert successes == []
        assert failures == []


class TestValidationError:
    def test_error_message_includes_path(self):
        path = Path("some/skill.yml")
        error = ValidationError(path, ["field X is required"])
        assert "some/skill.yml" in str(error)
        assert "field X is required" in str(error)

    def test_multiple_errors(self):
        path = Path("skill.yml")
        errors = ["error 1", "error 2", "error 3"]
        exc = ValidationError(path, errors)
        assert exc.errors == errors


class TestSchemaConstraints:
    """Test that the schema correctly rejects specific invalid inputs."""

    def _make_skill(self, overrides: dict) -> dict:
        """Return a minimal valid skill dict, with overrides applied."""
        import copy
        base = yaml.safe_load((FIXTURES / "valid_skill.yml").read_text())
        # Deep-merge overrides
        for key, val in overrides.items():
            if isinstance(val, dict) and isinstance(base.get(key), dict):
                base[key].update(val)
            else:
                base[key] = val
        return base

    def test_invalid_status_rejected(self, tmp_path):
        skill = self._make_skill({"metadata": {"status": "pending"}})
        path = tmp_path / "skill.yml"
        path.write_text(yaml.dump(skill))
        with pytest.raises(ValidationError):
            validate_skill(path)

    def test_invalid_schema_version_rejected(self, tmp_path):
        skill = self._make_skill({"metadata": {"schema_version": "99.0"}})
        path = tmp_path / "skill.yml"
        path.write_text(yaml.dump(skill))
        with pytest.raises(ValidationError):
            validate_skill(path)

    def test_empty_approved_activities_rejected(self, tmp_path):
        skill = self._make_skill({"approved_activities": []})
        path = tmp_path / "skill.yml"
        path.write_text(yaml.dump(skill))
        with pytest.raises(ValidationError):
            validate_skill(path)

    def test_empty_control_points_rejected(self, tmp_path):
        skill = self._make_skill({"control_points": []})
        path = tmp_path / "skill.yml"
        path.write_text(yaml.dump(skill))
        with pytest.raises(ValidationError):
            validate_skill(path)

    def test_invalid_classification_rejected(self, tmp_path):
        skill = self._make_skill({
            "control_points": [{
                "id": "test",
                "description": "test",
                "classification": "do_nothing",
                "activation": "step",
            }]
        })
        path = tmp_path / "skill.yml"
        path.write_text(yaml.dump(skill))
        with pytest.raises(ValidationError):
            validate_skill(path)

    def test_vetoed_without_escalation_contact_rejected(self, tmp_path):
        """Rec 11: vetoed control point must have escalation_contact."""
        skill = self._make_skill({
            "control_points": [{
                "id": "test-veto",
                "description": "A vetoed control point.",
                "classification": "vetoed",
                "activation": "conditional",
                "trigger": "Something bad happened.",
                # escalation_contact intentionally omitted
            }]
        })
        path = tmp_path / "skill.yml"
        path.write_text(yaml.dump(skill))
        with pytest.raises(ValidationError):
            validate_skill(path)

    def test_needs_approval_without_who_reviews_rejected(self, tmp_path):
        """Rec 11: needs_approval control point must have who_reviews."""
        skill = self._make_skill({
            "control_points": [
                # Keep a vetoed cp to satisfy the base schema
                {
                    "id": "error-threshold-exceeded",
                    "description": "Errors exceeded.",
                    "classification": "vetoed",
                    "activation": "conditional",
                    "trigger": "Errors exceeded.",
                    "escalation_contact": "ops@example.com",
                },
                {
                    "id": "test-approval",
                    "description": "Needs approval.",
                    "classification": "needs_approval",
                    "activation": "step",
                    # who_reviews intentionally omitted
                },
            ]
        })
        path = tmp_path / "skill.yml"
        path.write_text(yaml.dump(skill))
        with pytest.raises(ValidationError):
            validate_skill(path)

    def test_conditional_activation_without_trigger_rejected(self, tmp_path):
        """Rec 10: activation: conditional requires trigger field."""
        skill = self._make_skill({
            "control_points": [
                {
                    "id": "test-conditional",
                    "description": "A conditional control point.",
                    "classification": "vetoed",
                    "activation": "conditional",
                    "escalation_contact": "ops@example.com",
                    # trigger intentionally omitted
                },
            ]
        })
        path = tmp_path / "skill.yml"
        path.write_text(yaml.dump(skill))
        with pytest.raises(ValidationError):
            validate_skill(path)

    def test_step_activation_unreferenced_produces_warning(self, tmp_path):
        """Rec 10: activation: step control point not referenced by any workflow step warns."""
        skill = self._make_skill({
            "control_points": [
                {
                    "id": "error-threshold-exceeded",
                    "description": "Errors exceeded.",
                    "classification": "vetoed",
                    "activation": "conditional",
                    "trigger": "Errors exceeded.",
                    "escalation_contact": "ops@example.com",
                },
                {
                    "id": "unreferenced-review",
                    "description": "A step review that is never referenced.",
                    "classification": "review",
                    "activation": "step",
                    "who_reviews": "Someone",
                },
            ]
        })
        path = tmp_path / "skill.yml"
        path.write_text(yaml.dump(skill))
        warnings = validate_skill(path)
        assert any("unreferenced-review" in w.message for w in warnings)

    def test_lifecycle_fields_optional(self, tmp_path):
        """Rec 3: created_at, approved_at, approved_by are not required from authors."""
        skill = self._make_skill({})
        # Remove lifecycle fields — schema should still accept the skill
        skill["metadata"].pop("created_at", None)
        skill["metadata"].pop("approved_at", None)
        skill["metadata"].pop("approved_by", None)
        skill["metadata"]["status"] = "draft"
        path = tmp_path / "skill.yml"
        path.write_text(yaml.dump(skill))
        # Should not raise — lifecycle fields are optional
        warnings = validate_skill(path)
        assert isinstance(warnings, list)

    def test_step_id_optional(self, tmp_path):
        """Rec 4: workflow step id is optional; activity id is used as fallback."""
        skill = self._make_skill({
            "workflow": {
                "steps": [
                    {"activity": "run-query", "control_point": "initial-review"},
                ]
            }
        })
        path = tmp_path / "skill.yml"
        path.write_text(yaml.dump(skill))
        warnings = validate_skill(path)
        assert isinstance(warnings, list)

    def test_control_point_name_optional(self, tmp_path):
        """Rec 7: control point name is optional."""
        skill = self._make_skill({
            "control_points": [
                {
                    "id": "error-threshold-exceeded",
                    "description": "Errors exceeded.",
                    "classification": "vetoed",
                    "activation": "conditional",
                    "trigger": "Errors exceeded.",
                    "escalation_contact": "ops@example.com",
                    # name intentionally omitted
                },
                {
                    "id": "initial-review",
                    "description": "Review the output before proceeding.",
                    "classification": "review",
                    "activation": "step",
                    "who_reviews": "Test reviewer",
                    # name intentionally omitted
                },
            ]
        })
        path = tmp_path / "skill.yml"
        path.write_text(yaml.dump(skill))
        warnings = validate_skill(path)
        assert isinstance(warnings, list)
