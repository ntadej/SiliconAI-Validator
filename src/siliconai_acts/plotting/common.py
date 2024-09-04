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


def plot_hist(
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
) -> tuple[Figure | None, Axes | None]:
    """Plot a column from a dataframe."""
    if not data:
        return None, None

    binning_function = log_binning if logx else linear_binning
    binning = binning_function(
        nbins,
        bin_range[0] if bin_range else min(data[0]),
        bin_range[1] if bin_range else max(data[0]),
        rounded=False,
    )

    fig, (ax_main, ax_ratio) = plt.subplots(
        nrows=2,
        sharex=True,
        figsize=(6, 4),
        height_ratios=[3, 1],
    )
    hist_main = None
    bins_main = None
    hist_list = []
    for d, label, color in zip(data, legend or [column], colors[: len(data)]):
        hist, bins = np.histogram(d, binning)  # type: ignore
        if hist_main is None:
            hist_main = hist
            bins_main = bins
        else:
            hist_list.append(hist)  # type: ignore
        hep.histplot(hist, bins, ax=ax_main, yerr=True, label=label, color=color)

    for i, label in enumerate(labels_extra or []):
        ax_main.text(0.05, 0.9 - i * 0.075, label, transform=ax_main.transAxes)

    ax_main.set_ylabel(label_y or "Entries")
    ax_main.tick_params(labelbottom=False)
    ax_ratio.set_xlabel(label_x or column)  # , labelpad=20)
    ax_ratio.set_ylabel("Ratio", loc="center")

    ax_ratio.set_ylim(0.8, 1.1999)

    plt.subplots_adjust(hspace=0.05)

    if logx:
        ax_main.set_xscale("log")
    if logy:
        ax_main.set_yscale("log")
        ax_main.set_ylim(
            None,
            ax_main.get_ylim()[1] * (3 * len(labels_extra or [])),
        )
    else:
        ax_main.set_ylim(
            ax_main.get_ylim()[0],
            ax_main.get_ylim()[1] * (1 + 0.075 * len(labels_extra or [])),
        )

    ax_ratio.axhline(1.0, linewidth=0.7, color="black", linestyle="dashed", zorder=0)

    if hist_main is None:
        raise RuntimeError

    for hist, color in zip(hist_list, colors[1 : len(data)]):
        ratio = np.divide(hist, hist_main, where=hist_main != 0)
        ratio[hist_main == 0] = 1
        hep.histplot(ratio, bins_main, ax=ax_ratio, yerr=False, color=color)

    if len(data) > 1:
        ax_main.legend()

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
    ax.scatter(data_x[0][:10000], data_y[0][:10000], s=0.1, color=colors[0])

    for i, label in enumerate(labels_extra or []):
        ax.text(0.05, 0.9 - i * 0.075, label, transform=ax.transAxes)

    if label_x:
        ax.set_xlabel(label_x)
    if label_y:
        ax.set_ylabel(label_y)

    return fig, ax
