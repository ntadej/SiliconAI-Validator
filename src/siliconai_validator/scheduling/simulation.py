# Copyright (C) 2024 Tadej Novak
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0

"""Event simulation utilities."""

from __future__ import annotations

import subprocess
from functools import partial
from multiprocessing import Pool
from typing import TYPE_CHECKING

import acts
from acts.examples.geant4 import RegionCreator
from acts.examples.simulation import (
    ParticleSelectorConfig,
    addFatras,
    addGeant4,
    addGenParticleSelection,
    addSimParticleSelection,
)

from siliconai_validator.common.enums import SimulationType
from siliconai_validator.common.utils import rm_tree
from siliconai_validator.scheduling.submission import (
    create_slurm_run_script,
    create_slurm_submission_script,
)

if TYPE_CHECKING:
    from pathlib import Path

    from siliconai_validator.cli.config import SimulationConfiguration
    from siliconai_validator.cli.logger import Logger

u = acts.UnitConstants

MIN_EVENTS_PER_PROCESS = 100_000
MAX_EVENTS_PER_MERGE = 1_000_000


def schedule_simulation(
    sequencer: acts.examples.Sequencer,
    rnd: acts.examples.RandomNumbers,
    simulation_type: SimulationType,
    detector: acts.Detector,
    tracking_geometry: acts.TrackingGeometry,
    field: acts.MagneticFieldProvider,
    output_path: Path | None = None,
    preselect_particles: ParticleSelectorConfig | None = None,
    postselect_particles: ParticleSelectorConfig | None = None,
    region_cuts: bool | None = False,
    log_level: acts.logging.Level | None = None,
    disable_secondaries: bool | None = False,
) -> None:
    """Schedule event simulation in the ACTS example framework."""
    region_list: list[RegionCreator] = []
    if region_cuts:
        region_list = [
            RegionCreator(
                name="TrackingRegion",
                volumes=["Pixels", "ShortStrips", "LongStrips"],
                electronCut=0.05,
                positronCut=0.05,
                gammaCut=0.05,
            ),
        ]

    addGenParticleSelection(sequencer, preselect_particles)

    if simulation_type is SimulationType.Fatras:
        addFatras(
            sequencer,
            trackingGeometry=tracking_geometry,
            field=field,
            rnd=rnd,
            enableInteractions=True,
            outputDirRoot=output_path,
            logLevel=log_level,
        )
    elif simulation_type is SimulationType.Geant4:
        addGeant4(
            sequencer,
            detector=detector,
            trackingGeometry=tracking_geometry,
            field=field,
            rnd=rnd,
            killVolume=tracking_geometry.highestTrackingVolume,
            killAfterTime=25 * u.ns,
            outputDirRoot=output_path,
            logLevel=log_level,
            regionList=region_list,
            killSecondaries=disable_secondaries,
            recordHitsOfSecondaries=not disable_secondaries,
        )

    addSimParticleSelection(sequencer, postselect_particles)


def run_simulation(
    simulation_type: SimulationType,
    seed: int,
    config: SimulationConfiguration,
    input_file: Path,
    output_path: Path,
    events: int,
    skip: int = 0,
) -> None:
    """Run event simulation."""
    rnd = acts.examples.RandomNumbers(seed=seed)

    # import detector lazily
    from siliconai_validator.common.detector import (
        odd_decorators,
        odd_detector,
        odd_field,
        odd_tracking_geometry,
    )

    sequencer = acts.examples.Sequencer(
        events=events,
        skip=skip,
        trackFpes=False,
        outputDir=output_path,
        numThreads=1,
    )

    for decorator in odd_decorators:
        sequencer.addContextDecorator(decorator)

    sequencer.addReader(
        acts.examples.RootParticleReader(
            level=acts.logging.WARNING,
            outputParticles="particles_generated",
            filePath=input_file,
        ),
    )

    schedule_simulation(
        sequencer,
        rnd,
        simulation_type,
        odd_detector,
        odd_tracking_geometry,
        odd_field,
        preselect_particles=ParticleSelectorConfig(
            # start before beampipe and reasonably close to the collision point
            rho=(0.0, 23.6 * u.mm),
            absZ=(0.0, 1.0 * u.m),
        ),
        postselect_particles=ParticleSelectorConfig(
            removeSecondaries=True,
            removeNeutral=True,
        )
        if config.disable_secondaries
        else None,
        disable_secondaries=config.disable_secondaries,
        output_path=output_path,
        region_cuts=False,
    )

    sequencer.run()


def run_simulation_range(
    task_id: int,
    begin_event: int,
    end_event: int,
    seed: int,
    config: SimulationConfiguration,
    simulation_type: SimulationType,
    input_path_base: Path,
    run_path_base: Path,
) -> None:
    """Run event simulation on an event range."""
    input_number = begin_event // MAX_EVENTS_PER_MERGE
    events = end_event - begin_event
    skip = begin_event - input_number * MAX_EVENTS_PER_MERGE
    run_path = run_path_base / f"proc_{task_id}"
    if not run_path.exists():
        run_path.mkdir(parents=True)

    run_simulation(
        simulation_type,
        seed + input_number * MAX_EVENTS_PER_MERGE,
        config,
        input_path_base / f"{input_number + 1}.root",
        run_path,
        events,
        skip,
    )


def run_simulation_multiprocess(
    logger: Logger,
    simulation_type: SimulationType,
    seed: int,
    config: SimulationConfiguration,
    events: int,
    processes: int,
    config_file: Path,
    output_name: str,
    output_path: Path,
    slurm: bool = False,
    postprocess: bool = False,
    run_task: tuple[int, int, int] | None = None,
) -> None:
    """Run event simulation in parallel."""
    logger.info("Running event simulation")

    if postprocess and not slurm:
        logger.error("Postprocessing can only be run with SLURM.")
        return

    if run_task is not None and run_task[0] >= 0:
        task_id, events, skip = run_task
        logger.info(
            "Running task #%d with %d events, skipping %d",
            task_id,
            events,
            skip,
        )
        run_simulation_range(
            task_id,
            skip,
            skip + events,
            seed,
            config,
            simulation_type,
            output_path / "particles",
            output_path / "run",
        )
        return

    njobs = events // MIN_EVENTS_PER_PROCESS
    njobs = njobs if slurm else min(processes, njobs)

    if not slurm and (njobs <= 1 or events < MIN_EVENTS_PER_PROCESS):
        error = "Not enough events to run in parallel."
        raise ValueError(error)

    chunksize = events // njobs

    ids = range(njobs)
    begins = range(0, events, chunksize)
    ends = [min(b + chunksize, events) for b in begins]

    if slurm:
        if not postprocess:
            logger.info(
                "Preparing %d jobs for %d events, %d each",
                njobs,
                events,
                chunksize,
            )

            script = create_slurm_submission_script(
                f"Simulation_{output_name}",
                output_path / "run",
            )
            for task_id, begin, end in zip(ids, begins, ends, strict=True):
                create_run_script(
                    task_id,
                    begin,
                    end,
                    config_file,
                    output_path / "run",
                )

            logger.info("Prepared submission script: %s", script)
            return
    else:
        logger.info(
            "Spawning %d processes for %d events, %d each",
            njobs,
            events,
            chunksize,
        )

        # run the process pool
        with Pool(processes) as p:
            p.starmap(
                partial(
                    run_simulation_range,
                    seed=seed,
                    config=config,
                    simulation_type=simulation_type,
                    input_path_base=output_path / "particles",
                    run_path_base=output_path / "run",
                ),
                zip(ids, begins, ends, strict=False),
            )

    # validate outputs
    if slurm and len(list(output_path.rglob("run/proc_*/SUCCESS"))) != njobs:
        logger.error("Some jobs did not complete successfully.")
        return

    # merge outputs
    njobs_merge = events // MAX_EVENTS_PER_MERGE
    files_per_merge = njobs // njobs_merge
    logger.info(
        "Merging outputs in %d files, %d inputs each",
        njobs_merge,
        files_per_merge,
    )

    if not (output_path / f"hits_{simulation_type.value}").exists():
        (output_path / f"hits_{simulation_type.value}").mkdir(parents=True)
    if not (output_path / f"particles_{simulation_type.value}").exists():
        (output_path / f"particles_{simulation_type.value}").mkdir(parents=True)

    # run the process pool for merging
    with Pool(processes) as p:
        p.starmap(
            partial(
                merge_results,
                simulation_type=simulation_type,
                njobs=njobs,
                njobs_merge=njobs_merge,
                output_path=output_path,
            ),
            zip(range(1, njobs_merge + 1), strict=True),
        )

    rm_tree(output_path / "run")


def create_run_script(
    task_id: int,
    begin_event: int,
    end_event: int,
    config_file: Path,
    run_path: Path,
) -> Path:
    """Create a script to run event simulation on an event range."""
    events = end_event - begin_event
    skip = begin_event
    script_run_path = run_path / f"proc_{task_id}"
    if not script_run_path.exists():
        script_run_path.mkdir(parents=True)

    command = (
        f"siliconai_validator simulate -c {config_file}"
        f" -t {task_id} -e {events} -s {skip}"
    )

    return create_slurm_run_script(script_run_path, command)


def merge_results(
    index: int,
    simulation_type: SimulationType,
    njobs: int,
    njobs_merge: int,
    output_path: Path,
) -> None:
    """Merge results from multiple event simulation runs."""
    files_per_merge = njobs // njobs_merge
    hits_files = [output_path / "run" / f"proc_{i}/hits.root" for i in range(njobs)]
    particles_files = [
        output_path / "run" / f"proc_{i}/particles_simulation.root"
        for i in range(njobs)
    ]

    hits_file_out = str(
        output_path / f"hits_{simulation_type.value}" / f"{index}.root",
    )
    particles_file_out = str(
        output_path / f"particles_{simulation_type.value}" / f"{index}.root",
    )

    subprocess.run(  # noqa: S603
        [  # noqa: S607
            "hadd",
            "-f",
            hits_file_out,
            *hits_files[files_per_merge * (index - 1) : files_per_merge * index],
        ],
        check=True,
    )
    subprocess.run(  # noqa: S603
        [  # noqa: S607
            "hadd",
            "-f",
            particles_file_out,
            *particles_files[files_per_merge * (index - 1) : files_per_merge * index],
        ],
        check=True,
    )
