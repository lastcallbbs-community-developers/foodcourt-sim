# pylint: disable=too-few-public-methods
from __future__ import annotations

import functools
from collections import Counter
from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from enum import Enum, auto, unique
from typing import Any, NamedTuple, Type


# from enum docs
class OrderedEnum(Enum):
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


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
class LevelId(Enum):
    TWO_TWELVE = 1
    HOT_POCKET = 2
    WINE_OCLOCK = 8
    MUMBAI_CHAAT = 6
    MR_CHILLY = 3
    KAZAN = 5
    SODA_TRENCH = 9
    ROSIES_DOUGHNUTS = 7
    ON_THE_FRIED_SIDE = 4
    SWEET_HEAT_BBQ = 14
    THE_WALRUS = 20
    MEAT_3 = 10
    CAFE_TRISTE = 13
    THE_COMMISSARY = 15
    DA_WINGS = 11
    BREAKSIDE_GRILL = 18
    CHAZ_CHEDDAR = 16
    HALF_CAFF_COFFEE = 17
    MILDREDS_NOOK = 19
    BELLYS = 12
    SUSHI_YEAH = 21


@unique
class ModuleId(Enum):
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
    id: ModuleId
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
    _MODULE_IDS = [ModuleId(149 + id.value) for id in LevelId]
    rack_width = 2

    def __post_init__(self, level: Level) -> None:
        self.jacks = [OutJack("START")]
        for options in level.order_signal_names:
            for name in options:
                self.jacks.append(OutJack(name))


class MainInput(Scanner):
    _MODULE_IDS = [ModuleId(199 + id.value) for id in LevelId]


@dataclass
class Input(Module):
    input_id: int


class EntityInput(Input):
    _MODULE_IDS = [ModuleId.INPUT_1X, ModuleId.INPUT_2X, ModuleId.INPUT_3X]

    def __post_init__(self, level: Level) -> None:
        self.jacks = [InJack(eid.name) for eid in level.entity_inputs[self.input_id]]


class Freezer(EntityInput):
    _MODULE_IDS = [
        ModuleId.FREEZER_1X,
        ModuleId.FREEZER_3X,
        ModuleId.FREEZER_7X,
    ]
    rack_width = 2


class ToppingInput(Input):
    def __post_init__(self, level: Level) -> None:
        self.jacks = [InJack(tid.name) for tid in level.topping_inputs[self.input_id]]


class FluidDispenser(ToppingInput):
    _MODULE_IDS = [
        ModuleId.FLUID_DISPENSER_1X,
        ModuleId.FLUID_DISPENSER_2X,
        ModuleId.FLUID_DISPENSER_3X,
    ]


class FluidCoater(ToppingInput):
    _MODULE_IDS = [ModuleId.FLUID_COATER]
    on_rack = False


class ToppingDispenser(ToppingInput):
    _MODULE_IDS = [ModuleId.TOPPING_DISPENSER, ModuleId.HALF_TOPPING_DISPENSER]


class SimpleMachine(Module):
    _MODULE_IDS = [
        ModuleId.CONVEYOR,
        ModuleId.OUTPUT,
        ModuleId.WASTE_BIN,
        ModuleId.DOUBLE_SLICER,
        ModuleId.HORIZONTAL_SLICER,
        ModuleId.TRIPLE_SLICER,
        ModuleId.ROTATOR,
        ModuleId.ROLLER,
        ModuleId.DOCKER,
        ModuleId.FLATTENER,
    ]
    on_rack = False


class Router(Module):
    _MODULE_IDS = [ModuleId.ROUTER]
    jacks = [InJack(name) for name in ["LEFT", "THRU", "RIGHT"]]


class Sensor(Module):
    _MODULE_IDS = [ModuleId.SENSOR]
    jacks = [OutJack("SENSE")]


class Sorter(Module):
    _MODULE_IDS = [ModuleId.SORTER]
    jacks = [OutJack("SENSE"), InJack("LEFT"), InJack("THRU"), InJack("RIGHT")]


class Cooker(Module):
    _MODULE_IDS = [ModuleId.GRILL, ModuleId.FRYER, ModuleId.MICROWAVE]
    jacks = [OutJack("SENSE"), InJack("EJECT")]


class Stacker(Module):
    _MODULE_IDS = [ModuleId.STACKER]
    jacks = [OutJack("STACK"), InJack("EJECT")]


class Multimixer(Module):
    _MODULE_IDS = [ModuleId.MULTIMIXER, ModuleId.MULTIMIXER_ENABLE]
    on_floor = False

    def __post_init__(self, level: Level) -> None:
        del level
        if self.id is ModuleId.MULTIMIXER:
            self.jacks = [
                *[InJack(f"IN_{i+1}") for i in range(4)],
                *[OutJack(f"OUT_{i+1}") for i in range(4)],
            ]
        else:
            assert self.id is ModuleId.MULTIMIXER_ENABLE
            self.jacks = [
                InJack("enable"),
                *[InJack(f"IN_{i+1}") for i in range(3)],
                *[OutJack(f"OUT_{i+1}") for i in range(3)],
            ]


@dataclass
class SmallCounter(Module):
    _MODULE_IDS = [ModuleId.SMALL_COUNTER]
    on_floor = False
    jacks = [OutJack("ZERO"), InJack("IN_1"), InJack("IN_2")]

    values: list[int]


@dataclass
class BigCounter(Module):
    _MODULE_IDS = [ModuleId.BIG_COUNTER]
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
    _MODULE_IDS = [ModuleId.SEQUENCER]
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


@unique
class PaintColor(Enum):
    RED = 0
    WHITE = 1
    BLUE = 2


@unique
class PaintMask(Enum):
    UPPER_2 = 0
    UPPER_1 = 1
    LOWER_1 = 2
    LOWER_2 = 3


@dataclass
class Painter(Module):
    _MODULE_IDS = [ModuleId.PAINTER]

    color: PaintColor
    mask: PaintMask


@dataclass
class Espresso(Module):
    _MODULE_IDS = [ModuleId.ESPRESSO]
    jacks = [InJack(name) for name in ["GRIND", "XTRACT", "STEAM", "EJECT"]]


@unique
class MusicMode(Enum):
    lead = 0
    bass = 1


@dataclass
class Animatronic(Module):
    _MODULE_IDS = [ModuleId.ANIMATRONIC]
    rack_width = 2
    jacks = [
        InJack(name) for name in ["DANCE", "SING", "GLASSES", "I", "IV", "V", "I'"]
    ]

    music_mode: MusicMode


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


class Wire(NamedTuple):
    module_1: int
    jack_1: int
    module_2: int
    jack_2: int


@dataclass
class Solution:  # pylint: disable=too-many-instance-attributes
    version: int
    level_id: LevelId
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
        elif isinstance(arg, ModuleId):
            index = next(i for i, m in enumerate(self.modules) if m.id is arg)
        module = self.modules[index]
        print(f"Wires to/from {module.id} (index {index}):")
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
                f"jack {jack_1} to jack {jack_2} of {module_2.id} (index {wire.module_2})"
            )

    def check(self, level: Level) -> None:
        assert level.id == self.level_id

        # make sure main input and scanners match the level
        main_input_index = -1
        for i, module in enumerate(self.modules):
            module.check()
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
        assert main_input_index != -1, "no main input module found"

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


class Level(NamedTuple):
    # included in save files, starts from 1, doesn't follow in-game order
    id: LevelId
    # human-readable name
    name: str
    # in-game level number, starts from 1
    number: int
    # names of order jacks (shared between main inputs and scanners)
    order_signal_names: list[str]
    # used for INPUT_* and FREEZER_*
    entity_inputs: list[list[EntityId]]
    # used for FLUID_DISPENSER_*, FLUID_COATER, TOPPING_DISPENSER, HALF_TOPPING_DISPENSER
    topping_inputs: list[list[ToppingId]]
    # final products of each order, keyed by order signals
    orders: dict[tuple[bool, ...], Entity]

    @property
    def internal_name(self) -> str:
        # prefix for save file name
        return self.name.lower().replace(" ", "-").replace("'", "")

    @property
    def order_list(self) -> list[tuple[tuple[bool, ...], Entity]]:
        return list(self.orders.items())


# simulation-only objects


@unique
class OperationId(OrderedEnum):
    COOK_FRYER = auto()
    COOK_MICROWAVE = auto()
    COOK_GRILL = auto()
    DOCK = auto()
    ROLL = auto()
    FLATTEN = auto()
    ESPRESSO_EXTRACT = auto()
    ESPRESSO_STEAM = auto()
    DISPENSE_FLUID = auto()
    DISPENSE_FLUID_MIXED = auto()
    COAT_FLUID = auto()
    DISPENSE_TOPPING = auto()


@dataclass(frozen=True, order=True)
class Operation:
    id: OperationId


def CookFryer() -> Operation:
    return Operation(OperationId.COOK_FRYER)


def CookMicrowave() -> Operation:
    return Operation(OperationId.COOK_MICROWAVE)


def CookGrill() -> Operation:
    return Operation(OperationId.COOK_GRILL)


def Dock() -> Operation:
    return Operation(OperationId.DOCK)


def Roll() -> Operation:
    return Operation(OperationId.ROLL)


def Flatten() -> Operation:
    return Operation(OperationId.FLATTEN)


@dataclass(frozen=True, order=True)
class Dispense(Operation):
    topping: ToppingId


def DispenseFluid(topping: ToppingId) -> Operation:
    return Dispense(OperationId.DISPENSE_FLUID, topping)


@dataclass(frozen=True, order=True)
class _DispenseFluidMixed(Dispense):
    topping_2: ToppingId

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, _DispenseFluidMixed):
            return NotImplemented
        assert self.id == other.id
        # order doesn't matter
        own_toppings = sorted([self.topping, self.topping_2])
        other_toppings = sorted([other.topping, other.topping_2])
        return own_toppings == other_toppings


def DispenseFluidMixed(topping_1: ToppingId, topping_2: ToppingId) -> Operation:
    return _DispenseFluidMixed(OperationId.DISPENSE_FLUID_MIXED, topping_1, topping_2)


def CoatFluid(topping_id: ToppingId) -> Operation:
    return Dispense(OperationId.COAT_FLUID, topping_id)


def DispenseTopping(topping_id: ToppingId) -> Operation:
    return Dispense(OperationId.DISPENSE_TOPPING, topping_id)


@unique
class EntityId(OrderedEnum):
    TRAY = auto()

    NACHO = auto()  # 2twelve
    PRETZEL = auto()  # 2twelve

    POCKET = auto()  # original hot pocket experience

    GLASS = auto()  # wine o'clock

    DOUGH = auto()  # mumbai chaat, rosie's doughnuts, chaz cheddar

    CONE = auto()  # mr chilly

    PELMENI = auto()  # kazan

    CUP = auto()  # soda trench, the walrus, cafe triste, half caff coffee, belly's
    LID = auto()  # soda trench, belly's

    CHICKEN = auto()  # on the fried side, da wings
    CHICKEN_HALF = auto()  # on the fried side, da wings
    CHICKEN_CUTLET = auto()  # on the fried side, da wings
    CHICKEN_LEG = auto()  # on the fried side, da wings

    WING_PLACEHOLDER = auto()  # da wings

    ROAST = auto()  # sweet heat bbq
    ROAST_SLICE = auto()  # sweet heat bbq
    RIBS = auto()  # sweet heat bbq
    RIBS_SLICE = auto()  # sweet heat bbq

    ICE = auto()  # the walrus

    MEAT = auto()  # meat+3, breakside grill, belly's
    BOWL = auto()  # meat+3, sushi yeah!

    PAPER = auto()  # cafe triste
    CIGARETTE_2X = auto()  # cafe triste
    CIGARETTE = auto()  # cafe triste

    PIZZA = auto()  # the commissary
    BURGER = auto()  # the commissary
    TENDER = auto()  # the commissary
    CORNDOG = auto()  # the commissary
    CURLY = auto()  # the commissary
    CRINKLE = auto()  # the commissary
    TOT = auto()  # the commissary
    PLAIN = auto()  # the commissary
    CHOCO = auto()  # the commissary

    BUN = auto()  # breakside grill, belly's
    BUN_TOP = auto()  # breakside grill, belly's
    BUN_BOTTOM = auto()  # breakside grill, belly's
    CHEESE = auto()  # breakside grill, belly's
    PICKLE = auto()  # breakside grill
    TOMATO = auto()  # breakside grill, mildred's nook

    EGG = auto()  # mildred's nook
    BACON = auto()  # mildred's nook
    BANGER = auto()  # mildred's nook
    FUNGUS = auto()  # mildred's nook
    BLACK = auto()  # mildred's nook
    BREAD = auto()  # mildred's nook

    POTATO = auto()  # belly's
    ONION = auto()  # belly's

    NORI = auto()  # sushi yeah!
    RICE = auto()  # sushi yeah!
    TUNA = auto()  # sushi yeah!
    SALMON = auto()  # sushi yeah!
    PLATE = auto()  # sushi yeah!
    TUNA_ROLL_2X = auto()  # sushi yeah!
    TUNA_ROLL = auto()  # sushi yeah!
    SALMON_ROLL_2X = auto()  # sushi yeah!
    SALMON_ROLL = auto()  # sushi yeah!


@unique
class ToppingId(OrderedEnum):
    CHEESE = auto()  # 2twelve, chaz cheddar

    RED = auto()  # wine o'clock
    WHITE = auto()  # wine o'clock

    TOMATO = auto()  # mumbai chaat
    MINT = auto()  # mumbai chaat
    YOGURT = auto()  # mumbai chaat

    CHOCO = auto()  # mr chilly, rosie's doughnuts
    VANILLA = auto()  # mr chilly

    COLA = auto()  # soda trench, the walrus

    BERRY = auto()  # rosie's doughnuts
    CANDY = auto()  # rosie's doughnuts

    BREADING = auto()  # on the fried side

    VODKA = auto()  # the walrus
    WHISKY = auto()  # the walrus
    LEMON = auto()  # the walrus

    MAC = auto()  # meat+3
    SLAW = auto()  # meat+3
    GREENS = auto()  # meat+3
    BEANS = auto()  # meat+3, mildred's nook

    LEAVES = auto()  # cafe triste
    COFFEE = auto()  # cafe triste, half caff coffee

    SAUCE = auto()  # da wings, chaz cheddar

    MEAT = auto()  # chaz cheddar
    VEGGIE = auto()  # chaz cheddar

    MILK = auto()  # half caff coffee
    WATER = auto()  # half caff coffee
    FOAM = auto()  # half caff coffee

    ORANGE = auto()  # belly's
    PURPLE = auto()  # belly's

    SOUP = auto()  # sushi yeah!


# these entities will not have their stack moved to whatever's below them when
# stacked on something else
STACK_ROOTS = [
    EntityId.TRAY,
    EntityId.CUP,  # see Cup
    EntityId.BUN_BOTTOM,  # see Burger
    EntityId.PLATE,
    EntityId.RICE,
]


@functools.total_ordering  # optimization note: this adds some overhead (see the docs)
@dataclass(eq=False)
class Entity:
    """Something that rides on conveyors."""

    id: EntityId
    # all the operations that were performed on this entity, in order
    operations: list[Operation] = field(default_factory=list)
    # the entities that are stacked on this entity
    stack: list[Entity] = field(default_factory=list)

    position: Position = field(default_factory=lambda: Position(-1, -1))

    def __post_init__(self) -> None:
        # TODO: this is just to make sure I implement things right, and should be removed once testing is done
        if self.id in (EntityId.CUP, EntityId.BUN_BOTTOM, EntityId.NORI):
            assert self.__class__ is not Entity, "code mistake: must use subclasses"

    def _compare_key(self) -> tuple[Any, ...]:
        return (self.id, self.operations, sorted(self.stack))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return self._compare_key() == other._compare_key()

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return self._compare_key() < other._compare_key()


@dataclass(eq=False)
class ChaatDough(Entity):
    """Dough for Mumbai Chaat."""

    id: EntityId = EntityId.DOUGH

    sauces: set[ToppingId] = field(default_factory=set)

    def check(self) -> None:
        assert not (self.sauces - {ToppingId.TOMATO, ToppingId.MINT, ToppingId.YOGURT})

    def _compare_key(self) -> tuple[Any, ...]:
        return (*super()._compare_key(), self.sauces)


@dataclass(eq=False)
class Cup(Entity):
    """Cup that can contain unordered fluids."""

    id: EntityId = EntityId.CUP
    # note: milk can be foamed as long as it's the only thing in the cup
    contents: Counter[ToppingId] = field(default_factory=Counter)

    def _compare_key(self) -> tuple[Any, ...]:
        # use +contents to discard negative and zero counts
        return (*super()._compare_key(), +self.contents)


@dataclass(eq=False)
class PaintableCup(Cup):
    """Paintable cup for Soda Trench."""

    id: EntityId = EntityId.CUP
    # cup paint colors, from top to bottom
    colors: list[PaintColor] = field(default_factory=lambda: [PaintColor.WHITE] * 3)

    def _compare_key(self) -> tuple[Any, ...]:
        return (*super()._compare_key(), self.colors)


@dataclass(eq=False)
class WingPlaceholder(Entity):
    """Placeholder entity for Da Wings order checking."""

    id: EntityId = EntityId.WING_PLACEHOLDER

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        # return an object that compares equal to E.CHICKEN_CUTLET and E.CHICKEN_LEG
        if other.id in (EntityId.CHICKEN_CUTLET, EntityId.CHICKEN_LEG):
            return self._compare_key()[1:] == other._compare_key()[1:]
        return False

    # __lt__() can be left as-is, since WING_PLACEHOLDER comes right after
    # CHICKEN_CUTLET and CHICKEN_LEG, and this should only be used in the level
    # definition anyway.


@dataclass(eq=False)
class Burger(Entity):
    """Burger for Breakside Grill and Belly's."""

    id: EntityId = EntityId.BUN_BOTTOM

    def _compare_key(self) -> tuple[Any, ...]:
        # stack order matters for this entity
        return (*super()._compare_key()[:-1], self.stack)


@dataclass(eq=False)
class PizzaDough(Entity):
    """Pizza dough for Chaz Cheddar."""

    id: EntityId = EntityId.DOUGH
    # TODO: rotate by swapping left_toppings and right_toppings
    left_toppings: set[ToppingId] = field(default_factory=set)
    right_toppings: set[ToppingId] = field(default_factory=set)

    def _compare_key(self) -> tuple[Any, ...]:
        return (
            *super()._compare_key(),
            self.left_toppings,
            self.right_toppings,
        )


@dataclass(eq=False)
class Nori(Entity):
    """Nori sheet for Sushi Yeah!"""

    id: EntityId = EntityId.NORI
    left_stack: list[Entity] = field(default_factory=list)
    right_stack: list[Entity] = field(default_factory=list)

    def check(self) -> None:
        assert not self.stack

    def _compare_key(self) -> tuple[Any, ...]:
        return (
            *super()._compare_key()[:-1],
            self.left_stack,
            self.right_stack,
        )


@dataclass
class State:
    modules: list[Module]
    entities: list[Entity]
    order_signals: tuple[bool, ...]

    @classmethod
    def from_solution(cls, level: Level, solution: Solution, order_index: int) -> State:
        assert solution.level_id == level.id
        order_signals = list(level.orders.keys())[order_index]
        return cls(deepcopy(solution.modules), [], order_signals)

    def add_entity(self, entity: Entity) -> None:
        self.entities.append(entity)
