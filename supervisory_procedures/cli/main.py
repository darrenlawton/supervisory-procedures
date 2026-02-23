"""supv — Supervisory Procedures CLI entry point."""

from __future__ import annotations

import click

from supervisory_procedures import __version__


@click.group()
@click.version_option(__version__, prog_name="supv")
def cli() -> None:
    """Supervisory Procedures — Skill-as-Code governance platform.

    Manage, validate, and author Agent Skill definitions.
    """


# Import and register sub-commands
from supervisory_procedures.cli.validate import validate  # noqa: E402
from supervisory_procedures.cli.list_skills import list_skills  # noqa: E402
from supervisory_procedures.cli.show import show  # noqa: E402
from supervisory_procedures.cli.wizard import new  # noqa: E402
from supervisory_procedures.cli.export import export  # noqa: E402

cli.add_command(validate)
cli.add_command(list_skills, name="list")
cli.add_command(show)
cli.add_command(new)
cli.add_command(export)
