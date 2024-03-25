"""Event generation utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import acts
from acts.examples.simulation import (
    EtaConfig,
    MomentumConfig,
    ParticleConfig,
    PhiConfig,
    addParticleGun,
)

from siliconai_acts.common.enums import EventType, ParticleType

if TYPE_CHECKING:
    from pathlib import Path

u = acts.UnitConstants


def schedule_event_generation(
    sequencer: acts.examples.Sequencer,
    rnd: acts.examples.RandomNumbers,
    event_type: EventType,
    particle_type: ParticleType = ParticleType.Muon,
    output_dir: Optional[Path] = None,
) -> None:
    """Schedule event generation in the ACTS example framework."""
    vertex_generator = acts.examples.GaussianVertexGenerator(
        mean=acts.Vector4(0, 0, 0, 0),
        stddev=acts.Vector4(10 * u.um, 10 * u.um, 50 * u.mm, 1 * u.ns),
    )

    if event_type is EventType.SingleParticle:
        pt_label = (100, 150)

        if particle_type is ParticleType.Muon:
            particle = acts.PdgParticle.eMuon
        elif particle_type is ParticleType.Electron:
            particle = acts.PdgParticle.eElectron
        elif particle_type is ParticleType.Photon:
            particle = acts.PdgParticle.ePhoton
        elif particle_type is ParticleType.Pion:
            particle = acts.PdgParticle.ePionPlus

        if isinstance(pt_label, tuple):
            momentum_config = MomentumConfig(pt_label[0], pt_label[1], transverse=True)
            eta_config = EtaConfig(-3.0, 3.0, uniform=False)
        else:
            momentum_config = MomentumConfig(pt_label, pt_label, transverse=True)  # type: ignore
            eta_config = EtaConfig(-3.0, 3.0, uniform=True)

        addParticleGun(
            sequencer,
            ParticleConfig(num=1, pdg=particle, randomizeCharge=True),
            momentum_config,
            eta_config,
            PhiConfig(0.0 * u.degree, 360.0 * u.degree),
            vtxGen=vertex_generator,
            multiplicity=1,
            rnd=rnd,
            outputDirRoot=output_dir,
        )

        return


def run_generation(output_path: Path, events: int, skip: int = 0) -> None:
    """Run event generation."""
    rnd = acts.examples.RandomNumbers(seed=42)

    sequencer = acts.examples.Sequencer(
        events=events,
        skip=skip,
        trackFpes=False,
        outputDir=output_path,
    )

    schedule_event_generation(
        sequencer,
        rnd,
        event_type=EventType.SingleParticle,
        particle_type=ParticleType.Muon,
        output_dir=output_path,
    )

    sequencer.run()
