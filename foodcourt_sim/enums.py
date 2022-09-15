from __future__ import annotations

from enum import Enum, auto, unique

__all__ = [
    "LevelId",
    "ModuleId",
    "MusicMode",
    "PaintColor",
    "PaintMask",
    "JackDirection",
    "OperationId",
    "EntityId",
    "ToppingId",
]


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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


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
    FLUID_COATER = 28  # rosie's doughnuts, on the fried side, da wings
    OUTPUT = 29
    SENSOR = 30
    ROUTER = 31
    SORTER = 32
    STACKER = 33
    WASTE_BIN = 34  # limit 2 for sweet heat bbq, 3 for da wings
    DOUBLE_SLICER = 35  # sweet heat bbq, cafe triste, sushi yeah!
    TRIPLE_SLICER = 36  # on the fried side, da wings
    ROTATOR = 37  # chaz cheddar
    ESPRESSO = 38  # cafe triste, half caff coffee
    ROLLER = 40  # cafe triste
    DOCKER = 41  # mumbai chaat
    FLATTENER = 42  # chaz cheddar
    PAINTER = 43  # soda trench
    MICROWAVE = 45  # hot pocket, the commissary
    GRILL = 46  # meat+3, breakside grill, mildred's nook
    FRYER = 47  # mumbai chaat, rosie's doughnuts, on the fried side, the commissary, da wings, belly's
    HALF_TOPPING_DISPENSER = 48  # chaz cheddar
    FREEZER_1X = 49
    FREEZER_7X = 51
    ANIMATRONIC = 52
    TOPPING_DISPENSER = 53  # candy sprinkler for doughnuts
    HORIZONTAL_SLICER = 54  # breakside grill, belly's
    FREEZER_3X = 55

    MAIN_INPUT_BASE = 199
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

    SCANNER_BASE = 149
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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


@unique
class MusicMode(Enum):
    """Selected music mode for the Animatronic module in Chaz Cheddar."""

    LEAD = 0
    BASS = 1

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


@unique
class PaintColor(Enum):
    """Selected color for the Painter module in Soda Trench."""

    RED = 0
    WHITE = 1
    BLUE = 2

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


@unique
class PaintMask(Enum):
    """Selected mask for the Painter module in Soda Trench."""

    UPPER_2 = 0
    UPPER_1 = 1
    LOWER_1 = 2
    LOWER_2 = 3

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


# simulation-only objects


@unique
class JackDirection(Enum):
    IN = auto()
    OUT = auto()

    def opposite(self) -> JackDirection:
        if self is JackDirection.IN:
            return JackDirection.OUT
        if self is JackDirection.OUT:
            return JackDirection.IN
        assert False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


@unique
class OperationId(OrderedEnum):
    COOK_FRYER = auto()
    COOK_MICROWAVE = auto()
    COOK_GRILL = auto()
    DOCK = auto()
    FLATTEN = auto()
    DISPENSE_FLUID = auto()
    DISPENSE_FLUID_MIXED = auto()
    COAT_FLUID = auto()
    DISPENSE_TOPPING = auto()


@unique
class EntityId(OrderedEnum):
    TRAY = auto()
    MULTITRAY = auto()

    NACHO = auto()  # 2twelve
    PRETZEL = auto()  # 2twelve

    POCKET = auto()  # hot pocket

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
    CIGARETTE_4X = auto()  # cafe triste
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
    TUNA_MAKI_4X = auto()  # sushi yeah!
    TUNA_MAKI_2X = auto()  # sushi yeah!
    TUNA_MAKI = auto()  # sushi yeah!
    SALMON_MAKI_4X = auto()  # sushi yeah!
    SALMON_MAKI_2X = auto()  # sushi yeah!
    SALMON_MAKI = auto()  # sushi yeah!


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
