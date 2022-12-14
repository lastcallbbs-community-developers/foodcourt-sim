# pylint: disable-next=unused-wildcard-import, wildcard-import
from collections import Counter

from foodcourt_sim.enums import EntityId, ToppingId
from foodcourt_sim.modules import Cup

E = EntityId
T = ToppingId


def test_cup():
    one_coffee = Cup(contents=Counter({T.COFFEE: 1}))
    assert Cup(contents=Counter({T.COFFEE: 1})) == one_coffee
    assert Cup(contents=Counter({T.COFFEE: 2})) != one_coffee
    assert Cup(contents=Counter({T.COFFEE: 1, T.MILK: 1})) != one_coffee
    assert Cup(contents=Counter({T.COFFEE: 1, T.MILK: 0})) == one_coffee
