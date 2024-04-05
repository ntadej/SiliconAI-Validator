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
        min(data[0]),
        max(data[0]),
        rounded=False,
    )

    fig, ax = plt.subplots(figsize=(6, 4))
    for d, label in zip(data, legend or [column]):
        hist, bins = np.histogram(d, binning)  # type: ignore
        hep.histplot(hist, bins, ax=ax, yerr=True, label=label)

    for i, label in enumerate(labels_extra or []):
        ax.text(0.05, 0.9 - i * 0.075, label, transform=ax.transAxes)

    ax.set_xlabel(label_x or column, labelpad=20)
    ax.set_ylabel(label_y or "Entries")

    if logx:
        ax.set_xscale("log")
    if logy:
        ax.set_yscale("log")
        ax.set_ylim(
            None,
            ax.get_ylim()[1] * (3 * len(labels_extra or [])),
        )
    else:
        ax.set_ylim(
            ax.get_ylim()[0],
            ax.get_ylim()[1] * (1 + 0.075 * len(labels_extra or [])),
        )

    if len(data) > 1:
        plt.legend()

    return fig, ax


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
    ax.scatter(data_x[0], data_y[0], s=0.1)

    for i, label in enumerate(labels_extra or []):
        ax.text(0.05, 0.9 - i * 0.075, label, transform=ax.transAxes)

    ax.set_xlabel(label_x)
    ax.set_ylabel(label_y)

    return fig, ax
