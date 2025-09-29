# Copyright (C) 2024 Tadej Novak
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0

"""Results validation."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import awkward as ak
import numpy as np
import pandas as pd
import uproot

from siliconai_validator.data.export import geometry_id_end, geometry_id_start
from siliconai_validator.plotting.common import plot_errorbar
from siliconai_validator.plotting.diagnostics import (
    diagnostics_plot,
    diagnostics_scatter_plot,
)
from siliconai_validator.plotting.utils import PDFDocument

if TYPE_CHECKING:
    from pathlib import Path

    from siliconai_validator.cli.config import Configuration


def preprocess_input(file: Path, key: str) -> pd.DataFrame:
    """Preprocess input data."""
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

    data["tpx"] = data["tpxq"]
    data["tpy"] = data["tpyq"]
    data["tpz"] = data["tpzq"]
    data["tpt"] = np.sqrt(data["tpx"] ** 2 + data["tpy"] ** 2)

    from siliconai_validator.data.utils import local_to_global_vec

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
    event: int = -1,
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
    columns_momentum = [
        "tpt",
        "tpx",
        "tpy",
        "tpz",
    ]
    columns = columns_position + columns_local_position + columns_momentum
    size = len(reference_data.groupby("event_id").size())

    labels_extra = [*config.labels, f"{size} events"]
    labels_extra_primary = [
        *labels_extra,
        "primary particles only",
    ]

    if event >= 0:
        file_suffix = f"{file_suffix}_{event}"

    with PDFDocument(config.output_path / f"validation_{file_suffix}.pdf") as pdf:
        if not isinstance(reference_data.index, pd.MultiIndex) or not isinstance(
            generated_data.index,
            pd.MultiIndex,
        ):
            error = "Index must be a MultiIndex"
            raise TypeError(error)

        if event >= 0:
            reference_data = reference_data.loc[[event]]
            generated_data = generated_data.loc[[event]]

        reference_hits = (
            reference_data.reset_index().groupby("event_id").count()["index"]
        )
        generated_hits = (
            generated_data.reset_index().groupby("event_id").count()["index"]
        )

        diff_hits = abs(reference_hits - generated_hits)

        if event >= 0:
            diagnostics_scatter_plot(
                pdf,
                [reference_data["tx"], generated_data["tx"]],
                [reference_data["ty"], generated_data["ty"]],
                "tx",
                "ty",
                "Primary hit",
                "Primary hit",
                labels_extra_primary,
            )

            diagnostics_scatter_plot(
                pdf,
                [reference_data["tz"], generated_data["tz"]],
                [reference_data["tr"], generated_data["tr"]],
                "tz",
                "tr",
                "Primary hit",
                "Primary hit",
                labels_extra_primary,
            )

        diagnostics_plot(
            pdf,
            [reference_hits, generated_hits],
            "nhits",
            "Primary hit",
            "Events",
            labels_extra_primary,
            legend=["Geant4", "Neural network"],
            errors=event < 0,
        )

        diagnostics_plot(
            pdf,
            [diff_hits],
            "nhits_diff",
            "Primary hit",
            "Events",
            labels_extra_primary,
            errors=event < 0,
        )

        for column in columns:
            diagnostics_plot(
                pdf,
                [reference_data[column], generated_data[column]],
                column,
                "Primary hit",
                "Hits",
                labels_extra_primary,
                legend=["Geant4", "Neural network"],
                errors=event < 0,
            )


def validate(config: Configuration, file: Path, event: int = -1) -> None:
    """Validate results."""
    reference = preprocess_input(file, "reference_data")
    generated = preprocess_input(file, "generated_data")

    validate_hits(config, file.stem, reference, generated, event)


def validate_reconstruction_performance(config: Configuration) -> None:
    """Validate reconstruction results."""
    reference_file_seeding = (
        config.output_path / "reference" / "performance_seeding.root"
    )
    generated_file_seeding = (
        config.output_path / "generated" / "performance_seeding.root"
    )

    reference_file_ckf = (
        config.output_path / "reference" / "performance_fitting_ckf.root"
    )
    generated_file_ckf = (
        config.output_path / "generated" / "performance_fitting_ckf.root"
    )

    import skhep_testdata

    with uproot.open(skhep_testdata.data_path("uproot-issue38c.root")) as fp:
        hist = fp["TEfficiencyName"]  # noqa: F841

    with (
        uproot.open(reference_file_seeding) as file_ref_seeding,
        uproot.open(generated_file_seeding) as file_gen_seeding,
        uproot.open(reference_file_ckf) as file_ref_ckf,
        uproot.open(generated_file_ckf) as file_gen_ckf,
        PDFDocument(config.output_path / "validation_reco_performance.pdf") as pdf,
    ):
        for file_ref, file_gen, file_label in [
            (file_ref_seeding, file_gen_seeding, "Seeding"),
            (file_ref_ckf, file_gen_ckf, "CKF"),
        ]:
            for variable, variable_label in [
                ("trackeff_vs_pT", "Track momentum [GeV]"),
                ("trackeff_vs_z0", "Track z_0 [mm]"),
            ]:
                reference_eff_passed = (
                    file_ref[variable].member("fPassedHistogram").to_numpy()
                )
                reference_eff_total = (
                    file_ref[variable].member("fTotalHistogram").to_numpy()
                )
                generated_eff_passed = (
                    file_gen[variable].member("fPassedHistogram").to_numpy()
                )
                generated_eff_total = (
                    file_gen[variable].member("fTotalHistogram").to_numpy()
                )

                indices = reference_eff_total[0] > 0
                indices_bins = np.append(reference_eff_total[0] > 0, False)
                indices_bins[np.nonzero(indices_bins)[0][-1] + 1] = True

                reference_passed = reference_eff_passed[0][indices]
                reference_total = reference_eff_total[0][indices]
                generated_passed = generated_eff_passed[0][indices]
                generated_total = generated_eff_total[0][indices]

                bins = reference_eff_total[1][indices_bins]
                bin_centers = bins[1:] - (bins[1] - bins[0]) / 2
                bin_errors = len(reference_total) * [(bins[1] - bins[0]) / 2]

                reference_efficiency = reference_passed / reference_total
                reference_err = (
                    np.sqrt(reference_passed) / reference_total * reference_efficiency
                )
                generated_efficiency = generated_passed / generated_total
                generated_err = (
                    np.sqrt(generated_passed) / generated_total * generated_efficiency
                )

                labels_extra = [
                    *config.labels,
                    f"{config.events} events",
                ]
                labels_extra_primary = [
                    *labels_extra,
                    "primary particles only",
                ]

                fig, _ = plot_errorbar(
                    bin_centers,
                    bin_errors,
                    [reference_efficiency, generated_efficiency],
                    [reference_err, generated_err],
                    legend=["Geant4", "Neural network"],
                    label_x=variable_label,
                    label_y=f"{file_label} efficiency",
                    labels_extra=labels_extra_primary,
                )
                if fig:
                    fig.set_size_inches(6, 5)
                    pdf.save(fig)
                    # plt.close(fig)


def validate_reconstruction_tracks(config: Configuration) -> None:
    """Validate reconstruction results."""
    reference_file = config.output_path / "reference" / "tracksummary_ckf.root"
    generated_file = config.output_path / "generated" / "tracksummary_ckf.root"

    reference_data = uproot.open(f"{reference_file}:tracksummary").arrays()
    generated_data = uproot.open(f"{generated_file}:tracksummary").arrays()

    with PDFDocument(config.output_path / "validation_reco_tracks.pdf") as pdf:
        for variable in [
            "eLOC0_fit",
            "eLOC1_fit",
            "ePHI_fit",
            "eTHETA_fit",
            "eQOP_fit",
            "res_eLOC0_fit",
            "pull_eLOC0_fit",
            "res_eLOC1_fit",
            "pull_eLOC1_fit",
            "res_ePHI_fit",
            "pull_ePHI_fit",
            "res_eTHETA_fit",
            "pull_eTHETA_fit",
            "res_eQOP_fit",
            "pull_eQOP_fit",
        ]:
            reference_value = ak.flatten(reference_data[variable]).to_numpy()
            generated_value = ak.flatten(generated_data[variable]).to_numpy()

            labels_extra = [
                *config.labels,
                f"{config.events} events",
            ]
            labels_extra_primary = [
                *labels_extra,
                "primary particles only",
            ]

            diagnostics_plot(
                pdf,
                [reference_value, generated_value],
                variable,
                "Track",
                "Tracks",
                labels_extra_primary,
                legend=["Geant4", "Neural network"],
                ratio="res_" not in variable and "pull_" not in variable,
            )
