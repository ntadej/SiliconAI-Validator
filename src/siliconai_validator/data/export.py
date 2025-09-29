# Copyright (C) 2024 Tadej Novak
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0

"""Data export helpers."""

from __future__ import annotations

from functools import partial
from multiprocessing import Pool
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import uproot

from siliconai_validator.plotting.diagnostics import process_hits, process_particles
from siliconai_validator.scheduling.submission import (
    create_slurm_run_script,
    create_slurm_submission_script,
)

if TYPE_CHECKING:
    from pathlib import Path

    from siliconai_validator.cli.config import Configuration
    from siliconai_validator.cli.logger import Logger


geometry_id_start = 1000000
geometry_id_end = 1000001


def process_particle_vertices_as_hits(
    vertex_data: pd.DataFrame,
    end_vertex: bool = False,
) -> pd.DataFrame:
    """Process particle vertices as hits."""
    vertex_data.insert(
        0,
        "index",
        vertex_data["number_of_hits"] + 1 if end_vertex else 0,
    )
    vertex_data = vertex_data.set_index(["event_id", "index"])
    vertex_data = vertex_data.drop(columns=["number_of_hits"])

    vertex_data.insert(
        0,
        "geometry_id",
        geometry_id_end if end_vertex else geometry_id_start,
    )
    vertex_data["geometry_id"] = vertex_data["geometry_id"].astype("uint64")

    vertex_data = vertex_data.rename(
        columns={
            "vx": "tx",
            "vy": "ty",
            "vz": "tz",
            "px": "tpx",
            "py": "tpy",
            "pz": "tpz",
        },
    )
    if end_vertex:
        vertex_data["tz"] = vertex_data["tx"]
        vertex_data["lx"] = vertex_data["tx"]
        vertex_data["ly"] = vertex_data["tx"]
    else:
        vertex_data["lx"] = vertex_data["tx"]
        vertex_data["ly"] = vertex_data["tz"] / vertex_data["tz"].abs().max() * 50

    vertex_data["lxq"] = (
        vertex_data["lx"].round(2).map(lambda x: np.trunc(100 * x) / 100)
    )
    vertex_data["lyq"] = (
        vertex_data["ly"].round(2).map(lambda x: np.trunc(100 * x) / 100)
    )

    vertex_data["tpxq"] = (
        vertex_data["tpx"].round(2).map(lambda x: np.trunc(100 * x) / 100)
    )
    vertex_data["tpyq"] = (
        vertex_data["tpy"].round(2).map(lambda x: np.trunc(100 * x) / 100)
    )
    vertex_data["tpzq"] = (
        vertex_data["tpz"].round(2).map(lambda x: np.trunc(100 * x) / 100)
    )

    return vertex_data.sort_index()


def export_hits_single(  # noqa: PLR0915
    index: int,
    logger: Logger,
    config: Configuration,
    fixed_length: bool = False,
) -> None:
    """Export single-file hits for ML usage."""
    logger.info("Loading particles data...")
    particles_columns_common = ["event_id", "particle_type", "number_of_hits"]
    particles_columns_vertex = [
        "event_id",
        "vx",
        "vy",
        "vz",
        "px",
        "py",
        "pz",
        "number_of_hits",
    ]
    particles_file_path = config.output_path / "particles_simulation" / f"{index}.root"
    particles = uproot.open(f"{particles_file_path}:particles").arrays()
    logger.info("Processing particles data...")
    particles_data_common: pd.DataFrame = process_particles(particles, primary=True)[
        particles_columns_common
    ]
    particles_data_vertex: pd.DataFrame = process_particles(particles, primary=True)[
        particles_columns_vertex
    ]
    particles_data_vertex_end: pd.DataFrame = particles_data_vertex.copy(deep=True)

    logger.info("Postprocessing particles data...")
    particles_data_common = particles_data_common.set_index("event_id")

    particles_data_vertex = process_particle_vertices_as_hits(
        particles_data_vertex,
        end_vertex=False,
    )
    particles_data_vertex_end = process_particle_vertices_as_hits(
        particles_data_vertex_end,
        end_vertex=True,
    )
    # TODO: fix end vertex pt

    logger.info("Loading hits data...")
    hits_columns = [
        "event_id",
        "geometry_id",
        "index",
        "tx",
        "ty",
        "tz",
        "tpx",
        "tpy",
        "tpz",
        "lx",
        "ly",
    ]
    hits_columns_out = [
        "geometry_id",
        "particle_type",
    ]
    hits_file_path = config.output_path / "hits" / f"{index}.root"
    hits = uproot.open(f"{hits_file_path}:hits").arrays()
    hits["barcode"] = hits["barcode"][:, 2]
    logger.info("Processing hits data...")
    hits_data: pd.DataFrame = process_hits(hits, primary=True)[hits_columns]
    hits_data["index"] = hits_data["index"] + 1
    hits_data = hits_data.set_index(["event_id", "index"])
    hits_data = hits_data.sort_index()
    quantized = ["lxq", "lyq", "tpxq", "tpyq", "tpzq"]
    for col in quantized:
        hits_data[col] = hits_data[col[:-1]].map(
            lambda x: np.trunc(np.floor(x * 100) if x > 0 else np.ceil(x * 100)) / 100,
        )
    hits_columns += quantized
    hits_columns_out += quantized

    logger.info("Merging particles and hits data...")
    cat_data = pd.concat(
        [particles_data_vertex, hits_data, particles_data_vertex_end],
    ).sort_index()

    output_data = cat_data.join(
        particles_data_common.reindex(cat_data.index, level=0),
    )

    if fixed_length:
        logger.info("Using fixed-lenght sequences...")
        hits_count = output_data.reset_index().groupby("event_id").size()
        hits_count_values = hits_count.value_counts()
        wanted_length = hits_count_values.head(1).index[0]
        logger.info("  sequence length: %d", wanted_length)
        output_data = output_data[output_data["number_of_hits"] == wanted_length - 2]
        output_size = output_data.reset_index().groupby("event_id").size().shape[0]
        logger.info("  remaining number of sequences: %d", output_size)
        output_data.index = output_data.index.remove_unused_levels().set_levels(
            list(range(output_size)),
            level=0,
        )

    output_data = output_data[hits_columns_out]

    logger.info("Exporting metadata...")
    output_data_float = output_data.select_dtypes(include=["float32", "float64"])
    meta_list = []
    meta_labels = []
    for c in hits_columns_out:
        if c not in output_data_float:
            continue

        meta_labels.append(c)
        meta_list.append(
            [
                output_data_float[c].min(),
                output_data_float[c].max(),
                output_data_float[c].mean(),
                output_data_float[c].std(),
            ],
        )

    metadata = pd.DataFrame(
        meta_list,
        columns=["min", "max", "mean", "std"],
        index=meta_labels,
    )

    logger.info("Exporting data...")
    with pd.HDFStore(config.output_path / "hits" / f"{index}.h5", mode="w") as store:
        output_data = output_data.reset_index()
        store.put("hits", output_data, format="table", complib="zlib")
        store.put("metadata", metadata, format="table", complib="zlib")

    # test
    logger.info("Validating data...")
    with pd.HDFStore(config.output_path / "hits" / f"{index}.h5", mode="r") as store:
        test_hits = store["hits"].set_index(["event_id", "index"])
        print(store.info())  # noqa: T201
        print(test_hits.loc[[0]])  # noqa: T201
        print(test_hits.dtypes)  # noqa: T201
        print(store["metadata"])  # noqa: T201
        print(store["metadata"].dtypes)  # noqa: T201


def export_hits(
    logger: Logger,
    config: Configuration,
    fixed_length: bool = False,
    task_id: int = -1,
    slurm: bool = False,
) -> None:
    """Export hits for ML usage."""
    nfiles = len(list((config.output_path / "hits").glob("*.root")))

    if slurm:
        logger.info("Preparing %d jobs for %d files", nfiles, nfiles)

        script = create_slurm_submission_script(
            f"Export_{config.output_name}",
            config.output_path / "run",
        )
        for index in range(1, nfiles + 1):
            create_run_script(
                index,
                config.location,
                config.output_path / "run",
            )

        logger.info("Prepared submission script: %s", script)
        return

    # run the process pool
    if task_id > 0:
        if task_id > nfiles:
            error = f"Task ID {task_id} is larger than the number of files {nfiles}."
            raise ValueError(error)

        logger.info("Running single task ID %d", task_id)
        export_hits_single(
            task_id,
            logger=logger,
            config=config,
            fixed_length=fixed_length,
        )
        return

    logger.info(
        "Spawning %d processes for %d files",
        config.global_config.threads,
        nfiles,
    )
    with Pool(config.global_config.threads) as p:
        p.starmap(
            partial(
                export_hits_single,
                logger=logger,
                config=config,
                fixed_length=fixed_length,
            ),
            zip(range(1, nfiles + 1), strict=True),
        )


def create_run_script(
    task_id: int,
    config_file: Path,
    run_path: Path,
) -> Path:
    """Create a script to run exporting on a file."""
    script_run_path = run_path / f"proc_{task_id}"
    if not script_run_path.exists():
        script_run_path.mkdir(parents=True)

    command = f"siliconai_validator export -c {config_file} -t {task_id}"

    return create_slurm_run_script(script_run_path, command)
