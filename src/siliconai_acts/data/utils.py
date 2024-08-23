"""Data utilities."""

import numpy as np

from siliconai_acts.common.detector import (
    odd_digi_config,
    odd_tracking_geometry,
)
from siliconai_acts.scheduling.digitization import get_coordinates_converter

coordinates_converter = get_coordinates_converter(
    odd_tracking_geometry,
    odd_digi_config,
)


def global_to_local(
    geometry_id: int,
    tx: float,
    ty: float,
    tz: float,
) -> tuple[float, float]:
    """Convert global coordinates to local coordinates."""
    if geometry_id == 0:
        return 0.0, 0.0

    return coordinates_converter.globalToLocal(geometry_id, tx, ty, tz)  # type: ignore


def local_to_global(
    geometry_id: int,
    lx: float,
    ly: float,
) -> tuple[float, float, float]:
    """Convert global coordinates to local coordinates."""
    if geometry_id == 0:
        return 0.0, 0.0, 0.0

    return coordinates_converter.localToGlobal(geometry_id, lx, ly)  # type: ignore


global_to_local_vec = np.vectorize(global_to_local)
local_to_global_vec = np.vectorize(local_to_global)
