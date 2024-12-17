"""Event digitization utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

import acts
import acts.examples
from acts.examples.simulation import addDigitization

if TYPE_CHECKING:
    from pathlib import Path

    from siliconai_acts.cli.logger import Logger


def schedule_digitization(
    sequencer: acts.examples.Sequencer,
    rnd: acts.examples.RandomNumbers,
    tracking_geometry: acts.TrackingGeometry,
    field: acts.MagneticFieldProvider,
    digitization_config: Path,
    output_path: Path | None = None,
    log_level: acts.logging.Level | None = None,
) -> None:
    """Schedule event digitization in the ACTS example framework."""
    addDigitization(
        sequencer,
        tracking_geometry,
        field,
        digiConfigFile=digitization_config,
        rnd=rnd,
        outputDirRoot=output_path,
        logLevel=log_level,
    )


def run_digitization(
    logger: Logger,
    seed: int,
    events: int,
    output_path: Path,
) -> None:
    """Run event digitization."""
    logger.info("Running event digitization")

    rnd = acts.examples.RandomNumbers(seed=seed)

    sequencer = acts.examples.Sequencer(
        events=events,
        trackFpes=False,
        outputDir=output_path,
        outputTimingFile="timing.digit.csv",
    )

    # import detector lazily
    from siliconai_acts.common.detector import (
        odd_decorators,
        odd_digi_config,
        odd_field,
        odd_tracking_geometry,
    )

    for decorator in odd_decorators:
        sequencer.addContextDecorator(decorator)

    sequencer.addReader(
        acts.examples.RootSimHitReader(
            level=acts.logging.WARNING,
            outputSimHits="simhits",
            filePath=output_path / "hits.root",
        ),
    )

    schedule_digitization(
        sequencer,
        rnd,
        odd_tracking_geometry,
        odd_field,
        odd_digi_config,
        output_path,
    )

    sequencer.run()


def get_coordinates_converter(
    tracking_geometry: acts.TrackingGeometry,
    digitization_config: Path,
) -> acts.examples.DigitizationCoordinatesConverter:
    """Initialize and return digitization coordinates converter."""
    # Digitization
    config = acts.examples.DigitizationAlgorithm.Config(
        digitizationConfigs=acts.examples.readDigiConfigFromJson(
            str(digitization_config),
        ),
        surfaceByIdentifier=tracking_geometry.geoIdSurfaceMap(),
    )

    return acts.examples.DigitizationCoordinatesConverter(config)
