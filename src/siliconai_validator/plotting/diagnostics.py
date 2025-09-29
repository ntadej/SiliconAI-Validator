# Copyright (C) 2024 Tadej Novak
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0

"""Diagnostics plots setup."""

from __future__ import annotations

from typing import TYPE_CHECKING

import acts
import awkward as ak
import matplotlib.pyplot as plt
import numpy as np
import uproot
from particle.pdgid import literals as particle_literals

from siliconai_validator.common.enums import ProductionStep, SimulationParticleOutcome
from siliconai_validator.data.utils import common_initial_barcode
from siliconai_validator.plotting.common import plot_hist, plot_scatter
from siliconai_validator.plotting.utils import PDFDocument

if TYPE_CHECKING:
    import pandas as pd

    from siliconai_validator.cli.config import Configuration

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
    "tr": r"Hit $r$ [mm]",
    "tx": r"Hit $x$ [mm]",
    "ty": r"Hit $y$ [mm]",
    "tz": r"Hit $z$ [mm]",
    "tt": r"Hit $t$ [ns]",
    "tpt": r"Hit particle transverse momentum $p_\mathrm{T}$ [GeV]",
    "tpx": r"Hit particle momentum $p_x$ [GeV]",
    "tpy": r"Hit particle momentum $p_y$ [GeV]",
    "tpz": r"Hit particle momentum $p_z$ [GeV]",
    "lx": r"Hit surface $x$",
    "ly": r"Hit surface $y$",
    "deltae": r"Hit energy loss [GeV]",
    "deltapt": r"Hit transverse momentum change $\Delta p_\mathrm{T}$ [GeV]",
    "deltapx": r"Hit momentum change $\Delta p_x$ [GeV]",
    "deltapy": r"Hit momentum change $\Delta p_y$ [GeV]",
    "deltapz": r"Hit momentum change $\Delta p_z$ [GeV]",
    "nhits": r"Number of hits",
    "nhits_diff": r"Difference in total number of hits",
    # reconstruction
    "eLOC0_fit": "x",
    "eLOC1_fit": "y",
    "ePHI_fit": r"$\phi$",
    "eTHETA_fit": r"$\theta$",
    "eQOP_fit": "q/p",
    "res_eLOC0_fit": r"$x-x_\text{truth}$",
    "pull_eLOC0_fit": r"$(x-x_\text{truth}) / \sigma_x$",
    "res_eLOC1_fit": r"$y-y_\text{truth}$",
    "pull_eLOC1_fit": r"$(y-y_\text{truth}) / \sigma_y$",
    "res_ePHI_fit": r"$\phi-\phi_\text{truth}$",
    "pull_ePHI_fit": r"$(\phi-\phi_\text{truth}) / \sigma_\phi$",
    "res_eTHETA_fit": r"$\theta-\theta_\text{truth}$",
    "pull_eTHETA_fit": r"$(\theta-\theta_\text{truth}) / \sigma_\theta$",
    "res_eQOP_fit": r"$q/p-q/p_\text{truth}$",
    "pull_eQOP_fit": r"$(q/p-q/p_\text{truth}) / \sigma_{q/p}$",
}

common_scales = {
    "vr": u.um,
    "vx": u.um,
    "vy": u.um,
    "vz": u.mm,
    "vt": u.ns,
    "tt": u.ns,
}

common_logx = {
    "deltae": False,
}
common_logy = {
    "e_loss": True,
    "deltae": True,
    "deltapt": True,
    "deltapx": True,
    "deltapy": True,
    "deltapz": True,
    "nhits": True,
    "nhits_diff": True,
    # reco
    "eLOC0_fit": True,
    "eLOC1_fit": False,
    "eQOP_fit": True,
    "res_eLOC0_fit": True,
    "pull_eLOC0_fit": True,
    "res_eLOC1_fit": True,
    "pull_eLOC1_fit": True,
    "res_eQOP_fit": True,
    "pull_eQOP_fit": True,
}

common_binning = {
    # "particle_type": (31, -15.5, 15.5),
    "q": (3, -1.5, 1.5),
    "number_of_hits": (40, 0, 40),
    "number_secondary_particles": (40, 0, 40),
    "vr": (50, -200, 200),
    "vx": (50, -200, 200),
    "vy": (50, -200, 200),
    "vz": (50, -200, 200),
    "tr": (120, 0, 1200),
    "tx": (440, -1100, 1100),
    "ty": (440, -1100, 1100),
    "tz": (120, -600, 600),
    "lx": (110, -55, 55),
    "ly": (110, -55, 55),
    "tpt": (150, 0, 150),
    "tpx": (200, -100, 100),
    "tpy": (200, -100, 100),
    "tpz": (200, -100, 100),
    "nhits": (40, 0, 40),
    "nhits_diff": (7, 0, 7),
    # reconstruction
    "eLOC0_fit": (40, -0.2, 0.2),
    "res_eLOC0_fit": (40, -0.2, 0.2),
    "pull_eLOC0_fit": (40, -10, 10),
    "eQOP_fit": (80, -4e-2, 4e-2),
    "res_ePHI_fit": (80, -4e-3, 4e-3),
    "pull_ePHI_fit": (80, -20, 20),
    "res_eQOP_fit": (80, -4e-2, 4e-2),
    "pull_eQOP_fit": (80, -20, 20),
}

pixel_boundary_r = 200


def diagnostics_label(container: str, step: ProductionStep) -> str:
    """Get diagnostics label."""
    return f"{container} after {step.title}"


def diagnostics_plot(
    pdf: PDFDocument,
    values: pd.Series[float] | list[float] | list[pd.Series[float]] | list[list[float]],
    column: str,
    label_x_base: str,
    label_y: str,
    labels_extra: list[str],
    logx: bool | None = None,
    logy: bool | None = None,
    legend: list[str] | None = None,
    errors: bool = True,
    ratio: bool = True,
) -> bool:
    """Diagnostics plot helper function."""
    label_x = common_labels.get(column)
    if label_x:
        label_x = label_x.replace("Particle", label_x_base)
        label_x = label_x.replace("Hit", label_x_base)

    if logx is None:
        logx = common_logx.get(column, False)
    if logy is None:
        logy = common_logy.get(column, False)
    binning = common_binning.get(column)
    nbins = binning[0] if binning else 25
    bin_range = binning[1:] if binning else None
    if bin_range and bin_range[0] == bin_range[1] and not bin_range[0]:
        bin_range = None

    values_out: list[pd.Series[float]] | list[list[float]]
    if isinstance(values, list):
        values_out = [value / common_scales.get(column, 1) for value in values]
    else:
        values_out = [values / common_scales.get(column, 1)]

    fig, _ = plot_hist(
        values_out,
        column,
        label_x=label_x,
        label_y=label_y,
        labels_extra=labels_extra,
        nbins=nbins,
        bin_range=bin_range,
        logx=logx,
        logy=logy,
        legend=legend,
        errors=errors,
        ratio=ratio,
    )
    if not fig:
        return False
    fig.set_size_inches(6, 5)
    pdf.save(fig)
    plt.close(fig)
    return True


def diagnostics_scatter_plot(
    pdf: PDFDocument,
    values_x: list[pd.Series[float] | np.typing.ArrayLike],
    values_y: list[pd.Series[float] | np.typing.ArrayLike],
    column_x: str,
    column_y: str,
    label_x_base: str,
    label_y_base: str,
    labels_extra: list[str],
    aspect: float | None = None,
) -> bool:
    """Diagnostics scatter plot helper function."""
    label_x = common_labels.get(column_x)
    if label_x:
        label_x = label_x.replace("Particle", label_x_base)
        label_x = label_x.replace("Hit", label_x_base)
    label_y = common_labels.get(column_y)
    if label_y:
        label_y = label_y.replace("Particle", label_y_base)
        label_y = label_y.replace("Hit", label_y_base)

    fig, ax = plot_scatter(
        [vx / common_scales.get(column_x, 1) for vx in values_x],
        [vy / common_scales.get(column_y, 1) for vy in values_y],
        label_x=label_x,
        label_y=label_y,
        labels_extra=labels_extra,
    )

    if not fig:
        return False
    if ax and aspect:
        ax.set_aspect(aspect)
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
            zip(ak.fields(tmp[:, 0]), ak.unzip(tmp[:, 0]), strict=False),
        )
        data_frame = ak.to_dataframe(ak.zip(data_columns))
    else:
        data_frame = ak.to_dataframe(tmp)
        data_frame = data_frame.drop(level="subentry", index=0)

    data_frame.insert(4, "vr", np.sqrt(data_frame["vx"] ** 2 + data_frame["vy"] ** 2))
    return data_frame


def plot_particles(config: Configuration, step: ProductionStep) -> None:  # noqa: C901
    """Plot particles."""
    if step is ProductionStep.Simulation:
        file_name = "particles_simulation.root"
    else:
        file_name = "particles.root"
    out_file_name = "diagnostics_" + file_name.replace(".root", ".pdf")

    file_path = config.output_path / file_name
    particles = uproot.open(f"{file_path}:particles").arrays()
    particles_data: pd.DataFrame = process_particles(particles, primary=True)
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
        # "vt",
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

    with PDFDocument(config.output_path / out_file_name) as pdf:
        for column in columns:
            diagnostics_plot(
                pdf,
                particles_data[column],
                column,
                "Primary particle" if step is ProductionStep.Simulation else "Particle",
                "Particles",
                labels_extra,
            )

        if step is ProductionStep.Simulation and len(particles_data_secondary):
            secondary_useful_base = particles_data_secondary[
                (
                    particles_data_secondary["outcome"]
                    == SimulationParticleOutcome.EscapedAndKilled.value
                )
                | (particles_data_secondary["number_of_hits"] > 0)
            ]
            secondary_useful = secondary_useful_base[
                abs(secondary_useful_base["particle_type"])
                <= particle_literals.gamma.abspid  # type: ignore
            ]
            secondary_cut = secondary_useful[secondary_useful["pt"] > cut]

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

            for counts in [
                particle_counts,
                particle_counts_cut,
            ]:
                diagnostics_plot(
                    pdf,
                    [counts],  # type: ignore[arg-type]
                    "number_secondary_particles",
                    "",
                    "Events",
                    labels_extra_with_cut
                    if counts is particle_counts_cut
                    else labels_extra,
                    logy=True,
                )

            for column in columns_secondary:
                if column[0] == "v":
                    continue
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
                if column[0] == "v":
                    continue
                diagnostics_plot(
                    pdf,
                    secondary_cut[column],
                    column,
                    "Secondary particle",
                    "Particles",
                    labels_extra_with_cut,
                    logy=True,
                )


def process_hits(hits: ak.Array, primary: bool = True) -> pd.DataFrame:
    """Process hits."""
    tmp = hits[:]

    data_frame: pd.DataFrame
    data_frame = ak.to_dataframe(tmp)
    if primary:
        data_frame = data_frame[data_frame["particle_id"] == common_initial_barcode]
    else:
        data_frame = data_frame[data_frame["particle_id"] != common_initial_barcode]

    data_frame["deltae"] = np.abs(data_frame["deltae"])

    data_frame.insert(3, "tr", np.sqrt(data_frame["tx"] ** 2 + data_frame["ty"] ** 2))
    data_frame.insert(
        8,
        "tpt",
        np.sqrt(data_frame["tpx"] ** 2 + data_frame["tpy"] ** 2),
    )
    data_frame.insert(
        13,
        "deltapt",
        np.sqrt(
            (data_frame["tpx"] + data_frame["deltapx"]) ** 2
            + (data_frame["tpy"] + data_frame["deltapy"]) ** 2,
        )
        - data_frame["tpt"],
    )

    data_frame["tpx"] += data_frame["deltapx"]
    data_frame["tpy"] += data_frame["deltapy"]
    data_frame["tpz"] += data_frame["deltapz"]
    data_frame["tpt"] += data_frame["deltapt"]

    from siliconai_validator.data.utils import global_to_local_vec

    if len(data_frame):
        local_data = global_to_local_vec(
            data_frame["geometry_id"],
            data_frame["tx"],
            data_frame["ty"],
            data_frame["tz"],
        )
        data_frame["lx"] = local_data[0]
        data_frame["lx"] = data_frame["lx"].astype("float32")
        data_frame["ly"] = local_data[1]
        data_frame["ly"] = data_frame["ly"].astype("float32")
    else:
        data_frame["lx"] = data_frame["tx"]
        data_frame["ly"] = data_frame["ty"]

    return data_frame


def plot_hits(config: Configuration) -> None:
    """Plot hits."""
    file_name = "hits.root"
    out_file_name = "diagnostics_" + file_name.replace(".root", ".pdf")

    file_path = config.output_path / file_name
    hits = uproot.open(f"{file_path}:hits").arrays()
    hits_data_primary: pd.DataFrame = process_hits(hits, primary=True)
    hits_data_secondary: pd.DataFrame = process_hits(hits, primary=False)

    hits_data_primary_pixel = hits_data_primary[
        hits_data_primary["tr"] < pixel_boundary_r
    ]
    hits_data_secondary_pixel = hits_data_secondary[
        hits_data_secondary["tr"] < pixel_boundary_r
    ]

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
    columns_momentum = [
        "deltae",
        "deltapt",
        "deltapx",
        "deltapy",
        "deltapz",
    ]
    columns = columns_position + columns_local_position + columns_momentum

    labels_extra = [
        *config.labels,
        f"{config.events} events",
    ]
    labels_extra_primary = [
        *labels_extra,
        "primary particles only",
    ]
    labels_extra_primary_pixel = [
        *labels_extra,
        "primary particles only, pixel only",
    ]
    labels_extra_secondary = [
        *labels_extra,
        "secondary particles only",
    ]
    labels_extra_secondary_pixel = [
        *labels_extra,
        "secondary particles only, pixel only",
    ]

    with PDFDocument(config.output_path / out_file_name) as pdf:
        for data, label_base, labels in zip(
            [
                hits_data_primary,
                hits_data_primary_pixel,
                hits_data_secondary,
                hits_data_secondary_pixel,
            ],
            [
                "Primary hit",
                "Primary hit",
                "Secondary hit",
                "Secondary hit",
            ],
            [
                labels_extra_primary,
                labels_extra_primary_pixel,
                labels_extra_secondary,
                labels_extra_secondary_pixel,
            ],
            strict=False,
        ):
            diagnostics_scatter_plot(
                pdf,
                [data["tx"]],
                [data["ty"]],
                "tx",
                "ty",
                label_base,
                label_base,
                labels,
                aspect=1,
            )

            diagnostics_scatter_plot(
                pdf,
                [data["tz"]],
                [data["tr"]],
                "tz",
                "tr",
                label_base,
                label_base,
                labels,
            )

            if len(data):
                hits_count = data.reset_index().groupby("event_id").count()["index"]
                diagnostics_plot(
                    pdf,
                    hits_count,
                    "nhits",
                    "Primary hit",
                    "Events",
                    labels_extra_primary,
                )

        for column in columns:
            diagnostics_plot(
                pdf,
                hits_data_primary[column],
                column,
                "Primary hit",
                "Hits",
                labels_extra_primary,
            )

        if len(hits_data_secondary):
            for column in columns:
                diagnostics_plot(
                    pdf,
                    hits_data_secondary[column],
                    column,
                    "Secondary hit",
                    "Hits",
                    labels_extra_secondary,
                )
