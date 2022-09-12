from __future__ import annotations

import dataclasses
import functools
from dataclasses import dataclass
from typing import Any

from .enums import OperationId, ToppingId

__all__ = [
    "Operation",
    "CookFryer",
    "CookMicrowave",
    "CookGrill",
    "Dock",
    "Flatten",
    "DispenseFluid",
    "DispenseFluidMixed",
    "CoatFluid",
    "DispenseTopping",
]


def _id_to_name(op_id: OperationId) -> str:
    return "".join(map(str.title, op_id.name.split("_")))


@functools.total_ordering  # optimization note: this adds some overhead (see the docs)
@dataclass(frozen=True, repr=False)
class Operation:
    id: OperationId

    def __repr__(self) -> str:
        field_descs = [
            f"{getattr(self, f.name)!r}"
            for f in dataclasses.fields(self)
            if f.name != "id"
        ]
        return f"{_id_to_name(self.id)}({', '.join(field_descs)})"

    def _compare_key(self) -> tuple[Any, ...]:
        return tuple(getattr(self, f.name) for f in dataclasses.fields(self))

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Operation):
            return NotImplemented
        return self._compare_key() < other._compare_key()


def CookFryer() -> Operation:
    return Operation(OperationId.COOK_FRYER)


def CookMicrowave() -> Operation:
    return Operation(OperationId.COOK_MICROWAVE)


def CookGrill() -> Operation:
    return Operation(OperationId.COOK_GRILL)


def Dock() -> Operation:
    return Operation(OperationId.DOCK)


def Flatten() -> Operation:
    return Operation(OperationId.FLATTEN)


@dataclass(frozen=True, repr=False)
class Dispense(Operation):
    topping: ToppingId


def DispenseFluid(topping: ToppingId) -> Operation:
    return Dispense(OperationId.DISPENSE_FLUID, topping)


@dataclass(frozen=True, repr=False)
class _DispenseFluidMixed(Dispense):
    topping_2: ToppingId

    def __post_init__(self):
        assert self.topping != self.topping_2, "duplicate mixed fluid"
        assert self.topping < self.topping_2, "mixed fluids are out of order"


def DispenseFluidMixed(topping_1: ToppingId, topping_2: ToppingId) -> Operation:
    if topping_1 > topping_2:
        # swap the toppings so the lower one is first
        topping_2, topping_1 = topping_1, topping_2
    return _DispenseFluidMixed(OperationId.DISPENSE_FLUID_MIXED, topping_1, topping_2)


def CoatFluid(topping_id: ToppingId) -> Operation:
    return Dispense(OperationId.COAT_FLUID, topping_id)


def DispenseTopping(topping_id: ToppingId) -> Operation:
    return Dispense(OperationId.DISPENSE_TOPPING, topping_id)
