"""Common enums."""

from enum import Enum


class ProductionStep(Enum):
    """Production step enum."""

    Generation = "evgen"
    Simulation = "simul"
    Digitization = "digi"
    Reconstruction = "reco"


class EventType(Enum):
    """Event type enum."""

    SingleParticle = "single_particle"


class ParticleType(Enum):
    """Particle type enum."""

    Muon = "mu"
    Electron = "e"
    Photon = "gamma"
    Pion = "pi"


class SimulationType(Enum):
    """Simulation type enum."""

    Geant4 = "geant4"
    Fatras = "fatras"
