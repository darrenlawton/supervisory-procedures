"""`supv validate` — validate one skill file or all files in a directory."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich import box

from supervisory_procedures.core.validator import (
    ValidationError,
    validate_directory,
    validate_skill,
)

console = Console()
err_console = Console(stderr=True)


@click.command()
@click.argument("path", default="registry/", type=click.Path(exists=True))
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Treat warnings (e.g. wildcard agents) as errors.",
)
def validate(path: str, strict: bool) -> None:
    """Validate skill YAML file(s) against the JSON Schema.

    PATH may be a single .yml file or a directory (searched recursively).
    Exits with code 1 if any skill fails validation.
    """
    target = Path(path)

    if target.is_file():
        _validate_single(target, strict)
    else:
        _validate_directory(target, strict)


def _validate_single(path: Path, strict: bool) -> None:
    try:
        warnings = validate_skill(path, strict=strict)
        console.print(f"[green]✓[/green] {path} — valid")
        for w in warnings:
            console.print(f"  [yellow]⚠[/yellow]  {w.message}")
    except ValidationError as exc:
        err_console.print(f"[red]✗[/red] {path} — INVALID")
        for msg in exc.errors:
            err_console.print(f"  [red]•[/red] {msg}")
        sys.exit(1)
    except ValueError as exc:
        err_console.print(f"[red]✗[/red] {path} — {exc}")
        sys.exit(1)


def _validate_directory(directory: Path, strict: bool) -> None:
    successes, failures = validate_directory(directory, strict=strict)

    if not successes and not failures:
        console.print(f"[yellow]No .yml files found under {directory}[/yellow]")
        return

    # Summary table
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Status", width=6)
    table.add_column("File")
    table.add_column("Warnings")

    for skill_path, warnings in successes:
        warn_text = str(len(warnings)) if warnings else ""
        table.add_row("[green]✓[/green]", str(skill_path), warn_text)

    for error in failures:
        table.add_row("[red]✗[/red]", str(error.path), "")

    console.print(table)

    # Print detailed warnings
    for skill_path, warnings in successes:
        for w in warnings:
            console.print(f"  [yellow]⚠[/yellow]  {skill_path}: {w.message}")

    # Print detailed errors to stderr
    if failures:
        err_console.print()
        for error in failures:
            err_console.print(f"[red]INVALID[/red] {error.path}:")
            for msg in error.errors:
                err_console.print(f"  • {msg}")

    total = len(successes) + len(failures)
    console.print(
        f"\n[bold]{len(successes)}/{total}[/bold] skills passed validation"
        + (" (strict mode)" if strict else "")
    )

    if failures:
        sys.exit(1)
