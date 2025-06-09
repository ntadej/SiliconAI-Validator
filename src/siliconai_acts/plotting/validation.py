"""Results validation."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np
import pandas as pd
import uproot

from siliconai_acts.data.export import geometry_id_end, geometry_id_start
from siliconai_acts.plotting.common import plot_errorbar
from siliconai_acts.plotting.diagnostics import (
    diagnostics_plot,
    diagnostics_scatter_plot,
)
from siliconai_acts.plotting.utils import PDFDocument

if TYPE_CHECKING:
    from pathlib import Path

    from siliconai_acts.cli.config import Configuration


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

    from siliconai_acts.data.utils import local_to_global_vec

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


def validate_reconstruction(config: Configuration) -> None:
    """Validate reconstruction results."""
    reference_file = config.output_path / "reference" / "performance_seeding.root"
    generated_file = config.output_path / "generated" / "performance_seeding.root"

    import skhep_testdata

    with uproot.open(skhep_testdata.data_path("uproot-issue38c.root")) as fp:
        hist = fp["TEfficiencyName"]  # noqa: F841

    with (
        uproot.open(reference_file) as file_ref,
        uproot.open(generated_file) as file_gen,
        PDFDocument(config.output_path / "validation_reco.pdf") as pdf,
    ):
        for variable, label in [
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

            fig, ax = plot_errorbar(
                bin_centers,
                bin_errors,
                [reference_efficiency, generated_efficiency],
                [reference_err, generated_err],
                legend=["Geant4", "Neural network"],
                label_x=label,
                label_y="Seeding efficiency",
                labels_extra=labels_extra_primary,
            )
            if fig:
                fig.set_size_inches(6, 5)
                pdf.save(fig)
                # plt.close(fig)
