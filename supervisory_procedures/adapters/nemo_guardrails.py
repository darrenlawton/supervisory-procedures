"""NeMo Guardrails adapter.

Generates two artefacts from a skill definition:
  - config.yml  : system prompt preamble + rail flow names
  - skill_rails.co : Colang subflow stubs for each veto trigger and required checkpoint

Developers fill in the condition logic inside the generated stubs.
"""

from __future__ import annotations

import re
import textwrap
from typing import Any

import yaml

from .base import BaseAdapter


def _colang_id(text: str) -> str:
    """Convert a slug or free text to a valid Colang identifier."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9_]", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


class NeMoGuardrailsAdapter(BaseAdapter):
    """Generate NeMo Guardrails configuration artefacts from a skill definition.

    Returns a dict with two keys:
        "config_yml"      : str — content of config.yml
        "skill_rails_co"  : str — content of the Colang .co file
    """

    def export(self, skill_data: dict[str, Any]) -> dict[str, str]:
        meta = skill_data.get("metadata", {})
        ctx = skill_data.get("context", {})
        scope = skill_data.get("scope", {})
        constraints = skill_data.get("constraints", {})
        veto_triggers = skill_data.get("hard_veto_triggers", [])
        checkpoints = skill_data.get("oversight_checkpoints", {})

        config_yml = self._build_config(meta, ctx, scope, constraints, veto_triggers, checkpoints)
        skill_rails_co = self._build_colang(meta, veto_triggers, checkpoints)

        return {
            "config_yml": config_yml,
            "skill_rails_co": skill_rails_co,
        }

    # ------------------------------------------------------------------
    # config.yml builder
    # ------------------------------------------------------------------

    def _build_config(
        self,
        meta: dict[str, Any],
        ctx: dict[str, Any],
        scope: dict[str, Any],
        constraints: dict[str, Any],
        veto_triggers: list[dict[str, Any]],
        checkpoints: dict[str, Any],
    ) -> str:
        skill_id = meta.get("id", "unknown")
        skill_name = meta.get("name", "Agent Skill")
        risk = ctx.get("risk_classification", "unknown")
        description = ctx.get("description", "").strip()
        rationale = ctx.get("business_rationale", "").strip()

        approved = "\n".join(
            f"      - {a}" for a in scope.get("approved_activities", [])
        )
        requirements = "\n".join(
            f"      - {r}" for r in constraints.get("procedural_requirements", [])
        )
        prohibitions = "\n".join(
            f"      - {a}" for a in constraints.get("unacceptable_actions", [])
        )

        # Rail flow names derived from veto triggers and required checkpoints
        input_rails: list[str] = []
        output_rails: list[str] = []

        for vt in veto_triggers:
            flow_name = f"check {_colang_id(vt['id'])}"
            input_rails.append(flow_name)

        wf_checkpoints = checkpoints.get("workflow_checkpoints", [])
        for cp in wf_checkpoints:
            if cp.get("required"):
                flow_name = f"checkpoint {_colang_id(cp['id'])}"
                output_rails.append(flow_name)

        config: dict[str, Any] = {
            "models": [],
            "instructions": [
                {
                    "type": "general",
                    "content": textwrap.dedent(f"""\
                        You are operating under the '{skill_name}' Agent Skill
                        (ID: {skill_id}, risk: {risk}).

                        BUSINESS CONTEXT:
                        {description}

                        RATIONALE:
                        {rationale}

                        APPROVED ACTIVITIES (you may ONLY do the following):
{approved}

                        PROCEDURAL REQUIREMENTS (you MUST follow these steps):
{requirements}

                        PROHIBITED ACTIONS (you must NEVER do any of the following):
{prohibitions}

                        Any action not listed in approved activities is forbidden.
                        Any hard veto condition immediately halts your operation.
                    """).strip(),
                }
            ],
            "rails": {
                "input": {"flows": input_rails},
                "output": {"flows": output_rails},
            },
        }

        return yaml.dump(config, sort_keys=False, allow_unicode=True, default_flow_style=False)

    # ------------------------------------------------------------------
    # Colang .co file builder
    # ------------------------------------------------------------------

    def _build_colang(
        self,
        meta: dict[str, Any],
        veto_triggers: list[dict[str, Any]],
        checkpoints: dict[str, Any],
    ) -> str:
        skill_id = meta.get("id", "unknown")
        lines: list[str] = [
            f"# Colang rail stubs generated from skill: {skill_id}",
            "# Fill in the condition logic marked with TODO",
            "",
        ]

        # Veto trigger subflows (input rails)
        for vt in veto_triggers:
            flow_id = _colang_id(vt["id"])
            action = vt.get("action", "halt_and_refuse")
            description = vt.get("description", "").strip()
            condition_hint = vt.get("condition_hint", "").strip()
            escalation = vt.get("escalation_contact", "")

            lines += [
                f"# Veto trigger: {vt['id']}",
                f"# {description}",
            ]
            if condition_hint:
                lines.append(f"# Condition hint: {condition_hint}")
            lines += [
                f"flow check {flow_id}",
                f'  # TODO: detect "{vt["id"]}" condition',
                f'  $triggered = False  # replace with real detection logic',
                "",
                f"  if $triggered",
            ]
            if action == "halt_and_escalate":
                lines += [
                    f'    bot say "I need to escalate this matter immediately."',
                ]
                if escalation:
                    lines += [
                        f'    # Notify: {escalation}',
                    ]
            elif action == "halt_and_notify":
                lines += [
                    f'    bot say "I cannot continue and have notified the relevant team."',
                ]
                if escalation:
                    lines += [
                        f'    # Notify: {escalation}',
                    ]
            else:  # halt_and_refuse
                lines += [
                    f'    bot say "I cannot proceed with this request."',
                ]
            lines += [
                f"    stop",
                "",
            ]

        # Required workflow checkpoint subflows (output rails)
        wf_checkpoints = checkpoints.get("workflow_checkpoints", [])
        for cp in wf_checkpoints:
            if not cp.get("required"):
                continue
            cp_id = _colang_id(cp["id"])
            cp_name = cp.get("name", cp["id"])
            cp_type = cp.get("checkpoint_type", "review")
            who = cp.get("who_reviews", "")
            sla = cp.get("sla_hours")

            lines += [
                f"# Workflow checkpoint: {cp['id']} ({cp_type})",
                f"# Reviewer: {who}" + (f" — SLA: {sla}h" if sla else ""),
                f"flow checkpoint {cp_id}",
                f'  # TODO: implement "{cp_name}" checkpoint ({cp_type})',
                f'  # Who reviews: {who}',
            ]
            if cp_type in ("approve", "halt"):
                lines += [
                    f'  $approved = False  # replace with approval check logic',
                    f"  if not $approved",
                    f'    bot say "Awaiting {cp_type} from {who}."',
                    f"    stop",
                ]
            else:
                lines += [
                    f'  # Notify {who} of this checkpoint',
                ]
            lines.append("")

        # Condition-triggered checkpoint stubs (informational comments only)
        ct_checkpoints = checkpoints.get("condition_triggered_checkpoints", [])
        if ct_checkpoints:
            lines += [
                "# -------------------------------------------------------",
                "# Condition-triggered checkpoint stubs",
                "# Wire these into your business logic flows as needed",
                "# -------------------------------------------------------",
                "",
            ]
            for cp in ct_checkpoints:
                cp_id = _colang_id(cp["id"])
                trigger = cp.get("trigger_condition", "").strip()
                who = cp.get("who_reviews", "")
                lines += [
                    f"# Checkpoint: {cp['id']}",
                    f"# Trigger: {trigger}",
                    f"flow handle {cp_id}",
                    f'  # TODO: triggered when: {trigger}',
                    f'  # Escalate to: {who}',
                    f'  bot say "This situation requires review by {who}."',
                    f"  stop",
                    "",
                ]

        return "\n".join(lines)
