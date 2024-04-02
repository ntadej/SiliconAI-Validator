"""Diagnostics plots setup."""

from __future__ import annotations

from typing import TYPE_CHECKING

import acts
import awkward as ak
import numpy as np
import uproot

from siliconai_acts.common.enums import ProductionStep
from siliconai_acts.plotting.common import plot_hist
from siliconai_acts.plotting.utils import PDFDocument

if TYPE_CHECKING:
    import pandas as pd

    from siliconai_acts.cli.config import Configuration

u = acts.UnitConstants

common_labels = {
    "particle_type": r"Particle ID",
    "vr": r"Production vertex $r$ [$\mu$m]",
    "vx": r"Production vertex $x$ [$\mu$m]",
    "vy": r"Production vertex $y$ [$\mu$m]",
    "vz": r"Production vertex $z$ [mm]",
    "vt": r"Production vertex $t$ [ns]",
    "p": r"Particle momentum $p$ [GeV]",
    "pt": r"Particle transverse momentum $p_\mathrm{T}$ [GeV]",
    "px": r"Particle momentum $p_x$ [GeV]",
    "py": r"Particle momentum $p_y$ [GeV]",
    "pz": r"Particle momentum $p_z$ [GeV]",
    "q": r"Particle charge $q$",
    "eta": r"Particle pseudorapidity $\eta$",
    "phi": r"Particle azimuthal angle $\phi$",
}

common_scales = {
    "vr": u.um,
    "vx": u.um,
    "vy": u.um,
    "vz": u.mm,
    "vt": u.ns,
}


def diagnostics_label(container: str, step: ProductionStep) -> str:
    """Get diagnostics label."""
    return f"{container} after {step.title}"


def process_particles(particles: ak.Array) -> pd.DataFrame:
    """Process particles."""
    tmp = particles[:]
    event = tmp.event_id
    tmp = ak.without_field(tmp, "event_id")
    data_columns = {"event_id": event} | dict(
        zip(ak.fields(tmp[:, 0]), ak.unzip(tmp[:, 0])),
    )
    data_frame: pd.DataFrame = ak.to_dataframe(ak.zip(data_columns))
    data_frame.insert(4, "vr", np.sqrt(data_frame["vx"] ** 2 + data_frame["vy"] ** 2))
    return data_frame


def plot_particles(config: Configuration, step: ProductionStep) -> None:
    """Plot particles."""
    if step is ProductionStep.Simulation:
        file_name = "particles_simulation.root"
    else:
        file_name = "particles.root"
    out_file_name = "diagnostics_" + file_name.replace(".root", ".pdf")

    file_path = config.output_path / file_name
    particles = uproot.open(f"{file_path}:particles").arrays()
    particles_data: pd.DataFrame = process_particles(particles)
    events = len(particles_data.index)

    columns = [
        "particle_type",
        "vr",
        "vx",
        "vy",
        "vz",
        "vt",
        "p",
        "pt",
        "px",
        "py",
        "pz",
        "q",
        "eta",
        "phi",
    ]

    with PDFDocument(config.output_path / out_file_name) as pdf:  # type: ignore
        for column in columns:
            fig, ax = plot_hist(
                [particles_data[column] / common_scales.get(column, 1)],
                column,
                label_x=common_labels.get(column),
                label_y="Particles",
                labels_extra=[
                    *config.labels,
                    f"{events} events, {diagnostics_label('particles', step)}",
                ],
            )
            if not fig:
                continue
            pdf.save(fig)
