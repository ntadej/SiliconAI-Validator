"""Common plotting helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import matplotlib as mpl
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from pandas import DataFrame


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


def plot_column(
    data: DataFrame,
    column: str,
    nbins: int = 25,
    logx: bool = False,
) -> tuple[Figure | None, Axes | None]:
    """Plot a column from a dataframe."""
    if data is None or data.empty:
        return None, None

    column_data = cast(list[float], data[column].tolist())  # type: ignore
    return plot_hist([column_data], column, nbins, logx)


def plot_hist(
    data: list[list[float]],
    column: str,
    nbins: int = 25,
    logx: bool = False,
    labels: list[str] | None = None,
) -> tuple[Figure | None, Axes | None]:
    """Plot a column from a dataframe."""
    if not data:
        return None, None

    binning_function = log_binning if logx else linear_binning
    binning = (
        common_binning[column]
        if column in common_binning
        else binning_function(
            nbins,
            min(data[0]),
            max(data[0]),
            rounded=False,
        )
    )

    fig, ax = plt.subplots(figsize=(6, 4))
    for d, label in zip(data, labels or [column]):
        hist, bins = np.histogram(d, binning)
        hep.histplot(hist, bins, ax=ax, yerr=True, label=label)
    # TODO: make the label configurable
    hep.atlas.label(
        "Internal",
        ax=ax,
        data=False,
        rlabel=r"$\sqrt{s} = \mathrm{13.6\ TeV}$",
    )
    ax.set_ylim(ax.get_ylim()[0], ax.get_ylim()[1] * 1.2)
    ax.set_xlabel(column)
    ax.set_ylabel("Tracks")
    if len(data) > 1:
        plt.legend()

    return fig, ax


common_binning: dict[str, list[float]] = {
    "track_pt": linear_binning(250, 0, 1000, rounded=True),
    "track_d0": linear_binning(100, -40, 40, rounded=False),
    "track_z0": linear_binning(100, -250, 250, rounded=False),
    "track_qOverP": linear_binning(100, -0.005, 0.005, rounded=False),
}
