# Copyright (C) 2024 Tadej Novak
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0

"""Event generation utilities."""

from __future__ import annotations

import subprocess
from functools import partial
from multiprocessing import Pool
from typing import TYPE_CHECKING

import acts
from acts.examples.simulation import (
    EtaConfig,
    MomentumConfig,
    ParticleConfig,
    PhiConfig,
    addParticleGun,
)

from siliconai_validator.common.enums import EventType, ParticleType
from siliconai_validator.common.utils import rm_tree
from siliconai_validator.scheduling.submission import (
    create_slurm_run_script,
    create_slurm_submission_script,
)

if TYPE_CHECKING:
    from pathlib import Path

    from siliconai_validator.cli.config import ProcessConfiguration
    from siliconai_validator.cli.logger import Logger

u = acts.UnitConstants

MIN_EVENTS_PER_PROCESS = 100_000
MAX_EVENTS_PER_MERGE = 1_000_000


def schedule_event_generation(
    sequencer: acts.examples.Sequencer,
    rnd: acts.examples.RandomNumbers,
    config: ProcessConfiguration,
    output_dir: Path | None = None,
) -> None:
    """Schedule event generation in the ACTS example framework."""
    vertex_generator = acts.examples.UniformVertexGenerator(
        min=acts.Vector4(
            -config.smearing[0] * u.um,
            -config.smearing[1] * u.um,
            -config.smearing[2] * u.mm,
            0,
        ),
        max=acts.Vector4(
            config.smearing[0] * u.um,
            config.smearing[1] * u.um,
            config.smearing[2] * u.mm,
            0,
        ),
    )

    if config.type is EventType.SingleParticle:
        if config.particle is ParticleType.Muon:
            particle = acts.PdgParticle.eMuon
        elif config.particle is ParticleType.Electron:
            particle = acts.PdgParticle.eElectron
        elif config.particle is ParticleType.Photon:
            particle = acts.PdgParticle.ePhoton
        elif config.particle is ParticleType.Pion:
            particle = acts.PdgParticle.ePionPlus

        if isinstance(config.pt, tuple):
            momentum_config = MomentumConfig(
                config.pt[0],
                config.pt[1],
                transverse=True,
            )
        else:
            momentum_config = MomentumConfig(
                config.pt,
                config.pt,
                transverse=True,
            )

        if isinstance(config.eta, tuple):
            eta_config = EtaConfig(config.eta[0], config.eta[1], uniform=True)
        else:
            eta_config = EtaConfig(config.eta, config.eta, uniform=True)

        if config.phi:
            phi_config = PhiConfig(config.phi[0], config.phi[1])
        else:
            phi_config = PhiConfig(0.0 * u.degree, 360.0 * u.degree)

        addParticleGun(
            sequencer,
            ParticleConfig(
                num=1,
                pdg=particle,
                randomizeCharge=config.randomize_charge,
            ),
            momentum_config,
            eta_config,
            phi_config,
            vtxGen=vertex_generator,
            multiplicity=1,
            rnd=rnd,
            outputDirRoot=output_dir,
        )

        return


def run_generation(
    seed: int,
    config: ProcessConfiguration,
    output_path: Path,
    events: int,
    skip: int = 0,
) -> None:
    """Run event generation."""
    rnd = acts.examples.RandomNumbers(seed=seed)

    sequencer = acts.examples.Sequencer(
        events=events,
        skip=skip,
        trackFpes=False,
        outputDir=output_path,
        outputTimingFile="timing.evgen.csv",
        numThreads=1,
    )

    schedule_event_generation(sequencer, rnd, config, output_path)

    sequencer.run()


def run_generation_range(
    task_id: int,
    begin_event: int,
    end_event: int,
    seed: int,
    config: ProcessConfiguration,
    run_path_base: Path,
) -> None:
    """Run event generation on an event range."""
    events = end_event - begin_event
    skip = begin_event
    run_path = run_path_base / f"proc_{task_id}"
    if not run_path.exists():
        run_path.mkdir(parents=True)

    run_generation(
        seed,
        config,
        run_path,
        events,
        skip,
    )


def run_generation_multiprocess(
    logger: Logger,
    seed: int,
    config: ProcessConfiguration,
    events: int,
    processes: int,
    config_file: Path,
    output_name: str,
    output_path: Path,
    slurm: bool = False,
    postprocess: bool = False,
    run_task: tuple[int, int, int] | None = None,
) -> None:
    """Run event generation in parallel."""
    logger.info("Running event generation")

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
        run_generation_range(
            task_id,
            skip,
            skip + events,
            seed,
            config,
            output_path / "run",
        )
        return

    njobs = events // MIN_EVENTS_PER_PROCESS
    njobs = njobs if slurm else min(processes, njobs)

    if njobs <= 1 or events < MIN_EVENTS_PER_PROCESS:
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
                f"Generation_{output_name}",
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
                    run_generation_range,
                    seed=seed,
                    config=config,
                    run_path_base=output_path / "run",
                ),
                zip(ids, begins, ends, strict=True),
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

    if not (output_path / "particles").exists():
        (output_path / "particles").mkdir(parents=True)
    if not (output_path / "vertices").exists():
        (output_path / "vertices").mkdir(parents=True)

    # run the process pool for merging
    with Pool(processes) as p:
        p.starmap(
            partial(
                merge_results,
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
    """Create a script to run event generation on an event range."""
    events = end_event - begin_event
    skip = begin_event
    script_run_path = run_path / f"proc_{task_id}"
    if not script_run_path.exists():
        script_run_path.mkdir(parents=True)

    command = (
        f"siliconai_validator generate -c {config_file}"
        f" -t {task_id} -e {events} -s {skip}"
    )

    return create_slurm_run_script(script_run_path, command)


def merge_results(index: int, njobs: int, njobs_merge: int, output_path: Path) -> None:
    """Merge results from multiple event generation runs."""
    files_per_merge = njobs // njobs_merge
    particles_files = [
        output_path / "run" / f"proc_{i}/particles.root" for i in range(njobs)
    ]
    vertices_files = [
        output_path / "run" / f"proc_{i}/vertices.root" for i in range(njobs)
    ]

    particles_file_out = str(output_path / "particles" / f"{index}.root")
    vertices_file_out = str(output_path / "vertices" / f"{index}.root")

    subprocess.run(  # noqa: S603
        [  # noqa: S607
            "hadd",
            "-f",
            particles_file_out,
            *particles_files[files_per_merge * (index - 1) : files_per_merge * index],
        ],
        check=True,
    )
    subprocess.run(  # noqa: S603
        [  # noqa: S607
            "hadd",
            "-f",
            vertices_file_out,
            *vertices_files[files_per_merge * (index - 1) : files_per_merge * index],
        ],
        check=True,
    )
