"""Common enums."""

from enum import Enum


class ProductionStep(Enum):
    """Production step enum."""

    GENERATION = "evgen"
    SIMULATION = "simul"
    DIGITIZATION = "digi"
    RECONSTRUCTION = "reco"
