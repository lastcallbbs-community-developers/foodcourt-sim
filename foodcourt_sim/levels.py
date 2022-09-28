import itertools
from collections import Counter
from dataclasses import InitVar, dataclass, field

from .entities import (
    ChaatDough,
    Cup,
    Entity,
    Multitray,
    PaintableCup,
    PizzaDough,
    SushiBowl,
    SushiPlate,
    WingPlaceholder,
)
from .enums import EntityId, LevelId, ModuleId, PaintColor, ToppingId
from .operations import (
    CoatFluid,
    CookFryer,
    CookGrill,
    CookMicrowave,
    DispenseFluid,
    DispenseFluidMixed,
    DispenseTopping,
    Dock,
    Flatten,
)

__all__ = ["Level", "LEVELS", "BY_ID", "BY_NUMBER"]


@dataclass
class Level:
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
    # how many entities can be stacked on one tray
    tray_capacity: int
    orders: InitVar[dict[tuple[bool, ...], Entity]]
    # order signals for each order
    order_signals: list[tuple[bool, ...]] = field(init=False)
    # final products for each order
    order_products: list[Entity] = field(init=False)

    def __post_init__(self, orders):
        self.order_signals = list(orders.keys())
        self.order_products = [orders[sig] for sig in self.order_signals]

    @property
    def internal_name(self) -> str:
        # prefix for save file name
        return self.name.lower().replace(" ", "-").replace("'", "")


E = EntityId
T = ToppingId


def tray(component: Entity) -> Entity:
    return Entity(E.TRAY, stack=component)


def multitray(*components: Entity) -> Entity:
    return Multitray(multistack=list(components))


def ith_true(i: int, n: int) -> tuple[bool, ...]:
    "Return a tuple of length n where the i-th element is True and the rest are False."
    l = [False] * n
    l[i] = True
    return tuple(l)


def chaat_helper(dock: bool) -> Entity:
    ops = []
    if dock:
        ops.append(Dock())
    ops.extend([CookFryer()] * 2)
    return ChaatDough(operations=ops, sauces={T.TOMATO, T.MINT, T.YOGURT})


def meat_3_helper(mac: bool, slaw: bool, greens: bool, beans: bool) -> Entity:
    dishes = [Entity(E.MEAT, [CookGrill()] * 4)]
    if mac:
        dishes.append(Entity(E.BOWL, [DispenseFluid(T.MAC)]))
    if slaw:
        dishes.append(Entity(E.BOWL, [DispenseFluid(T.SLAW)]))
    if greens:
        dishes.append(Entity(E.BOWL, [DispenseFluid(T.GREENS)]))
    if beans:
        dishes.append(Entity(E.BOWL, [DispenseFluid(T.BEANS)]))
    return multitray(*dishes)


def build_burger(middle: list[Entity]) -> Entity:
    """Build a burger by recursively stacking its components."""
    assert len(set(map(id, middle))) == len(
        middle
    ), "same entity repeated multiple times in build_burger()"

    bottom = Entity(E.BUN_BOTTOM)
    top = bottom
    for entity in middle:
        assert not entity.stack, "burger parts should not be pre-stacked"
        top.stack = entity
        top = entity

    top.stack = Entity(E.BUN_TOP)
    return bottom


def breakside_helper(count: int, cheese: bool, pickle: bool, tomato: bool) -> Entity:
    parts = []
    for _ in range(count):
        parts.append(Entity(E.MEAT, [CookGrill()] * 4))
        if cheese:
            parts.append(Entity(E.CHEESE))

    if pickle:
        parts.append(Entity(E.PICKLE))
    if tomato:
        parts.append(Entity(E.TOMATO))
    return tray(build_burger(parts))


def chaz_cheddar_helper(
    meat_l: bool, meat_r: bool, veggie_l: bool, veggie_r: bool
) -> Entity:
    dough = PizzaDough(
        operations=[Flatten()] * 2,
        left_toppings={T.SAUCE, T.CHEESE},
        right_toppings={T.SAUCE, T.CHEESE},
    )
    if meat_l:
        dough.left_toppings.add(T.MEAT)
    if meat_r:
        dough.right_toppings.add(T.MEAT)
    if veggie_l:
        dough.left_toppings.add(T.VEGGIE)
    if veggie_r:
        dough.right_toppings.add(T.VEGGIE)
    return tray(dough)


def nook_helper(order_id: int) -> Entity:
    cook_times = {
        E.EGG: 2 if order_id == 0 else 4,
        E.BACON: 4,
        E.BANGER: 4,
        E.TOMATO: 2,
        E.FUNGUS: 2,
        E.BLACK: 2,
        E.BREAD: 1,
    }
    return Multitray(
        operations=[DispenseFluid(T.BEANS)],
        multistack=[
            Entity(id, [CookGrill()] * time) for id, time in cook_times.items()
        ],
    )


def bellys_helper(cheese: bool, side_id: EntityId, drink: ToppingId) -> Entity:
    parts = [Entity(E.MEAT, [CookFryer()] * 4)]
    if cheese:
        parts.append(Entity(E.CHEESE))
    burger = build_burger(parts)
    cup = Cup(stack=Entity(E.LID), contents=Counter({drink: 2}))
    side = Cup(stack=Entity(side_id, [CookFryer()] * 4))
    return multitray(burger, cup, side)


def nigiri(fish: EntityId) -> Entity:
    return Entity(E.RICE, stack=Entity(fish))


LEVELS = [
    Level(
        id=LevelId.TWO_TWELVE,
        name="2Twelve",
        number=1,
        order_signal_names=["NACHO", "PRETZEL"],
        entity_inputs=[[E.NACHO], [E.PRETZEL]],
        topping_inputs=[[T.CHEESE]],
        tray_capacity=1,
        orders={
            (True, False): tray(Entity(E.NACHO, [DispenseFluid(T.CHEESE)])),
            (False, True): tray(Entity(E.PRETZEL)),
        },
    ),
    Level(
        id=LevelId.HOT_POCKET,
        name="Original Hot Pocket Experience",
        number=2,
        order_signal_names=["POCKET"],
        entity_inputs=[[E.POCKET]],
        topping_inputs=[],
        tray_capacity=1,
        orders={
            (True,): tray(Entity(E.POCKET, [CookMicrowave()] * 4)),
        },
    ),
    Level(
        id=LevelId.WINE_OCLOCK,
        name="Wine O'Clock",
        number=3,
        order_signal_names=["RED", "WHITE"],
        entity_inputs=[[E.GLASS]],
        topping_inputs=[[T.RED, T.WHITE]],
        tray_capacity=1,
        orders={
            (True, False): tray(Entity(E.GLASS, [DispenseFluid(T.RED)] * 2)),
            (False, True): tray(Entity(E.GLASS, [DispenseFluid(T.WHITE)] * 2)),
        },
    ),
    Level(
        id=LevelId.MUMBAI_CHAAT,
        name="Mumbai Chaat",
        number=4,
        order_signal_names=["POORI", "PAPDI"],
        entity_inputs=[[E.DOUGH]],
        topping_inputs=[[T.TOMATO, T.MINT, T.YOGURT]],
        tray_capacity=1,
        orders={
            ith_true(i, 2): tray(chaat_helper(dock))
            for i, dock in enumerate([False, True])
        },
    ),
    Level(
        id=LevelId.MR_CHILLY,
        name="Mr. Chilly",
        number=5,
        order_signal_names=["CHOCO", "VANILLA", "TWIST", "SMALL", "MEDIUM", "LARGE"],
        entity_inputs=[[E.CONE]],
        topping_inputs=[[T.CHOCO, T.VANILLA]],
        tray_capacity=1,
        orders={
            (*ith_true(i, 3), *ith_true(j, 3)): tray(Entity(E.CONE, [op] * count))
            for i, op in enumerate(
                [
                    DispenseFluid(T.CHOCO),
                    DispenseFluid(T.VANILLA),
                    DispenseFluidMixed(T.CHOCO, T.VANILLA),
                ]
            )
            for j, count in enumerate([2, 3, 4])
        },
    ),
    Level(
        id=LevelId.KAZAN,
        name="KAZAN",
        number=6,
        order_signal_names=[
            "1 PC.",
            "3 PCS.",
            "6 PCS.",
            "10 PCS.",
            "15 PCS.",
            "21 PCS.",
        ],
        entity_inputs=[[E.PELMENI]],
        topping_inputs=[],
        tray_capacity=21,
        orders={
            ith_true(i, 6): multitray(*[Entity(E.PELMENI)] * count)
            for i, count in enumerate([1, 3, 6, 10, 15, 21])
        },
    ),
    Level(
        id=LevelId.SODA_TRENCH,
        name="Soda Trench",
        number=7,
        order_signal_names=["COKE", "DIET C.", "PEPSI", "DIET P."],
        entity_inputs=[[E.CUP, E.LID]],
        topping_inputs=[[T.COLA]],
        tray_capacity=1,
        orders={
            ith_true(i, 4): tray(
                PaintableCup(
                    stack=Entity(E.LID),
                    contents=Counter({T.COLA: 2}),
                    colors=[color_1, PaintColor.WHITE, color_2],
                )
            )
            for i, (color_2, color_1) in enumerate(
                itertools.product(
                    [PaintColor.RED, PaintColor.BLUE],
                    [PaintColor.RED, PaintColor.WHITE],
                )
            )
        },
    ),
    Level(
        id=LevelId.ROSIES_DOUGHNUTS,
        name="Rosie's Doughnuts",
        number=8,
        order_signal_names=["ONE", "SIX", "DOZEN", "PLAIN", "CHOCO", "BERRY"],
        entity_inputs=[[E.DOUGH]],
        topping_inputs=[[T.CHOCO], [T.BERRY], [T.CANDY]],
        tray_capacity=12,
        orders={
            (*ith_true(j, 3), *ith_true(i, 3)): multitray(
                *[Entity(E.DOUGH, [*[CookFryer()] * 2, *ops])] * count
            )
            for i, ops in enumerate(
                [
                    [],
                    [CoatFluid(T.CHOCO), DispenseTopping(T.CANDY)],
                    [CoatFluid(T.BERRY), DispenseTopping(T.CANDY)],
                ]
            )
            for j, count in enumerate([1, 6, 12])
        },
    ),
    Level(
        id=LevelId.ON_THE_FRIED_SIDE,
        name="On the Fried Side",
        number=9,
        order_signal_names=["WHOLE", "HALF", "CUTLET", "LEG"],
        entity_inputs=[[E.CHICKEN]],
        topping_inputs=[[T.BREADING]],
        tray_capacity=1,
        orders={
            ith_true(i, 4): tray(
                Entity(id, [CoatFluid(T.BREADING), *[CookFryer()] * cook_time])
            )
            for i, (id, cook_time) in enumerate(
                {
                    E.CHICKEN: 8,
                    E.CHICKEN_HALF: 8,
                    E.CHICKEN_CUTLET: 4,
                    E.CHICKEN_LEG: 4,
                }.items()
            )
        },
    ),
    Level(
        id=LevelId.SWEET_HEAT_BBQ,
        name="Sweet Heat BBQ",
        number=10,
        order_signal_names=["ROAST", "RIBS", "200G", "400G", "600G"],
        entity_inputs=[[E.ROAST, E.RIBS]],
        topping_inputs=[],
        tray_capacity=6,
        orders={
            (*ith_true(i, 2), *ith_true(j, 3)): multitray(
                *[Entity(id)] * (count if id is E.RIBS_SLICE else 2 * count)
            )
            for i, id in enumerate([E.ROAST_SLICE, E.RIBS_SLICE])
            for j, count in enumerate(range(1, 4))
        },
    ),
    Level(
        id=LevelId.THE_WALRUS,
        name="The Walrus",
        number=11,
        order_signal_names=["WHISKY", "W. SOUR", "HIGHBALL", "COLA"],
        entity_inputs=[[E.ICE], [E.CUP]],
        topping_inputs=[[T.VODKA, T.WHISKY], [T.COLA, T.LEMON]],
        tray_capacity=1,
        orders={
            ith_true(0, 4): tray(Cup(contents=Counter({T.WHISKY: 1}))),
            ith_true(1, 4): tray(
                Cup(contents=Counter({T.WHISKY: 2, T.LEMON: 1}), stack=Entity(E.ICE))
            ),
            ith_true(2, 4): tray(
                Cup(
                    contents=Counter({T.WHISKY: 2, T.LEMON: 1, T.COLA: 2}),
                    stack=Entity(E.ICE),
                )
            ),
            ith_true(3, 4): tray(
                Cup(contents=Counter({T.COLA: 5}), stack=Entity(E.ICE))
            ),
        },
    ),
    Level(
        id=LevelId.MEAT_3,
        name="Meat+3",
        number=12,
        order_signal_names=["MAC", "SLAW", "GREENS", "BEANS"],
        entity_inputs=[[E.MEAT], [E.BOWL]],
        topping_inputs=[[T.MAC], [T.SLAW], [T.GREENS], [T.BEANS]],
        tray_capacity=4,
        orders={
            key: meat_3_helper(*key)
            for key in [
                (True, True, True, False),
                (True, True, False, True),
                (True, False, True, True),
                (False, True, True, True),
            ]
        },
    ),
    Level(
        id=LevelId.CAFE_TRISTE,
        name="Cafe Triste",
        number=13,
        order_signal_names=["DU JOUR"],
        entity_inputs=[[E.PAPER], [E.CUP]],
        topping_inputs=[[T.LEAVES]],
        tray_capacity=9,
        orders={
            (True,): multitray(
                Cup(contents=Counter({T.COFFEE: 1})), *[Entity(E.CIGARETTE)] * 8
            )
        },
    ),
    Level(
        id=LevelId.THE_COMMISSARY,
        name="The Commissary",
        number=14,
        order_signal_names=["MON.", "TUES.", "WED.", "THUR.", "FRI."],
        entity_inputs=[
            [E.PIZZA, E.BURGER, E.TENDER, E.CORNDOG, E.CURLY, E.CRINKLE, E.TOT],
            [E.PLAIN, E.CHOCO],
        ],
        topping_inputs=[],
        tray_capacity=3,
        orders={
            ith_true(0, 5): multitray(
                Entity(E.TENDER, [CookFryer()] * 4),
                Entity(E.CRINKLE, [CookFryer()] * 4),
                Entity(E.CHOCO),
            ),
            ith_true(1, 5): multitray(
                Entity(E.BURGER, [CookMicrowave()] * 4),
                Entity(E.TOT, [CookFryer()] * 4),
                Entity(E.PLAIN),
            ),
            ith_true(2, 5): multitray(
                Entity(E.CORNDOG, [CookFryer()] * 4),
                Entity(E.TOT, [CookFryer()] * 4),
                Entity(E.CHOCO),
            ),
            ith_true(3, 5): multitray(
                Entity(E.TENDER, [CookFryer()] * 4),
                Entity(E.CURLY, [CookFryer()] * 4),
                Entity(E.PLAIN),
            ),
            ith_true(4, 5): multitray(
                Entity(E.PIZZA, [CookMicrowave()] * 4),
                Entity(E.CRINKLE, [CookFryer()] * 4),
                Entity(E.CHOCO),
            ),
        },
    ),
    Level(
        id=LevelId.DA_WINGS,
        name="Da Wings",
        number=15,
        order_signal_names=["3 PCS.", "6 PCS.", "9 PCS."],
        entity_inputs=[[E.CHICKEN]],
        topping_inputs=[[T.SAUCE]],
        tray_capacity=9,
        orders={
            ith_true(i, 3): multitray(
                *[
                    WingPlaceholder(
                        operations=[*[CookFryer()] * 2, CoatFluid(T.SAUCE)],
                    )
                ]
                * count
            )
            for i, count in enumerate([3, 6, 9])
        },
    ),
    Level(
        id=LevelId.BREAKSIDE_GRILL,
        name="Breakside Grill",
        number=16,
        order_signal_names=["SINGLE", "DOUBLE", "TRIPLE", "CHEESE", "PICKLE", "TOMATO"],
        entity_inputs=[[E.MEAT], [E.BUN], [E.CHEESE, E.PICKLE, E.TOMATO]],
        topping_inputs=[],
        tray_capacity=1,
        orders={
            (*ith_true(count - 1, 3), *options): breakside_helper(count, *options)
            for count in range(1, 4)
            for options in itertools.product([False, True], repeat=3)
        },
    ),
    Level(
        id=LevelId.CHAZ_CHEDDAR,
        name="Chaz Cheddar",
        number=17,
        order_signal_names=["MEAT L.", "MEAT R.", "VEGGIE L.", "VEGGIE R."],
        entity_inputs=[[E.DOUGH]],
        topping_inputs=[[T.SAUCE], [T.CHEESE], [T.MEAT], [T.VEGGIE]],
        tray_capacity=1,
        orders={
            key: chaz_cheddar_helper(*key)
            for meat_l, veggie_l, meat_r, veggie_r in itertools.product(
                [False, True], repeat=4
            )
            for key in [(meat_l, meat_r, veggie_l, veggie_r)]
        },
    ),
    Level(
        id=LevelId.HALF_CAFF_COFFEE,
        name="Half Caff Coffee",
        number=18,
        order_signal_names=["ESPRE.", "DOPPIO", "LATTE", "CAPP.", "AMER."],
        entity_inputs=[[E.CUP]],
        topping_inputs=[[T.MILK], [T.WATER]],
        tray_capacity=1,
        orders={
            ith_true(0, 5): tray(Cup(contents=Counter({T.COFFEE: 1}))),
            ith_true(1, 5): tray(Cup(contents=Counter({T.COFFEE: 2}))),
            ith_true(2, 5): tray(
                Cup(contents=Counter({T.COFFEE: 1, T.MILK: 2, T.FOAM: 1}))
            ),
            ith_true(3, 5): tray(
                Cup(contents=Counter({T.COFFEE: 1, T.MILK: 1, T.FOAM: 2}))
            ),
            ith_true(4, 5): tray(Cup(contents=Counter({T.COFFEE: 1, T.WATER: 3}))),
        },
    ),
    Level(
        id=LevelId.MILDREDS_NOOK,
        name="Mildred's Nook",
        number=19,
        order_signal_names=["SOFT", "HARD"],
        entity_inputs=[
            [E.EGG],
            [E.BACON, E.BANGER],
            [E.TOMATO, E.FUNGUS, E.BLACK],
            [E.BREAD],
        ],
        topping_inputs=[[T.BEANS]],
        tray_capacity=7,
        orders={ith_true(i, 2): nook_helper(i) for i in range(2)},
    ),
    Level(
        id=LevelId.BELLYS,
        name="Belly's",
        number=20,
        order_signal_names=["PLAIN", "CHEESE", "ORANGE", "PURPLE", "POTATO", "ONION"],
        entity_inputs=[
            [E.MEAT, E.POTATO, E.ONION],
            [E.BUN, E.CHEESE],
            [E.CUP, E.LID],
        ],
        topping_inputs=[[T.ORANGE, T.PURPLE]],
        tray_capacity=3,
        orders={
            (*ith_true(i, 2), *ith_true(k, 2), *ith_true(j, 2)): bellys_helper(
                cheese=cheese, side_id=side_id, drink=drink
            )
            for i, cheese in enumerate([False, True])
            for j, side_id in enumerate([E.POTATO, E.ONION])
            for k, drink in enumerate([T.ORANGE, T.PURPLE])
        },
    ),
    Level(
        id=LevelId.SUSHI_YEAH,
        name="Sushi Yeah!",
        number=21,
        order_signal_names=[
            "T. MAKI",
            "S. MAKI",
            "T. NIGIRI",
            "S. NIGIRI",
            "SASHIMI",
            "SOUP",
        ],
        entity_inputs=[[E.NORI, E.RICE], [E.TUNA, E.SALMON], [E.PLATE, E.BOWL]],
        topping_inputs=[[T.SOUP]],
        tray_capacity=1,
        orders={
            ith_true(0, 6): tray(SushiPlate(multistack=[Entity(E.TUNA_MAKI)] * 4)),
            ith_true(1, 6): tray(SushiPlate(multistack=[Entity(E.SALMON_MAKI)] * 4)),
            ith_true(2, 6): tray(SushiPlate(multistack=[nigiri(E.TUNA)] * 2)),
            ith_true(3, 6): tray(SushiPlate(multistack=[nigiri(E.SALMON)] * 2)),
            ith_true(4, 6): tray(
                SushiBowl(multistack=[nigiri(E.TUNA), nigiri(E.SALMON)])
            ),
            ith_true(5, 6): tray(SushiBowl(operations=[DispenseFluid(T.SOUP)])),
        },
    ),
]

BY_ID = {level.id: level for level in LEVELS}
BY_NUMBER = {level.number: level for level in LEVELS}


def _make_allowed_modules() -> tuple[
    dict[LevelId, dict[ModuleId, int]], dict[LevelId, set[ModuleId]]
]:
    M = ModuleId
    default_modules = {
        M.MULTIMIXER,
        M.MULTIMIXER_ENABLE,
        M.SEQUENCER,
        M.SMALL_COUNTER,
        M.BIG_COUNTER,
        M.SENSOR,
        M.ROUTER,
        M.SORTER,
        M.WASTE_BIN,
    }
    provided = {
        LevelId.TWO_TWELVE: {M.INPUT_1X: 2, M.FLUID_DISPENSER_1X: 1},
        LevelId.HOT_POCKET: {M.FREEZER_1X: 1},
        LevelId.WINE_OCLOCK: {M.INPUT_1X: 1, M.FLUID_DISPENSER_2X: 1},
        LevelId.MUMBAI_CHAAT: {M.INPUT_1X: 1, M.FLUID_DISPENSER_3X: 1},
        LevelId.MR_CHILLY: {M.INPUT_1X: 1, M.FLUID_DISPENSER_2X: 1},
        LevelId.KAZAN: {M.INPUT_1X: 1},
        LevelId.SODA_TRENCH: {M.INPUT_2X: 1, M.FLUID_DISPENSER_1X: 1},
        LevelId.ROSIES_DOUGHNUTS: {
            M.INPUT_1X: 1,
            M.FLUID_COATER: 2,
            M.TOPPING_DISPENSER: 1,
        },
        LevelId.ON_THE_FRIED_SIDE: {M.INPUT_1X: 1, M.FLUID_COATER: 1},
        LevelId.SWEET_HEAT_BBQ: {M.INPUT_2X: 1},
        LevelId.THE_WALRUS: {M.INPUT_1X: 1, M.FREEZER_1X: 1, M.FLUID_DISPENSER_2X: 2},
        LevelId.MEAT_3: {M.INPUT_1X: 1, M.FREEZER_1X: 1, M.FLUID_DISPENSER_1X: 4},
        LevelId.CAFE_TRISTE: {M.INPUT_1X: 2, M.TOPPING_DISPENSER: 1},
        LevelId.THE_COMMISSARY: {M.INPUT_2X: 1, M.FREEZER_7X: 1},
        LevelId.DA_WINGS: {M.INPUT_1X: 1, M.FLUID_COATER: 1},
        LevelId.BREAKSIDE_GRILL: {M.INPUT_1X: 2, M.INPUT_3X: 1},
        LevelId.CHAZ_CHEDDAR: {M.INPUT_1X: 1, M.HALF_TOPPING_DISPENSER: 4},
        LevelId.HALF_CAFF_COFFEE: {M.INPUT_1X: 1, M.FLUID_DISPENSER_1X: 2},
        LevelId.MILDREDS_NOOK: {
            M.INPUT_1X: 2,
            M.INPUT_2X: 1,
            M.INPUT_3X: 1,
            M.FLUID_DISPENSER_1X: 1,
        },
        LevelId.BELLYS: {M.INPUT_2X: 2, M.FREEZER_3X: 1, M.FLUID_DISPENSER_2X: 1},
        LevelId.SUSHI_YEAH: {M.INPUT_2X: 3, M.FLUID_DISPENSER_1X: 1},
    }
    buyable: dict[LevelId, set[ModuleId]] = {
        LevelId.TWO_TWELVE: set(),
        LevelId.HOT_POCKET: {M.MICROWAVE, M.SMALL_COUNTER},
        LevelId.WINE_OCLOCK: {
            M.MULTIMIXER,
            M.MULTIMIXER_ENABLE,
            M.SMALL_COUNTER,
            M.SORTER,
        },
        LevelId.MUMBAI_CHAAT: {M.DOCKER, M.FRYER} | (default_modules - {M.BIG_COUNTER}),
        LevelId.MR_CHILLY: set(default_modules),
        LevelId.KAZAN: set(default_modules),
        LevelId.SODA_TRENCH: {M.PAINTER} | default_modules,
        LevelId.ROSIES_DOUGHNUTS: {M.FRYER} | default_modules,
        LevelId.ON_THE_FRIED_SIDE: {M.TRIPLE_SLICER, M.FRYER} | default_modules,
        LevelId.SWEET_HEAT_BBQ: {M.DOUBLE_SLICER} | default_modules,
        LevelId.THE_WALRUS: set(default_modules),
        LevelId.MEAT_3: {M.GRILL} | default_modules,
        LevelId.CAFE_TRISTE: {M.ROLLER, M.DOUBLE_SLICER, M.ESPRESSO} | default_modules,
        LevelId.THE_COMMISSARY: {M.MICROWAVE, M.FRYER} | default_modules,
        LevelId.DA_WINGS: {M.TRIPLE_SLICER, M.FRYER} | default_modules,
        LevelId.BREAKSIDE_GRILL: {M.HORIZONTAL_SLICER, M.GRILL} | default_modules,
        LevelId.CHAZ_CHEDDAR: {M.FLATTENER, M.ROTATOR, M.ANIMATRONIC} | default_modules,
        LevelId.HALF_CAFF_COFFEE: {M.ESPRESSO} | default_modules,
        LevelId.MILDREDS_NOOK: {M.GRILL} | default_modules,
        LevelId.BELLYS: {M.HORIZONTAL_SLICER, M.FRYER} | default_modules,
        LevelId.SUSHI_YEAH: {M.ROLLER, M.DOUBLE_SLICER} | default_modules,
    }
    for level_id in LevelId:
        # these modules are always provided
        provided[level_id][M.OUTPUT] = 1
        provided[level_id][ModuleId(M.MAIN_INPUT_BASE.value + level_id.value)] = 1
        # these modules are always allowed
        buyable[level_id] |= {
            M.CONVEYOR,
            M.STACKER,
            ModuleId(M.SCANNER_BASE.value + level_id.value),
        }

    buyable[LevelId.CAFE_TRISTE].remove(M.WASTE_BIN)
    buyable[LevelId.CHAZ_CHEDDAR].remove(M.WASTE_BIN)

    return provided, buyable


PROVIDED_MODULES, BUYABLE_MODULES = _make_allowed_modules()
