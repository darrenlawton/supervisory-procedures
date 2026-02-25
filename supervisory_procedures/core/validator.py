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


def _step_id(step: dict[str, Any]) -> str:
    """Return the effective step ID — explicit id if present, else the activity id."""
    return step.get("id") or step.get("activity", "?")


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

    # Cross-reference: workflow step activity IDs must exist in approved_activities
    approved_ids = {a["id"] for a in data.get("approved_activities", []) if isinstance(a, dict)}
    for step in data.get("workflow", {}).get("steps", []):
        activity = step.get("activity", "")
        if activity and activity not in approved_ids:
            warnings.append(ValidationWarning(
                path,
                f"Workflow step '{_step_id(step)}': activity '{activity}' not found in approved_activities",
            ))

    # Rec 10: activation: step requires the control point to be referenced by a workflow step
    referenced_cps = {
        step.get("control_point")
        for step in data.get("workflow", {}).get("steps", [])
        if step.get("control_point")
    }
    for cp in data.get("control_points", []):
        if cp.get("activation") == "step" and cp["id"] not in referenced_cps:
            warnings.append(ValidationWarning(
                path,
                f"Control point '{cp['id']}' has activation: step but is not referenced "
                f"by any workflow step via control_point",
            ))

    # Staleness check: only applies to directory-based skill.yml files
    if path.name == "skill.yml":
        warnings.extend(_check_skill_md_freshness(path, data))
        warnings.extend(_check_artifact_consistency(path, data))

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


def _check_artifact_consistency(path: Path, data: dict[str, Any]) -> list[ValidationWarning]:
    """Warn on inconsistencies between skill.yml declarations and supporting artifacts.

    Checks:
    1. Escalation contacts in control points vs resources/escalation_contacts.md
    2. Applicable regulations vs resources/regulations.md headings/references
    3. Shared skill existence for workflow steps that use uses_skill
    4. Unreferenced scripts in scripts/
    """
    warnings: list[ValidationWarning] = []
    skill_dir = path.parent
    registry_root = path.parent.parent.parent  # registry/<area>/<skill>/skill.yml

    # 1. Escalation contacts
    escalation_contacts_path = skill_dir / "resources" / "escalation_contacts.md"
    if escalation_contacts_path.exists():
        contacts_text = escalation_contacts_path.read_text().lower()
        for cp in data.get("control_points", []):
            contact = cp.get("escalation_contact", "")
            if contact and contact.lower() not in contacts_text:
                warnings.append(ValidationWarning(
                    path,
                    f"Control point '{cp['id']}' escalation_contact '{contact}' "
                    f"not found in resources/escalation_contacts.md",
                ))

    # 2. Applicable regulations vs resources/regulations.md
    regulations_path = skill_dir / "resources" / "regulations.md"
    if regulations_path.exists():
        regs_text = regulations_path.read_text()
        for reg in data.get("context", {}).get("applicable_regulations", []):
            # Check for a keyword from the regulation string (first meaningful token)
            keyword = reg.split("—")[0].strip().split()[0] if reg else ""
            if keyword and keyword.lower() not in regs_text.lower():
                warnings.append(ValidationWarning(
                    path,
                    f"Regulation '{reg}' from context.applicable_regulations has no matching "
                    f"reference in resources/regulations.md",
                ))

    # 3. Shared skill existence for uses_skill references
    for step in data.get("workflow", {}).get("steps", []):
        uses = step.get("uses_skill", "")
        if uses:
            shared_dir = registry_root / uses
            if not shared_dir.exists():
                warnings.append(ValidationWarning(
                    path,
                    f"Workflow step '{_step_id(step)}': uses_skill '{uses}' "
                    f"does not exist in registry/",
                ))

    # 4. Unreferenced scripts
    scripts_dir = skill_dir / "scripts"
    if scripts_dir.exists():
        declared_scripts: set[str] = set()
        for artifact_script in data.get("artifacts", {}).get("scripts", []):
            declared_scripts.add(artifact_script.get("file", ""))

        referenced_in_activities = set()
        for activity in data.get("approved_activities", []):
            aid = activity.get("id", "")
            if aid:
                referenced_in_activities.add(aid.replace("-", "_") + ".py")

        for script_file in scripts_dir.glob("*.py"):
            name = script_file.name
            if name not in declared_scripts and name not in referenced_in_activities:
                warnings.append(ValidationWarning(
                    path,
                    f"scripts/{name} is not referenced by any activity id or declared in artifacts.scripts",
                ))

    return warnings


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
