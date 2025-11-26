# Copyright (C) 2024 Tadej Novak
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0

"""Detector helper utilities."""

from __future__ import annotations

from pathlib import Path

import acts
from acts.examples.odd import getOpenDataDetector

u = acts.UnitConstants

# ODD configs
# TODO: getOpenDataDetectorDirectory() needs to be fixed upstream
odd_directory: Path = Path("dependencies") / "build" / "_deps" / "odd-src"
odd_material_map: Path = odd_directory / "data/odd-material-maps.root"
odd_digi_config: Path = odd_directory / "config/odd-digi-smearing-config.json"
odd_seeding_config: Path = odd_directory / "config/odd-seeding-config.json"
odd_material_decorator: acts.IMaterialDecorator = acts.IMaterialDecorator.fromFile(
    odd_material_map,
)

# ODD
odd_detector = getOpenDataDetector(
    materialDecorator=odd_material_decorator,
    odd_dir=odd_directory,
    logLevel=acts.logging.ERROR,
)
odd_tracking_geometry = odd_detector.trackingGeometry()
odd_decorators = odd_detector.contextDecorators()
odd_field = acts.ConstantBField(acts.Vector3(0.0, 0.0, 2.0 * u.T))
