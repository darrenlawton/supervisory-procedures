"""`supv export` — export a skill to generic JSON."""

from __future__ import annotations

import json
import sys

import click
from rich.console import Console

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
def export(skill_id: str, registry: str | None) -> None:
    """Export a skill definition as a platform-agnostic JSON envelope.

    SKILL_ID should be in the form <business_area>/<skill-name>.
    """
    reg = SkillRegistry(registry_path=registry)

    try:
        skill_data = reg.get_skill(skill_id)
    except SkillNotFoundError:
        err_console.print(f"[red]Skill '{skill_id}' not found in registry.[/red]")
        sys.exit(1)

    envelope = {
        "export_format": "supervisory-skill-v1",
        "skill_id": skill_data.get("metadata", {}).get("id", "unknown"),
        "skill": skill_data,
    }
    click.echo(json.dumps(envelope, indent=2, ensure_ascii=False, default=str))
