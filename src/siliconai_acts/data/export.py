"""Data export helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import uproot

from siliconai_acts.plotting.diagnostics import process_hits, process_particles

if TYPE_CHECKING:
    from siliconai_acts.cli.config import Configuration
    from siliconai_acts.cli.logging import Logger


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


def export_hits(logger: Logger, config: Configuration) -> None:
    """Export hits for ML usage."""
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
    particles_file_path = config.output_path / "particles_simulation.root"
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
    hits_file_path = config.output_path / "hits.root"
    hits = uproot.open(f"{hits_file_path}:hits").arrays()
    logger.info("Processing hits data...")
    hits_data: pd.DataFrame = process_hits(hits, primary=True)[hits_columns]
    hits_data["index"] = hits_data["index"] + 1
    hits_data = hits_data.set_index(["event_id", "index"])
    hits_data = hits_data.sort_index()
    quantized = ["lxq", "lyq", "tpxq", "tpyq", "tpzq"]
    for col in quantized:
        hits_data[col] = (
            hits_data[col[:-1]].round(2).map(lambda x: np.trunc(100 * x) / 100)
        )
    hits_columns += quantized

    logger.info("Merging particles and hits data...")
    cat_data = pd.concat(
        [particles_data_vertex, hits_data, particles_data_vertex_end],
    ).sort_index()

    output_data = cat_data.join(
        particles_data_common.reindex(cat_data.index, level=0),
    )

    logger.info("Exporting metadata...")
    output_data_float = output_data.select_dtypes(include=["float32", "float64"])
    meta_list = []
    meta_labels = []
    for c in hits_columns + particles_columns_vertex:
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
    with pd.HDFStore(config.output_path / "hits.h5", mode="w") as store:
        store["hits"] = output_data
        store["metadata"] = metadata

    # test
    logger.info("Validating data...")
    with pd.HDFStore(config.output_path / "hits.h5", mode="r") as store:
        print(store.info())  # noqa: T201
        print(store["hits"].loc[[0]])  # noqa: T201
        print(store["hits"].dtypes)  # noqa: T201
        print(store["metadata"])  # noqa: T201
        print(store["metadata"].dtypes)  # noqa: T201
