# pylint: disable=too-few-public-methods
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Type

from .models import (
    Action,
    CoatFluid,
    Direction,
    Dock,
    EmergencyStop,
    Entity,
    EntityId,
    Flatten,
    InJack,
    Level,
    LevelId,
    Module,
    ModuleId,
    MoveEntity,
    MusicMode,
    Operation,
    OperationId,
    OutJack,
    PaintableCup,
    PaintColor,
    PaintMask,
    PizzaDough,
    Position,
    RemoveEntity,
    ToppingId,
)

# Module subclasses


@dataclass
class TargetsSelf(Module):
    def target_pos(self) -> Position:
        return self.floor_position.copy()


@dataclass
class TargetsFront(Module):
    def target_pos(self) -> Position:
        target = self.floor_position.copy()
        target.shift_by(self.direction)
        return target


@dataclass
class Scanner(TargetsFront):
    _MODULE_IDS = [ModuleId(149 + id.value) for id in LevelId]
    rack_width = 2
    price = 20

    def __post_init__(self, level: Level) -> None:
        self.jacks = [OutJack("START")]
        for options in level.order_signal_names:
            for name in options:
                self.jacks.append(OutJack(name))
        super().__post_init__(level)


@dataclass
class MainInput(Scanner, TargetsSelf):
    _MODULE_IDS = [ModuleId(199 + id.value) for id in LevelId]
    price = 0


@dataclass
class Input(TargetsSelf):
    input_id: int


@dataclass
class EntityInput(Input):
    _MODULE_IDS = [ModuleId.INPUT_1X, ModuleId.INPUT_2X, ModuleId.INPUT_3X]

    entity_ids: list[EntityId] = field(init=False)

    def __post_init__(self, level: Level) -> None:
        self.entity_ids = level.entity_inputs[self.input_id]
        self.jacks = [InJack(eid.name) for eid in self.entity_ids]
        super().__post_init__(level)


class Freezer(EntityInput):
    _MODULE_IDS = [
        ModuleId.FREEZER_1X,
        ModuleId.FREEZER_3X,
        ModuleId.FREEZER_7X,
    ]
    rack_width = 2


@dataclass
class ToppingInput(Input):
    topping_ids: list[ToppingId] = field(init=False)

    def __post_init__(self, level: Level) -> None:
        self.topping_ids = level.topping_inputs[self.input_id]
        self.jacks = [InJack(tid.name) for tid in self.topping_ids]
        super().__post_init__(level)


class FluidDispenser(ToppingInput, TargetsFront):
    _MODULE_IDS = [
        ModuleId.FLUID_DISPENSER_1X,
        ModuleId.FLUID_DISPENSER_2X,
        ModuleId.FLUID_DISPENSER_3X,
    ]


class FluidCoater(ToppingInput):
    _MODULE_IDS = [ModuleId.FLUID_COATER]
    on_rack = False

    def __post_init__(self, level: Level) -> None:
        super().__post_init__(level)
        self.jacks = []  # remove the jacks added by ToppingInput
        assert len(self.topping_ids) == 1

    def update(self, target: Optional[Entity]) -> list[Action]:
        if target is None:
            return []
        target.operations.append(CoatFluid(self.topping_ids[0]))
        return [MoveEntity(target, self.direction)]


class ToppingDispenser(ToppingInput):
    _MODULE_IDS = [ModuleId.TOPPING_DISPENSER, ModuleId.HALF_TOPPING_DISPENSER]


class Conveyor(TargetsSelf):
    _MODULE_IDS = [ModuleId.CONVEYOR]
    price = 5
    on_rack = False

    def update(self, target: Optional[Entity]) -> list[Action]:
        if target is None:
            return []
        # TODO: incoming priority will be dealt elsewhere
        return [MoveEntity(target, self.direction, force=False)]


class SimpleMachine(TargetsSelf):
    on_rack = False


class Output(SimpleMachine):
    _MODULE_IDS = [ModuleId.OUTPUT]
    price = 0


@dataclass
class Router(Module):
    _MODULE_IDS = [ModuleId.ROUTER]
    price = 10
    jacks = [InJack(name) for name in ["LEFT", "THRU", "RIGHT"]]

    current_direction: Direction = field(init=False)

    def __post_init__(self, level: Level) -> None:
        super().__post_init__(level)
        self.current_direction = self.direction

    # MoveEntity(..., force=False)


class Sensor(TargetsFront):
    _MODULE_IDS = [ModuleId.SENSOR]
    price = 5
    jacks = [OutJack("SENSE")]


class Sorter(TargetsSelf):
    _MODULE_IDS = [ModuleId.SORTER]
    price = 10
    jacks = [OutJack("SENSE"), InJack("LEFT"), InJack("THRU"), InJack("RIGHT")]


@dataclass
class Stacker(Module):
    _MODULE_IDS = [ModuleId.STACKER]
    price = 20
    jacks = [OutJack("STACK"), InJack("EJECT")]

    stack: list[Entity] = field(default_factory=list)


@dataclass
class Cooker(TargetsSelf):
    _MODULE_IDS = [ModuleId.GRILL, ModuleId.FRYER, ModuleId.MICROWAVE]
    price = 20
    jacks = [OutJack("SENSE"), InJack("EJECT")]

    _operation: Operation = field(init=False)

    def __post_init__(self, level: Level) -> None:
        super().__post_init__(level)
        self._operation = Operation(
            {
                ModuleId.GRILL: OperationId.COOK_GRILL,
                ModuleId.FRYER: OperationId.COOK_FRYER,
                ModuleId.MICROWAVE: OperationId.COOK_MICROWAVE,
            }[self.id]
        )

    def update(self, target: Optional[Entity]) -> list[Action]:
        if target is None:
            return []
        target.operations.append(self._operation)
        # TODO: handle eject
        return []


@dataclass
class WasteBin(SimpleMachine):
    _MODULE_IDS = [ModuleId.WASTE_BIN]
    price = 20

    is_full: bool = False

    def update(self, target: Optional[Entity]) -> list[Action]:
        if target is None:
            return []
        if self.is_full:
            raise EmergencyStop(
                "This waste bin has already been used.", self.floor_position
            )
        self.is_full = True
        return [RemoveEntity(target)]


class DoubleSlicer(SimpleMachine):
    _MODULE_IDS = [ModuleId.DOUBLE_SLICER]
    price = 20


class TripleSlicer(SimpleMachine):
    _MODULE_IDS = [ModuleId.TRIPLE_SLICER]
    price = 20


class HorizontalSlicer(SimpleMachine):
    _MODULE_IDS = [ModuleId.HORIZONTAL_SLICER]
    price = 20


class Roller(SimpleMachine):
    _MODULE_IDS = [ModuleId.ROLLER]
    price = 20


class Docker(SimpleMachine):
    _MODULE_IDS = [ModuleId.DOCKER]
    price = 20

    def update(self, target: Optional[Entity]) -> list[Action]:
        if target is None:
            return []
        target.operations.append(Dock())
        return [MoveEntity(target, self.direction)]


class Flattener(SimpleMachine):
    _MODULE_IDS = [ModuleId.FLATTENER]
    price = 20

    def update(self, target: Optional[Entity]) -> list[Action]:
        if target is None:
            return []
        target.operations.append(Flatten())
        return [MoveEntity(target, self.direction)]


class Rotator(SimpleMachine):
    _MODULE_IDS = [ModuleId.ROTATOR]
    price = 20

    def update(self, target: Optional[Entity]) -> list[Action]:
        if target is None:
            return []
        assert isinstance(target, PizzaDough)
        # swap left and right toppings
        target.left_toppings, target.right_toppings = (
            target.right_toppings,
            target.left_toppings,
        )
        return [MoveEntity(target, self.direction)]


@dataclass
class Painter(TargetsSelf):
    _MODULE_IDS = [ModuleId.PAINTER]
    price = 40

    color: PaintColor
    mask: PaintMask

    def update(self, target: Optional[Entity]) -> list[Action]:
        if target is None:
            return []
        assert isinstance(target, PaintableCup)
        # paint colors go from top to bottom
        if self.mask is PaintMask.UPPER_2:
            indices = [0, 1]
        elif self.mask is PaintMask.UPPER_1:
            indices = [0]
        elif self.mask is PaintMask.LOWER_1:
            indices = [2]
        elif self.mask is PaintMask.LOWER_2:
            indices = [1, 2]
        for i in indices:
            target.colors[i] = self.color
        return [MoveEntity(target, self.direction)]


@dataclass
class Espresso(Module):
    _MODULE_IDS = [ModuleId.ESPRESSO]
    price = 40
    jacks = [InJack(name) for name in ["GRIND", "XTRACT", "STEAM", "EJECT"]]

    grind_count: int = 0


@dataclass
class Animatronic(Module):
    _MODULE_IDS = [ModuleId.ANIMATRONIC]
    rack_width = 2
    price = 40
    jacks = [
        InJack(name) for name in ["DANCE", "SING", "GLASSES", "I", "IV", "V", "I'"]
    ]

    music_mode: MusicMode


class Multimixer(Module):
    _MODULE_IDS = [ModuleId.MULTIMIXER]
    on_floor = False
    price = 1
    jacks = [
        *[InJack(f"IN_{i+1}") for i in range(4)],
        *[OutJack(f"OUT_{i+1}") for i in range(4)],
    ]


class MultimixerEnable(Multimixer):
    _MODULE_IDS = [ModuleId.MULTIMIXER_ENABLE]
    price = 1
    jacks = [
        InJack("ENABLE"),
        *[InJack(f"IN_{i+1}") for i in range(3)],
        *[OutJack(f"OUT_{i+1}") for i in range(3)],
    ]


@dataclass
class SmallCounter(Module):
    _MODULE_IDS = [ModuleId.SMALL_COUNTER]
    on_floor = False
    price = 3
    jacks = [OutJack("ZERO"), InJack("IN_1"), InJack("IN_2")]

    values: list[int]
    count: int = 0

    def check(self) -> None:
        super().check()
        assert len(self.values) == 2
        assert all(-9 <= x <= 9 for x in self.values)


@dataclass
class BigCounter(Module):
    _MODULE_IDS = [ModuleId.BIG_COUNTER]
    on_floor = False
    price = 5
    jacks = [
        OutJack("ZERO"),
        OutJack("POS"),
        InJack("IN_1"),
        InJack("IN_2"),
        InJack("IN_3"),
        InJack("IN_4"),
    ]

    values: list[int]
    count: int = 0

    def check(self) -> None:
        super().check()
        assert len(self.values) == 4
        assert all(-99 <= x <= 99 for x in self.values)


@dataclass
class Sequencer(Module):
    _MODULE_IDS = [ModuleId.SEQUENCER]
    rack_width = 2
    on_floor = False
    price = 5
    jacks = [
        InJack("START"),
        InJack("STOP"),
        OutJack("A"),
        OutJack("B"),
        OutJack("C"),
        OutJack("D"),
    ]

    rows: list[list[bool]]
    current_row: int = -1

    def check(self) -> None:
        super().check()
        assert len(self.rows) == 12
        assert all(len(r) == 4 for r in self.rows)


def populate_module_table() -> dict[ModuleId, Type[Module]]:
    lookup: dict[ModuleId, Type[Module]] = {}
    # dynamically pick up all Module subclasses in this module
    for value in globals().values():
        if (
            isinstance(value, type)
            and issubclass(value, Module)
            and hasattr(value, "_MODULE_IDS")
        ):
            # pylint: disable-next=protected-access
            for module_id in value._MODULE_IDS:  # type: ignore  # dynamically checked
                assert isinstance(module_id, ModuleId)
                assert (
                    module_id not in lookup
                ), f"{module_id} is claimed by {lookup[module_id]} and {value}"
                lookup[module_id] = value

    assert lookup.keys() == set(
        ModuleId
    ), f"unhandled module ids: {set(ModuleId) - lookup.keys()}"
    return lookup


MODULE_LOOKUP = populate_module_table()
