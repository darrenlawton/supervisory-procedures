"""`supv render` — generate SKILL.md from skill.yml."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console

from supervisory_procedures.core.registry import SkillRegistry
from supervisory_procedures.core.access_control import SkillNotFoundError
from supervisory_procedures.core.renderer import render_skill_md

console = Console()
err_console = Console(stderr=True)

_DEFAULT_REGISTRY = Path(__file__).parent.parent.parent / "registry"


@click.command()
@click.argument("skill_id")
@click.option(
    "--registry",
    default=None,
    type=click.Path(exists=True, file_okay=False),
    help="Override default registry path.",
)
@click.option(
    "--stdout",
    is_flag=True,
    default=False,
    help="Print generated SKILL.md to stdout instead of writing to disk.",
)
def render(skill_id: str, registry: str | None, stdout: bool) -> None:
    """Generate SKILL.md from skill.yml for a skill.

    SKILL_ID should be in the form <business_area>/<skill-name>.

    The generated file is written to the skill's directory alongside skill.yml.
    SKILL.md is derived entirely from skill.yml — never edit it by hand.
    """
    registry_path = Path(registry) if registry else _DEFAULT_REGISTRY
    reg = SkillRegistry(registry_path=registry_path)

    try:
        skill_data = reg.get_skill(skill_id)
    except SkillNotFoundError:
        err_console.print(f"[red]Skill '{skill_id}' not found in registry.[/red]")
        sys.exit(1)

    content = render_skill_md(skill_data)

    if stdout:
        click.echo(content, nl=False)
        return

    skill_dir = Path(skill_data["_skill_dir"])
    out_path = skill_dir / "SKILL.md"
    out_path.write_text(content)
    console.print(f"[green]✓[/green] Rendered [bold]{out_path}[/bold]")
