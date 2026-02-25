"""Renderer — generates an Agent Skills compatible SKILL.md from skill.yml data."""

from __future__ import annotations

import re
from typing import Any

_SHARED = "registry/shared"
_MAX_DESCRIPTION = 1024


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_skill_md(skill_data: dict[str, Any]) -> str:
    """Generate a complete SKILL.md string from a validated skill data dict."""
    sections = [
        _frontmatter(skill_data),
        _header(skill_data),
        _initialisation(skill_data),
        _approved_activities(skill_data),
        _unacceptable_actions(skill_data),
        _vetoed_conditions(skill_data),
        _oversight_checkpoints(skill_data),
        _condition_triggered_controls(skill_data),
        _workflow(skill_data),
    ]
    return "\n".join(s for s in sections if s).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _skill_id(skill_data: dict[str, Any]) -> str:
    return skill_data.get("metadata", {}).get("id", "unknown")


def _skill_yml_path(skill_data: dict[str, Any]) -> str:
    return f"registry/{_skill_id(skill_data)}/skill.yml"


def _cp_index(skill_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {cp["id"]: cp for cp in skill_data.get("control_points", [])}


def _inline(text: str) -> str:
    """Collapse multi-line YAML strings to a single line."""
    return " ".join(text.split())


def _cp_display_name(cp: dict[str, Any]) -> str:
    """Return display name for a control point: explicit name or title-cased id."""
    if cp.get("name"):
        return cp["name"]
    return re.sub(r"-", " ", cp["id"]).title()


def _checkpoint_gate_cmd(skill_id: str, cp: dict[str, Any]) -> str:
    """Build a checkpoint_gate.py bash invocation from a control point dict."""
    args = [
        f"python {_SHARED}/checkpoint-gate/scripts/checkpoint_gate.py",
        f"  --skill {skill_id}",
        "  --session ${CLAUDE_SESSION_ID}",
        f"  --control-point {cp['id']}",
        f"  --classification {cp.get('classification', '')}",
    ]
    if cp.get("who_reviews"):
        args.append(f'  --reviewer "{cp["who_reviews"]}"')
    if cp.get("sla_hours"):
        args.append(f"  --sla-hours {cp['sla_hours']}")
    if cp.get("escalation_contact"):
        args.append(f"  --contact {cp['escalation_contact']}")
    return " \\\n".join(args)


def _audit_log_cmd(skill_id: str, action: str) -> str:
    return (
        f"python {_SHARED}/audit-logging/scripts/audit_log.py \\\n"
        f"  --skill {skill_id} \\\n"
        f"  --session ${{CLAUDE_SESSION_ID}} \\\n"
        f"  --action {action}"
    )


def _validate_activity_cmd(skill_yml_path: str, step_id: str) -> str:
    return (
        f"python {_SHARED}/validate-activity/scripts/validate_activity.py \\\n"
        f"  --skill {skill_yml_path} \\\n"
        f"  --step {step_id}"
    )


def _halt_comment(classification: str) -> str:
    return {
        "vetoed": "# Exit code 2 — halt all processing immediately.",
        "needs_approval": "# PENDING — halt here and await explicit approval before continuing.",
        "review": "# PENDING — halt here and await reviewer clearance before continuing.",
        "notify": "# NOTIFY — human is informed; agent may continue.",
    }.get(classification, "")


def _effective_step_id(step: dict[str, Any]) -> str:
    """Return the effective step ID — explicit id if present, else the activity id."""
    return step.get("id") or step.get("activity", "?")


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------

def _frontmatter(skill_data: dict[str, Any]) -> str:
    meta = skill_data.get("metadata", {})
    ctx = skill_data.get("context", {})

    name = meta.get("id", "").split("/")[-1]

    raw_desc = _inline(ctx.get("description", ""))
    area = meta.get("business_area", "").replace("_", " ")
    skill_name = meta.get("name", "")
    risk = ctx.get("risk_classification", "")
    agents = ", ".join(meta.get("authorised_agents", []))

    use_when = f"Use when {skill_name} is needed for {area} operations."
    suffix = f" {use_when} Risk: {risk}. Authorised agents: {agents}."

    if len(raw_desc) + len(suffix) > _MAX_DESCRIPTION:
        raw_desc = raw_desc[: _MAX_DESCRIPTION - len(suffix) - 3] + "..."

    description = raw_desc + suffix
    return f'---\nname: {name}\ndescription: "{description}"\n---\n'


def _header(skill_data: dict[str, Any]) -> str:
    meta = skill_data.get("metadata", {})
    ctx = skill_data.get("context", {})
    sup = meta.get("supervisor", {})

    regs = ctx.get("applicable_regulations", [])
    reg_str = " | ".join(regs) if regs else "None specified"

    return (
        f"# {meta.get('name', '')}\n\n"
        f"> **Governed Skill** — Supervisor: {sup.get('name', '')} ({sup.get('role', '')})\n"
        f"> Risk: **{ctx.get('risk_classification', '')}** | "
        f"Version: {meta.get('version', '')} | "
        f"Regulations: {reg_str}\n\n"
        "*All steps, controls, and restrictions below are defined by your supervisor. "
        "Follow this procedure exactly.*\n\n---"
    )


def _initialisation(skill_data: dict[str, Any]) -> str:
    sid = _skill_id(skill_data)
    return (
        "## Initialisation\n\n"
        "Before any other action, record that this skill has been invoked:\n\n"
        f"```bash\n{_audit_log_cmd(sid, 'skill_invoked')}\n```\n\n---"
    )


def _approved_activities(skill_data: dict[str, Any]) -> str:
    syml = _skill_yml_path(skill_data)
    activities = skill_data.get("approved_activities", [])

    validate_cmd = (
        f"python {_SHARED}/validate-activity/scripts/validate_activity.py \\\n"
        f"  --skill {syml} \\\n"
        f"  --step <step-id>"
    )

    rows = "\n".join(
        f"| `{act['id']}` | {act['description']} |" for act in activities
    )

    return (
        "## Approved Activities\n\n"
        "You may **only** perform activities listed below. "
        "Validate each step before executing:\n\n"
        f"```bash\n{validate_cmd}\n```\n\n"
        "If `\"allowed\": false` — halt immediately and log the attempt.\n\n"
        "| Activity ID | Description |\n"
        "|-------------|-------------|\n"
        f"{rows}\n\n---"
    )


def _unacceptable_actions(skill_data: dict[str, Any]) -> str:
    actions = skill_data.get("constraints", {}).get("unacceptable_actions", [])
    if not actions:
        return ""
    items = "\n".join(f"- {a}" for a in actions)
    return f"## What You Must Never Do\n\n{items}\n\n---"


def _vetoed_conditions(skill_data: dict[str, Any]) -> str:
    sid = _skill_id(skill_data)
    vetoed = [cp for cp in skill_data.get("control_points", []) if cp.get("classification") == "vetoed"]
    if not vetoed:
        return ""

    lines = [
        "## Vetoed Conditions — Halt Immediately",
        "",
        "If any of these conditions arise, invoke the checkpoint immediately and halt. "
        "No human override is possible.",
        "",
    ]

    for cp in vetoed:
        cmd = _checkpoint_gate_cmd(sid, cp)
        lines += [f"### {cp['id']} — {_cp_display_name(cp)}", "", _inline(cp.get("description", ""))]
        if cp.get("trigger"):
            lines += ["", f"**Trigger:** {_inline(cp['trigger'])}"]
        lines += ["", f"```bash\n{cmd}\n{_halt_comment('vetoed')}\n```", ""]

    lines.append("---")
    return "\n".join(lines)


def _oversight_checkpoints(skill_data: dict[str, Any]) -> str:
    """Control points with activation: step (referenced from workflow steps)."""
    sid = _skill_id(skill_data)
    checkpoints = [
        cp for cp in skill_data.get("control_points", [])
        if cp.get("classification") not in ("vetoed", "auto")
        and cp.get("activation") == "step"
    ]
    if not checkpoints:
        return ""

    lines = [
        "## Oversight Checkpoints",
        "",
        "These checkpoints are invoked at specific workflow steps (see Workflow section).",
        "",
    ]

    for cp in checkpoints:
        classification = cp.get("classification", "")
        meta_parts = [f"Classification: **{classification}**"]
        if cp.get("who_reviews"):
            meta_parts.append(f"Reviewer: {cp['who_reviews']}")
        if cp.get("sla_hours"):
            meta_parts.append(f"SLA: {cp['sla_hours']}h")

        cmd = _checkpoint_gate_cmd(sid, cp)
        comment = _halt_comment(classification)
        bash = f"```bash\n{cmd}\n{comment}\n```" if comment else f"```bash\n{cmd}\n```"

        lines += [
            f"### {cp['id']} — {_cp_display_name(cp)}",
            "",
            " | ".join(meta_parts),
            "",
            _inline(cp.get("description", "")),
            "",
            bash,
            "",
        ]

    lines.append("---")
    return "\n".join(lines)


def _condition_triggered_controls(skill_data: dict[str, Any]) -> str:
    """Control points with activation: conditional."""
    sid = _skill_id(skill_data)
    checkpoints = [
        cp for cp in skill_data.get("control_points", [])
        if cp.get("classification") not in ("vetoed", "auto")
        and cp.get("activation") == "conditional"
    ]
    if not checkpoints:
        return ""

    lines = [
        "## Condition-Triggered Controls",
        "",
        "These activate when their trigger condition is met during any workflow step.",
        "",
    ]

    for cp in checkpoints:
        classification = cp.get("classification", "")
        meta_parts = [f"Classification: **{classification}**"]
        if cp.get("who_reviews"):
            meta_parts.append(f"Reviewer: {cp['who_reviews']}")
        if cp.get("sla_hours"):
            meta_parts.append(f"SLA: {cp['sla_hours']}h")

        cmd = _checkpoint_gate_cmd(sid, cp)
        comment = _halt_comment(classification)
        bash = f"```bash\n{cmd}\n{comment}\n```" if comment else f"```bash\n{cmd}\n```"

        lines += [
            f"### {cp['id']} — {_cp_display_name(cp)}",
            "",
            " | ".join(meta_parts),
            "",
            f"**Trigger:** {_inline(cp['trigger'])}",
            "",
            _inline(cp.get("description", "")),
            "",
            bash,
            "",
        ]

    lines.append("---")
    return "\n".join(lines)


def _workflow(skill_data: dict[str, Any]) -> str:
    sid = _skill_id(skill_data)
    syml = _skill_yml_path(skill_data)
    steps = skill_data.get("workflow", {}).get("steps", [])
    cp_idx = _cp_index(skill_data)
    activity_map = {
        a["id"]: a["description"]
        for a in skill_data.get("approved_activities", [])
    }

    if not steps:
        return ""

    lines = [
        "## Workflow",
        "",
        "Execute steps in this exact order. Do not skip, reorder, or add steps.",
        "",
    ]

    for i, step in enumerate(steps, 1):
        step_id = _effective_step_id(step)
        activity_id = step.get("activity", "")
        activity = activity_map.get(activity_id, activity_id)
        cp_ref = step.get("control_point")
        cp = cp_idx.get(cp_ref) if cp_ref else None

        validate_cmd = _validate_activity_cmd(syml, step_id)
        audit_cmd = _audit_log_cmd(sid, step_id)

        lines += [
            f"### Step {i} — {step_id}",
            "",
            f"**Activity:** {activity}",  # resolved description
            "",
            f"```bash\n{validate_cmd}\n\n{audit_cmd}\n```",
        ]

        if cp:
            classification = cp.get("classification", "")
            cmd = _checkpoint_gate_cmd(sid, cp)
            comment = _halt_comment(classification)
            bash = f"```bash\n{cmd}\n{comment}\n```" if comment else f"```bash\n{cmd}\n```"

            label = {
                "auto": "auto — agent proceeds automatically",
                "needs_approval": "halt and await approval",
                "review": "halt and await review",
                "notify": "notify and continue",
            }.get(classification, classification)

            lines += ["", f"Control point **{cp_ref}** ({label}):", "", bash]

        lines.append("")

    return "\n".join(lines)
