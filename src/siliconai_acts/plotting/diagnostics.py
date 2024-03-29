"""Diagnostics plots setup."""

import awkward as ak
import numpy as np
import pandas as pd
import uproot

from siliconai_acts.cli.config import GlobalConfiguration
from siliconai_acts.plotting.common import plot_column
from siliconai_acts.plotting.utils import PDFDocument


def process_particles(particles: ak.Array) -> pd.DataFrame:
    """Process particles."""
    tmp = particles[ak.num(particles.particle_id) == 1]
    event = tmp.event_id
    tmp = ak.without_field(tmp, "event_id")
    data_columns = {"event_id": event} | dict(
        zip(ak.fields(tmp[:, 0]), ak.unzip(tmp[:, 0])),
    )
    data_frame: pd.DataFrame = ak.to_dataframe(ak.zip(data_columns))
    data_frame.insert(4, "vr", np.sqrt(data_frame["vx"] ** 2 + data_frame["vy"] ** 2))
    return data_frame


def plot_particles(global_config: GlobalConfiguration) -> None:
    """Plot particles."""
    file_path = global_config.output_path / "particles.root"
    particles = uproot.open(f"{file_path}:particles").arrays()
    particles_data: pd.DataFrame = process_particles(particles)

    with PDFDocument(global_config.output_path / "diagnostics.pdf") as pdf:  # type: ignore
        for column in particles_data.columns:
            fig, ax = plot_column(particles_data, column)
            if not fig:
                continue
            pdf.save(fig)
