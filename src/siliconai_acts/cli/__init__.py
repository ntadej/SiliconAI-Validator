"""SiliconAI ACTS CLI."""

from os import environ
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

    environ["NUMEXPR_MAX_THREADS"] = str(config.global_config.threads)

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

    environ["NUMEXPR_MAX_THREADS"] = str(config.global_config.threads)

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

        from siliconai_acts.plotting.diagnostics import plot_hits, plot_particles

        plot_particles(config, ProductionStep.Simulation)
        plot_hits(config)


@application.command()
def reconstruct(
    config_file: Annotated[
        Path,
        typer.Option(
            "-c",
            "--config",
            envvar="SILICONAI_ACTS_CONFIG",
            help="Task configuration file.",
        ),
    ],
    hits_type: Annotated[
        str,
        typer.Option(
            "-t",
            "--type",
            help="Input hits type.",
        ),
    ] = "original",
    diagnostics: Annotated[
        bool,
        typer.Option(
            "-d",
            "--diagnostics",
            help="Prepare diagnostics plots.",
        ),
    ] = False,
    digi_only: Annotated[
        bool,
        typer.Option(
            "--digi-only",
            help="Run digitization only.",
        ),
    ] = False,
    events: Annotated[
        int,
        typer.Option(
            "-e",
            "--events",
            help="Number of events to run",
        ),
    ] = 0,
    skip: Annotated[
        int,
        typer.Option(
            "-s",
            "--skip",
            help="Number of events to skip",
        ),
    ] = 0,
) -> None:
    """Generate particles."""
    global_config = GlobalConfiguration.load(state)
    config = Configuration(config_file, global_config)
    logger = setup_logger(global_config, "reconstruct")

    environ["NUMEXPR_MAX_THREADS"] = str(config.global_config.threads)

    from siliconai_acts.scheduling.reconstruction import run_reconstruction

    run_reconstruction(
        logger,
        config.seed,
        events if events > 0 else config.events,
        global_config.threads,
        config.output_path,
        skip if skip > 0 else 0,
        hits_type,
        digi_only,
    )

    if diagnostics:
        pass


@application.command()
def export(
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
    """Export events."""
    global_config = GlobalConfiguration.load(state)
    config = Configuration(config_file, global_config)
    logger = setup_logger(global_config, "export")

    environ["NUMEXPR_MAX_THREADS"] = str(config.global_config.threads)

    logger.info("Exporting data")

    from siliconai_acts.data.export import export_hits

    export_hits(logger, config)


@application.command("import")
def import_data(
    config_file: Annotated[
        Path,
        typer.Option(
            "-c",
            "--config",
            envvar="SILICONAI_ACTS_CONFIG",
            help="Task configuration file.",
        ),
    ],
    file: Annotated[
        Path,
        typer.Option(
            "-f",
            "--file",
            envvar="SILICONAI_ACTS_FILE",
            help="Output file to import.",
        ),
    ],
) -> None:
    """Import ML results."""
    global_config = GlobalConfiguration.load(state)
    config = Configuration(config_file, global_config)
    logger = setup_logger(global_config, "import")

    environ["NUMEXPR_MAX_THREADS"] = str(config.global_config.threads)

    logger.info("Importing results")

    from siliconai_acts.data.importing import import_results

    import_results(logger, config, file)


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

    environ["NUMEXPR_MAX_THREADS"] = str(config.global_config.threads)

    logger.info("Creating diagnostics plots")

    setup_style()

    from siliconai_acts.plotting.diagnostics import plot_hits, plot_particles

    plot_particles(config, ProductionStep.Generation)
    plot_particles(config, ProductionStep.Simulation)
    plot_hits(config)


@application.command()
def validate(
    config_file: Annotated[
        Path,
        typer.Option(
            "-c",
            "--config",
            envvar="SILICONAI_ACTS_CONFIG",
            help="Task configuration file.",
        ),
    ],
    file: Annotated[
        Path,
        typer.Option(
            "-f",
            "--file",
            envvar="SILICONAI_ACTS_FILE",
            help="Output file to validate.",
        ),
    ],
) -> None:
    """Validate ML results."""
    global_config = GlobalConfiguration.load(state)
    config = Configuration(config_file, global_config)
    logger = setup_logger(global_config, "validate")

    environ["NUMEXPR_MAX_THREADS"] = str(config.global_config.threads)

    logger.info("Validating results")

    setup_style()

    from siliconai_acts.plotting.validation import validate

    validate(config, file)


@application.command()
def validate_reco(
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
    """Validate ML results."""
    global_config = GlobalConfiguration.load(state)
    config = Configuration(config_file, global_config)
    logger = setup_logger(global_config, "validate_reco")

    environ["NUMEXPR_MAX_THREADS"] = str(config.global_config.threads)

    logger.info("Validating reconstruction results")

    setup_style()

    from siliconai_acts.plotting.validation import validate_reconstruction

    validate_reconstruction(config)
