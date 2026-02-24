"""`supv show` — display full skill details."""

from __future__ import annotations

import sys

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from supervisory_procedures.core.registry import SkillRegistry
from supervisory_procedures.core.access_control import SkillNotFoundError

console = Console()
err_console = Console(stderr=True)


@click.command()
@click.argument("skill_id")
@click.option(
    "--registry",
    default=None,
    type=click.Path(exists=True, file_okay=False),
    help="Override default registry path.",
)
@click.option(
    "--raw",
    is_flag=True,
    default=False,
    help="Print raw YAML without formatting.",
)
def show(skill_id: str, registry: str | None, raw: bool) -> None:
    """Display full details for a skill.

    SKILL_ID should be in the form <business_area>/<skill-name>,
    e.g. retail_banking/loan-application-processing
    """
    reg = SkillRegistry(registry_path=registry)

    try:
        skill_data = reg.get_skill(skill_id)
    except SkillNotFoundError:
        err_console.print(f"[red]Skill '{skill_id}' not found in registry.[/red]")
        sys.exit(1)

    if raw:
        click.echo(yaml.dump(skill_data, sort_keys=False, allow_unicode=True))
        return

    _render_skill(skill_data)


_CLASSIFICATION_COLOUR = {
    "vetoed": "bold red",
    "needs_approval": "red",
    "review": "yellow",
    "notify": "cyan",
    "auto": "green",
}

_RISK_COLOUR = {"low": "green", "medium": "yellow", "high": "red", "critical": "bold red"}
_STATUS_COLOUR = {"approved": "green", "draft": "yellow", "deprecated": "dim"}


def _render_skill(data: dict) -> None:
    meta = data.get("metadata", {})
    ctx = data.get("context", {})
    scope = data.get("scope", {})
    constraints = data.get("constraints", {})
    control_points = data.get("control_points", [])
    workflow_steps = data.get("workflow", {}).get("steps", [])

    status = meta.get("status", "")
    status_colour = _STATUS_COLOUR.get(status, "white")

    # Header
    console.print()
    console.print(
        Panel(
            Text.from_markup(
                f"[bold]{meta.get('name', '')}[/bold]  "
                f"v{meta.get('version', '')}  "
                f"[{status_colour}][{status}][/{status_colour}]\n"
                f"[dim]{meta.get('id', '')}[/dim]"
            ),
            title="Agent Skill",
            border_style="blue",
        )
    )

    # Supervisor + dates
    sup = meta.get("supervisor", {})
    console.print(f"[bold]Supervisor:[/bold] {sup.get('name', '')} ({sup.get('role', '')}) — {sup.get('email', '')}")
    console.print(f"[bold]Created:[/bold] {meta.get('created_at', '')}")
    if meta.get("approved_at"):
        console.print(f"[bold]Approved:[/bold] {meta['approved_at']} by {meta.get('approved_by', '')}")
    console.print(f"[bold]Authorised agents:[/bold] {', '.join(meta.get('authorised_agents', []))}")

    # Context
    console.print()
    console.rule("[bold]Context[/bold]")
    risk = ctx.get("risk_classification", "")
    risk_colour = _RISK_COLOUR.get(risk, "white")
    console.print(f"[bold]Risk:[/bold] [{risk_colour}]{risk}[/{risk_colour}]")
    console.print(f"[bold]Description:[/bold] {ctx.get('description', '').strip()}")
    console.print(f"[bold]Rationale:[/bold] {ctx.get('business_rationale', '').strip()}")
    regs = ctx.get("applicable_regulations", [])
    if regs:
        console.print("[bold]Regulations:[/bold]")
        for r in regs:
            console.print(f"  • {r}")

    # Scope
    console.print()
    console.rule("[bold]Approved Activities[/bold]")
    for activity in scope.get("approved_activities", []):
        console.print(f"  [green]✓[/green] [cyan]{activity['id']}[/cyan]  {activity['description']}")

    # Constraints
    console.print()
    console.rule("[bold]Constraints[/bold]")
    console.print("[bold]Procedural requirements:[/bold]")
    for req in constraints.get("procedural_requirements", []):
        console.print(f"  [blue]→[/blue] {req}")
    console.print("[bold]Unacceptable actions:[/bold]")
    for action in constraints.get("unacceptable_actions", []):
        console.print(f"  [red]✗[/red] {action}")

    # Control points
    if control_points:
        console.print()
        console.rule("[bold]Control Points[/bold]")
        for cp in control_points:
            classification = cp.get("classification", "")
            colour = _CLASSIFICATION_COLOUR.get(classification, "white")
            sla = f"  SLA: {cp['sla_hours']}h" if cp.get("sla_hours") else ""
            console.print(
                f"  [bold {colour}]{cp.get('id', '')}[/bold {colour}]"
                f"  [{colour}][{classification}][/{colour}]{sla}"
            )
            console.print(f"    {cp.get('description', '').strip()}")
            if cp.get("trigger_condition"):
                console.print(f"    Trigger: {cp['trigger_condition']}")
            if cp.get("who_reviews"):
                console.print(f"    Reviews: {cp['who_reviews']}")
            if cp.get("escalation_contact"):
                console.print(f"    Escalate to: {cp['escalation_contact']}")

    # Workflow
    if workflow_steps:
        console.print()
        console.rule("[bold]Workflow[/bold]")
        for i, step in enumerate(workflow_steps, 1):
            cp_ref = f"  → {step['control_point']}" if step.get("control_point") else ""
            console.print(f"  [dim]{i:2}.[/dim] [cyan]{step.get('id', '')}[/cyan]{cp_ref}")
            console.print(f"       activity: {step.get('activity', '')}")

    console.print()
