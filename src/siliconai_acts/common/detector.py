"""Detector helper utilities."""

from pathlib import Path

import acts
from acts.examples.odd import getOpenDataDetector, getOpenDataDetectorDirectory

u = acts.UnitConstants

# ODD configs
odd_directory: Path = getOpenDataDetectorDirectory()
odd_material_map: Path = odd_directory / "data/odd-material-maps.root"
odd_digi_config: Path = odd_directory / "config/odd-digi-smearing-config.json"
odd_seeding_config: Path = odd_directory / "config/odd-seeding-config.json"
odd_material_decorator: acts.IMaterialDecorator = acts.IMaterialDecorator.fromFile(
    odd_material_map,
)

# ODD
odd_detector, odd_tracking_geometry, odd_decorators = getOpenDataDetector(
    odd_material_decorator,
    odd_directory,
    logLevel=acts.logging.ERROR,
)
odd_field = acts.ConstantBField(acts.Vector3(0.0, 0.0, 2.0 * u.T))
