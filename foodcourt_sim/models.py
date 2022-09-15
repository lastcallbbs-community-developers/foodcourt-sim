from __future__ import annotations

import functools
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, unique
from typing import TYPE_CHECKING, Any, NamedTuple, Optional

from .enums import LevelId, ModuleId
from .errors import InvalidSolutionError

if TYPE_CHECKING:
    from .entities import Entity
    from .enums import ToppingId
    from .levels import Level
    from .modules import Module


__all__ = [
    "Direction",
    "RelativeDirection",
    "Position",
    "Wire",
    "Solution",
    "MoveEntity",
]


@unique
class Direction(Enum):
    RIGHT = 0
    UP = 1
    LEFT = 2
    DOWN = 3

    def right(self) -> Direction:
        return Direction((self.value - 1) % 4)

    def left(self) -> Direction:
        return Direction((self.value + 1) % 4)

    def back(self) -> Direction:
        return Direction((self.value + 2) % 4)

    def relative_to(self, base: Direction) -> RelativeDirection:
        return RelativeDirection((self.value - base.value) % 4)


@unique
class RelativeDirection(Enum):
    FRONT = 0
    RIGHT = 1
    BACK = 2
    LEFT = 3


class Position(NamedTuple):
    # origin is at lower left corner
    column: int
    row: int

    def __repr__(self) -> str:
        return f"({self.column}, {self.row})"

    def copy(self) -> Position:
        return Position(self.column, self.row)

    def shift_by(self, direction: Direction) -> Position:
        col, row = self
        if direction is Direction.RIGHT:
            col += 1
        elif direction is Direction.LEFT:
            col -= 1
        elif direction is Direction.UP:
            row += 1
        elif direction is Direction.DOWN:
            row -= 1
        return Position(col, row)


class Wire(NamedTuple):
    module_1: int
    jack_1: int
    module_2: int
    jack_2: int


@dataclass(repr=False)
class Solution:  # pylint: disable=too-many-instance-attributes
    version: int
    level_id: LevelId
    name: str
    solved: bool
    time: int
    cost: int
    modules: list[Module]
    wires: list[Wire]
    filename: Optional[str] = field(compare=False)

    def __repr__(self) -> str:
        lines = []
        lines.append("Solution(")
        lines.append(f"  version={self.version!r},")
        lines.append(f"  level_id={self.level_id!r},")
        lines.append(f"  name={self.name!r},")
        lines.append(f"  solved={self.solved!r},")
        if self.solved:
            lines.append(f"  time={self.time!r},")
            lines.append(f"  cost={self.cost!r},")

        lines.append("  modules=[")
        for module in self.modules:
            lines.append(f"    {module!r},")
        lines.append("  ],")

        lines.append("  wires=[")
        for wire in self.wires:
            lines.append(f"    {wire!r},")
        lines.append("  ]")
        lines.append(")")

        return "\n".join(lines)

    @functools.cached_property
    def level(self) -> Level:
        from .levels import BY_ID  # pylint: disable=import-outside-toplevel

        return BY_ID[self.level_id]

    def check(self) -> None:
        main_input_index = -1
        occupied_rack_slots = [[False] * 11 for _ in range(3)]
        occupied_floor_slots = [[False] * 6 for _ in range(7)]
        module_indices: dict[ModuleId, list[int]] = defaultdict(list)
        cost = 0
        for i, module in enumerate(self.modules):
            module.check()
            # make sure main input and scanners match the level
            if (
                ModuleId.MAIN_INPUT_BASE.value
                < module.id.value
                <= ModuleId.MAIN_INPUT_BASE.value + len(LevelId)
            ):
                if main_input_index != -1:
                    raise InvalidSolutionError(
                        f"duplicate main input module found at index {i} (first was at {main_input_index})"
                    )
                main_input_index = i
                if (
                    module.id.value
                    != ModuleId.MAIN_INPUT_BASE.value + self.level_id.value
                ):
                    raise InvalidSolutionError(
                        f"mismatched main input ({module.id}) for level {self.level_id.name} at index {i}"
                    )
            if (
                ModuleId.SCANNER_BASE.value
                < module.id.value
                <= ModuleId.SCANNER_BASE.value + len(LevelId)
            ):
                if module.id.value != ModuleId.SCANNER_BASE.value + self.level_id.value:
                    raise InvalidSolutionError(
                        f"incorrect scanner ({module.id}) for level {self.level_id.name} at index {i}"
                    )
            # check for rack collisions
            if module.on_rack:
                pos = module.rack_position
                for _ in range(module.rack_width):
                    if occupied_rack_slots[pos.row][pos.column]:
                        raise InvalidSolutionError(f"rack collision at {pos}")
                    occupied_rack_slots[pos.row][pos.column] = True
                    pos = pos.shift_by(Direction.RIGHT)
            # check for floor collisions
            if module.on_floor:
                pos = module.floor_position
                width = 2 if module.id is ModuleId.OUTPUT else 1
                for _ in range(width):
                    if occupied_floor_slots[pos.row][pos.column]:
                        raise InvalidSolutionError(f"floor collision at {pos}")
                    occupied_floor_slots[pos.row][pos.column] = True
                    pos = pos.shift_by(Direction.RIGHT)
            module_indices[module.id].append(i)
            cost += module.price
        if main_input_index == -1:
            raise InvalidSolutionError("no main input module found")

        if (
            self.level_id is LevelId.SWEET_HEAT_BBQ
            and len(module_indices[ModuleId.WASTE_BIN]) > 2
        ):
            raise InvalidSolutionError(
                "too many waste bins for Sweet Heat BBQ (limit of 2)"
            )
        if (
            self.level_id is LevelId.DA_WINGS
            and len(module_indices[ModuleId.WASTE_BIN]) > 3
        ):
            raise InvalidSolutionError("too many waste bins for Da Wings (limit of 3)")

        # check that wires reference existing modules
        num_modules = len(self.modules)
        for wire in self.wires:
            if not 0 <= wire.module_1 < num_modules:
                raise InvalidSolutionError(
                    f"module index {wire.module_1} is out of bounds"
                )
            if not 0 <= wire.module_2 < num_modules:
                raise InvalidSolutionError(
                    f"module index {wire.module_1} is out of bounds"
                )
            module_1 = self.modules[wire.module_1]
            module_2 = self.modules[wire.module_2]
            if not 0 <= wire.jack_1 < len(module_1.jacks):
                raise InvalidSolutionError(
                    f"jack index {wire.jack_1} is out of bounds for module {module_1}"
                )
            if not 0 <= wire.jack_2 < len(module_2.jacks):
                raise InvalidSolutionError(
                    f"jack index {wire.jack_2} is out of bounds for module {module_2}"
                )

            # check that in jacks are only connected to out jacks and vice versa
            if (
                module_1.jacks[wire.jack_1].direction
                is module_2.jacks[wire.jack_2].direction
            ):
                raise InvalidSolutionError(
                    f"{module_1}, jack {wire.jack_1} is connected to {module_2}, jack {wire.jack_2} with the same direction"
                )

        if self.solved:
            if self.cost != cost:
                raise InvalidSolutionError(
                    "calculated cost doesn't match recorded cost"
                )
        else:
            self.cost = cost


@functools.total_ordering  # optimization note: this adds some overhead (see the docs)
@dataclass(frozen=True, eq=False)
class MoveEntity:
    """Represents a pending entity movement on the factory floor."""

    entity: Entity
    direction: Direction
    force: bool = True

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MoveEntity):
            return NotImplemented
        return (id(self.entity), self.direction, self.force) == (
            id(other.entity),
            other.direction,
            other.force,
        )

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, MoveEntity):
            return NotImplemented
        return (id(self.entity), self.direction.value, self.force) < (
            id(other.entity),
            other.direction.value,
            other.force,
        )

    @functools.cached_property
    def source(self) -> Position:
        return self.entity.position

    @functools.cached_property
    def dest(self) -> Position:
        return self.entity.position.shift_by(self.direction)
