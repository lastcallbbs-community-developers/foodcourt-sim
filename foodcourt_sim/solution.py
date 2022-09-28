from __future__ import annotations

import dataclasses
import functools
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, NamedTuple, Optional

from . import logger
from .enums import JackDirection, LevelId, ModuleId
from .errors import InvalidSolutionError
from .levels import BUYABLE_MODULES, BY_ID, PROVIDED_MODULES
from .models import Direction, Position

if TYPE_CHECKING:
    from .levels import Level
    from .modules import Module


__all__ = ["Wire", "Solution"]


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
        for i, module in enumerate(self.modules):
            lines.append(f"    {i}: {module!r},")
        lines.append("  ],")

        lines.append("  wires=[")
        for wire in self.wires:
            lines.append(f"    {wire!r},")
        lines.append("  ]")
        lines.append(")")

        return "\n".join(lines)

    @functools.cached_property
    def level(self) -> Level:
        return BY_ID[self.level_id]

    def check(self) -> None:
        occupied_rack_slots = [[False] * 11 for _ in range(3)]
        occupied_floor_slots = [[False] * 6 for _ in range(7)]
        module_indices: dict[ModuleId, list[int]] = defaultdict(list)
        cost = 0

        provided_counts = PROVIDED_MODULES[self.level_id].copy()
        for i, module in enumerate(self.modules):
            module.check()
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

            if module.can_delete:
                if module.id not in BUYABLE_MODULES[self.level_id]:
                    raise InvalidSolutionError(
                        f"illegal buyable module ({module.id}) for level {self.level_id.name} at index {i}"
                    )
            else:
                if module.id not in provided_counts:
                    raise InvalidSolutionError(
                        f"illegal provided module ({module.id}) for level {self.level_id.name} at index {i}"
                    )
                provided_counts[module.id] -= 1
                if provided_counts[module.id] < 0:
                    raise InvalidSolutionError(
                        f"too many {module.id} modules for level {self.level_id.name} at index {i}"
                    )
        for module_id, count in provided_counts.items():
            if count > 0:
                raise InvalidSolutionError(
                    f"provided module {module_id} is missing for level {self.level_id.name}"
                )
            if count < 0:
                raise InvalidSolutionError(
                    f"too many {module_id} modules for level {self.level_id.name}"
                )

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

        if self.solved and self.cost != cost:
            logger.warning(
                '%s, "%s": calculated cost doesn\'t match recorded cost',
                self.level.name,
                self.name,
            )
        self.cost = cost

    def normalize(self) -> Solution:
        """Normalize the internals so identical-appearing solutions export to
        identical files (excluding wire layering).
        """
        modules = [m.copy(self.level) for m in self.modules]
        # set unused positions to (1000, 0) (the game already does this sometimes)
        for module in modules:
            if not module.on_rack:
                module.rack_position = Position(1000, 0)
            if not module.on_floor:
                module.floor_position = Position(1000, 0)

        # mapping from module output jacks to module with connected input jack
        wire_map: dict[Module, dict[int, tuple[Module, int]]] = defaultdict(dict)
        # normalize wire directions
        for wire in self.wires:
            module_1 = modules[wire.module_1]
            module_2 = modules[wire.module_2]
            jack_1 = wire.jack_1
            jack_2 = wire.jack_2
            if module_1.jacks[wire.jack_1].direction is JackDirection.IN:
                # reverse wire
                module_1, jack_1, module_2, jack_2 = module_2, jack_2, module_1, jack_1
            wire_map[module_1][jack_1] = (module_2, jack_2)

        # sort modules by floor position, rack position, then module id
        modules.sort(key=lambda m: (m.floor_position, m.rack_position, m.id))

        # regenerate wire list
        wires = []
        for i, module_1 in enumerate(modules):
            for jack_1, (module_2, jack_2) in wire_map[module_1].items():
                wires.append(
                    Wire(
                        module_1=i,
                        jack_1=jack_1,
                        module_2=modules.index(module_2),
                        jack_2=jack_2,
                    )
                )
        wires.sort()

        return dataclasses.replace(self, modules=modules, wires=wires)
