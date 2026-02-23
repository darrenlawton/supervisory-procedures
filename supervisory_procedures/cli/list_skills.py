"""`supv list` — list skills in the registry."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich import box

from supervisory_procedures.core.registry import SkillRegistry

console = Console()

_STATUS_COLOUR = {
    "approved": "green",
    "draft": "yellow",
    "deprecated": "dim",
}


@click.command()
@click.option(
    "--business-area",
    "-b",
    default=None,
    help="Filter by business area slug, e.g. retail_banking",
)
@click.option(
    "--status",
    "-s",
    default=None,
    type=click.Choice(["draft", "approved", "deprecated"]),
    help="Filter by skill status.",
)
@click.option(
    "--registry",
    default=None,
    type=click.Path(exists=True, file_okay=False),
    help="Override default registry path.",
)
def list_skills(business_area: str | None, status: str | None, registry: str | None) -> None:
    """List skills in the registry.

    Displays skill ID, name, status, risk classification, and version.
    """
    reg = SkillRegistry(registry_path=registry)
    skills = reg.list_skills(business_area=business_area, status=status)

    if not skills:
        msg = "No skills found"
        if business_area:
            msg += f" in business area '{business_area}'"
        if status:
            msg += f" with status '{status}'"
        console.print(f"[yellow]{msg}[/yellow]")
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Status", width=10)
    table.add_column("Risk", width=8)
    table.add_column("Version", width=8)
    table.add_column("Supervisor")

    for meta in skills:
        skill_status = meta.get("status", "")
        colour = _STATUS_COLOUR.get(skill_status, "white")
        supervisor = meta.get("supervisor", {})
        table.add_row(
            meta.get("id", ""),
            meta.get("name", ""),
            f"[{colour}]{skill_status}[/{colour}]",
            _risk_cell(meta.get("risk_classification", "")),
            meta.get("version", ""),
            supervisor.get("name", ""),
        )

    console.print(table)
    console.print(f"[dim]{len(skills)} skill(s)[/dim]")


def _risk_cell(risk: str) -> str:
    colours = {"low": "green", "medium": "yellow", "high": "red", "critical": "bold red"}
    colour = colours.get(risk, "white")
    return f"[{colour}]{risk}[/{colour}]" if risk else ""
