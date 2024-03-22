"""SiliconAI ACTS CLI."""

from pathlib import Path
from sys import argv
from typing import Annotated

import typer

from siliconai_acts import __version__
from siliconai_acts.cli.config import (
    GlobalConfiguration,
    TyperState,
    config_missing,
)
from siliconai_acts.cli.logging import setup_logger

application = typer.Typer()
state = TyperState()


def version_callback(value: bool) -> None:
    """Version callback."""
    if value:
        typer.echo(f"SiliconAI ACTS, version {__version__}")
        raise typer.Exit()


@application.callback()
def main(
    ctx: typer.Context,
    config: Annotated[
        Path,
        typer.Option(
            "-g",
            "--global-config",
            envvar="SILICONAI_ACTS_GLOBAL_CONFIG",
            help="Global configuration file.",
        ),
    ] = Path(
        "config.toml",
    ),
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Run with debug printouts.",
        ),
    ] = False,
    version: Annotated[  # noqa: ARG001
        bool,
        typer.Option(
            "--version",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """SiliconAI ACTS CLI app."""
    if ctx.invoked_subcommand != "config" and not config.exists():  # pragma: no cover
        if "--help" in argv:
            return
        config_missing(config)

    state.config_file = config
    state.debug = debug


@application.command()
def config(
    generate: Annotated[
        bool,
        typer.Option("--generate", help="Generate empty configuration."),
    ] = False,
) -> None:
    """Print or generate configuration."""
    if generate:
        GlobalConfiguration.generate_empty(state.config_file)
    else:
        GlobalConfiguration.load(state, full_information=False)


@application.command()
def generate() -> None:
    """Generate particles."""
    global_config = GlobalConfiguration.load(state)
    logger = setup_logger(global_config, "generate")

    logger.info("Hello World!")
