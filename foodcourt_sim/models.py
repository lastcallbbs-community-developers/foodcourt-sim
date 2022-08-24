# pylint: disable=too-few-public-methods
from __future__ import annotations

from dataclasses import InitVar, dataclass
from enum import Enum, unique
from typing import Any, NamedTuple, Type


class Position(NamedTuple):
    column: int
    row: int


@unique
class Direction(Enum):
    RIGHT = 0
    UP = 1
    DOWN = 2
    LEFT = 3


@unique
class JackDirection(Enum):
    IN = 1
    OUT = 2


@dataclass
class Jack:
    name: str
    direction: JackDirection


# convenient shortcuts for defining jacks
def InJack(name: str) -> Jack:
    return Jack(name, JackDirection.IN)


def OutJack(name: str) -> Jack:
    return Jack(name, JackDirection.OUT)


@unique
class ModuleTypeId(Enum):
    MULTIMIXER_ENABLE = 10
    SEQUENCER = 11
    SMALL_COUNTER = 12
    BIG_COUNTER = 13
    MULTIMIXER = 14
    CONVEYOR = 20
    INPUT_1X = 22
    INPUT_2X = 23
    INPUT_3X = 24
    FLUID_DISPENSER_1X = 25
    FLUID_DISPENSER_2X = 26
    FLUID_DISPENSER_3X = 27
    FLUID_COATER = 28  # icing for doughnuts, sauce for da wings
    OUTPUT = 29
    SENSOR = 30
    ROUTER = 31
    SORTER = 32
    STACKER = 33
    WASTE_BIN = 34
    DOUBLE_SLICER = 35  # sweet heat bbq, cafe triste, sushi yeah!
    TRIPLE_SLICER = 36  # on the fried side, da wings
    ROTATOR = 37
    ESPRESSO = 38
    ROLLER = 40
    DOCKER = 41
    FLATTENER = 42
    PAINTER = 43
    MICROWAVE = 45
    GRILL = 46
    FRYER = 47
    HALF_TOPPING_DISPENSER = 48  # chaz cheddar
    FREEZER_1X = 49
    FREEZER_7X = 51
    ANIMATRONIC = 52
    TOPPING_DISPENSER = 53  # candy sprinkler for doughnuts, breadcrumbs for chicken
    HORIZONTAL_SLICER = 54  # breakside grill, bellys
    FREEZER_3X = 55

    TWO_TWELVE_INPUT = 200
    HOT_POCKET_INPUT = 201
    WINE_INPUT = 207
    MUMBAI_CHAAT_INPUT = 205
    MR_CHILLY_INPUT = 202
    KAZAN_INPUT = 204
    SODA_TRENCH_INPUT = 208
    ROSIES_DOUGHNUTS_INPUT = 206
    ON_THE_FRIED_SIDE_INPUT = 203
    SWEET_HEAT_BBQ_INPUT = 213
    THE_WALRUS_INPUT = 219
    MEAT_3_INPUT = 209
    CAFE_TRISTE_INPUT = 212
    THE_COMMISSARY_INPUT = 214
    DA_WINGS_INPUT = 210
    BREAKSIDE_GRILL_INPUT = 217
    CHAZ_CHEDDAR_INPUT = 215
    HALF_CAFF_COFFEE_INPUT = 216
    MILDREDS_NOOK_INPUT = 218
    BELLYS_INPUT = 211
    SUSHI_YEAH_INPUT = 220

    TWO_TWELVE_SCANNER = 150
    HOT_POCKET_SCANNER = 151
    WINE_SCANNER = 157
    MUMBAI_CHAAT_SCANNER = 155
    MR_CHILLY_SCANNER = 152
    KAZAN_SCANNER = 154
    SODA_TRENCH_SCANNER = 158
    ROSIES_DOUGHNUTS_SCANNER = 156
    ON_THE_FRIED_SIDE_SCANNER = 153
    SWEET_HEAT_BBQ_SCANNER = 163
    THE_WALRUS_SCANNER = 169
    MEAT_3_SCANNER = 159
    CAFE_TRISTE_SCANNER = 162
    THE_COMMISSARY_SCANNER = 164
    DA_WINGS_SCANNER = 160
    BREAKSIDE_GRILL_SCANNER = 167
    CHAZ_CHEDDAR_SCANNER = 165
    HALF_CAFF_COFFEE_SCANNER = 166
    MILDREDS_NOOK_SCANNER = 168
    BELLYS_SCANNER = 161
    SUSHI_YEAH_SCANNER = 170


@dataclass
class Module:
    rack_width = 1
    on_rack = True
    on_floor = True
    jacks = []  # type: ignore

    level: InitVar[Level]
    type: ModuleTypeId
    can_delete: bool
    rack_position: Position
    floor_position: Position
    direction: Direction

    def __post_init__(self, level: Level) -> None:
        pass

    def check(self) -> None:
        # check that positions are in-bounds
        if self.on_floor:
            assert 0 <= self.floor_position.row < 7
            assert 0 <= self.floor_position.column < 6
        if self.on_rack:
            assert 0 <= self.rack_position.row < 3
            assert self.rack_position.column >= 0
            assert self.rack_position.column + self.rack_width <= 11


@dataclass
class Scanner(Module):
    _TYPE_IDS = [ModuleTypeId(149 + i) for i in range(1, 22)]
    rack_width = 2

    def __post_init__(self, level: Level) -> None:
        self.jacks = [OutJack("START")]
        for options in level.order_options:
            for name in options:
                self.jacks.append(OutJack(name))


class MainInput(Scanner):
    _TYPE_IDS = [ModuleTypeId(199 + i) for i in range(1, 22)]


@dataclass
class Input(Module):
    input_id: int


class SolidInput(Input):
    _TYPE_IDS = [ModuleTypeId.INPUT_1X, ModuleTypeId.INPUT_2X, ModuleTypeId.INPUT_3X]

    def __post_init__(self, level: Level) -> None:
        self.jacks = [InJack(name) for name in level.solid_inputs[self.input_id]]


class Freezer(SolidInput):
    _TYPE_IDS = [
        ModuleTypeId.FREEZER_1X,
        ModuleTypeId.FREEZER_3X,
        ModuleTypeId.FREEZER_7X,
    ]
    rack_width = 2


class OtherInput(Input):
    def __post_init__(self, level: Level) -> None:
        self.jacks = [InJack(name) for name in level.other_inputs[self.input_id]]


class FluidDispenser(OtherInput):
    _TYPE_IDS = [
        ModuleTypeId.FLUID_DISPENSER_1X,
        ModuleTypeId.FLUID_DISPENSER_2X,
        ModuleTypeId.FLUID_DISPENSER_3X,
    ]


class FluidCoater(OtherInput):
    _TYPE_IDS = [ModuleTypeId.FLUID_COATER]
    on_rack = False


class ToppingDispenser(OtherInput):
    _TYPE_IDS = [ModuleTypeId.TOPPING_DISPENSER, ModuleTypeId.HALF_TOPPING_DISPENSER]


class SimpleMachine(Module):
    _TYPE_IDS = [
        ModuleTypeId.CONVEYOR,
        ModuleTypeId.OUTPUT,
        ModuleTypeId.WASTE_BIN,
        ModuleTypeId.DOUBLE_SLICER,
        ModuleTypeId.HORIZONTAL_SLICER,
        ModuleTypeId.TRIPLE_SLICER,
        ModuleTypeId.ROTATOR,
        ModuleTypeId.ROLLER,
        ModuleTypeId.DOCKER,
        ModuleTypeId.FLATTENER,
    ]
    on_rack = False


class Router(Module):
    _TYPE_IDS = [ModuleTypeId.ROUTER]
    jacks = [InJack(name) for name in ["LEFT", "THRU", "RIGHT"]]


class Sensor(Module):
    _TYPE_IDS = [ModuleTypeId.SENSOR]
    jacks = [OutJack("SENSE")]


class Sorter(Module):
    _TYPE_IDS = [ModuleTypeId.SORTER]
    jacks = [OutJack("SENSE"), InJack("LEFT"), InJack("THRU"), InJack("RIGHT")]


class Cooker(Module):
    _TYPE_IDS = [ModuleTypeId.GRILL, ModuleTypeId.FRYER, ModuleTypeId.MICROWAVE]
    jacks = [OutJack("SENSE"), InJack("EJECT")]


class Stacker(Module):
    _TYPE_IDS = [ModuleTypeId.STACKER]
    jacks = [OutJack("STACK"), InJack("EJECT")]


class Multimixer(Module):
    _TYPE_IDS = [ModuleTypeId.MULTIMIXER, ModuleTypeId.MULTIMIXER_ENABLE]
    on_floor = False

    def __post_init__(self, level: Level) -> None:
        del level
        if self.type is ModuleTypeId.MULTIMIXER:
            self.jacks = [
                *[InJack(f"IN_{i+1}") for i in range(4)],
                *[OutJack(f"OUT_{i+1}") for i in range(4)],
            ]
        else:
            assert self.type is ModuleTypeId.MULTIMIXER_ENABLE
            self.jacks = [
                InJack("enable"),
                *[InJack(f"IN_{i+1}") for i in range(3)],
                *[OutJack(f"OUT_{i+1}") for i in range(3)],
            ]


@dataclass
class SmallCounter(Module):
    _TYPE_IDS = [ModuleTypeId.SMALL_COUNTER]
    on_floor = False
    jacks = [OutJack("ZERO"), InJack("IN_1"), InJack("IN_2")]

    values: list[int]


@dataclass
class BigCounter(Module):
    _TYPE_IDS = [ModuleTypeId.BIG_COUNTER]
    on_floor = False
    jacks = [
        OutJack("ZERO"),
        OutJack("POS"),
        InJack("IN_1"),
        InJack("IN_2"),
        InJack("IN_3"),
        InJack("IN_4"),
    ]

    values: list[int]


@dataclass
class Sequencer(Module):
    _TYPE_IDS = [ModuleTypeId.SEQUENCER]
    on_floor = False
    rack_width = 2
    jacks = [
        InJack("START"),
        InJack("STOP"),
        OutJack("A"),
        OutJack("B"),
        OutJack("C"),
        OutJack("D"),
    ]

    rows: list[list[bool]]


@dataclass
class Painter(Module):
    _TYPE_IDS = [ModuleTypeId.PAINTER]

    color: int
    mask: int


class Espresso(Module):
    _TYPE_IDS = [ModuleTypeId.ESPRESSO]
    jacks = [InJack(name) for name in ["GRIND", "XTRACT", "STEAM", "EJECT"]]


@unique
class MusicMode(Enum):
    lead = 0
    bass = 1


@dataclass
class Animatronic(Module):
    _TYPE_IDS = [ModuleTypeId.ANIMATRONIC]
    rack_width = 2
    jacks = [
        InJack(name) for name in ["DANCE", "SING", "GLASSES", "I", "IV", "V", "I'"]
    ]

    music_mode: MusicMode


def populate_module_table() -> dict[ModuleTypeId, Type[Module]]:
    lookup: dict[ModuleTypeId, Type[Module]] = {}
    # dynamically pick up all Module subclasses in this module
    for value in globals().values():
        if (
            isinstance(value, type)
            and issubclass(value, Module)
            and hasattr(value, "_TYPE_IDS")
        ):
            # pylint: disable-next=protected-access
            for type_id in value._TYPE_IDS:  # type: ignore  # dynamically checked
                assert isinstance(type_id, ModuleTypeId)
                assert (
                    type_id not in lookup
                ), f"{type_id} is claimed by {lookup[type_id]} and {value}"
                lookup[type_id] = value

    assert lookup.keys() == set(
        ModuleTypeId
    ), f"unhandled module types: {set(ModuleTypeId) - lookup.keys()}"
    return lookup


MODULE_LOOKUP = populate_module_table()


class Wire(NamedTuple):
    module_1: int
    jack_1: int
    module_2: int
    jack_2: int


@dataclass
class Solution:  # pylint: disable=too-many-instance-attributes
    version: int
    level: int
    name: str
    solved: bool
    time: int
    cost: int
    modules: list[Module]
    wires: list[Wire]

    def dump_wires_to(self, arg: Any) -> None:
        """used for reverse engineering"""
        if isinstance(arg, Module):
            index = self.modules.index(arg)
        elif isinstance(arg, int):
            index = arg
        elif isinstance(arg, ModuleTypeId):
            index = next(i for i, m in enumerate(self.modules) if m.type is arg)
        module = self.modules[index]
        print(f"Wires to/from {module.type} (index {index}):")
        connections = []
        for i, wire in enumerate(self.wires):
            if index not in (wire.module_1, wire.module_2):
                continue
            if wire.module_2 == index:
                wire = Wire(wire.module_2, wire.jack_2, wire.module_1, wire.jack_1)
            connections.append((i, wire))
        connections.sort(key=lambda x: x[1].jack_1)
        for i, wire in connections:
            module_2 = self.modules[wire.module_2]
            jack_1 = str(wire.jack_1)
            jack_2 = str(wire.jack_2)
            if wire.jack_2 < len(module_2.jacks):
                j2 = module_2.jacks[wire.jack_2]
                jack_2 = repr(j2.name.upper())
                other_direction = JackDirection(3 - j2.direction.value)
                jack_1 += f" ({other_direction.name})".ljust(6)
            print(
                f"jack {jack_1} to jack {jack_2} of {module_2.type} (index {wire.module_2})"
            )

    def check(self, level: Level) -> None:
        assert level.internal_id == self.level

        # make sure main input and scanners match the level
        main_input_index = -1
        for i, module in enumerate(self.modules):
            module.check()
            if 200 <= module.type.value <= 220:
                assert (
                    main_input_index == -1
                ), f"duplicate main input module found at index {i} (first was at {main_input_index})"
                main_input_index = i
                assert (
                    module.type.value == level.internal_id + 199
                ), f"mismatched main input ({module.type}) for level {level.internal_name} at index {i}"
            if 150 <= module.type.value <= 170:
                assert (
                    module.type.value == level.internal_id + 149
                ), f"incorrect scanner ({module.type}) for level {level.internal_name} at index {i}"
        assert main_input_index != -1, "no main input module found"

        # check that wires reference existing modules
        num_modules = len(self.modules)
        for wire in self.wires:
            assert wire.module_1 < num_modules
            assert wire.module_2 < num_modules
            module_1 = self.modules[wire.module_1]
            module_2 = self.modules[wire.module_2]
            assert wire.jack_1 < len(module_1.jacks), f"{module_1}, jack {wire.jack_1}"
            assert wire.jack_2 < len(module_2.jacks), f"{module_2}, jack {wire.jack_2}"


class Level(NamedTuple):
    # human-readable name
    name: str
    # in-game level number, starts from 1, included in save files
    number: int
    # prefix for save file name
    internal_name: str
    # starts from 0, doesn't follow in-game order
    internal_id: int
    # exclusive groups of order signals (shared between main inputs and scanners)
    order_options: list[list[str]]
    # used for INPUT_* and FREEZER_*
    solid_inputs: list[list[str]]
    # used for FLUID_DISPENSER_*, FLUID_COATER, TOPPING_DISPENSER, HALF_TOPPING_DISPENSER
    other_inputs: list[list[str]]
