from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Position
    from .modules import Module


__all__ = [
    "SimulationError",
    "InvalidSolutionError",
    "InternalSimulationError",
    "EmergencyStop",
    "TimeLimitExceeded",
    "TooManyActiveInputs",
]


class InvalidSolutionError(Exception):
    pass


class SimulationError(Exception):
    """Base exception for any sort of simulation errors."""

    def __init__(self, message: str, *positions: Position):
        self.message = message
        self.positions = positions
        self.time = -1
        super().__init__(message)

    def __str__(self) -> str:
        parts = []
        if self.time >= 0:
            parts.append(f"Tick {self.time}")
        if self.positions:
            parts.append(", ".join(map(str, self.positions)))
        if parts:
            return " @ ".join(parts) + ": " + self.message
        return self.message


class InternalSimulationError(SimulationError):
    """Raised when there's a problem in the simulation code itself, rather than the solution."""


class TimeLimitExceeded(SimulationError):
    """Raised when the solution doesn't finish within the specified time limit."""

    def __init__(self) -> None:
        super().__init__("Time limit exceeded.")


class EmergencyStop(SimulationError):
    """Raised when the simulation stops due to a error in the solution."""

    def __init__(self, message: str, position: Position, *extra_positions: Position):
        super().__init__(message, position, *extra_positions)


class TooManyActiveInputs(EmergencyStop):
    def __init__(self, module: Module):
        super().__init__(
            "This machine has too many active inputs.", module.floor_position
        )


if TYPE_CHECKING:
    del Position, Module
del TYPE_CHECKING
del annotations
