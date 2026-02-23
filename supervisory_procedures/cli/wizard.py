"""`supv new` — guided wizard for authoring a new skill YAML."""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

import click
import questionary
import yaml
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel

console = Console()
err_console = Console(stderr=True)

_DEFAULT_REGISTRY = Path(__file__).parent.parent.parent / "registry"

_RISK_LEVELS = ["low", "medium", "high", "critical"]
_VETO_ACTIONS = ["halt_and_escalate", "halt_and_notify", "halt_and_refuse"]
_CHECKPOINT_TYPES = ["review", "approve", "notify", "halt"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slug(text: str) -> str:
    """Convert free text to a kebab-case slug."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text


def _collect_list(prompt: str, min_items: int = 1) -> list[str]:
    """Prompt the user to enter items one at a time until they enter an empty line."""
    items: list[str] = []
    console.print(f"[bold]{prompt}[/bold] (enter each item, blank line when done)")
    while True:
        val = questionary.text("  →").ask()
        if val is None:
            sys.exit(0)  # Ctrl-C
        val = val.strip()
        if not val:
            if len(items) < min_items:
                console.print(f"  [yellow]Please enter at least {min_items} item(s).[/yellow]")
                continue
            break
        items.append(val)
    return items


def _ask(question: str, **kwargs: Any) -> str:
    val = questionary.text(question, **kwargs).ask()
    if val is None:
        sys.exit(0)
    return val.strip()


def _ask_select(question: str, choices: list[str]) -> str:
    val = questionary.select(question, choices=choices).ask()
    if val is None:
        sys.exit(0)
    return val


def _ask_confirm(question: str, default: bool = False) -> bool:
    val = questionary.confirm(question, default=default).ask()
    if val is None:
        sys.exit(0)
    return val


# ---------------------------------------------------------------------------
# Wizard steps
# ---------------------------------------------------------------------------

def _step_business_area(registry_path: Path) -> str:
    """Step 1 — select or create a business area."""
    console.rule("[bold cyan]Step 1 / 10 — Business Area[/bold cyan]")
    existing = sorted(
        d.name for d in registry_path.iterdir() if d.is_dir() and not d.name.startswith(".")
    ) if registry_path.exists() else []

    choices = existing + ["+ Create new business area"]
    selected = _ask_select("Select business area:", choices)

    if selected == "+ Create new business area":
        name = _ask("New business area name (e.g. commercial_lending):")
        slug_name = re.sub(r"[^a-z0-9_]", "_", name.lower())
        console.print(f"  → Will create: [cyan]{slug_name}[/cyan]")
        return slug_name
    return selected


def _step_name_version(business_area: str) -> tuple[str, str, str, str]:
    """Step 2 — skill name, version, id."""
    console.rule("[bold cyan]Step 2 / 10 — Skill Name & Version[/bold cyan]")
    name = _ask("Skill name (display name):")
    version = _ask("Version:", default="1.0.0")
    suggested_id = f"{business_area}/{_slug(name)}"
    console.print(f"  → Suggested ID: [cyan]{suggested_id}[/cyan]")
    if not _ask_confirm("Use this ID?", default=True):
        custom_id = _ask("Enter custom ID (format: business_area/kebab-name):")
        suggested_id = custom_id
    slug_name = suggested_id.split("/", 1)[-1] if "/" in suggested_id else _slug(name)
    return name, version, suggested_id, slug_name


def _step_supervisor() -> dict[str, str]:
    """Step 3 — supervisor details."""
    console.rule("[bold cyan]Step 3 / 10 — Supervisor Details[/bold cyan]")
    return {
        "name": _ask("Supervisor full name:"),
        "email": _ask("Supervisor email:"),
        "role": _ask("Supervisor role/title:"),
    }


def _step_context() -> dict[str, Any]:
    """Step 4 — context block."""
    console.rule("[bold cyan]Step 4 / 10 — Context[/bold cyan]")
    description = _ask("Description (what business activity does this skill govern?):")
    rationale = _ask("Business rationale (why is AI appropriate here?):")

    regulations: list[str] = []
    console.print("Applicable regulations (e.g. FCA CONC 5.2) — blank line when done:")
    while True:
        reg = questionary.text("  →").ask()
        if reg is None:
            sys.exit(0)
        reg = reg.strip()
        if not reg:
            break
        regulations.append(reg)

    risk = _ask_select("Risk classification:", _RISK_LEVELS)
    return {
        "description": description,
        "business_rationale": rationale,
        "applicable_regulations": regulations,
        "risk_classification": risk,
    }


def _step_scope() -> dict[str, Any]:
    """Step 5 — approved activities."""
    console.rule("[bold cyan]Step 5 / 10 — Scope (Approved Activities)[/bold cyan]")
    activities = _collect_list("Approved activities — what the agent MAY do:", min_items=1)
    return {"approved_activities": activities}


def _step_constraints() -> dict[str, Any]:
    """Step 6 — procedural requirements and unacceptable actions."""
    console.rule("[bold cyan]Step 6 / 10 — Constraints[/bold cyan]")
    requirements = _collect_list("Procedural requirements — steps the agent MUST follow:", min_items=1)
    unacceptable = _collect_list("Unacceptable actions — what the agent must NEVER do:", min_items=1)
    return {
        "procedural_requirements": requirements,
        "unacceptable_actions": unacceptable,
    }


def _step_veto_triggers() -> list[dict[str, Any]]:
    """Step 7 — hard veto triggers."""
    console.rule("[bold cyan]Step 7 / 10 — Hard Veto Triggers[/bold cyan]")
    console.print("Add at least one hard veto trigger — conditions that immediately halt the agent.")
    triggers: list[dict[str, Any]] = []

    while True:
        console.print(f"\n  [bold]Veto trigger #{len(triggers) + 1}[/bold]")
        veto_id = _ask("  ID (slug, e.g. sanctions-hit):")
        description = _ask("  Description (plain English condition):")
        condition_hint = _ask("  Condition hint for developers (optional — press Enter to skip):")
        action = _ask_select("  Action:", _VETO_ACTIONS)
        escalation = _ask("  Escalation contact (optional — press Enter to skip):")

        trigger: dict[str, Any] = {
            "id": _slug(veto_id) if veto_id else f"veto-{len(triggers) + 1}",
            "description": description,
            "action": action,
        }
        if condition_hint:
            trigger["condition_hint"] = condition_hint
        if escalation:
            trigger["escalation_contact"] = escalation

        triggers.append(trigger)

        if not _ask_confirm("\nAdd another veto trigger?", default=False):
            break

    return triggers


def _step_workflow_checkpoints() -> list[dict[str, Any]]:
    """Step 8 — workflow checkpoints."""
    console.rule("[bold cyan]Step 8 / 10 — Workflow Checkpoints[/bold cyan]")
    console.print("Define named stages in the normal workflow that require oversight.")
    checkpoints: list[dict[str, Any]] = []

    if not _ask_confirm("Add workflow checkpoints?", default=True):
        return checkpoints

    while True:
        console.print(f"\n  [bold]Workflow checkpoint #{len(checkpoints) + 1}[/bold]")
        cp_id = _ask("  ID (slug):")
        cp_name = _ask("  Name:")
        cp_desc = _ask("  Description:")
        cp_type = _ask_select("  Checkpoint type:", _CHECKPOINT_TYPES)
        required = _ask_confirm("  Required?", default=True)
        who = _ask("  Who reviews/approves?:")
        sla_str = _ask("  SLA in hours (optional — press Enter to skip):")
        sla = int(sla_str) if sla_str.isdigit() else None

        cp: dict[str, Any] = {
            "id": _slug(cp_id) if cp_id else f"checkpoint-{len(checkpoints) + 1}",
            "name": cp_name,
            "description": cp_desc,
            "checkpoint_type": cp_type,
            "required": required,
            "who_reviews": who,
        }
        if sla:
            cp["sla_hours"] = sla

        checkpoints.append(cp)

        if not _ask_confirm("\nAdd another workflow checkpoint?", default=False):
            break

    return checkpoints


def _step_condition_checkpoints() -> list[dict[str, Any]]:
    """Step 9 — condition-triggered checkpoints."""
    console.rule("[bold cyan]Step 9 / 10 — Condition-Triggered Checkpoints[/bold cyan]")
    console.print("Define checkpoints triggered by deviations or anomalies.")
    checkpoints: list[dict[str, Any]] = []

    if not _ask_confirm("Add condition-triggered checkpoints?", default=False):
        return checkpoints

    while True:
        console.print(f"\n  [bold]Condition checkpoint #{len(checkpoints) + 1}[/bold]")
        cp_id = _ask("  ID (slug):")
        cp_name = _ask("  Name:")
        trigger = _ask("  Trigger condition (plain English):")
        cp_desc = _ask("  Description (what happens at this checkpoint):")
        cp_type = _ask_select("  Checkpoint type:", _CHECKPOINT_TYPES)
        who = _ask("  Who reviews/approves?:")
        sla_str = _ask("  SLA in hours (optional — press Enter to skip):")
        sla = int(sla_str) if sla_str.isdigit() else None

        cp: dict[str, Any] = {
            "id": _slug(cp_id) if cp_id else f"cond-checkpoint-{len(checkpoints) + 1}",
            "name": cp_name,
            "trigger_condition": trigger,
            "description": cp_desc,
            "checkpoint_type": cp_type,
            "who_reviews": who,
        }
        if sla:
            cp["sla_hours"] = sla

        checkpoints.append(cp)

        if not _ask_confirm("\nAdd another condition-triggered checkpoint?", default=False):
            break

    return checkpoints


def _step_agents_and_save(
    skill_data: dict[str, Any],
    registry_path: Path,
    skill_slug: str,
    business_area: str,
) -> None:
    """Step 10 — authorised agents, YAML preview, save."""
    console.rule("[bold cyan]Step 10 / 10 — Authorised Agents & Save[/bold cyan]")
    console.print(
        "Enter the agent IDs authorised to load this skill.\n"
        "Use format [cyan]<function>-agent-<environment>[/cyan], e.g. loan-processor-agent-prod\n"
        "Enter [yellow]*[/yellow] to allow all agents (not recommended)."
    )
    agents = _collect_list("Authorised agent IDs:", min_items=1)
    if "*" in agents:
        console.print("[yellow]⚠  Warning: wildcard '*' permits all agents. Consider restricting.[/yellow]")

    skill_data["metadata"]["authorised_agents"] = agents

    # Preview
    console.rule("[bold]YAML Preview[/bold]")
    yaml_str = yaml.dump(skill_data, sort_keys=False, allow_unicode=True, default_flow_style=False)
    console.print(Syntax(yaml_str, "yaml", theme="monokai", line_numbers=True))

    if not _ask_confirm("\nSave this skill?", default=True):
        console.print("[yellow]Skill not saved.[/yellow]")
        return

    # Determine output path
    business_dir = registry_path / business_area
    business_dir.mkdir(parents=True, exist_ok=True)
    out_path = business_dir / f"{skill_slug}.yml"

    if out_path.exists():
        if not _ask_confirm(f"File {out_path} already exists. Overwrite?", default=False):
            console.print("[yellow]Skill not saved.[/yellow]")
            return

    out_path.write_text(yaml_str)
    console.print(f"\n[green]✓[/green] Saved to [bold]{out_path}[/bold]")

    # Validate immediately
    from supervisory_procedures.core.validator import validate_skill, ValidationError
    try:
        warnings = validate_skill(out_path)
        console.print("[green]✓[/green] Schema validation passed")
        for w in warnings:
            console.print(f"  [yellow]⚠[/yellow]  {w.message}")
    except ValidationError as exc:
        err_console.print("[red]✗[/red] Schema validation failed — please review and fix:")
        for msg in exc.errors:
            err_console.print(f"  • {msg}")

    # Git instructions
    console.print()
    console.print(Panel(
        f"[bold]Next steps:[/bold]\n\n"
        f"  git add {out_path}\n"
        f"  git commit -m 'feat: add {skill_data['metadata']['id']} skill'\n"
        f"  git push origin <your-branch>\n"
        f"  # Then open a pull request for review",
        title="Git workflow",
        border_style="green",
    ))


# ---------------------------------------------------------------------------
# Main command
# ---------------------------------------------------------------------------

@click.command()
@click.option(
    "--registry",
    default=None,
    type=click.Path(file_okay=False),
    help="Override default registry path.",
)
def new(registry: str | None) -> None:
    """Launch the guided wizard to create a new Agent Skill YAML.

    Walks through 10 steps covering all required schema fields and writes
    a validated YAML file to the registry.
    """
    registry_path = Path(registry) if registry else _DEFAULT_REGISTRY

    console.print()
    console.print(Panel(
        "[bold]Supervisory Procedures — New Skill Wizard[/bold]\n\n"
        "This wizard will guide you through creating an Agent Skill definition.\n"
        "Press [cyan]Enter[/cyan] to accept defaults, [red]Ctrl-C[/red] to cancel at any time.",
        border_style="blue",
    ))
    console.print()

    # Step 1
    business_area = _step_business_area(registry_path)

    # Step 2
    name, version, skill_id, skill_slug = _step_name_version(business_area)

    # Step 3
    supervisor = _step_supervisor()

    # Step 4
    context = _step_context()

    # Step 5
    scope = _step_scope()

    # Step 6
    constraints = _step_constraints()

    # Step 7
    veto_triggers = _step_veto_triggers()

    # Step 8
    workflow_checkpoints = _step_workflow_checkpoints()

    # Step 9
    condition_checkpoints = _step_condition_checkpoints()

    # Assemble skill dict
    today = date.today().isoformat()
    skill_data: dict[str, Any] = {
        "metadata": {
            "id": skill_id,
            "name": name,
            "version": version,
            "schema_version": "1.0",
            "business_area": business_area,
            "supervisor": supervisor,
            "status": "draft",
            "created_at": today,
            "approved_at": None,
            "approved_by": None,
        },
        "context": context,
        "scope": scope,
        "constraints": constraints,
        "hard_veto_triggers": veto_triggers,
        "oversight_checkpoints": {
            "workflow_checkpoints": workflow_checkpoints,
            "condition_triggered_checkpoints": condition_checkpoints,
        },
    }

    # Step 10
    _step_agents_and_save(skill_data, registry_path, skill_slug, business_area)
