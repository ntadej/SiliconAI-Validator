"""Configuration utilities."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import tomli_w

from siliconai_acts.common.enums import EventType, ParticleType, SimulationType

from .logger import Table, config_table, error_panel, info_panel


class TyperState:
    """Execution configuration state."""

    def __init__(self) -> None:
        """Initialize configuration state."""
        self.config_file: Path = Path("config.toml")
        self.debug: bool = False


class GlobalConfiguration:
    """Global configuration."""

    def __init__(
        self,
        location: Path,
        debug: bool = False,
        full_information: bool = False,
    ) -> None:
        """Initialize configuration."""
        self.location: Path = location

        with location.open(mode="rb") as f:
            config = tomllib.load(f)

        self.debug: bool = debug
        self.output_path: Path = Path("run")
        self.threads: int = 1

        if "common" in config and "threads" in config["common"]:
            self.threads = int(config["common"]["threads"])

        if (
            "output" in config
            and "path" in config["output"]
            and config["output"]["path"]
        ):
            self.output_path = Path(config["output"]["path"])

        info_panel(self.to_table(full_information), title="Global Configuration")

    def to_object(self) -> dict[str, Any]:
        """Convert configuration to object."""
        return {
            "common": {
                "threads": self.threads,
            },
            "output": {
                "path": str(self.output_path),
                "debug": self.debug,
            },
        }

    def to_table(self, full_information: bool = False) -> Table:
        """Convert configuration to table."""
        table = config_table()

        table.add_row("Location:", print_path(self.location))
        table.add_row("Output path:", print_path(self.output_path))
        table.add_row("Threads:", str(self.threads))

        if full_information:
            table.add_row()
            table.add_row("Debug:", str(self.debug))

        return table

    @classmethod
    def load(
        cls,
        state: TyperState,
        full_information: bool = True,
    ) -> GlobalConfiguration:
        """Load configuration from CLI state."""
        if not state.config_file.exists():
            config_missing(state.config_file)

        return cls(state.config_file, state.debug, full_information)

    @classmethod
    def generate_empty(cls, location: Path) -> None:
        """Generate empty config file."""
        if location.exists():
            error_message = (
                f"Configuration file [blue]'{location}'[/blue] already exists."
            )
            raise error_panel(error_message)

        config = {
            "data": {
                "path": "data",
            },
            "output": {
                "path": "run",
            },
        }

        with location.open("wb") as f:
            tomli_w.dump(config, f)

        cls(location)


class Configuration:
    """Task configuration."""

    def __init__(self, location: Path, global_config: GlobalConfiguration) -> None:
        """Initialize task configuration."""
        self.location: Path = location

        if not location.exists():
            task_config_missing(location)

        with location.open(mode="rb") as f:
            config = tomllib.load(f)

        match config:
            case {
                "name": str(),
                "labels": list(),
                "process": dict(),
                "simulation": dict(),
            }:
                pass
            case _:
                error = f"invalid task configuration: {config}"
                raise ValueError(error)

        self.name: str = config["name"]
        self.labels: list[str] = config.get("labels", [])
        self.events: int = int(config.get("events", 1000))
        self.seed: int = int(config.get("seed", 42))
        self.global_config: GlobalConfiguration = global_config
        self.output_path: Path = global_config.output_path / self.output_name
        self.process: ProcessConfiguration = ProcessConfiguration(
            config["process"],
            global_config,
        )
        self.simulation: SimulationConfiguration = SimulationConfiguration(
            config["simulation"],
            global_config,
        )

        info_panel(self.to_table(), title="Task Configuration")
        info_panel(self.process.to_table(), title="Process Configuration")
        info_panel(self.simulation.to_table(), title="Simulation Configuration")

    def __repr__(self) -> str:
        """Return the string representation of the configuration."""
        return self.name

    @property
    def output_name(self) -> str:
        """Return the sanitized output name."""
        return self.name.replace(" ", "_")

    def to_object(self) -> dict[str, Any]:
        """Convert configuration to object."""
        return {
            "name": self.name,
            "labels": self.labels,
            "events": self.events,
            "seed": self.seed,
            "output_name": self.output_name,
            "output_path": self.output_path,
        }

    def to_table(self) -> Table:
        """Convert configuration to table."""
        table = config_table()

        table.add_row("name:", self.name)
        table.add_row("name (output):", self.output_name)
        table.add_row("labels:", str(self.labels))
        table.add_row("location:", print_path(self.location))
        table.add_row("output path:", print_path(self.output_path))
        table.add_row()
        table.add_row("events:", str(self.events))
        table.add_row("seed:", str(self.seed))

        return table


class ProcessConfiguration:
    """Process configuration."""

    def __init__(
        self,
        config: dict[str, Any],
        _global_config: GlobalConfiguration,
    ) -> None:
        """Initialize process configuration."""
        match config:
            case {
                "type": str(),
                "particle": str(),
                "pt": list() | float() | int(),
                "eta": list() | float() | int(),
            }:
                pass
            case _:
                error = f"invalid task configuration: {config}"
                raise ValueError(error)

        self.type: EventType = EventType(config["type"])
        self.particle: ParticleType = ParticleType(config["particle"])
        self.pt: tuple[float, float] | float = (
            tuple(config["pt"])
            if isinstance(config["pt"], list)
            else float(config["pt"])
        )
        self.eta: tuple[float, float] | float = (
            tuple(config["eta"])
            if isinstance(config["eta"], list)
            else float(config["eta"])
        )

        self.smearing: tuple[float, float, float] = tuple(
            config.get("smearing", [0, 0, 50]),
        )

    def to_object(self) -> dict[str, Any]:
        """Convert configuration to object."""
        return {
            "type": self.type.value,
            "particle": self.particle.value,
            "pt": self.pt,
            "eta": self.eta,
            "smearing": self.smearing,
        }

    def to_table(self) -> Table:
        """Convert configuration to table."""
        table = config_table()

        table.add_row("type:", self.type.value)
        table.add_row("particle:", self.particle.value)
        table.add_row("pt:", str(self.pt))
        table.add_row("eta:", str(self.eta))
        table.add_row("smearing:", str(self.smearing))

        return table


class SimulationConfiguration:
    """Simulation configuration."""

    def __init__(
        self,
        config: dict[str, Any],
        _global_config: GlobalConfiguration,
    ) -> None:
        """Initialize simulation configuration."""
        match config:
            case {
                "type": str(),
            }:
                pass
            case _:
                error = f"invalid task configuration: {config}"
                raise ValueError(error)

        self.type: SimulationType = SimulationType(config["type"])
        self.secondaries_min_pt: float = config.get("secondaries_min_pt", 0)
        self.disable_secondaries: bool = config.get("disable_secondaries", False)

    def to_object(self) -> dict[str, Any]:
        """Convert configuration to object."""
        return {
            "type": self.type.value,
            "disable_secondaries": self.disable_secondaries,
            "secondaries_min_pt": self.secondaries_min_pt,
        }

    def to_table(self) -> Table:
        """Convert configuration to table."""
        table = config_table()

        table.add_row("type:", self.type.value)
        table.add_row("disable secondaries:", str(self.disable_secondaries))
        table.add_row("secondaries min pt:", str(self.secondaries_min_pt))

        return table


def config_missing(config_file: Path) -> None:
    """Print config missing message."""
    error_message = (
        f"Configuration file [blue]'{config_file}'[/blue] does not exist.\n"
        "Please run"
        " [blue]'siliconai_acts config [bold]--generate[/bold]'[/blue]"
        " to generate it.\n"
        "Optionally you can specify the path using the"
        " [blue]'[bold]--global-config[/bold]'[/blue] option"
        " or using the environment variable"
        " [blue bold]SILICONAI_ACTS_GLOBAL_CONFIG[/blue bold].]"
    )
    raise error_panel(error_message)


def task_config_missing(config_file: Path) -> None:
    """Print config missing message."""
    error_message = (
        f"Task configuration file [blue]'{config_file}'[/blue] does not exist.\n"
        "Optionally you can specify the path using the"
        " [blue]'[bold]--config[/bold]'[/blue] option"
        " or using the environment variable"
        " [blue bold]SILICONAI_ACTS_CONFIG[/blue bold].]"
    )
    raise error_panel(error_message)


def print_path(path: Path | None) -> str:
    """Print path."""
    if not path:
        return "None"

    string = str(path)
    if string.startswith("/"):
        return string

    return f"./{string}"
