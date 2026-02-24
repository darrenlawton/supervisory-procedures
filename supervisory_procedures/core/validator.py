"""YAML load + JSON Schema validation for skill files."""

from __future__ import annotations

import functools
import json
from pathlib import Path
from typing import Any

import yaml
import jsonschema
from jsonschema import Draft202012Validator, FormatChecker

# Path to the bundled schema — resolved relative to this file
_SCHEMA_PATH = Path(__file__).parent.parent.parent / "schema" / "skill.schema.json"

_WILDCARD_AGENT = "*"


class ValidationError(Exception):
    """Raised when a skill file fails schema validation."""

    def __init__(self, path: Path, errors: list[str]) -> None:
        self.path = path
        self.errors = errors
        summary = "; ".join(errors)
        super().__init__(f"{path}: {summary}")


class ValidationWarning:
    """Non-fatal validation warning (e.g. wildcard agent)."""

    def __init__(self, path: Path, message: str) -> None:
        self.path = path
        self.message = message

    def __str__(self) -> str:
        return f"WARNING {self.path}: {self.message}"


@functools.cache
def _load_schema() -> dict[str, Any]:
    with _SCHEMA_PATH.open() as f:
        return json.load(f)


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML skill file and return as a dict. Raises ValueError on parse errors."""
    try:
        with path.open() as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML parse error in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level YAML must be a mapping")
    return data


def validate_skill(
    path: Path,
    strict: bool = False,
) -> list[ValidationWarning]:
    """Validate a single skill YAML file against the JSON Schema.

    Returns a (possibly empty) list of ValidationWarning objects.
    Raises ValidationError if the skill is invalid.

    In strict mode, warnings are also raised as errors.
    """
    data = load_yaml(path)
    schema = _load_schema()

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    raw_errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))

    if raw_errors:
        messages = [_format_jsonschema_error(e) for e in raw_errors]
        raise ValidationError(path, messages)

    warnings = _collect_warnings(path, data)

    if strict and warnings:
        raise ValidationError(path, [w.message for w in warnings])

    return warnings


def _collect_warnings(path: Path, data: dict[str, Any]) -> list[ValidationWarning]:
    warnings: list[ValidationWarning] = []
    meta = data.get("metadata", {})

    agents: list[str] = meta.get("authorised_agents", [])
    if _WILDCARD_AGENT in agents:
        warnings.append(
            ValidationWarning(
                path,
                "authorised_agents contains '*' — all agents are permitted. "
                "Consider restricting to named agent IDs.",
            )
        )

    status = meta.get("status", "")
    if status == "approved":
        if not meta.get("approved_at"):
            warnings.append(
                ValidationWarning(path, "status is 'approved' but approved_at is null")
            )
        if not meta.get("approved_by"):
            warnings.append(
                ValidationWarning(path, "status is 'approved' but approved_by is null")
            )

    # Cross-reference: workflow step activity IDs must exist in scope.approved_activities
    approved_ids = {a["id"] for a in data.get("scope", {}).get("approved_activities", []) if isinstance(a, dict)}
    for step in data.get("workflow", {}).get("steps", []):
        activity = step.get("activity", "")
        if activity and activity not in approved_ids:
            warnings.append(ValidationWarning(
                path,
                f"Workflow step '{step.get('id', '?')}': activity '{activity}' not found in scope.approved_activities",
            ))

    # Staleness check: only applies to directory-based skill.yml files
    if path.name == "skill.yml":
        warnings.extend(_check_skill_md_freshness(path, data))

    return warnings


def _check_skill_md_freshness(path: Path, data: dict[str, Any]) -> list[ValidationWarning]:
    """Warn if SKILL.md is missing or out of sync with the current render of skill.yml."""
    from supervisory_procedures.core.renderer import render_skill_md  # avoid circular at module level

    skill_md_path = path.parent / "SKILL.md"

    if not skill_md_path.exists():
        return [ValidationWarning(
            path,
            f"SKILL.md not found — run `supv render {data.get('metadata', {}).get('id', '')}` to generate it",
        )]

    expected = render_skill_md(data)
    actual = skill_md_path.read_text()

    if actual.strip() != expected.strip():
        return [ValidationWarning(
            path,
            f"SKILL.md is stale — run `supv render {data.get('metadata', {}).get('id', '')}` to regenerate it",
        )]

    return []


def validate_directory(
    directory: Path,
    strict: bool = False,
) -> tuple[list[tuple[Path, list[ValidationWarning]]], list[ValidationError]]:
    """Validate all skill YAML files under directory recursively.

    Returns:
        (successes, failures)
        successes: list of (path, warnings) for valid skills
        failures: list of ValidationError for invalid skills
    """
    successes: list[tuple[Path, list[ValidationWarning]]] = []
    failures: list[ValidationError] = []

    for yml_path in sorted(directory.rglob("*.yml")):
        try:
            warnings = validate_skill(yml_path, strict=strict)
            successes.append((yml_path, warnings))
        except ValidationError as exc:
            failures.append(exc)
        except ValueError as exc:
            failures.append(ValidationError(yml_path, [str(exc)]))

    return successes, failures


def _format_jsonschema_error(error: jsonschema.ValidationError) -> str:
    path = " -> ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
    return f"[{path}] {error.message}"
