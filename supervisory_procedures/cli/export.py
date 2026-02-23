"""`supv export` — export a skill to NeMo Guardrails or generic JSON."""

from __future__ import annotations

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
    "--format",
    "-f",
    "fmt",
    required=True,
    type=click.Choice(["nemo", "json"]),
    help="Export format: nemo (NeMo Guardrails) or json (generic JSON).",
)
@click.option(
    "--output-dir",
    "-o",
    default=None,
    type=click.Path(file_okay=False),
    help="Directory to write exported files (nemo only). Defaults to stdout for json.",
)
@click.option(
    "--registry",
    default=None,
    type=click.Path(exists=True, file_okay=False),
    help="Override default registry path.",
)
def export(skill_id: str, fmt: str, output_dir: str | None, registry: str | None) -> None:
    """Export a skill definition to an agent framework format.

    SKILL_ID should be in the form <business_area>/<skill-name>.

    Formats:
      nemo  — NeMo Guardrails config.yml + skill_rails.co Colang stubs
      json  — Platform-agnostic JSON envelope
    """
    reg = SkillRegistry(registry_path=registry)

    try:
        skill_data = reg.get_skill(skill_id)
    except SkillNotFoundError:
        err_console.print(f"[red]Skill '{skill_id}' not found in registry.[/red]")
        sys.exit(1)

    if fmt == "nemo":
        from supervisory_procedures.adapters.nemo_guardrails import NeMoGuardrailsAdapter
        adapter = NeMoGuardrailsAdapter()
        result = adapter.export(skill_data)

        if output_dir:
            from pathlib import Path
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            (out / "config.yml").write_text(result["config_yml"])
            (out / "skill_rails.co").write_text(result["skill_rails_co"])
            console.print(f"[green]✓[/green] Exported to {out}/config.yml and {out}/skill_rails.co")
        else:
            console.rule("config.yml")
            click.echo(result["config_yml"])
            console.rule("skill_rails.co")
            click.echo(result["skill_rails_co"])

    elif fmt == "json":
        from supervisory_procedures.adapters.generic_json import GenericJsonAdapter
        adapter = GenericJsonAdapter()
        result = adapter.export(skill_data)
        click.echo(result)
