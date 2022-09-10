from __future__ import annotations

import functools
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, unique
from typing import TYPE_CHECKING, NamedTuple

from .enums import LevelId, ModuleId

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
    modules: list[Module] = field(repr=False)
    wires: list[Wire] = field(repr=False)

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

    # def dump_wires_to(self, arg: Any) -> None:
    #     """used for reverse engineering"""
    #     if isinstance(arg, Module):
    #         index = self.modules.index(arg)
    #     elif isinstance(arg, int):
    #         index = arg
    #     elif isinstance(arg, ModuleId):
    #         index = next(i for i, m in enumerate(self.modules) if m.id is arg)
    #     module = self.modules[index]
    #     print(f"Wires to/from {module.id} (index {index}):")
    #     connections = []
    #     for i, wire in enumerate(self.wires):
    #         if index not in (wire.module_1, wire.module_2):
    #             continue
    #         if wire.module_2 == index:
    #             wire = Wire(wire.module_2, wire.jack_2, wire.module_1, wire.jack_1)
    #         connections.append((i, wire))
    #     connections.sort(key=lambda x: x[1].jack_1)
    #     for i, wire in connections:
    #         module_2 = self.modules[wire.module_2]
    #         jack_1 = str(wire.jack_1)
    #         jack_2 = str(wire.jack_2)
    #         if wire.jack_2 < len(module_2.jacks):
    #             j2 = module_2.jacks[wire.jack_2]
    #             jack_2 = repr(j2.name.upper())
    #             jack_1 += f" ({j2.direction.opposite().name})".ljust(6)
    #         print(
    #             f"jack {jack_1} to jack {jack_2} of {module_2.id} (index {wire.module_2})"
    #         )

    def check(self, level: Level) -> None:
        assert level.id == self.level_id

        main_input_index = -1
        occupied_rack_slots = [[False] * 11 for _ in range(3)]
        module_indices: dict[ModuleId, list[int]] = defaultdict(list)
        cost = 0
        for i, module in enumerate(self.modules):
            module.check()
            # make sure main input and scanners match the level
            if 200 <= module.id.value <= 220:
                assert (
                    main_input_index == -1
                ), f"duplicate main input module found at index {i} (first was at {main_input_index})"
                main_input_index = i
                assert (
                    module.id.value == level.id.value + 199
                ), f"mismatched main input ({module.id}) for level {level.internal_name} at index {i}"
            if 150 <= module.id.value <= 170:
                assert (
                    module.id.value == level.id.value + 149
                ), f"incorrect scanner ({module.id}) for level {level.internal_name} at index {i}"
            # check for rack collisions
            if module.on_rack:
                pos = module.rack_position
                assert not (
                    occupied_rack_slots[pos.row][pos.column]
                ), f"rack collision at {module.rack_position}"
                for i in range(module.rack_width):
                    occupied_rack_slots[pos.row][pos.column + i] = True
            module_indices[module.id].append(i)
            cost += module.price
        assert main_input_index != -1, "no main input module found"

        if level.id is LevelId.SWEET_HEAT_BBQ:
            assert (
                len(module_indices[ModuleId.WASTE_BIN]) <= 2
            ), "too many waste bins for Sweet Heat BBQ (limit of 2)"

        # check that wires reference existing modules
        num_modules = len(self.modules)
        for wire in self.wires:
            assert 0 <= wire.module_1 < num_modules
            assert 0 <= wire.module_2 < num_modules
            module_1 = self.modules[wire.module_1]
            module_2 = self.modules[wire.module_2]
            assert (
                0 <= wire.jack_1 < len(module_1.jacks)
            ), f"{module_1}, jack {wire.jack_1}"
            assert (
                0 <= wire.jack_2 < len(module_2.jacks)
            ), f"{module_2}, jack {wire.jack_2}"

            # check that in jacks are only connected to out jacks and vice versa
            assert (
                module_1.jacks[wire.jack_1].direction
                is not module_2.jacks[wire.jack_2].direction
            ), f"{module_1}, jack {wire.jack_1} is connected to {module_2}, jack {wire.jack_2} with the same direction"

        if self.solved:
            assert self.cost == cost, "calculated cost doesn't match recorded cost"


@dataclass(frozen=True)
class MoveEntity:
    """Represents a pending entity movement on the factory floor."""

    entity: Entity
    direction: Direction
    force: bool = True

    @functools.cached_property
    def position(self) -> Position:
        return self.entity.position

    @functools.cached_property
    def dest(self) -> Position:
        return self.entity.position.shift_by(self.direction)
