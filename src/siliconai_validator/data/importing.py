# Copyright (C) 2024 Tadej Novak
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0

"""Results importing."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np
import pandas as pd
import uproot

from siliconai_validator.data.export import geometry_id_end, geometry_id_start
from siliconai_validator.data.utils import common_initial_barcode

if TYPE_CHECKING:
    from pathlib import Path

    from siliconai_validator.cli.config import Configuration
    from siliconai_validator.cli.logger import Logger


def preprocess_input(file: Path, key: str) -> pd.DataFrame:
    """Preprocess input data."""
    mass = 0.10566

    with pd.HDFStore(file, mode="r") as store:
        data: pd.DataFrame = cast("pd.DataFrame", store[key])

    data = data.drop(
        data[
            (data["geometry_id"] == geometry_id_start)
            | (data["geometry_id"] == geometry_id_end)
        ].index,
    )
    data["lx"] = data["lxq"]
    data["ly"] = data["lyq"]

    data["tpxq"] -= data["deltapxq"]
    data["tpyq"] -= data["deltapyq"]
    data["tpzq"] -= data["deltapzq"]

    data["tpx"] = data["tpxq"]
    data["tpy"] = data["tpyq"]
    data["tpz"] = data["tpzq"]
    data["tpt"] = np.sqrt(data["tpx"] ** 2 + data["tpy"] ** 2)
    data["te"] = np.sqrt(
        data["tpx"] ** 2 + data["tpy"] ** 2 + data["tpz"] ** 2 + mass**2,
    )

    data["deltapx"] = data["deltapxq"]
    data["deltapy"] = data["deltapyq"]
    data["deltapz"] = data["deltapzq"]
    data["deltapt"] = (
        np.sqrt(
            (data["tpx"] + data["deltapx"]) ** 2 + (data["tpy"] + data["deltapy"]) ** 2,
        )
        - data["tpt"]
    )
    data["deltae"] = -np.sqrt(
        data["deltapx"] ** 2 + data["deltapy"] ** 2 + data["deltapz"] ** 2,
    )

    from siliconai_validator.data.utils import local_to_global_vec

    try:
        global_data = local_to_global_vec(
            data["geometry_id"],
            data["lxq"],
            data["lyq"],
        )
    except RuntimeError:
        global_data = [0, 0, 0]
    data["tx"] = global_data[0]
    data["tx"] = data["tx"].astype("float32")
    data["ty"] = global_data[1]
    data["ty"] = data["ty"].astype("float32")
    data["tz"] = global_data[2]
    data["tz"] = data["tz"].astype("float32")
    data["tr"] = np.sqrt(data["tx"] ** 2 + data["ty"] ** 2)

    return data


def write_hits_tree(
    logger: Logger,
    config: Configuration,
    data: pd.DataFrame,
    suffix: str,
) -> None:
    """Write hits tree."""
    output_file = config.output_path / f"hits_{suffix}.root"

    logger.info("Writing %s hits to %s", suffix, output_file)

    with uproot.recreate(output_file) as f:
        f.mktree(
            "hits",
            {
                "event_id": "uint32",
                "geometry_id": "uint64",
                "barcode": "uint64",
                "tx": "float32",
                "ty": "float32",
                "tz": "float32",
                "tt": "float32",
                "tpx": "float32",
                "tpy": "float32",
                "tpz": "float32",
                "te": "float32",
                "deltapx": "float32",
                "deltapy": "float32",
                "deltapz": "float32",
                "deltae": "float32",
                "index": "int32",
            },
        )

        event_id = data.index.get_level_values("event_id")
        hit_index = data.index.get_level_values("index")
        f["hits"].extend(
            {
                "event_id": event_id,
                "geometry_id": data["geometry_id"].astype("uint64"),
                "barcode": [common_initial_barcode] * len(event_id),
                "tx": data["tx"],
                "ty": data["ty"],
                "tz": data["tz"],
                "tt": [0] * len(event_id),  # set time to 0 for now
                "tpx": data["tpx"],
                "tpy": data["tpy"],
                "tpz": data["tpz"],
                "te": data["te"],
                "deltapx": data["deltapx"],
                "deltapy": data["deltapy"],
                "deltapz": data["deltapz"],
                "deltae": data["deltae"],
                "index": hit_index,
            },
        )

        logger.info(
            "Written %d entries in %d baskets",
            f["hits"].num_entries,
            f["hits"].num_baskets,
        )


def import_results(logger: Logger, config: Configuration, file: Path) -> None:
    """Validate results."""
    logger.info("Importing data from %s", file)

    reference = preprocess_input(file, "reference_data")
    generated = preprocess_input(file, "generated_data")

    write_hits_tree(logger, config, reference, "reference")
    write_hits_tree(logger, config, generated, "generated")
