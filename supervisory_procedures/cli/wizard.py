"""`supv new` — guided wizard for authoring a new skill YAML."""

from __future__ import annotations

import re
import sys
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
_CLASSIFICATIONS = ["auto", "notify", "review", "needs_approval", "vetoed"]


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


def _q(fn: Any, *args: Any, **kwargs: Any) -> Any:
    """Call a questionary function; exit cleanly on Ctrl-C (None result)."""
    val = fn(*args, **kwargs).ask()
    if val is None:
        sys.exit(0)
    return val


def _ask(question: str, **kwargs: Any) -> str:
    return _q(questionary.text, question, **kwargs).strip()


def _ask_select(question: str, choices: list[str]) -> str:
    return _q(questionary.select, question, choices=choices)


def _ask_confirm(question: str, default: bool = False) -> bool:
    return _q(questionary.confirm, question, default=default)


def _collect_list(prompt: str, min_items: int = 1) -> list[str]:
    """Prompt the user to enter items one at a time until they enter a blank line."""
    items: list[str] = []
    console.print(f"[bold]{prompt}[/bold] (enter each item, blank line when done)")
    while True:
        val = _q(questionary.text, "  →").strip()
        if not val:
            if len(items) < min_items:
                console.print(f"  [yellow]Please enter at least {min_items} item(s).[/yellow]")
                continue
            break
        items.append(val)
    return items


# ---------------------------------------------------------------------------
# Wizard steps
# ---------------------------------------------------------------------------

def _step_business_area(registry_path: Path) -> str:
    """Step 1 / 8 — select or create a business area."""
    console.rule("[bold cyan]Step 1 / 8 — Business Area[/bold cyan]")
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
    """Step 2 / 8 — skill name, version, id."""
    console.rule("[bold cyan]Step 2 / 8 — Skill Name & Version[/bold cyan]")
    name = _ask("Skill name (display name):")
    version = _ask("Version:", default="1.0.0")
    suggested_id = f"{business_area}/{_slug(name)}"
    console.print(f"  → Suggested ID: [cyan]{suggested_id}[/cyan]")
    if not _ask_confirm("Use this ID?", default=True):
        suggested_id = _ask("Enter custom ID (format: business_area/kebab-name):")
    slug_name = suggested_id.split("/", 1)[-1] if "/" in suggested_id else _slug(name)
    return name, version, suggested_id, slug_name


def _step_supervisor() -> dict[str, str]:
    """Step 3 / 8 — supervisor details."""
    console.rule("[bold cyan]Step 3 / 8 — Supervisor Details[/bold cyan]")
    return {
        "name": _ask("Supervisor full name:"),
        "email": _ask("Supervisor email:"),
        "role": _ask("Supervisor role/title:"),
    }


def _step_context() -> dict[str, Any]:
    """Step 4 / 8 — context block."""
    console.rule("[bold cyan]Step 4 / 8 — Context[/bold cyan]")
    description = _ask("Description (what business activity does this skill govern?):")
    rationale = _ask("Business rationale (why is AI appropriate here?):")
    regulations = _collect_list("Applicable regulations (e.g. FCA CONC 5.2):", min_items=0)
    risk = _ask_select("Risk classification:", _RISK_LEVELS)
    return {
        "description": description,
        "business_rationale": rationale,
        "applicable_regulations": regulations,
        "risk_classification": risk,
    }


def _step_approved_activities() -> list[dict[str, str]]:
    """Step 5 / 8 — approved activities (exhaustive allowlist)."""
    console.rule("[bold cyan]Step 5 / 8 — Approved Activities[/bold cyan]")
    console.print(
        "Enter each approved activity. You'll be prompted for a description then an ID slug.\n"
        "[dim]Audit logging is automatic — do not add an audit-log activity.[/dim]"
    )
    activities: list[dict[str, str]] = []
    while True:
        console.print(f"\n  [bold]Activity #{len(activities) + 1}[/bold] (blank description to finish)")
        desc = _ask("  Description:").strip()
        if not desc:
            if len(activities) < 1:
                console.print("  [yellow]Please enter at least 1 activity.[/yellow]")
                continue
            break
        suggested_id = _slug(desc)[:40]
        act_id = _ask(f"  ID (slug):", default=suggested_id).strip()
        activities.append({"id": act_id or suggested_id, "description": desc})
    return activities


def _step_constraints() -> dict[str, Any]:
    """Step 6 / 8 — procedural requirements and unacceptable actions."""
    console.rule("[bold cyan]Step 6 / 8 — Constraints[/bold cyan]")
    console.print(
        "[dim]Procedural requirements are cross-cutting behavioural principles only.\n"
        "Do not repeat constraints already expressed by workflow ordering, control points,\n"
        "or unacceptable_actions.[/dim]"
    )
    requirements = _collect_list("Procedural requirements:", min_items=0)
    unacceptable = _collect_list("Unacceptable actions — what the agent must NEVER do:", min_items=1)
    return {
        "procedural_requirements": requirements,
        "unacceptable_actions": unacceptable,
    }


def _step_control_points() -> list[dict[str, Any]]:
    """Step 7 / 8 — control points (unified veto + oversight model)."""
    console.rule("[bold cyan]Step 7 / 8 — Control Points[/bold cyan]")
    console.print(
        "Define control points — moments where the agent must pause, notify, or halt.\n"
        "Classifications: [bold]vetoed[/bold] = halt unconditionally, "
        "[bold]needs_approval[/bold] = explicit sign-off required, "
        "[bold]review[/bold] = human reviews before proceeding, "
        "[bold]notify[/bold] = human informed but not blocked, "
        "[bold]auto[/bold] = agent proceeds without human involvement.\n\n"
        "Activation: [bold]conditional[/bold] = fires when a trigger condition is detected "
        "(at any workflow step), [bold]step[/bold] = fires when referenced by a specific workflow step."
    )
    control_points: list[dict[str, Any]] = []

    while True:
        console.print(f"\n  [bold]Control point #{len(control_points) + 1}[/bold]")
        cp_id = _slug(_ask("  ID (slug, e.g. sanctions-match):"))
        cp_desc = _ask("  Description:")
        classification = _ask_select("  Classification:", _CLASSIFICATIONS)
        activation = _ask_select("  Activation:", ["conditional", "step"])

        cp: dict[str, Any] = {
            "id": cp_id or f"cp-{len(control_points) + 1}",
            "description": cp_desc,
            "classification": classification,
            "activation": activation,
        }

        if activation == "conditional":
            trigger = _ask("  Trigger condition — plain English:")
            cp["trigger"] = trigger

        if classification in ("needs_approval", "review", "notify"):
            who = _ask("  Who reviews/approves?:")
            cp["who_reviews"] = who
        elif classification == "vetoed":
            escalation = _ask("  Escalation contact (email or team name):")
            cp["escalation_contact"] = escalation

        sla_str = _ask("  SLA in hours (optional, press Enter to skip):")
        if sla_str.isdigit():
            cp["sla_hours"] = int(sla_str)

        control_points.append(cp)

        if not _ask_confirm("\nAdd another control point?", default=False):
            break

    return control_points


def _step_workflow(approved_activities: list[dict[str, str]]) -> dict[str, Any]:
    """Step 8 / 8 — workflow steps."""
    console.rule("[bold cyan]Step 8 / 8 — Workflow Steps[/bold cyan]")
    console.print(
        "Define the ordered steps the agent will execute.\n"
        "[dim]Step ID defaults to the activity ID if left blank.[/dim]"
    )
    choices = [f"{a['id']}  —  {a['description']}" for a in approved_activities]
    choice_to_id = {c: a["id"] for c, a in zip(choices, approved_activities)}
    steps: list[dict[str, Any]] = []

    while True:
        console.print(f"\n  [bold]Step #{len(steps) + 1}[/bold]")
        selected = _ask_select("  Activity:", choices)
        activity = choice_to_id[selected]
        step_id_input = _ask("  Step ID (optional, press Enter to default to activity ID):").strip()
        cp_ref = _ask("  Control point ID to attach (optional, press Enter to skip):")

        step: dict[str, Any] = {"activity": activity}
        if step_id_input and step_id_input != activity:
            step["id"] = _slug(step_id_input) or step_id_input
        if cp_ref:
            step["control_point"] = cp_ref

        steps.append(step)

        if not _ask_confirm("\nAdd another workflow step?", default=True):
            break

    return {"steps": steps}


def _step_agents_and_save(
    skill_data: dict[str, Any],
    registry_path: Path,
    skill_slug: str,
    business_area: str,
) -> None:
    """Final step — authorised agents, YAML preview, save."""
    console.rule("[bold cyan]Final Step — Authorised Agents & Save[/bold cyan]")
    console.print(
        "Enter the agent IDs authorised to load this skill.\n"
        "Use format [cyan]<function>-agent-<environment>[/cyan], e.g. loan-processor-agent-prod\n"
        "Enter [yellow]*[/yellow] to allow all agents (not recommended)."
    )
    agents = _collect_list("Authorised agent IDs:", min_items=1)
    if "*" in agents:
        console.print("[yellow]Warning: wildcard '*' permits all agents. Consider restricting.[/yellow]")

    skill_data["metadata"]["authorised_agents"] = agents

    # Preview
    console.rule("[bold]YAML Preview[/bold]")
    yaml_str = yaml.dump(skill_data, sort_keys=False, allow_unicode=True, default_flow_style=False)
    console.print(Syntax(yaml_str, "yaml", theme="monokai", line_numbers=True))

    if not _ask_confirm("\nSave this skill?", default=True):
        console.print("[yellow]Skill not saved.[/yellow]")
        return

    # Determine output path (directory-based: business_area/skill-name/skill.yml)
    skill_dir = registry_path / business_area / skill_slug
    skill_dir.mkdir(parents=True, exist_ok=True)
    out_path = skill_dir / "skill.yml"

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
        f"  git add {skill_dir}\n"
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

    Walks through 8 steps covering all required schema fields and writes
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

    business_area = _step_business_area(registry_path)
    name, version, skill_id, skill_slug = _step_name_version(business_area)
    supervisor = _step_supervisor()
    context = _step_context()
    approved_activities = _step_approved_activities()
    constraints = _step_constraints()
    control_points = _step_control_points()
    workflow = _step_workflow(approved_activities)

    skill_data: dict[str, Any] = {
        "metadata": {
            "id": skill_id,
            "name": name,
            "version": version,
            "schema_version": "2.1",
            "business_area": business_area,
            "supervisor": supervisor,
            "status": "draft",
        },
        "context": context,
        "approved_activities": approved_activities,
        "constraints": constraints,
        "control_points": control_points,
        "workflow": workflow,
    }

    _step_agents_and_save(skill_data, registry_path, skill_slug, business_area)
