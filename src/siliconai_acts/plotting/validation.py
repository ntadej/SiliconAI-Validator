"""Results validation."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np
import pandas as pd

from siliconai_acts.data.export import geometry_id_end, geometry_id_start
from siliconai_acts.plotting.diagnostics import diagnostics_plot
from siliconai_acts.plotting.utils import PDFDocument

if TYPE_CHECKING:
    from pathlib import Path

    from siliconai_acts.cli.config import Configuration


def preprocess_input(file: Path, key: str) -> pd.DataFrame:
    """Preprocess input data."""
    with pd.HDFStore(file, mode="r") as store:
        data: pd.DataFrame = cast(pd.DataFrame, store[key])

    data = data.drop(
        data[
            (data["geometry_id"] == geometry_id_start)
            | (data["geometry_id"] == geometry_id_end)
        ].index,
    )
    data["lx"] = data["lxq"]
    data["ly"] = data["lyq"]

    from siliconai_acts.data.utils import local_to_global_vec

    global_data = local_to_global_vec(
        data["geometry_id"],
        data["lxq"],
        data["lyq"],
    )
    data["tx"] = global_data[0]
    data["tx"] = data["tx"].astype("float32")
    data["ty"] = global_data[1]
    data["ty"] = data["ty"].astype("float32")
    data["tz"] = global_data[2]
    data["tz"] = data["tz"].astype("float32")
    data["tr"] = np.sqrt(data["tx"] ** 2 + data["ty"] ** 2)

    return data


def validate_hits(
    config: Configuration,
    file_suffix: str,
    reference_data: pd.DataFrame,
    generated_data: pd.DataFrame,
) -> None:
    """Validate and plot hits."""
    columns_position = [
        "tr",
        "tx",
        "ty",
        "tz",
        # "tt",
    ]
    columns_local_position = [
        "lx",
        "ly",
    ]
    columns = columns_position + columns_local_position

    labels_extra = [
        *config.labels,
        f"{config.events} events, simulated hits",
    ]
    labels_extra_primary = [
        *labels_extra,
        "primary particles only",
    ]

    with PDFDocument(config.output_path / f"validation_{file_suffix}.pdf") as pdf:  # type: ignore
        for column in columns:
            diagnostics_plot(
                pdf,
                [reference_data[column], generated_data[column]],
                column,
                "Primary hit",
                "Hits",
                labels_extra_primary,
                legend=["Reference", "Generated"],
            )


def validate(config: Configuration, file: Path) -> None:
    """Validate results."""
    reference = preprocess_input(file, "reference_data")
    generated = preprocess_input(file, "generated_data")

    validate_hits(config, file.stem, reference, generated)
