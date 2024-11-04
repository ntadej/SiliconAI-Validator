"""Event reconstruction utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import acts
import acts.examples
from acts.examples.reconstruction import (
    AmbiguityResolutionConfig,
    CkfConfig,
    TrackSelectorConfig,
    addAmbiguityResolution,
    addCKFTracks,
    addSeeding,
)

from siliconai_acts.scheduling.digitization import schedule_digitization

if TYPE_CHECKING:
    from pathlib import Path

    from siliconai_acts.cli.logging import Logger


u = acts.UnitConstants


def schedule_reconstruction(
    sequencer: acts.examples.Sequencer,
    rnd: acts.examples.RandomNumbers,
    tracking_geometry: acts.TrackingGeometry,
    field: acts.MagneticFieldProvider,
    seeding_config: Path,
    output_path: Optional[Path] = None,
    log_level: Optional[acts.logging.Level] = None,
) -> None:
    """Schedule event reconstruction in the ACTS example framework."""
    initial_sigmas = [
        1 * u.mm,
        1 * u.mm,
        1 * u.degree,
        1 * u.degree,
        0.1 * u.e / u.GeV,
        1 * u.ns,
    ]

    addSeeding(
        sequencer,
        tracking_geometry,
        field,
        initialSigmas=initial_sigmas,
        initialSigmaPtRel=0.1,
        initialVarInflation=[1.0] * 6,
        geoSelectionConfigFile=seeding_config,
        rnd=rnd,
        outputDirRoot=output_path,
        logLevel=log_level,
    )

    addCKFTracks(
        sequencer,
        tracking_geometry,
        field,
        TrackSelectorConfig(
            pt=(0.0, None),
            absEta=(None, 3.0),
            loc0=(-4.0 * u.mm, 4.0 * u.mm),
            nMeasurementsMin=7,
            maxHoles=2,
            maxOutliers=2,
        ),
        CkfConfig(
            chi2CutOffMeasurement=15.0,
            chi2CutOffOutlier=25.0,
            numMeasurementsCutOff=10,
            seedDeduplication=True,
            stayOnSeed=True,
            pixelVolumes=[16, 17, 18],
            stripVolumes=[23, 24, 25],
            maxPixelHoles=1,
            maxStripHoles=2,
        ),
        writeCovMat=True,
        outputDirRoot=output_path,
        logLevel=log_level,
    )

    addAmbiguityResolution(
        sequencer,
        AmbiguityResolutionConfig(
            maximumSharedHits=3,
            maximumIterations=1000000,
            nMeasurementsMin=7,
        ),
        writeCovMat=True,
        outputDirRoot=output_path,
        logLevel=acts.logging.WARNING if log_level is None else log_level,
    )


def run_reconstruction(
    logger: Logger,
    seed: int,
    events: int,
    threads: int,
    output_path: Path,
    skip: int = 0,
    suffix: str = "original",
    digi_only: bool = False,
) -> None:
    """Run event digitization."""
    logger.info("Running event digitization")

    rnd = acts.examples.RandomNumbers(seed=seed)

    input_file = "hits.root" if suffix == "original" else f"hits_{suffix}.root"
    output_path_reco = output_path / suffix

    sequencer = acts.examples.Sequencer(
        events=events,
        skip=skip,
        numThreads=threads,
        trackFpes=False,
        outputDir=output_path_reco,
        outputTimingFile="timing.recon.csv",
    )

    # import detector lazily
    from siliconai_acts.common.detector import (
        odd_decorators,
        odd_digi_config,
        odd_field,
        odd_seeding_config,
        odd_tracking_geometry,
    )

    for decorator in odd_decorators:
        sequencer.addContextDecorator(decorator)

    sequencer.addReader(
        acts.examples.RootSimHitReader(
            level=acts.logging.WARNING,
            outputSimHits="simhits",
            filePath=output_path / input_file,
        ),
    )

    sequencer.addReader(
        acts.examples.RootParticleReader(
            level=acts.logging.WARNING,
            outputParticles="particles",
            filePath=output_path / "particles_simulation.root",
        ),
    )
    sequencer.addWhiteboardAlias("particles_selected", "particles")

    schedule_digitization(
        sequencer,
        rnd,
        odd_tracking_geometry,
        odd_field,
        odd_digi_config,
        output_path_reco,
    )

    if not digi_only:
        schedule_reconstruction(
            sequencer,
            rnd,
            odd_tracking_geometry,
            odd_field,
            odd_seeding_config,
            output_path_reco,
        )

    sequencer.run()
