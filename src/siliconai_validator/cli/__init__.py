# Copyright (C) 2024 Tadej Novak
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0

"""SiliconAI Validator CLI."""

from __future__ import annotations

from os import environ
from pathlib import Path
from sys import argv
from typing import Annotated

import typer

from siliconai_validator import __version__
from siliconai_validator.cli.config import (
    Configuration,
    GlobalConfiguration,
    TyperState,
    config_missing,
)
from siliconai_validator.cli.logger import setup_logger
from siliconai_validator.common.enums import ProductionStep, SimulationType

application = typer.Typer()
state = TyperState()


def version_callback(value: bool) -> None:
    """Version callback."""
    if value:
        typer.echo(f"SiliconAI Validator, version {__version__}")
        raise typer.Exit()


@application.callback()
def main(
    ctx: typer.Context,
    config: Annotated[
        Path,
        typer.Option(
            "-g",
            "--global-config",
            envvar="SILICONAI_VALIDATOR_GLOBAL_CONFIG",
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
    """SiliconAI Validator CLI app."""
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
            envvar="SILICONAI_VALIDATOR_CONFIG",
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
    task_id: Annotated[
        int,
        typer.Option(
            "-t",
            "--task-id",
            help="Specific task ID to run.",
        ),
    ] = -1,
    slurm: Annotated[
        bool,
        typer.Option(
            "--slurm",
            help="Run simulation through SLURM scheduler.",
        ),
    ] = False,
    postprocess: Annotated[
        bool,
        typer.Option(
            "--postprocess",
            help="Run postprocessing after SLURM jobs are done.",
        ),
    ] = False,
) -> None:
    """Generate particles."""
    global_config = GlobalConfiguration.load(state)
    config = Configuration(config_file, global_config)
    logger = setup_logger(global_config, "generate")

    environ["NUMEXPR_MAX_THREADS"] = str(config.global_config.threads)

    from siliconai_validator.scheduling.generation import run_generation_multiprocess

    run_generation_multiprocess(
        logger,
        config.seed,
        config.process,
        config.events,
        global_config.threads,
        config_file,
        config.output_name,
        config.output_path,
        run_task=(task_id, events, skip),
        slurm=slurm,
        postprocess=postprocess,
    )

    if diagnostics:
        from siliconai_validator.plotting.common import setup_style
        from siliconai_validator.plotting.diagnostics import plot_particles

        setup_style()
        plot_particles(config, ProductionStep.Generation)


@application.command()
def simulate(
    config_file: Annotated[
        Path,
        typer.Option(
            "-c",
            "--config",
            envvar="SILICONAI_VALIDATOR_CONFIG",
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
    task_id: Annotated[
        int,
        typer.Option(
            "-t",
            "--task-id",
            help="Specific task ID to run.",
        ),
    ] = -1,
    fatras: Annotated[
        bool,
        typer.Option(
            "--fatras",
            help="Use Fast Simulation (FATRAS) instead of full Geant4 simulation.",
        ),
    ] = False,
    slurm: Annotated[
        bool,
        typer.Option(
            "--slurm",
            help="Run simulation through SLURM scheduler.",
        ),
    ] = False,
    postprocess: Annotated[
        bool,
        typer.Option(
            "--postprocess",
            help="Run postprocessing after SLURM jobs are done.",
        ),
    ] = False,
) -> None:
    """Generate particles."""
    global_config = GlobalConfiguration.load(state)
    config = Configuration(config_file, global_config)
    simulation_type = SimulationType.Fatras if fatras else SimulationType.Geant4
    logger = setup_logger(global_config, "simulate")

    environ["NUMEXPR_MAX_THREADS"] = str(config.global_config.threads)

    from siliconai_validator.scheduling.simulation import run_simulation_multiprocess

    run_simulation_multiprocess(
        logger,
        simulation_type,
        config.seed,
        config.simulation,
        config.events,
        global_config.threads,
        config_file,
        config.output_name,
        config.output_path,
        run_task=(task_id, events, skip),
        slurm=slurm,
        postprocess=postprocess,
    )

    if diagnostics:
        from siliconai_validator.plotting.common import setup_style
        from siliconai_validator.plotting.diagnostics import plot_hits, plot_particles

        setup_style()
        plot_particles(config, ProductionStep.Simulation, simulation_type)
        plot_hits(config, simulation_type)


@application.command()
def reconstruct(
    config_file: Annotated[
        Path,
        typer.Option(
            "-c",
            "--config",
            envvar="SILICONAI_VALIDATOR_CONFIG",
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
    fatras: Annotated[
        bool,
        typer.Option(
            "--fatras",
            help="Use Fast Simulation (FATRAS) instead of full Geant4 simulation.",
        ),
    ] = False,
) -> None:
    """Generate particles."""
    global_config = GlobalConfiguration.load(state)
    config = Configuration(config_file, global_config)
    simulation_type = SimulationType.Fatras if fatras else SimulationType.Geant4
    logger = setup_logger(global_config, "reconstruct")

    environ["NUMEXPR_MAX_THREADS"] = str(config.global_config.threads)

    from siliconai_validator.scheduling.reconstruction import run_reconstruction

    run_reconstruction(
        logger,
        simulation_type,
        config.seed,
        events if events > 0 else config.events,
        global_config.threads,
        config.output_path,
        max(skip, 0),
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
            envvar="SILICONAI_VALIDATOR_CONFIG",
            help="Task configuration file.",
        ),
    ],
    fixed_length: Annotated[
        bool,
        typer.Option(
            "--fixed-length",
            help="Only select fixed-lenght sequences (the ones with highest rate).",
        ),
    ] = False,
    task_id: Annotated[
        int,
        typer.Option(
            "-t",
            "--task-id",
            help="Specific task ID to run.",
        ),
    ] = -1,
    fatras: Annotated[
        bool,
        typer.Option(
            "--fatras",
            help="Use Fast Simulation (FATRAS) instead of full Geant4 simulation.",
        ),
    ] = False,
    slurm: Annotated[
        bool,
        typer.Option(
            "--slurm",
            help="Run simulation through SLURM scheduler.",
        ),
    ] = False,
) -> None:
    """Export events."""
    global_config = GlobalConfiguration.load(state)
    config = Configuration(config_file, global_config)
    simulation_type = SimulationType.Fatras if fatras else SimulationType.Geant4
    logger = setup_logger(global_config, "export")

    environ["NUMEXPR_MAX_THREADS"] = str(config.global_config.threads)

    logger.info("Exporting data")

    from siliconai_validator.data.export import export_hits

    export_hits(
        logger,
        config,
        simulation_type,
        fixed_length=fixed_length,
        slurm=slurm,
        task_id=task_id,
    )


@application.command("import")
def import_data(
    config_file: Annotated[
        Path,
        typer.Option(
            "-c",
            "--config",
            envvar="SILICONAI_VALIDATOR_CONFIG",
            help="Task configuration file.",
        ),
    ],
    file: Annotated[
        Path,
        typer.Option(
            "-f",
            "--file",
            envvar="SILICONAI_VALIDATOR_FILE",
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

    from siliconai_validator.data.importing import import_results

    import_results(logger, config, file)


@application.command()
def diagnostics(
    config_file: Annotated[
        Path,
        typer.Option(
            "-c",
            "--config",
            envvar="SILICONAI_VALIDATOR_CONFIG",
            help="Task configuration file.",
        ),
    ],
    fatras: Annotated[
        bool,
        typer.Option(
            "--fatras",
            help="Use Fast Simulation (FATRAS) instead of full Geant4 simulation.",
        ),
    ] = False,
) -> None:
    """Run diagnostics and make plots."""
    global_config = GlobalConfiguration.load(state)
    config = Configuration(config_file, global_config)
    simulation_type = SimulationType.Fatras if fatras else SimulationType.Geant4
    logger = setup_logger(global_config, "diagnostics")

    environ["NUMEXPR_MAX_THREADS"] = str(config.global_config.threads)

    logger.info("Creating diagnostics plots")

    from siliconai_validator.plotting.common import setup_style
    from siliconai_validator.plotting.diagnostics import plot_hits, plot_particles

    setup_style()
    plot_particles(config, ProductionStep.Generation)
    plot_particles(config, ProductionStep.Simulation, simulation_type)
    plot_hits(config, simulation_type)


@application.command()
def validate(
    config_file: Annotated[
        Path,
        typer.Option(
            "-c",
            "--config",
            envvar="SILICONAI_VALIDATOR_CONFIG",
            help="Task configuration file.",
        ),
    ],
    file: Annotated[
        Path,
        typer.Option(
            "-f",
            "--file",
            envvar="SILICONAI_VALIDATOR_FILE",
            help="Output file to validate.",
        ),
    ],
    event: Annotated[
        int,
        typer.Option(
            "-e",
            "--event",
            help="Specific event to validate.",
        ),
    ] = -1,
) -> None:
    """Validate ML results."""
    global_config = GlobalConfiguration.load(state)
    config = Configuration(config_file, global_config)
    logger = setup_logger(global_config, "validate")

    environ["NUMEXPR_MAX_THREADS"] = str(config.global_config.threads)

    logger.info("Validating results")

    from siliconai_validator.plotting.common import setup_style
    from siliconai_validator.plotting.validation import validate

    setup_style()
    validate(config, file, event)


@application.command()
def validate_reco(
    config_file: Annotated[
        Path,
        typer.Option(
            "-c",
            "--config",
            envvar="SILICONAI_VALIDATOR_CONFIG",
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

    from siliconai_validator.plotting.common import setup_style
    from siliconai_validator.plotting.validation import (
        validate_reconstruction_performance,
        validate_reconstruction_tracks,
    )

    setup_style()
    validate_reconstruction_performance(config)
    validate_reconstruction_tracks(config)
