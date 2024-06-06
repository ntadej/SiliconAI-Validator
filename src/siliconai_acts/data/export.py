"""Data export helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import uproot

from siliconai_acts.plotting.diagnostics import process_hits, process_particles

if TYPE_CHECKING:
    from siliconai_acts.cli.config import Configuration


geometry_id_start = 10000


def export_hits(config: Configuration) -> None:
    """Export hits for ML usage."""
    particles_columns_common = ["event_id", "particle_type"]
    particles_columns_vertex = ["event_id", "vx", "vy", "vz"]
    particles_file_path = config.output_path / "particles.root"
    particles = uproot.open(f"{particles_file_path}:particles").arrays()
    particles_data_common: pd.DataFrame = process_particles(particles, primary=True)[
        particles_columns_common
    ]
    particles_data_vertex: pd.DataFrame = process_particles(particles, primary=True)[
        particles_columns_vertex
    ]
    particles_data_common = particles_data_common.set_index("event_id")
    particles_data_vertex.insert(0, "index", 0)
    particles_data_vertex = particles_data_vertex.set_index(["event_id", "index"])

    particles_data_vertex.insert(0, "geometry_id", geometry_id_start)
    particles_data_vertex["geometry_id"] = particles_data_vertex["geometry_id"].astype(
        "uint64",
    )
    particles_data_vertex = particles_data_vertex.rename(
        columns={"vx": "tx", "vy": "ty", "vz": "tz"},
    )
    particles_data_vertex["lx"] = particles_data_vertex["tx"]
    particles_data_vertex["ly"] = (
        particles_data_vertex["tz"] / particles_data_vertex["tz"].abs().max() * 50
    )
    particles_data_vertex["lxq"] = particles_data_vertex["lx"].round(2)
    particles_data_vertex["lyq"] = particles_data_vertex["ly"].round(2)
    particles_data_vertex = particles_data_vertex.sort_index()

    hits_columns = ["event_id", "geometry_id", "index", "tx", "ty", "tz", "lx", "ly"]
    hits_file_path = config.output_path / "hits.root"
    hits = uproot.open(f"{hits_file_path}:hits").arrays()
    hits_data: pd.DataFrame = process_hits(hits, primary=True)[hits_columns]
    hits_data["index"] = hits_data["index"] + 1
    hits_data = hits_data.set_index(["event_id", "index"])
    hits_data = hits_data.sort_index()
    hits_data["lxq"] = hits_data["lx"].round(2).map(lambda x: np.trunc(100 * x) / 100)
    hits_data["lyq"] = (
        hits_data["ly"].round(2).round(2).map(lambda x: np.trunc(100 * x) / 100)
    )
    hits_columns += ["lxq", "lyq"]

    cat_data = pd.concat([particles_data_vertex, hits_data]).sort_index()

    output_data = cat_data.join(
        particles_data_common.reindex(cat_data.index, level=0),
    )

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

    with pd.HDFStore(config.output_path / "hits.h5", mode="w") as store:
        store["hits"] = output_data
        store["metadata"] = metadata

    # test
    with pd.HDFStore(config.output_path / "hits.h5", mode="r") as store:
        print(store.info())  # noqa: T201
        print(store["hits"])  # noqa: T201
        print(store["hits"].dtypes)  # noqa: T201
        print(store["metadata"])  # noqa: T201
        print(store["metadata"].dtypes)  # noqa: T201
