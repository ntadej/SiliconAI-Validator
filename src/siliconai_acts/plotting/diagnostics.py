"""Diagnostics plots setup."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import acts
import awkward as ak
import matplotlib.pyplot as plt
import numpy as np
import uproot
from particle.pdgid import literals as particle_literals

from siliconai_acts.common.enums import ProductionStep, SimulationParticleStatus
from siliconai_acts.plotting.common import plot_hist
from siliconai_acts.plotting.utils import PDFDocument

if TYPE_CHECKING:
    import pandas as pd

    from siliconai_acts.cli.config import Configuration

u = acts.UnitConstants

common_labels = {
    "particle_type": r"Particle ID",
    "vr": r"Particle production vertex $r$ [$\mu$m]",
    "vx": r"Particle production vertex $x$ [$\mu$m]",
    "vy": r"Particle production vertex $y$ [$\mu$m]",
    "vz": r"Particle production vertex $z$ [mm]",
    "vt": r"Particle production vertex $t$ [ns]",
    "p": r"Particle momentum $p$ [GeV]",
    "pt": r"Particle transverse momentum $p_\mathrm{T}$ [GeV]",
    "px": r"Particle momentum $p_x$ [GeV]",
    "py": r"Particle momentum $p_y$ [GeV]",
    "pz": r"Particle momentum $p_z$ [GeV]",
    "q": r"Particle charge $q$",
    "eta": r"Particle pseudorapidity $\eta$",
    "phi": r"Particle azimuthal angle $\phi$",
    "e_loss": r"Particle energy loss [GeV]",
    "number_of_hits": r"Particle number of hits",
    "number_secondary_particles": r"Number of secondary particles",
}

common_scales = {
    "vr": u.um,
    "vx": u.um,
    "vy": u.um,
    "vz": u.mm,
    "vt": u.ns,
}

common_logy = {
    "e_loss": True,
}


def diagnostics_label(container: str, step: ProductionStep) -> str:
    """Get diagnostics label."""
    return f"{container} after {step.title}"


def diagnostics_plot(
    pdf: PDFDocument,
    values: pd.Series[float] | np.typing.ArrayLike,
    column: str,
    label_x_base: str,
    label_y: str,
    labels_extra: list[str],
    logy: Optional[bool] = None,
) -> bool:
    """Diagnostics plot helper function."""
    label_x = common_labels.get(column)
    if label_x:
        label_x = label_x.replace("Particle", label_x_base)

    if logy is None:
        logy = common_logy.get(column, False)

    fig, ax = plot_hist(
        [values / common_scales.get(column, 1)],
        column,
        label_x=label_x,
        label_y=label_y,
        labels_extra=labels_extra,
        logy=logy,
    )
    if not fig:
        return False
    fig.set_size_inches(6, 5)
    pdf.save(fig)
    plt.close(fig)
    return True


def process_particles(particles: ak.Array, primary: bool = True) -> pd.DataFrame:
    """Process particles."""
    tmp = particles[:]
    event = tmp.event_id

    data_frame: pd.DataFrame
    if primary:
        tmp = ak.without_field(tmp, "event_id")
        data_columns = {"event_id": event} | dict(
            zip(ak.fields(tmp[:, 0]), ak.unzip(tmp[:, 0])),
        )
        data_frame = ak.to_dataframe(ak.zip(data_columns))
    else:
        data_frame = ak.to_dataframe(tmp)
        data_frame = data_frame.drop(level="subentry", index=0)

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
    particles_data_secondary: pd.DataFrame = process_particles(particles, primary=False)
    events = len(particles_data.index)

    columns_base = [
        "particle_type",
        "q",
    ]
    columns_position = [
        "eta",
        "phi",
    ]
    columns_momentum = [
        "p",
        "pt",
        "px",
        "py",
        "pz",
    ]
    columns_vertex = [
        "vr",
        "vx",
        "vy",
        "vz",
        "vt",
    ]
    columns = columns_base + columns_position + columns_momentum
    if step is ProductionStep.Generation:
        columns += columns_vertex
    else:
        columns += ["e_loss", "number_of_hits"]
        columns_secondary = columns[:]
        columns_secondary += columns_vertex

    labels_extra = [
        *config.labels,
        f"{events} events, {diagnostics_label('particles', step)}",
    ]
    if step is ProductionStep.Simulation:
        cut = config.simulation.secondaries_min_pt
        labels_extra_with_cut = [
            *labels_extra,
            rf"with $p_\mathrm{{T}} > {cut:.2f}$ GeV",
        ]
        labels_extra_special = [
            *labels_extra,
            rf"with PDG ID > {particle_literals.gamma.abspid}",  # type: ignore
        ]

    with PDFDocument(config.output_path / out_file_name) as pdf:  # type: ignore
        for column in columns:
            diagnostics_plot(
                pdf,
                particles_data[column],
                column,
                "Primary particle" if step is ProductionStep.Simulation else "Particle",
                "Particles",
                labels_extra,
            )

        if step is ProductionStep.Simulation:
            secondary_useful_base = particles_data_secondary[
                (
                    particles_data_secondary["status"]
                    == SimulationParticleStatus.EscapedAndKilled.value
                )
                | (particles_data_secondary["number_of_hits"] > 0)
            ]
            secondary_useful = secondary_useful_base[
                abs(secondary_useful_base["particle_type"])
                <= particle_literals.gamma.abspid  # type: ignore
            ]
            secondary_cut = secondary_useful[secondary_useful["pt"] > cut]
            secondary_special = secondary_useful_base[
                abs(secondary_useful_base["particle_type"])
                > particle_literals.gamma.abspid  # type: ignore
            ]

            particle_counts = (
                secondary_useful.groupby(["event_id"])["particle_id"].count().to_numpy()
            )
            particle_counts = np.pad(
                particle_counts,
                (0, events - len(particle_counts)),
                "constant",
            )
            particle_counts_cut = (
                secondary_cut.groupby(["event_id"])["particle_id"].count().to_numpy()
            )
            particle_counts_cut = np.pad(
                particle_counts_cut,
                (0, events - len(particle_counts_cut)),
                "constant",
            )
            particle_counts_special = (
                secondary_special.groupby(["event_id"])["particle_id"]
                .count()
                .to_numpy()
            )
            particle_counts_special = np.pad(
                particle_counts_special,
                (0, events - len(particle_counts_special)),
                "constant",
            )

            for counts in [
                particle_counts,
                particle_counts_cut,
                particle_counts_special,
            ]:
                diagnostics_plot(
                    pdf,
                    counts,
                    "number_secondary_particles",
                    "",
                    "Events",
                    labels_extra_special
                    if counts is particle_counts_special
                    else labels_extra_with_cut
                    if counts is particle_counts_cut
                    else labels_extra,
                    logy=True,
                )

            for column in columns_secondary:
                diagnostics_plot(
                    pdf,
                    secondary_useful[column],
                    column,
                    "Secondary particle",
                    "Particles",
                    labels_extra,
                    logy=True,
                )
            for column in columns_secondary:
                diagnostics_plot(
                    pdf,
                    secondary_cut[column],
                    column,
                    "Secondary particle",
                    "Particles",
                    labels_extra_with_cut,
                    logy=True,
                )
            for column in columns_secondary:
                diagnostics_plot(
                    pdf,
                    secondary_special[column],
                    column,
                    "Secondary particle",
                    "Particles",
                    labels_extra_special,
                    logy=True,
                )
