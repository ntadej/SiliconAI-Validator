# Copyright (C) 2024 Tadej Novak
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0

"""Common plotting helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib as mpl
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from pandas import Series


colors = ["red", "blue"]


def setup_style() -> None:
    """Use ATLAS plotting style by default, but without labels."""
    hep.style.use(hep.style.ATLAS)

    mpl.rcParams["axes.labelsize"] = "large"


def linear_binning(
    nbins: int,
    start: float,
    end: float,
    rounded: bool = True,
) -> list[float]:
    """Generate linear binning with N bins from start to end.

    The binning is rounded by default but that can be disabled.
    """
    edges: list[float] = []
    for i in range(nbins + 1):
        if rounded:
            edges.append(round(start + i * (end - start) / nbins))
        else:
            edges.append(start + i * (end - start) / nbins)

    return edges


def log_binning(
    nbins: int,
    start: float,
    end: float,
    rounded: bool = True,
) -> list[float]:
    """Generate logarithmic binning with N bins from start to end.

    The binning is rounded by default but that can be disabled.
    """
    f = pow(end / start, 1.0 / nbins)

    edges: list[float] = []
    for i in range(nbins + 1):
        if rounded:
            edges.append(round(start * pow(f, i)))
        else:
            edges.append(start * pow(f, i))

    return edges


def plot_hist(  # noqa: C901 PLR0912
    data: list[list[float]] | list[Series[float]],
    column: str,
    nbins: int = 25,
    bin_range: tuple[float, float] | None = None,
    logx: bool = False,
    logy: bool = False,
    label_x: str | None = None,
    label_y: str | None = None,
    labels_extra: list[str] | None = None,
    legend: list[str] | None = None,
    errors: bool = True,
) -> tuple[Figure | None, Axes | None]:
    """Plot a column from a dataframe."""
    if not data:
        return None, None

    ratio = len(data) > 1

    binning_function = log_binning if logx else linear_binning
    binning = binning_function(
        nbins,
        bin_range[0] if bin_range else min(data[0]),
        bin_range[1] if bin_range else max(data[0]),
        rounded=False,
    )

    if ratio:
        fig, (ax_main, ax_ratio) = plt.subplots(
            nrows=2,
            sharex=True,
            figsize=(6, 4),
            height_ratios=[3, 1],
        )
    else:
        fig, ax_main = plt.subplots(figsize=(6, 4))
        ax_ratio = None

    hist_main = None
    bins_main = None
    hist_list = []
    for d, label, color in zip(
        data,
        legend or [column],
        colors[: len(data)],
        strict=True,
    ):
        hist, bins = np.histogram(d, binning)  # type: ignore
        if hist_main is None:
            hist_main = hist
            bins_main = bins
        else:
            hist_list.append(hist)
        hep.histplot(hist, bins, ax=ax_main, yerr=errors, label=label, color=color)

    label_offset = 0.1 if ratio else 0.075

    for i, label in enumerate(labels_extra or []):
        ax_main.text(0.05, 0.9 - i * label_offset, label, transform=ax_main.transAxes)

    ax_main.set_ylabel(label_y or "Entries")
    if ax_ratio:
        ax_main.tick_params(labelbottom=False)

        ax_ratio.set_xlabel(label_x or column)  # , labelpad=20)
        ax_ratio.set_ylabel("Ratio", loc="center")

        ax_ratio.set_ylim(0.9, 1.0999)

        plt.subplots_adjust(hspace=0.05)
    else:
        ax_main.set_xlabel(label_x or column)  # , labelpad=20)

    if logx:
        ax_main.set_xscale("log")
    if logy:
        ax_main.set_yscale("log")
        ax_main.set_ylim(
            1 if "nhits" in column else None,
            ax_main.get_ylim()[1] * (10 ** len(labels_extra or [])),
        )
    else:
        ax_main.set_ylim(
            ax_main.get_ylim()[0],
            ax_main.get_ylim()[1] * (1 + label_offset * len(labels_extra or [])),
        )

    if ax_ratio:
        ax_ratio.axhline(
            1.0,
            linewidth=0.7,
            color="black",
            linestyle="dashed",
            zorder=0,
        )

    if hist_main is None:
        raise RuntimeError

    if ratio:
        for hist, color in zip(hist_list, colors[1 : len(data)], strict=True):
            ratio_hist = np.divide(hist, hist_main, where=hist_main != 0)
            ratio_hist[hist_main == 0] = 1
            hep.histplot(ratio_hist, bins_main, ax=ax_ratio, yerr=False, color=color)

    if len(data) > 1:
        ax_main.legend(loc=1, bbox_to_anchor=(0.975, 0.925))

    return fig, ax_main


def plot_errorbar(
    x: list[float],
    xerr: list[float],
    y: list[list[float]],
    yerr: list[list[float]],
    legend: list[str],
    label_x: str,
    label_y: str,
    logx: bool = False,
    logy: bool = False,
    labels_extra: list[str] | None = None,
) -> tuple[Figure | None, Axes | None]:
    """Plot a column from a dataframe."""
    if not y:
        return None, None

    ratio = False  # len(data) > 1

    if ratio:
        fig, (ax_main, ax_ratio) = plt.subplots(
            nrows=2,
            sharex=True,
            figsize=(6, 4),
            height_ratios=[3, 1],
        )
    else:
        fig, ax_main = plt.subplots(figsize=(6, 4))
        ax_ratio = None

    for yi, yerri, label, color in zip(y, yerr, legend, colors[: len(y)], strict=True):
        plt.errorbar(
            x,
            yi,
            xerr=xerr,
            yerr=yerri,
            linestyle="",
            label=label,
            color=color,
        )

    label_offset = 0.1 if ratio else 0.075

    for i, label in enumerate(labels_extra or []):
        ax_main.text(0.05, 0.9 - i * label_offset, label, transform=ax_main.transAxes)

    ax_main.set_ylabel(label_y or "Entries")
    if ax_ratio:
        ax_main.tick_params(labelbottom=False)

        ax_ratio.set_xlabel(label_x)
        ax_ratio.set_ylabel("Ratio", loc="center")

        ax_ratio.set_ylim(0.9, 1.0999)

        plt.subplots_adjust(hspace=0.05)
    else:
        ax_main.set_xlabel(label_x)

    if logx:
        ax_main.set_xscale("log")
    if logy:
        ax_main.set_yscale("log")
        ax_main.set_ylim(
            None,
            ax_main.get_ylim()[1] * (10 ** len(labels_extra or [])),
        )
    else:
        ax_main.set_ylim(
            0,  # ax_main.get_ylim()[0],
            ax_main.get_ylim()[1] * (1 + 2 * label_offset * len(labels_extra or [])),
        )

    if ax_ratio:
        ax_ratio.axhline(
            1.0,
            linewidth=0.7,
            color="black",
            linestyle="dashed",
            zorder=0,
        )

    # TODO: ratio

    if len(y) > 1:
        ax_main.legend(loc=1, bbox_to_anchor=(0.975, 0.925))

    return fig, ax_main


def plot_scatter(
    data_x: list[list[float]] | list[Series[float]],
    data_y: list[list[float]] | list[Series[float]],
    label_x: str | None = None,
    label_y: str | None = None,
    labels_extra: list[str] | None = None,
) -> tuple[Figure | None, Axes | None]:
    """Plot a scatter plot from a dataframe."""
    if not data_x or not data_y:
        return None, None

    fig, ax = plt.subplots(figsize=(6, 4))
    for i in range(len(data_x)):
        ax.scatter(data_x[i][:10000], data_y[i][:10000], s=0.1, color=colors[i])

    for i, label in enumerate(labels_extra or []):
        ax.text(0.05, 0.9 - i * 0.075, label, transform=ax.transAxes)

    if label_x:
        ax.set_xlabel(label_x)
    if label_y:
        ax.set_ylabel(label_y)

    return fig, ax
