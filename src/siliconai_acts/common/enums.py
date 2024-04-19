"""Common enums."""

from enum import Enum


class ProductionStep(Enum):
    """Production step enum."""

    Generation = "evgen"
    Simulation = "simul"
    Digitization = "digi"
    Reconstruction = "reco"

    @property
    def title(self) -> str:
        """Get human-readable title."""
        if self is ProductionStep.Generation:
            return "event generation"
        if self is ProductionStep.Simulation:
            return "simulation"
        if self is ProductionStep.Digitization:
            return "digitization"
        if self is ProductionStep.Reconstruction:
            return "reconstruction"
        raise RuntimeError()


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


class SimulationParticleOutcome(Enum):
    """Simulated particle outcome enum."""

    Alive = 0
    Interaction = 1
    EscapedAndKilled = 2
    SlowAndKilled = 3
    SecondaryAndKilled = 4
