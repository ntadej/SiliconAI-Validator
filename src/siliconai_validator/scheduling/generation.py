"""Event generation utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

import acts
from acts.examples.simulation import (
    EtaConfig,
    MomentumConfig,
    ParticleConfig,
    PhiConfig,
    addParticleGun,
)

from siliconai_validator.common.enums import EventType, ParticleType

if TYPE_CHECKING:
    from pathlib import Path

    from siliconai_validator.cli.config import ProcessConfiguration
    from siliconai_validator.cli.logger import Logger

u = acts.UnitConstants


def schedule_event_generation(
    sequencer: acts.examples.Sequencer,
    rnd: acts.examples.RandomNumbers,
    config: ProcessConfiguration,
    output_dir: Path | None = None,
) -> None:
    """Schedule event generation in the ACTS example framework."""
    vertex_generator = acts.examples.UniformVertexGenerator(
        min=acts.Vector4(
            -config.smearing[0] * u.um,
            -config.smearing[1] * u.um,
            -config.smearing[2] * u.mm,
            0,
        ),
        max=acts.Vector4(
            config.smearing[0] * u.um,
            config.smearing[1] * u.um,
            config.smearing[2] * u.mm,
            0,
        ),
    )

    if config.type is EventType.SingleParticle:
        if config.particle is ParticleType.Muon:
            particle = acts.PdgParticle.eMuon
        elif config.particle is ParticleType.Electron:
            particle = acts.PdgParticle.eElectron
        elif config.particle is ParticleType.Photon:
            particle = acts.PdgParticle.ePhoton
        elif config.particle is ParticleType.Pion:
            particle = acts.PdgParticle.ePionPlus

        if isinstance(config.pt, tuple):
            momentum_config = MomentumConfig(
                config.pt[0],
                config.pt[1],
                transverse=True,
            )
        else:
            momentum_config = MomentumConfig(
                config.pt,
                config.pt,
                transverse=True,
            )

        if isinstance(config.eta, tuple):
            eta_config = EtaConfig(config.eta[0], config.eta[1], uniform=True)
        else:
            eta_config = EtaConfig(config.eta, config.eta, uniform=True)

        if config.phi:
            phi_config = PhiConfig(config.phi[0], config.phi[1])
        else:
            phi_config = PhiConfig(0.0 * u.degree, 360.0 * u.degree)

        addParticleGun(
            sequencer,
            ParticleConfig(
                num=1,
                pdg=particle,
                randomizeCharge=config.randomize_charge,
            ),
            momentum_config,
            eta_config,
            phi_config,
            vtxGen=vertex_generator,
            multiplicity=1,
            rnd=rnd,
            outputDirRoot=output_dir,
        )

        return


def run_generation(
    logger: Logger,
    seed: int,
    config: ProcessConfiguration,
    output_path: Path,
    events: int,
    skip: int = 0,
) -> None:
    """Run event generation."""
    logger.info("Running event generation")

    rnd = acts.examples.RandomNumbers(seed=seed)

    sequencer = acts.examples.Sequencer(
        events=events,
        skip=skip,
        trackFpes=False,
        outputDir=output_path,
        outputTimingFile="timing.evgen.csv",
    )

    schedule_event_generation(sequencer, rnd, config, output_path)

    sequencer.run()
