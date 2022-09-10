from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Position
    from .modules import Module


__all__ = ["EmergencyStop", "TooManyActiveInputs"]


class EmergencyStop(Exception):
    def __init__(self, message: str, position: Position, *extra_positions: Position):
        self.message = message
        self.positions = [position, *extra_positions]
        self.time = -1
        super().__init__(message)

    def __str__(self) -> str:
        time_str = ""
        if self.time >= 0:
            time_str = f"Tick {self.time}, "
        return f"{time_str}{', '.join(map(str, self.positions))}: {self.message}"


class TooManyActiveInputs(EmergencyStop):
    def __init__(self, module: Module):
        super().__init__(
            "This machine has too many active inputs.", module.floor_position
        )
