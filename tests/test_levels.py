# pylint: disable=line-too-long
import itertools
from collections import Counter

from foodcourt_sim.entities import (
    ChaatDough,
    Cup,
    Entity,
    Multitray,
    PaintableCup,
    PizzaDough,
    SushiBowl,
    SushiPlate,
)
from foodcourt_sim.enums import EntityId, LevelId, ModuleId, PaintColor, ToppingId
from foodcourt_sim.levels import BUYABLE_MODULES, BY_ID, build_burger, multitray, tray
from foodcourt_sim.operations import (
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

E = EntityId
T = ToppingId


def test_2twelve():
    level = BY_ID[LevelId.TWO_TWELVE]
    orders = [Entity(E.TRAY), *level.order_products]

    # fmt: off
    assert tray(Entity(E.NACHO, [DispenseFluid(T.CHEESE)])) == orders[1]
    assert tray(Entity(E.NACHO)) != orders[1]
    assert tray(Entity(E.PRETZEL)) != orders[1]
    assert tray(Entity(E.PRETZEL)) == orders[2]
    # fmt: on


def test_hot_pocket():
    level = BY_ID[LevelId.HOT_POCKET]
    orders = [Entity(E.TRAY), *level.order_products]

    # fmt: off
    assert tray(Entity(E.POCKET, [CookMicrowave()]*4)) == orders[1]
    # fmt: on


def test_wine_oclock():
    level = BY_ID[LevelId.WINE_OCLOCK]
    orders = [Entity(E.TRAY), *level.order_products]

    # fmt: off
    assert tray(Entity(E.GLASS, [DispenseFluid(T.RED)]*2)) == orders[1]
    assert tray(Entity(E.GLASS, [DispenseFluid(T.WHITE)]*2)) == orders[2]
    # fmt: on


def test_mumbai_chaat():
    level = BY_ID[LevelId.MUMBAI_CHAAT]
    orders = [Entity(E.TRAY), *level.order_products]

    # fmt: off
    assert tray(ChaatDough(operations=[CookFryer()]*2, sauces={T.TOMATO, T.MINT, T.YOGURT})) == orders[1]
    assert tray(ChaatDough(operations=[Dock(), CookFryer(), CookFryer()], sauces={T.TOMATO, T.MINT, T.YOGURT})) == orders[2]
    # fmt: on


def test_mr_chilly():
    level = BY_ID[LevelId.MR_CHILLY]
    orders = [Entity(E.TRAY), *level.order_products]

    # fmt: off
    assert tray(Entity(E.CONE, [DispenseFluid(T.CHOCO)]*2)) == orders[1]
    assert tray(Entity(E.CONE, [DispenseFluid(T.CHOCO)]*3)) == orders[2]
    assert tray(Entity(E.CONE, [DispenseFluid(T.CHOCO)]*4)) == orders[3]
    assert tray(Entity(E.CONE, [DispenseFluid(T.VANILLA)]*2)) == orders[4]
    assert tray(Entity(E.CONE, [DispenseFluid(T.VANILLA)]*3)) == orders[5]
    assert tray(Entity(E.CONE, [DispenseFluid(T.VANILLA)]*4)) == orders[6]
    assert tray(Entity(E.CONE, [DispenseFluidMixed(T.CHOCO, T.VANILLA)]*2)) == orders[7]
    assert tray(Entity(E.CONE, [DispenseFluidMixed(T.CHOCO, T.VANILLA)]*3)) == orders[8]
    assert tray(Entity(E.CONE, [DispenseFluidMixed(T.CHOCO, T.VANILLA)]*4)) == orders[9]
    assert tray(Entity(E.CONE, [DispenseFluidMixed(T.VANILLA, T.CHOCO)]*2)) == orders[7]
    assert tray(Entity(E.CONE, [DispenseFluidMixed(T.VANILLA, T.CHOCO)]*3)) == orders[8]
    assert tray(Entity(E.CONE, [DispenseFluidMixed(T.VANILLA, T.CHOCO)]*4)) == orders[9]
    # fmt: on


def test_kazan():
    level = BY_ID[LevelId.KAZAN]
    orders = [Multitray(), *level.order_products]

    # fmt: off
    assert multitray(*[Entity(E.PELMENI)]*1) == orders[1]
    assert multitray(*[Entity(E.PELMENI)]*3) == orders[2]
    assert multitray(*[Entity(E.PELMENI)]*6) == orders[3]
    assert multitray(*[Entity(E.PELMENI)]*10) == orders[4]
    assert multitray(*[Entity(E.PELMENI)]*15) == orders[5]
    assert multitray(*[Entity(E.PELMENI)]*21) == orders[6]
    # fmt: on


def test_soda_trench():
    level = BY_ID[LevelId.SODA_TRENCH]
    orders = [Entity(E.TRAY), *level.order_products]

    # fmt: off
    assert tray(PaintableCup(stack=Entity(E.LID), contents=Counter({T.COLA: 2}), colors=[PaintColor.RED,   PaintColor.WHITE, PaintColor.RED])) == orders[1]
    assert tray(PaintableCup(stack=Entity(E.LID), contents=Counter({T.COLA: 2}), colors=[PaintColor.WHITE, PaintColor.WHITE, PaintColor.RED])) == orders[2]
    assert tray(PaintableCup(stack=Entity(E.LID), contents=Counter({T.COLA: 2}), colors=[PaintColor.RED,   PaintColor.WHITE, PaintColor.BLUE])) == orders[3]
    assert tray(PaintableCup(stack=Entity(E.LID), contents=Counter({T.COLA: 2}), colors=[PaintColor.WHITE, PaintColor.WHITE, PaintColor.BLUE])) == orders[4]
    assert tray(Cup(stack=Entity(E.LID), contents=Counter({T.COLA: 2}))) != orders[1]
    assert tray(Cup(stack=Entity(E.LID), contents=Counter({T.COLA: 2}))) != orders[1]
    # fmt: on


def test_rosies_doughnuts():
    level = BY_ID[LevelId.ROSIES_DOUGHNUTS]
    orders = [Multitray(), *level.order_products]

    # fmt: off
    assert multitray(*[Entity(E.DOUGH, [*[CookFryer()]*2])]*1) == orders[1]
    assert multitray(*[Entity(E.DOUGH, [*[CookFryer()]*2])]*6) == orders[2]
    assert multitray(*[Entity(E.DOUGH, [*[CookFryer()]*2])]*12) == orders[3]
    assert multitray(*[Entity(E.DOUGH, [*[CookFryer()]*2, CoatFluid(T.CHOCO), DispenseTopping(T.CANDY)])]*1) == orders[4]
    assert multitray(*[Entity(E.DOUGH, [*[CookFryer()]*2, CoatFluid(T.CHOCO), DispenseTopping(T.CANDY)])]*6) == orders[5]
    assert multitray(*[Entity(E.DOUGH, [*[CookFryer()]*2, CoatFluid(T.CHOCO), DispenseTopping(T.CANDY)])]*12) == orders[6]
    assert multitray(*[Entity(E.DOUGH, [*[CookFryer()]*2, CoatFluid(T.BERRY), DispenseTopping(T.CANDY)])]*1) == orders[7]
    assert multitray(*[Entity(E.DOUGH, [*[CookFryer()]*2, CoatFluid(T.BERRY), DispenseTopping(T.CANDY)])]*6) == orders[8]
    assert multitray(*[Entity(E.DOUGH, [*[CookFryer()]*2, CoatFluid(T.BERRY), DispenseTopping(T.CANDY)])]*12) == orders[9]
    # fmt: on


def test_on_the_fried_side():
    level = BY_ID[LevelId.ON_THE_FRIED_SIDE]
    orders = [Entity(E.TRAY), *level.order_products]

    # fmt: off
    assert tray(Entity(E.CHICKEN,        [CoatFluid(T.BREADING), *[CookFryer()]*8])) == orders[1]
    assert tray(Entity(E.CHICKEN_HALF,   [CoatFluid(T.BREADING), *[CookFryer()]*8])) == orders[2]
    assert tray(Entity(E.CHICKEN_CUTLET, [CoatFluid(T.BREADING), *[CookFryer()]*4])) == orders[3]
    assert tray(Entity(E.CHICKEN_LEG,    [CoatFluid(T.BREADING), *[CookFryer()]*4])) == orders[4]
    # fmt: on


def test_sweet_heat_bbq():
    level = BY_ID[LevelId.SWEET_HEAT_BBQ]
    orders = [Multitray(), *level.order_products]

    # fmt: off
    assert multitray(*[Entity(E.ROAST_SLICE)]*2) == orders[1]
    assert multitray(*[Entity(E.ROAST_SLICE)]*4) == orders[2]
    assert multitray(*[Entity(E.ROAST_SLICE)]*6) == orders[3]
    assert multitray(*[Entity(E.RIBS_SLICE)]*1) == orders[4]
    assert multitray(*[Entity(E.RIBS_SLICE)]*2) == orders[5]
    assert multitray(*[Entity(E.RIBS_SLICE)]*3) == orders[6]
    # fmt: on


def test_the_walrus():
    level = BY_ID[LevelId.THE_WALRUS]
    orders = [Entity(E.TRAY), *level.order_products]

    # fmt: off
    assert tray(Cup(contents=Counter({T.WHISKY: 1}))) == orders[1]
    assert tray(Cup(stack=Entity(E.ICE), contents=Counter({T.WHISKY: 2, T.LEMON: 1}))) == orders[2]
    assert tray(Cup(stack=Entity(E.ICE), contents=Counter({T.WHISKY: 2, T.LEMON: 1, T.COLA: 2}))) == orders[3]
    assert tray(Cup(stack=Entity(E.ICE), contents=Counter({T.COLA: 5}))) == orders[4]
    # fmt: on


def test_meat_3():
    level = BY_ID[LevelId.MEAT_3]
    orders = [Multitray(), *level.order_products]

    # fmt: off
    assert multitray(
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.BOWL, [DispenseFluid(T.MAC)]),
        Entity(E.BOWL, [DispenseFluid(T.SLAW)]),
        Entity(E.BOWL, [DispenseFluid(T.GREENS)]),
        Entity(E.BOWL, [DispenseFluid(T.BEANS)]),
    ) != orders[1]
    assert multitray(
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.BOWL, [DispenseFluid(T.MAC)]),
        Entity(E.BOWL, [DispenseFluid(T.SLAW)]),
        Entity(E.BOWL, [DispenseFluid(T.GREENS)]),
    ) == orders[1]
    assert multitray(
        Entity(E.BOWL, [DispenseFluid(T.SLAW)]),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.BOWL, [DispenseFluid(T.GREENS)]),
        Entity(E.BOWL, [DispenseFluid(T.MAC)]),
    ) == orders[1]
    assert multitray(
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.BOWL, [DispenseFluid(T.MAC)]),
        Entity(E.BOWL, [DispenseFluid(T.SLAW)]),
        Entity(E.BOWL, [DispenseFluid(T.BEANS)]),
    ) == orders[2]
    assert multitray(
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.BOWL, [DispenseFluid(T.MAC)]),
        Entity(E.BOWL, [DispenseFluid(T.GREENS)]),
        Entity(E.BOWL, [DispenseFluid(T.BEANS)]),
    ) == orders[3]
    assert multitray(
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.BOWL, [DispenseFluid(T.SLAW)]),
        Entity(E.BOWL, [DispenseFluid(T.GREENS)]),
        Entity(E.BOWL, [DispenseFluid(T.BEANS)]),
    ) == orders[4]
    # fmt: on


def test_cafe_triste():
    level = BY_ID[LevelId.CAFE_TRISTE]
    orders = [Multitray(), *level.order_products]

    # fmt: off
    assert multitray(*[Entity(E.CIGARETTE)]*8, Cup(contents=Counter({T.COFFEE: 1}))) == orders[1]
    assert multitray(Cup(contents=Counter({T.COFFEE: 1})), *[Entity(E.CIGARETTE)]*8) == orders[1]
    assert multitray(*[Entity(E.CIGARETTE)]*3, Cup(contents=Counter({T.COFFEE: 1})), *[Entity(E.CIGARETTE)]*5) == orders[1]
    assert multitray(*[Entity(E.CIGARETTE)]*7, Cup(contents=Counter({T.COFFEE: 1}))) != orders[1]
    assert multitray(*[Entity(E.CIGARETTE)]*8, Cup(contents=Counter({T.COFFEE: 1, T.MILK: 1}))) != orders[1]
    # fmt: on


def test_the_commissary():
    level = BY_ID[LevelId.THE_COMMISSARY]
    orders = [Multitray(), *level.order_products]

    # fmt: off
    assert multitray(
        Entity(E.CRINKLE, [CookFryer()]*4),
        Entity(E.CHOCO),
        Entity(E.TENDER, [CookFryer()]*4),
    ) == orders[1]
    assert multitray(
        Entity(E.TOT, [CookFryer()]*4),
        Entity(E.PLAIN),
        Entity(E.BURGER, [CookMicrowave()]*4),
    ) == orders[2]
    assert multitray(
        Entity(E.TOT, [CookFryer()]*4),
        Entity(E.CHOCO),
        Entity(E.CORNDOG, [CookFryer()]*4),
    ) == orders[3]
    assert multitray(
        Entity(E.CURLY, [CookFryer()]*4),
        Entity(E.PLAIN),
        Entity(E.TENDER, [CookFryer()]*4),
    ) == orders[4]
    assert multitray(
        Entity(E.CRINKLE, [CookFryer()]*4),
        Entity(E.CHOCO),
        Entity(E.PIZZA, [CookMicrowave()]*4),
    ) == orders[5]
    # fmt: on


def test_da_wings():
    level = BY_ID[LevelId.DA_WINGS]
    orders = [Multitray(), *level.order_products]

    parts = [E.CHICKEN_CUTLET, E.CHICKEN_LEG]
    for ids in itertools.product(parts, repeat=3):
        # fmt: off
        assert multitray(*[Entity(id, [*[CookFryer()]*2, CoatFluid(T.SAUCE)]) for id in ids]) == orders[1]
        # fmt: on
    for ids in itertools.product(parts, repeat=6):
        # fmt: off
        assert multitray(*[Entity(id, [*[CookFryer()]*2, CoatFluid(T.SAUCE)]) for id in ids]) == orders[2]
        # fmt: on
    for ids in itertools.product(parts, repeat=9):
        # fmt: off
        assert multitray(*[Entity(id, [*[CookFryer()]*2, CoatFluid(T.SAUCE)]) for id in ids]) == orders[3]
        # fmt: on


def test_breakside():
    level = BY_ID[LevelId.BREAKSIDE_GRILL]
    orders = [Entity(E.TRAY), *level.order_products]

    # fmt: off
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
    ])) == orders[1]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.TOMATO),
    ])) == orders[2]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.PICKLE),
    ])) == orders[3]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.PICKLE),
        Entity(E.TOMATO),
    ])) == orders[4]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
    ])) == orders[5]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
        Entity(E.TOMATO),
    ])) == orders[6]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
        Entity(E.PICKLE),
    ])) == orders[7]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
        Entity(E.PICKLE),
        Entity(E.TOMATO),
    ])) == orders[8]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.MEAT, [CookGrill()]*4),
    ])) == orders[9]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.TOMATO),
    ])) == orders[10]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.PICKLE),
    ])) == orders[11]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.PICKLE),
        Entity(E.TOMATO),
    ])) == orders[12]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
    ])) == orders[13]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
        Entity(E.TOMATO),
    ])) == orders[14]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
        Entity(E.PICKLE),
    ])) == orders[15]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
        Entity(E.PICKLE),
        Entity(E.TOMATO),
    ])) == orders[16]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.MEAT, [CookGrill()]*4),
    ])) == orders[17]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.TOMATO),
    ])) == orders[18]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.PICKLE),
    ])) == orders[19]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.PICKLE),
        Entity(E.TOMATO),
    ])) == orders[20]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
    ])) == orders[21]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
        Entity(E.TOMATO),
    ])) == orders[22]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
        Entity(E.PICKLE),
    ])) == orders[23]
    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.CHEESE),
        Entity(E.PICKLE),
        Entity(E.TOMATO),
    ])) == orders[24]

    assert tray(build_burger([
        Entity(E.MEAT, [CookGrill()]*4),
        Entity(E.PICKLE),
        Entity(E.CHEESE),
    ])) != orders[7]
    # fmt: on


def test_chaz_cheddar():
    level = BY_ID[LevelId.CHAZ_CHEDDAR]
    orders = [Entity(E.TRAY), *level.order_products]

    plain = {T.SAUCE, T.CHEESE}
    veg = plain | {T.VEGGIE}
    meat = plain | {T.MEAT}
    # fmt: off
    assert tray(PizzaDough(operations=[Flatten()]*2, left_toppings=plain,    right_toppings=plain))    == orders[1]
    assert tray(PizzaDough(operations=[Flatten()]*2, left_toppings=plain,    right_toppings=veg))      == orders[2]
    assert tray(PizzaDough(operations=[Flatten()]*2, left_toppings=plain,    right_toppings=meat))     == orders[3]
    assert tray(PizzaDough(operations=[Flatten()]*2, left_toppings=plain,    right_toppings=veg|meat)) == orders[4]
    assert tray(PizzaDough(operations=[Flatten()]*2, left_toppings=veg,      right_toppings=plain))    == orders[5]
    assert tray(PizzaDough(operations=[Flatten()]*2, left_toppings=veg,      right_toppings=veg))      == orders[6]
    assert tray(PizzaDough(operations=[Flatten()]*2, left_toppings=veg,      right_toppings=meat))     == orders[7]
    assert tray(PizzaDough(operations=[Flatten()]*2, left_toppings=veg,      right_toppings=veg|meat)) == orders[8]
    assert tray(PizzaDough(operations=[Flatten()]*2, left_toppings=meat,     right_toppings=plain))    == orders[9]
    assert tray(PizzaDough(operations=[Flatten()]*2, left_toppings=meat,     right_toppings=veg))      == orders[10]
    assert tray(PizzaDough(operations=[Flatten()]*2, left_toppings=meat,     right_toppings=meat))     == orders[11]
    assert tray(PizzaDough(operations=[Flatten()]*2, left_toppings=meat,     right_toppings=veg|meat)) == orders[12]
    assert tray(PizzaDough(operations=[Flatten()]*2, left_toppings=veg|meat, right_toppings=plain))    == orders[13]
    assert tray(PizzaDough(operations=[Flatten()]*2, left_toppings=veg|meat, right_toppings=veg))      == orders[14]
    assert tray(PizzaDough(operations=[Flatten()]*2, left_toppings=veg|meat, right_toppings=meat))     == orders[15]
    assert tray(PizzaDough(operations=[Flatten()]*2, left_toppings=veg|meat, right_toppings=veg|meat)) == orders[16]

    assert tray(PizzaDough(operations=[Flatten()]*2, right_toppings=plain,    left_toppings=plain))    == orders[1]
    assert tray(PizzaDough(operations=[Flatten()]*2, right_toppings=plain,    left_toppings=veg))      == orders[2]
    assert tray(PizzaDough(operations=[Flatten()]*2, right_toppings=plain,    left_toppings=meat))     == orders[3]
    assert tray(PizzaDough(operations=[Flatten()]*2, right_toppings=plain,    left_toppings=veg|meat)) == orders[4]
    assert tray(PizzaDough(operations=[Flatten()]*2, right_toppings=veg,      left_toppings=plain))    == orders[5]
    assert tray(PizzaDough(operations=[Flatten()]*2, right_toppings=veg,      left_toppings=veg))      == orders[6]
    assert tray(PizzaDough(operations=[Flatten()]*2, right_toppings=veg,      left_toppings=meat))     == orders[7]
    assert tray(PizzaDough(operations=[Flatten()]*2, right_toppings=veg,      left_toppings=veg|meat)) == orders[8]
    assert tray(PizzaDough(operations=[Flatten()]*2, right_toppings=meat,     left_toppings=plain))    == orders[9]
    assert tray(PizzaDough(operations=[Flatten()]*2, right_toppings=meat,     left_toppings=veg))      == orders[10]
    assert tray(PizzaDough(operations=[Flatten()]*2, right_toppings=meat,     left_toppings=meat))     == orders[11]
    assert tray(PizzaDough(operations=[Flatten()]*2, right_toppings=meat,     left_toppings=veg|meat)) == orders[12]
    assert tray(PizzaDough(operations=[Flatten()]*2, right_toppings=veg|meat, left_toppings=plain))    == orders[13]
    assert tray(PizzaDough(operations=[Flatten()]*2, right_toppings=veg|meat, left_toppings=veg))      == orders[14]
    assert tray(PizzaDough(operations=[Flatten()]*2, right_toppings=veg|meat, left_toppings=meat))     == orders[15]
    assert tray(PizzaDough(operations=[Flatten()]*2, right_toppings=veg|meat, left_toppings=veg|meat)) == orders[16]
    # fmt: on


def test_half_caff_coffee():
    level = BY_ID[LevelId.HALF_CAFF_COFFEE]
    orders = [Entity(E.TRAY), *level.order_products]

    # fmt: off
    assert tray(Cup(contents=Counter({T.COFFEE: 1}))) == orders[1]
    assert tray(Cup(contents=Counter({T.COFFEE: 2}))) == orders[2]
    assert tray(Cup(contents=Counter({T.COFFEE: 1, T.MILK: 2, T.FOAM: 1}))) == orders[3]
    assert tray(Cup(contents=Counter({T.COFFEE: 1, T.MILK: 1, T.FOAM: 2}))) == orders[4]
    assert tray(Cup(contents=Counter({T.COFFEE: 1, T.WATER: 3}))) == orders[5]
    # fmt: on


def test_mildreds_nook():
    level = BY_ID[LevelId.MILDREDS_NOOK]
    orders = [Multitray(), *level.order_products]

    # fmt: off
    assert Multitray(
        operations=[DispenseFluid(T.BEANS)],
        multistack=[
            Entity(E.EGG,    [CookGrill()] * 2),
            Entity(E.BACON,  [CookGrill()] * 4),
            Entity(E.BANGER, [CookGrill()] * 4),
            Entity(E.TOMATO, [CookGrill()] * 2),
            Entity(E.FUNGUS, [CookGrill()] * 2),
            Entity(E.BLACK,  [CookGrill()] * 2),
            Entity(E.BREAD,  [CookGrill()] * 1),
        ],
    ) == orders[1]
    assert Multitray(
        operations=[DispenseFluid(T.BEANS)],
        multistack=[
            Entity(E.EGG,    [CookGrill()] * 4),
            Entity(E.BACON,  [CookGrill()] * 4),
            Entity(E.BANGER, [CookGrill()] * 4),
            Entity(E.TOMATO, [CookGrill()] * 2),
            Entity(E.FUNGUS, [CookGrill()] * 2),
            Entity(E.BLACK,  [CookGrill()] * 2),
            Entity(E.BREAD,  [CookGrill()] * 1),
        ],
    ) == orders[2]
    # fmt: on


def test_bellys():
    level = BY_ID[LevelId.BELLYS]
    orders = [Multitray(), *level.order_products]

    # fmt: off
    assert multitray(
        build_burger([Entity(E.MEAT, [CookFryer()]*4)]),
        Cup(stack=Entity(E.POTATO, [CookFryer()]*4)),
        Cup(stack=Entity(E.LID), contents=Counter({T.ORANGE: 2})),
    ) == orders[1]
    assert multitray(
        build_burger([Entity(E.MEAT, [CookFryer()]*4)]),
        Cup(stack=Entity(E.POTATO, [CookFryer()]*4)),
        Cup(stack=Entity(E.LID), contents=Counter({T.PURPLE: 2})),
    ) == orders[2]
    assert multitray(
        build_burger([Entity(E.MEAT, [CookFryer()]*4)]),
        Cup(stack=Entity(E.ONION, [CookFryer()]*4)),
        Cup(stack=Entity(E.LID), contents=Counter({T.ORANGE: 2})),
    ) == orders[3]
    assert multitray(
        build_burger([Entity(E.MEAT, [CookFryer()]*4)]),
        Cup(stack=Entity(E.ONION, [CookFryer()]*4)),
        Cup(stack=Entity(E.LID), contents=Counter({T.PURPLE: 2})),
    ) == orders[4]
    assert multitray(
        build_burger([Entity(E.MEAT, [CookFryer()]*4), Entity(E.CHEESE)]),
        Cup(stack=Entity(E.POTATO, [CookFryer()]*4)),
        Cup(stack=Entity(E.LID), contents=Counter({T.ORANGE: 2})),
    ) == orders[5]
    assert multitray(
        build_burger([Entity(E.MEAT, [CookFryer()]*4), Entity(E.CHEESE)]),
        Cup(stack=Entity(E.POTATO, [CookFryer()]*4)),
        Cup(stack=Entity(E.LID), contents=Counter({T.PURPLE: 2})),
    ) == orders[6]
    assert multitray(
        build_burger([Entity(E.MEAT, [CookFryer()]*4), Entity(E.CHEESE)]),
        Cup(stack=Entity(E.ONION, [CookFryer()]*4)),
        Cup(stack=Entity(E.LID), contents=Counter({T.ORANGE: 2})),
    ) == orders[7]
    assert multitray(
        build_burger([Entity(E.MEAT, [CookFryer()]*4), Entity(E.CHEESE)]),
        Cup(stack=Entity(E.ONION, [CookFryer()]*4)),
        Cup(stack=Entity(E.LID), contents=Counter({T.PURPLE: 2})),
    ) == orders[8]
    # fmt: on


def test_sushi_yeah():
    level = BY_ID[LevelId.SUSHI_YEAH]
    orders = [Entity(E.TRAY), *level.order_products]

    # fmt: off
    assert tray(SushiPlate(multistack=[Entity(E.TUNA_MAKI)]*4)) == orders[1]
    assert tray(SushiPlate(multistack=[Entity(E.SALMON_MAKI)]*4)) == orders[2]
    assert tray(SushiPlate(multistack=[Entity(E.RICE, stack=Entity(E.TUNA))]*2)) == orders[3]
    assert tray(SushiPlate(multistack=[Entity(E.RICE, stack=Entity(E.SALMON))]*2)) == orders[4]
    assert tray(SushiBowl(multistack=[Entity(E.RICE, stack=Entity(E.TUNA)), Entity(E.RICE, stack=Entity(E.SALMON))])) == orders[5]
    assert tray(SushiBowl(multistack=[Entity(E.RICE, stack=Entity(E.SALMON)), Entity(E.RICE, stack=Entity(E.TUNA))])) == orders[5]
    assert tray(SushiBowl(multistack=[Entity(E.RICE, stack=Entity(E.TUNA))]*2)) != orders[5]
    assert tray(SushiBowl(multistack=[Entity(E.RICE, stack=Entity(E.SALMON))]*2)) != orders[5]
    assert tray(SushiBowl(operations=[DispenseFluid(T.SOUP)])) == orders[6]
    # fmt: on


def test_buyable():
    buyable_ref = {
        LevelId.TWO_TWELVE: {
            ModuleId.STACKER,
            ModuleId.TWO_TWELVE_SCANNER,
            ModuleId.CONVEYOR,
        },
        LevelId.HOT_POCKET: {
            ModuleId.STACKER,
            ModuleId.CONVEYOR,
            ModuleId.HOT_POCKET_SCANNER,
            ModuleId.MICROWAVE,
            ModuleId.SMALL_COUNTER,
        },
        LevelId.WINE_OCLOCK: {
            ModuleId.STACKER,
            ModuleId.MULTIMIXER_ENABLE,
            ModuleId.WINE_SCANNER,
            ModuleId.MULTIMIXER,
            ModuleId.SORTER,
            ModuleId.CONVEYOR,
            ModuleId.SMALL_COUNTER,
        },
        LevelId.MUMBAI_CHAAT: {
            ModuleId.STACKER,
            ModuleId.FRYER,
            ModuleId.WASTE_BIN,
            ModuleId.ROUTER,
            ModuleId.SEQUENCER,
            ModuleId.SORTER,
            ModuleId.CONVEYOR,
            ModuleId.SENSOR,
            ModuleId.SMALL_COUNTER,
            ModuleId.MULTIMIXER_ENABLE,
            ModuleId.MULTIMIXER,
            ModuleId.MUMBAI_CHAAT_SCANNER,
            ModuleId.DOCKER,
        },
        LevelId.MR_CHILLY: {
            ModuleId.STACKER,
            ModuleId.WASTE_BIN,
            ModuleId.ROUTER,
            ModuleId.SEQUENCER,
            ModuleId.SORTER,
            ModuleId.CONVEYOR,
            ModuleId.SENSOR,
            ModuleId.SMALL_COUNTER,
            ModuleId.MULTIMIXER_ENABLE,
            ModuleId.MR_CHILLY_SCANNER,
            ModuleId.MULTIMIXER,
            ModuleId.BIG_COUNTER,
        },
        LevelId.KAZAN: {
            ModuleId.STACKER,
            ModuleId.KAZAN_SCANNER,
            ModuleId.WASTE_BIN,
            ModuleId.ROUTER,
            ModuleId.SEQUENCER,
            ModuleId.SORTER,
            ModuleId.CONVEYOR,
            ModuleId.SENSOR,
            ModuleId.SMALL_COUNTER,
            ModuleId.MULTIMIXER_ENABLE,
            ModuleId.MULTIMIXER,
            ModuleId.BIG_COUNTER,
        },
        LevelId.SODA_TRENCH: {
            ModuleId.STACKER,
            ModuleId.PAINTER,
            ModuleId.WASTE_BIN,
            ModuleId.ROUTER,
            ModuleId.SEQUENCER,
            ModuleId.SODA_TRENCH_SCANNER,
            ModuleId.SORTER,
            ModuleId.CONVEYOR,
            ModuleId.SENSOR,
            ModuleId.SMALL_COUNTER,
            ModuleId.MULTIMIXER_ENABLE,
            ModuleId.MULTIMIXER,
            ModuleId.BIG_COUNTER,
        },
        LevelId.ROSIES_DOUGHNUTS: {
            ModuleId.STACKER,
            ModuleId.FRYER,
            ModuleId.WASTE_BIN,
            ModuleId.ROUTER,
            ModuleId.SEQUENCER,
            ModuleId.SORTER,
            ModuleId.ROSIES_DOUGHNUTS_SCANNER,
            ModuleId.SENSOR,
            ModuleId.SMALL_COUNTER,
            ModuleId.CONVEYOR,
            ModuleId.MULTIMIXER_ENABLE,
            ModuleId.MULTIMIXER,
            ModuleId.BIG_COUNTER,
        },
        LevelId.ON_THE_FRIED_SIDE: {
            ModuleId.STACKER,
            ModuleId.FRYER,
            ModuleId.WASTE_BIN,
            ModuleId.TRIPLE_SLICER,
            ModuleId.ROUTER,
            ModuleId.SEQUENCER,
            ModuleId.SORTER,
            ModuleId.CONVEYOR,
            ModuleId.SENSOR,
            ModuleId.SMALL_COUNTER,
            ModuleId.MULTIMIXER_ENABLE,
            ModuleId.ON_THE_FRIED_SIDE_SCANNER,
            ModuleId.MULTIMIXER,
            ModuleId.BIG_COUNTER,
        },
        LevelId.SWEET_HEAT_BBQ: {
            ModuleId.STACKER,
            ModuleId.WASTE_BIN,
            ModuleId.ROUTER,
            ModuleId.SEQUENCER,
            ModuleId.SORTER,
            ModuleId.CONVEYOR,
            ModuleId.SENSOR,
            ModuleId.SMALL_COUNTER,
            ModuleId.MULTIMIXER_ENABLE,
            ModuleId.SWEET_HEAT_BBQ_SCANNER,
            ModuleId.MULTIMIXER,
            ModuleId.BIG_COUNTER,
            ModuleId.DOUBLE_SLICER,
        },
        LevelId.THE_WALRUS: {
            ModuleId.STACKER,
            ModuleId.WASTE_BIN,
            ModuleId.ROUTER,
            ModuleId.SEQUENCER,
            ModuleId.SORTER,
            ModuleId.CONVEYOR,
            ModuleId.SENSOR,
            ModuleId.SMALL_COUNTER,
            ModuleId.THE_WALRUS_SCANNER,
            ModuleId.MULTIMIXER_ENABLE,
            ModuleId.MULTIMIXER,
            ModuleId.BIG_COUNTER,
        },
        LevelId.MEAT_3: {
            ModuleId.STACKER,
            ModuleId.WASTE_BIN,
            ModuleId.ROUTER,
            ModuleId.SEQUENCER,
            ModuleId.SORTER,
            ModuleId.MEAT_3_SCANNER,
            ModuleId.SENSOR,
            ModuleId.SMALL_COUNTER,
            ModuleId.CONVEYOR,
            ModuleId.MULTIMIXER_ENABLE,
            ModuleId.MULTIMIXER,
            ModuleId.BIG_COUNTER,
            ModuleId.GRILL,
        },
        LevelId.CAFE_TRISTE: {
            ModuleId.STACKER,
            ModuleId.CAFE_TRISTE_SCANNER,
            ModuleId.ROUTER,
            ModuleId.SEQUENCER,
            ModuleId.SORTER,
            ModuleId.CONVEYOR,
            ModuleId.SENSOR,
            ModuleId.SMALL_COUNTER,
            ModuleId.ROLLER,
            ModuleId.MULTIMIXER_ENABLE,
            ModuleId.MULTIMIXER,
            ModuleId.BIG_COUNTER,
            ModuleId.DOUBLE_SLICER,
            ModuleId.ESPRESSO,
        },
        LevelId.THE_COMMISSARY: {
            ModuleId.STACKER,
            ModuleId.FRYER,
            ModuleId.WASTE_BIN,
            ModuleId.THE_COMMISSARY_SCANNER,
            ModuleId.ROUTER,
            ModuleId.SEQUENCER,
            ModuleId.SORTER,
            ModuleId.MICROWAVE,
            ModuleId.SENSOR,
            ModuleId.SMALL_COUNTER,
            ModuleId.CONVEYOR,
            ModuleId.MULTIMIXER_ENABLE,
            ModuleId.MULTIMIXER,
            ModuleId.BIG_COUNTER,
        },
        LevelId.DA_WINGS: {
            ModuleId.STACKER,
            ModuleId.DA_WINGS_SCANNER,
            ModuleId.FRYER,
            ModuleId.WASTE_BIN,
            ModuleId.TRIPLE_SLICER,
            ModuleId.ROUTER,
            ModuleId.SEQUENCER,
            ModuleId.SORTER,
            ModuleId.CONVEYOR,
            ModuleId.SENSOR,
            ModuleId.SMALL_COUNTER,
            ModuleId.MULTIMIXER_ENABLE,
            ModuleId.MULTIMIXER,
            ModuleId.BIG_COUNTER,
        },
        LevelId.BREAKSIDE_GRILL: {
            ModuleId.STACKER,
            ModuleId.WASTE_BIN,
            ModuleId.ROUTER,
            ModuleId.SEQUENCER,
            ModuleId.BREAKSIDE_GRILL_SCANNER,
            ModuleId.SORTER,
            ModuleId.HORIZONTAL_SLICER,
            ModuleId.SENSOR,
            ModuleId.SMALL_COUNTER,
            ModuleId.CONVEYOR,
            ModuleId.MULTIMIXER_ENABLE,
            ModuleId.MULTIMIXER,
            ModuleId.BIG_COUNTER,
            ModuleId.GRILL,
        },
        LevelId.CHAZ_CHEDDAR: {
            ModuleId.STACKER,
            ModuleId.ROTATOR,
            ModuleId.ROUTER,
            ModuleId.SEQUENCER,
            ModuleId.SORTER,
            ModuleId.CONVEYOR,
            ModuleId.SENSOR,
            ModuleId.SMALL_COUNTER,
            ModuleId.FLATTENER,
            ModuleId.CHAZ_CHEDDAR_SCANNER,
            ModuleId.MULTIMIXER_ENABLE,
            ModuleId.MULTIMIXER,
            ModuleId.ANIMATRONIC,
            ModuleId.BIG_COUNTER,
        },
        LevelId.HALF_CAFF_COFFEE: {
            ModuleId.STACKER,
            ModuleId.WASTE_BIN,
            ModuleId.ROUTER,
            ModuleId.SEQUENCER,
            ModuleId.SORTER,
            ModuleId.CONVEYOR,
            ModuleId.SENSOR,
            ModuleId.SMALL_COUNTER,
            ModuleId.HALF_CAFF_COFFEE_SCANNER,
            ModuleId.MULTIMIXER_ENABLE,
            ModuleId.MULTIMIXER,
            ModuleId.BIG_COUNTER,
            ModuleId.ESPRESSO,
        },
        LevelId.MILDREDS_NOOK: {
            ModuleId.STACKER,
            ModuleId.MILDREDS_NOOK_SCANNER,
            ModuleId.WASTE_BIN,
            ModuleId.ROUTER,
            ModuleId.SEQUENCER,
            ModuleId.SORTER,
            ModuleId.CONVEYOR,
            ModuleId.SENSOR,
            ModuleId.SMALL_COUNTER,
            ModuleId.MULTIMIXER_ENABLE,
            ModuleId.MULTIMIXER,
            ModuleId.BIG_COUNTER,
            ModuleId.GRILL,
        },
        LevelId.BELLYS: {
            ModuleId.STACKER,
            ModuleId.FRYER,
            ModuleId.WASTE_BIN,
            ModuleId.ROUTER,
            ModuleId.SEQUENCER,
            ModuleId.SORTER,
            ModuleId.HORIZONTAL_SLICER,
            ModuleId.SENSOR,
            ModuleId.SMALL_COUNTER,
            ModuleId.CONVEYOR,
            ModuleId.MULTIMIXER_ENABLE,
            ModuleId.BELLYS_SCANNER,
            ModuleId.MULTIMIXER,
            ModuleId.BIG_COUNTER,
        },
        LevelId.SUSHI_YEAH: {
            ModuleId.STACKER,
            ModuleId.WASTE_BIN,
            ModuleId.ROUTER,
            ModuleId.SEQUENCER,
            ModuleId.SORTER,
            ModuleId.CONVEYOR,
            ModuleId.SENSOR,
            ModuleId.SMALL_COUNTER,
            ModuleId.ROLLER,
            ModuleId.MULTIMIXER_ENABLE,
            ModuleId.MULTIMIXER,
            ModuleId.SUSHI_YEAH_SCANNER,
            ModuleId.BIG_COUNTER,
            ModuleId.DOUBLE_SLICER,
        },
    }

    for level_id in LevelId:
        assert (
            BUYABLE_MODULES[level_id] == buyable_ref[level_id]
        ), f"bad buyable modules for {level_id.name}"
