"""Event simulation utilities."""

from __future__ import annotations

import subprocess
from functools import partial
from multiprocessing import Pool
from typing import TYPE_CHECKING, Optional

import acts
from acts.examples.geant4 import RegionCreator
from acts.examples.simulation import (
    ParticleSelectorConfig,
    addFatras,
    addGeant4,
)

from siliconai_acts.common.enums import SimulationType
from siliconai_acts.common.utils import rm_tree

if TYPE_CHECKING:
    from pathlib import Path

    from siliconai_acts.cli.config import SimulationConfiguration
    from siliconai_acts.cli.logging import Logger

u = acts.UnitConstants


def schedule_simulation(
    sequencer: acts.examples.Sequencer,
    rnd: acts.examples.RandomNumbers,
    simulation_type: SimulationType,
    detector: acts.Detector,
    tracking_geometry: acts.TrackingGeometry,
    field: acts.MagneticFieldProvider,
    input_collection: str = "particles_input",
    output_path: Optional[Path] = None,
    preselect_particles: Optional[ParticleSelectorConfig] = None,
    postselect_particles: Optional[ParticleSelectorConfig] = None,
    region_cuts: Optional[bool] = False,
    log_level: Optional[acts.logging.Level] = None,
    disable_secondaries: Optional[bool] = False,
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

    if simulation_type is SimulationType.Fatras:
        addFatras(
            sequencer,
            trackingGeometry=tracking_geometry,
            field=field,
            rnd=rnd,
            enableInteractions=True,
            preSelectParticles=preselect_particles,
            postSelectParticles=postselect_particles,
            inputParticles=input_collection,
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
            inputParticles=input_collection,
            preSelectParticles=preselect_particles,
            postSelectParticles=postselect_particles,
            killVolume=tracking_geometry.worldVolume,
            killAfterTime=25 * u.ns,
            outputDirRoot=output_path,
            logLevel=log_level,
            regionList=region_list,
            killSecondaries=disable_secondaries,
            recordHitsOfSecondaries=not disable_secondaries,
        )


def run_simulation(
    seed: int,
    config: SimulationConfiguration,
    input_path: Path,
    output_path: Path,
    events: int,
    skip: int = 0,
) -> None:
    """Run event simulation."""
    rnd = acts.examples.RandomNumbers(seed=seed)

    # import detector lazily
    from siliconai_acts.common.detector import (
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
            outputParticles="particles_input",
            filePath=input_path / "particles.root",
        ),
    )

    schedule_simulation(
        sequencer,
        rnd,
        config.type,
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
    output_path: Path,
) -> None:
    """Run event simulation on an event range."""
    events = end_event - begin_event
    skip = begin_event

    run_simulation(
        seed,
        config,
        output_path,
        output_path / f"proc_{task_id}",
        events,
        skip,
    )


def run_simulation_multiprocess(
    logger: Logger,
    seed: int,
    config: SimulationConfiguration,
    events: int,
    processes: int,
    output_path: Path,
) -> None:
    """Run event simulation in parallel."""
    logger.info("Running event simulation")

    if processes <= 1:
        run_simulation(seed, config, output_path, output_path, events)
        return

    chunksize = events // (processes - 1)
    ids = range(processes)
    begins = range(0, events, chunksize)
    ends = [min(b + chunksize, events) for b in begins]

    # run the process pool
    with Pool(processes) as p:
        p.starmap(
            partial(
                run_simulation_range,
                seed=seed,
                config=config,
                output_path=output_path,
            ),
            zip(ids, begins, ends),
        )

    # merge outputs
    hits_files = [str(file) for file in output_path.rglob("proc_*/hits.root")]
    particles_files = [
        str(file) for file in output_path.rglob("proc_*/particles_simulation.root")
    ]
    hits_file_out = str(output_path / "hits.root")
    particles_file_out = str(output_path / "particles_simulation.root")

    subprocess.run(["hadd", "-f", hits_file_out, *hits_files], check=True)
    subprocess.run(["hadd", "-f", particles_file_out, *particles_files], check=True)

    proc_folders = output_path.glob("proc_*")
    for folder in proc_folders:
        rm_tree(folder)
