"""SiliconAI ACTS CLI."""

from pathlib import Path
from sys import argv
from typing import Annotated

import typer

from siliconai_acts import __version__
from siliconai_acts.cli.config import (
    Configuration,
    GlobalConfiguration,
    TyperState,
    config_missing,
)
from siliconai_acts.cli.logging import setup_logger
from siliconai_acts.common.enums import ProductionStep
from siliconai_acts.plotting.common import setup_style

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
def generate(
    config_file: Annotated[
        Path,
        typer.Option(
            "-c",
            "--config",
            envvar="SILICONAI_ACTS_CONFIG",
            help="Task configuration file.",
        ),
    ],
    diagnostics: Annotated[
        bool,
        typer.Option(
            "-d",
            "--diagnostics",
            help="Prepare diagnostics plots.",
        ),
    ] = False,
) -> None:
    """Generate particles."""
    global_config = GlobalConfiguration.load(state)
    config = Configuration(config_file, global_config)
    logger = setup_logger(global_config, "generate")

    from siliconai_acts.scheduling.generation import run_generation

    run_generation(
        logger,
        config.seed,
        config.process,
        config.output_path,
        config.events,
    )

    if diagnostics:
        setup_style()

        from siliconai_acts.plotting.diagnostics import plot_particles

        plot_particles(config, ProductionStep.Generation)


@application.command()
def simulate(
    config_file: Annotated[
        Path,
        typer.Option(
            "-c",
            "--config",
            envvar="SILICONAI_ACTS_CONFIG",
            help="Task configuration file.",
        ),
    ],
    diagnostics: Annotated[
        bool,
        typer.Option(
            "-d",
            "--diagnostics",
            help="Prepare diagnostics plots.",
        ),
    ] = False,
) -> None:
    """Generate particles."""
    global_config = GlobalConfiguration.load(state)
    config = Configuration(config_file, global_config)
    logger = setup_logger(global_config, "simulate")

    from siliconai_acts.scheduling.simulation import run_simulation_multiprocess

    run_simulation_multiprocess(
        logger,
        config.seed,
        config.simulation,
        config.events,
        global_config.threads,
        config.output_path,
    )

    if diagnostics:
        setup_style()

        from siliconai_acts.plotting.diagnostics import plot_particles

        plot_particles(config, ProductionStep.Simulation)


@application.command()
def diagnostics(
    config_file: Annotated[
        Path,
        typer.Option(
            "-c",
            "--config",
            envvar="SILICONAI_ACTS_CONFIG",
            help="Task configuration file.",
        ),
    ],
) -> None:
    """Run diagnostics and make plots."""
    global_config = GlobalConfiguration.load(state)
    config = Configuration(config_file, global_config)
    logger = setup_logger(global_config, "diagnostics")

    logger.info("Creating diagnostics plots")

    setup_style()

    from siliconai_acts.plotting.diagnostics import plot_particles

    plot_particles(config, ProductionStep.Generation)
    plot_particles(config, ProductionStep.Simulation)
