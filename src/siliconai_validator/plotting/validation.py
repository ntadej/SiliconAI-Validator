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


def validate_reconstruction_performance(  # noqa: C901 PLR0915
    config: Configuration,
    extended: bool = False,
) -> None:
    """Validate reconstruction results."""
    if extended:
        original_file_seeding = (
            config.output_path / "reco_geant4" / "performance_seeding.root"
        )
        fatras_file_seeding = (
            config.output_path / "reco_fatras" / "performance_seeding.root"
        )
    reference_file_seeding = (
        config.output_path / "reco_reference" / "performance_seeding.root"
    )
    generated_file_seeding = (
        config.output_path / "reco_generated" / "performance_seeding.root"
    )

    if extended:
        original_file_ckf = (
            config.output_path / "reco_geant4" / "performance_fitting_ckf.root"
        )
        fatras_file_ckf = (
            config.output_path / "reco_fatras" / "performance_fitting_ckf.root"
        )
    reference_file_ckf = (
        config.output_path / "reco_reference" / "performance_fitting_ckf.root"
    )
    generated_file_ckf = (
        config.output_path / "reco_generated" / "performance_fitting_ckf.root"
    )

    if extended:
        original_file_ambi = (
            config.output_path / "reco_geant4" / "performance_fitting_ambi.root"
        )
        fatras_file_ambi = (
            config.output_path / "reco_fatras" / "performance_fitting_ambi.root"
        )
    reference_file_ambi = (
        config.output_path / "reco_reference" / "performance_fitting_ambi.root"
    )
    generated_file_ambi = (
        config.output_path / "reco_generated" / "performance_fitting_ambi.root"
    )

    import skhep_testdata

    with uproot.open(skhep_testdata.data_path("uproot-issue38c.root")) as fp:
        hist = fp["TEfficiencyName"]  # noqa: F841

    with (
        uproot.open(reference_file_seeding) as file_ref_seeding,
        uproot.open(generated_file_seeding) as file_gen_seeding,
        uproot.open(reference_file_ckf) as file_ref_ckf,
        uproot.open(generated_file_ckf) as file_gen_ckf,
        uproot.open(reference_file_ambi) as file_ref_ambi,
        uproot.open(generated_file_ambi) as file_gen_ambi,
        PDFDocument(config.output_path / "validation_reco_performance.pdf") as pdf,
    ):
        if extended:
            file_orig_seeding = uproot.open(original_file_seeding)
            file_fatras_seeding = uproot.open(fatras_file_seeding)
            file_orig_ckf = uproot.open(original_file_ckf)
            file_fatras_ckf = uproot.open(fatras_file_ckf)
            file_orig_ambi = uproot.open(original_file_ambi)
            file_fatras_ambi = uproot.open(fatras_file_ambi)

        for file_orig, file_fatras, file_ref, file_gen, file_label in [
            (
                file_orig_seeding if extended else None,
                file_fatras_seeding if extended else None,
                file_ref_seeding,
                file_gen_seeding,
                "Seeding",
            ),
            (
                file_orig_ckf if extended else None,
                file_fatras_ckf if extended else None,
                file_ref_ckf,
                file_gen_ckf,
                "CKF",
            ),
            (
                file_orig_ambi if extended else None,
                file_fatras_ambi if extended else None,
                file_ref_ambi,
                file_gen_ambi,
                "Ambiguity resolution",
            ),
        ]:
            for variable, variable_label in [
                ("trackeff_vs_pT", "Track momentum [GeV]"),
                ("trackeff_vs_z0", "Track z_0 [mm]"),
            ]:
                if extended and file_orig is not None and file_fatras is not None:
                    original_eff_passed = (
                        file_orig[variable].member("fPassedHistogram").to_numpy()
                    )
                    original_eff_total = (
                        file_orig[variable].member("fTotalHistogram").to_numpy()
                    )
                    fatras_eff_passed = (
                        file_fatras[variable].member("fPassedHistogram").to_numpy()
                    )
                    fatras_eff_total = (
                        file_fatras[variable].member("fTotalHistogram").to_numpy()
                    )
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

                if extended:
                    original_passed = original_eff_passed[0][indices]
                    original_total = original_eff_total[0][indices]
                    fatras_passed = fatras_eff_passed[0][indices]
                    fatras_total = fatras_eff_total[0][indices]
                reference_passed = reference_eff_passed[0][indices]
                reference_total = reference_eff_total[0][indices]
                generated_passed = generated_eff_passed[0][indices]
                generated_total = generated_eff_total[0][indices]

                bins = reference_eff_total[1][indices_bins]
                bin_centers = bins[1:] - (bins[1] - bins[0]) / 2
                bin_errors = len(reference_total) * [(bins[1] - bins[0]) / 2]

                if extended:
                    original_efficiency = original_passed / original_total
                    original_err = (
                        np.sqrt(original_passed) / original_total * original_efficiency
                    )
                    fatras_efficiency = fatras_passed / fatras_total
                    fatras_err = (
                        np.sqrt(fatras_passed) / fatras_total * fatras_efficiency
                    )
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
                    [
                        original_efficiency,
                        reference_efficiency,
                        fatras_efficiency,
                        generated_efficiency,
                    ]
                    if extended
                    else [reference_efficiency, generated_efficiency],
                    [original_err, reference_err, fatras_err, generated_err]
                    if extended
                    else [reference_err, generated_err],
                    legend=["Geant4", "Geant4 (rounded)", "Fatras", "Neural network"]
                    if extended
                    else ["Geant4", "Neural network"],
                    label_x=variable_label,
                    label_y=f"{file_label} efficiency",
                    labels_extra=labels_extra_primary,
                )
                if fig:
                    fig.set_size_inches(6, 5)
                    pdf.save(fig)
                    # plt.close(fig)


def validate_reconstruction_tracks(
    config: Configuration,
    extended: bool = False,
) -> None:
    """Validate reconstruction results."""
    if extended:
        original_file = config.output_path / "reco_geant4" / "tracksummary_ambi.root"
        fatras_file = config.output_path / "reco_fatras" / "tracksummary_ambi.root"
    reference_file = config.output_path / "reco_reference" / "tracksummary_ambi.root"
    generated_file = config.output_path / "reco_generated" / "tracksummary_ambi.root"

    if extended:
        original_data = uproot.open(f"{original_file}:tracksummary").arrays()
        fatras_data = uproot.open(f"{fatras_file}:tracksummary").arrays()
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
            if extended:
                original_value = ak.flatten(original_data[variable]).to_numpy()
                fatras_value = ak.flatten(fatras_data[variable]).to_numpy()
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
                [original_value, reference_value, fatras_value, generated_value]
                if extended
                else [reference_value, generated_value],
                variable,
                "Track",
                "Tracks",
                labels_extra_primary,
                legend=["Geant4", "Geant4 (rounded)", "Fatras", "Neural network"]
                if extended
                else ["Geant4", "Neural network"],
                ratio="res_" not in variable and "pull_" not in variable,
            )
