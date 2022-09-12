from __future__ import annotations

import dataclasses
from dataclasses import InitVar, dataclass, field
from typing import TYPE_CHECKING, NamedTuple, Optional, Sequence, Type, Union

from .entities import (
    Burger,
    ChaatDough,
    Cup,
    Entity,
    Multitray,
    Nori,
    PaintableCup,
    PizzaDough,
    SushiBowl,
    SushiPlate,
)
from .enums import (
    EntityId,
    JackDirection,
    LevelId,
    ModuleId,
    OperationId,
    PaintMask,
    ToppingId,
)
from .errors import (
    EmergencyStop,
    InternalSimulationError,
    InvalidSolutionError,
    TooManyActiveInputs,
)
from .models import Direction, MoveEntity, RelativeDirection
from .operations import (
    CoatFluid,
    DispenseFluid,
    DispenseFluidMixed,
    DispenseTopping,
    Dock,
    Flatten,
    Operation,
)

if TYPE_CHECKING:
    from .enums import MusicMode, PaintColor
    from .levels import Level
    from .models import Position
    from .simulator import State


class Jack(NamedTuple):
    name: str
    direction: JackDirection


# convenient shortcuts for defining jacks
def InJack(name: str) -> Jack:
    return Jack(name, JackDirection.IN)


def OutJack(name: str) -> Jack:
    return Jack(name, JackDirection.OUT)


@dataclass(init=False)
class Signals:
    # signal values to use while evaluating the current tick
    values: list[bool] = field(init=False)
    # signal values to use for the next tick
    next_values: list[bool] = field(init=False)

    def __init__(self, num_jacks: int):
        self.values = [False] * num_jacks
        self.next_values = self.values.copy()

    def update(self) -> None:
        """Advance to the next tick and clear all pending signals."""
        self.values = self.next_values.copy()
        self.next_values = [False] * len(self.values)


@dataclass
class Module:
    _input_directions = {RelativeDirection.BACK}
    rack_width = 1
    on_rack = True
    on_floor = True
    price = 0
    jacks = []  # type: ignore

    level: InitVar[Level]
    id: ModuleId
    can_delete: bool
    rack_position: Position
    floor_position: Position
    direction: Direction

    signals: Signals = field(init=False, repr=False)

    def __post_init__(self, level: Level) -> None:
        del level
        self.signals = Signals(len(self.jacks) if self.on_rack else 0)

    def __hash__(self) -> int:
        return hash((self.id.value, self.floor_position, self.rack_position))

    def copy(self, level: Level) -> Module:
        return dataclasses.replace(self, level=level)

    def emergency_stop(self, message: str, *extra_positions: Position) -> EmergencyStop:
        return EmergencyStop(message, self.floor_position, *extra_positions)

    def check(self) -> None:
        # make sure this class is hashable
        hash(self)
        # check that positions are in-bounds
        if self.on_floor:
            if not (
                0 <= self.floor_position.row < 7 and 0 <= self.floor_position.column < 6
            ):
                raise InvalidSolutionError("Floor position out-of-bounds")
        if self.on_rack:
            if not (
                0 <= self.rack_position.row < 3
                and self.rack_position.column >= 0
                and self.rack_position.column + self.rack_width <= 11
            ):
                raise InvalidSolutionError("Rack position out-of-bounds")

        assert len(self.signals.values) == len(self.jacks)
        if not self.on_rack:
            assert (
                not self.jacks
            ), f"non-rack module shouldn't have any jacks: {self.jacks}"

    def _get_signal(self, key: Union[str, int]) -> bool:
        """Return the current signal value on an input jack."""
        assert self.on_rack, "called _get_signal on non-rack module"
        if isinstance(key, str):
            idx = next(i for i, jack in enumerate(self.jacks) if jack.name == key)
        else:
            idx = key
        assert (
            self.jacks[idx].direction is JackDirection.IN
        ), f"tried to get value of output jack {key}"
        return self.signals.values[idx]

    def _get_signals(self) -> list[bool]:
        """Return the current signal values for all input jacks."""
        assert self.on_rack, "called _get_signals on non-rack module"
        return [
            value
            for value, jack in zip(self.signals.values, self.jacks)
            if jack.direction is JackDirection.IN
        ]

    def _get_signal_count(self) -> int:
        """Return the number of currently active input signals."""
        return sum(self._get_signals())

    def _set_signal(
        self,
        key: Union[str, int],
        value: bool,
        state: State,
        seen: Optional[set[tuple[Module, int]]] = None,
    ) -> None:
        """Set the signal value on an output jack for the next tick."""
        assert self.on_rack, "called _set_signal on non-rack module"
        if isinstance(key, str):
            idx = next(i for i, jack in enumerate(self.jacks) if jack.name == key)
        else:
            idx = key
        assert (
            self.jacks[idx].direction is JackDirection.OUT
        ), f"tried to set value of input jack {key}"
        prev_value = self.signals.next_values[idx]
        self.signals.next_values[idx] = value
        if value != prev_value and (self, idx) in state.wire_map:
            other, other_idx = state.wire_map[self, idx]
            if seen is None:
                seen = set()
            if (other, other_idx) not in seen:
                # pylint: disable-next=protected-access  # other is always a Module
                other._set_input_signal(other_idx, value, state, seen)

    def _set_input_signal(
        self, idx: int, value: bool, state: State, seen: set[tuple[Module, int]]
    ) -> None:
        """Used by Multimixers to propagate signals immediately."""
        del state
        assert self.jacks[idx].direction is JackDirection.IN
        self.signals.next_values[idx] = value
        seen.add((self, idx))

    def _set_signals(
        self,
        values: Sequence[bool],
        state: State,
        seen: Optional[set[tuple[Module, int]]] = None,
    ) -> None:
        """Set the signal values on a set of output jacks for the next tick."""
        output_jack_indices = [
            i
            for i, jack in enumerate(self.jacks)
            if jack.direction is JackDirection.OUT
        ]
        if len(output_jack_indices) != len(values):
            raise ValueError("slice and values lengths don't match")
        if seen is None:
            seen = set()
        for i, value in zip(output_jack_indices, values):
            self._set_signal(i, value, state, seen)

    def debug_str(self) -> str:
        return ""

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        """Update internal state and output signals for a single tick."""
        del stage, state
        return []

    def handle_moves(
        self,
        state: State,
        moves: list[MoveEntity],
        ignore_collisions: bool = False,
        dry_run: bool = False,
    ) -> Optional[MoveEntity]:
        """Resolve movements onto this module.

        Return the movement to perform, or None if no movement should be performed.

        If `ignore_collisions` is True, then consider the current position to be
        empty for the purposes of collision checking.
        If `dry_run` is True, don't modify any simulation state.

        Note: the default implementation does not handle collisions with
        existing entities on this module.
        """
        del state, ignore_collisions, dry_run
        if len(moves) > 1:
            raise self.emergency_stop(
                "These products have collided.", *[m.source for m in moves]
            )
        if (
            moves[0].direction.back().relative_to(self.direction)
            not in self._input_directions
        ):
            raise self.emergency_stop(
                "Products cannot enter from this direction.", moves[0].source
            )
        return moves[0]


# Module subclasses


class Scanner(Module):
    _MODULE_IDS = [ModuleId(ModuleId.SCANNER_BASE.value + id.value) for id in LevelId]
    _input_directions = set()  # type: ignore
    rack_width = 2
    price = 20

    def __post_init__(self, level: Level) -> None:
        self.jacks = [OutJack("SCAN")]
        for name in level.order_signal_names:
            self.jacks.append(OutJack(name))
        super().__post_init__(level)

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 2:
            return []
        target = state.get_entity(self.floor_position.shift_by(self.direction))
        enable = target is not None and target.id in (EntityId.TRAY, EntityId.MULTITRAY)
        if enable:
            values = [enable, *state.order_signals]
        else:
            values = [False] * len(self.jacks)
        self._set_signals(values, state)
        return []


class MainInput(Module):
    _MODULE_IDS = [
        ModuleId(ModuleId.MAIN_INPUT_BASE.value + id.value) for id in LevelId
    ]
    _input_directions = set()  # type: ignore
    rack_width = 2

    def __post_init__(self, level: Level) -> None:
        self.jacks = [OutJack("START")]
        for name in level.order_signal_names:
            self.jacks.append(OutJack(name))
        super().__post_init__(level)

    def check(self) -> None:
        if self.floor_position.row != 6:
            raise InvalidSolutionError("Tray input must be on the top row")
        if self.direction is not Direction.DOWN:
            raise InvalidSolutionError("Tray input must face down")

    def zeroth_tick(self, state: State) -> None:
        self._set_signal("START", True, state)
        self._set_signals([True, *state.order_signals], state)
        tray: Entity
        if state.level.tray_capacity == 1:
            tray = Entity(EntityId.TRAY, position=self.floor_position)
        else:
            tray = Multitray(
                position=self.floor_position, capacity=state.level.tray_capacity
            )
        state.add_entity(tray)

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 1:
            return []
        tray = state.get_entity(self.floor_position)
        if tray is not None:
            # only on first tick
            self._set_signals([False] * len(self.jacks), state)
            return [MoveEntity(tray, self.direction)]
        return []


@dataclass
class Input(Module):
    _input_directions = set()  # type: ignore

    input_id: int

    __hash__ = Module.__hash__


@dataclass
class EntityInput(Input):
    _MODULE_IDS = [ModuleId.INPUT_1X, ModuleId.INPUT_2X, ModuleId.INPUT_3X]

    entity_ids: list[EntityId] = field(init=False)

    __hash__ = Module.__hash__

    def __post_init__(self, level: Level) -> None:
        self.entity_ids = level.entity_inputs[self.input_id]
        self.jacks = [InJack(eid.name) for eid in self.entity_ids]
        super().__post_init__(level)

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 1:
            return []
        input_count = sum(self._get_signals())
        if input_count > 1:
            raise TooManyActiveInputs(self)
        if input_count == 0:
            return []
        idx = self.signals.values.index(True)
        eid = self.entity_ids[idx]
        entity: Entity
        if state.level.id is LevelId.SODA_TRENCH and eid is EntityId.CUP:
            entity = PaintableCup(position=self.floor_position, capacity=2)
        elif state.level.id is LevelId.MUMBAI_CHAAT and eid is EntityId.DOUGH:
            entity = ChaatDough(position=self.floor_position)
        elif state.level.id is LevelId.CHAZ_CHEDDAR and eid is EntityId.DOUGH:
            entity = PizzaDough(position=self.floor_position)
        elif eid is EntityId.CUP:
            capacity = {
                LevelId.WINE_OCLOCK: 2,
                LevelId.THE_WALRUS: 5,
                LevelId.CAFE_TRISTE: 4,
                LevelId.HALF_CAFF_COFFEE: 4,
                LevelId.BELLYS: 2,
            }[state.level.id]
            entity = Cup(position=self.floor_position, capacity=capacity)
        elif eid is EntityId.NORI:
            entity = Nori(position=self.floor_position)
        elif eid is EntityId.PLATE:
            entity = SushiPlate(position=self.floor_position)
        elif state.level.id is LevelId.SUSHI_YEAH and eid is EntityId.BOWL:
            entity = SushiBowl(position=self.floor_position)
        else:
            entity = Entity(id=eid, position=self.floor_position)
        state.add_entity(entity)
        return [MoveEntity(entity, self.direction)]


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

    __hash__ = Module.__hash__

    def __post_init__(self, level: Level) -> None:
        self.topping_ids = level.topping_inputs[self.input_id]
        self.jacks = [InJack(tid.name) for tid in self.topping_ids]
        super().__post_init__(level)


class FluidDispenser(ToppingInput):
    _MODULE_IDS = [
        ModuleId.FLUID_DISPENSER_1X,
        ModuleId.FLUID_DISPENSER_2X,
        ModuleId.FLUID_DISPENSER_3X,
    ]

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 1:
            return []
        input_count = self._get_signal_count()
        if input_count > 1 and state.level.id is not LevelId.MR_CHILLY:
            raise TooManyActiveInputs(self)
        if input_count == 0:
            return []
        topping = self.topping_ids[self.signals.values.index(True)]
        pos = self.floor_position.shift_by(self.direction)
        target = state.get_entity(pos)
        if target is None:
            raise self.emergency_stop(
                "There is no product beneath this dispenser.", pos
            )
        # can operate on top of tray
        if target.id is EntityId.TRAY and target.stack is not None:
            target = target.stack
        error = self.emergency_stop(
            "This liquid cannot be applied to this product.", pos
        )
        op = DispenseFluid(topping)
        if isinstance(target, Cup):
            target.add_fluid(topping, error)
            return []
        if isinstance(target, ChaatDough):
            target.add_sauce(topping, error)
            return []
        if state.level.id is LevelId.MILDREDS_NOOK and target.id is EntityId.MULTITRAY:
            capacity = 1
        elif target.id in (EntityId.NACHO, EntityId.GLASS, EntityId.BOWL):
            capacity = 2
        elif target.id is EntityId.CONE:
            if input_count == 2:
                op = DispenseFluidMixed(self.topping_ids[0], self.topping_ids[1])
            capacity = 4
        else:
            raise error
        # check that any existing fluids match and we won't go over capacity
        if target.operations and (
            target.operations[-1] != op or len(target.operations) >= capacity
        ):
            raise error
        target.operations.append(op)
        return []


class FluidCoater(ToppingInput):
    _MODULE_IDS = [ModuleId.FLUID_COATER]
    _input_directions = {RelativeDirection.BACK}
    on_rack = False

    def __post_init__(self, level: Level) -> None:
        super().__post_init__(level)
        self.jacks = []  # remove the jacks added by ToppingInput
        assert (
            len(self.topping_ids) == 1
        ), "invalid level: too many toppings for FluidCoater"

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 1:
            return []
        target = state.get_entity(self.floor_position)
        if target is None:
            return []
        target.operations.append(CoatFluid(self.topping_ids[0]))
        return [MoveEntity(target, self.direction)]


class ToppingDispenser(ToppingInput):
    _MODULE_IDS = [ModuleId.TOPPING_DISPENSER]
    _input_directions = {RelativeDirection.BACK}

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 1:
            return []
        target = state.get_entity(self.floor_position)
        if self._get_signal(0):
            if target is None:
                raise self.emergency_stop("There is no product beneath this dispenser.")
            target.operations.append(DispenseTopping(self.topping_ids[0]))
        if target is not None:
            return [MoveEntity(target, self.direction)]
        return []


class HalfToppingDispenser(ToppingInput):
    _MODULE_IDS = [ModuleId.HALF_TOPPING_DISPENSER]
    _input_directions = {RelativeDirection.BACK}

    def check(self) -> None:
        super().check()
        if self.direction not in (
            Direction.UP,
            Direction.DOWN,
        ):
            raise InvalidSolutionError(
                "Pizza topping dispenser can only face up or down"
            )

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 1:
            return []
        entity = state.get_entity(self.floor_position)
        if self._get_signal(0):
            if entity is None:
                raise self.emergency_stop("There is no product beneath this dispenser.")
            target = entity
            # can operate on top of tray
            if target.id is EntityId.TRAY and target.stack is not None:
                target = target.stack
            if not isinstance(target, PizzaDough):
                raise self.emergency_stop(
                    "This topping cannot be applied to this product."
                )
            target.left_toppings.add(self.topping_ids[0])
        if entity is not None:
            return [MoveEntity(entity, self.direction)]
        return []


class Conveyor(Module):
    _MODULE_IDS = [ModuleId.CONVEYOR]
    price = 5
    on_rack = False

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 1:
            return []
        target = state.get_entity(self.floor_position)
        if target is None:
            return []
        # dest = state.get_entity(self.floor_position.shift_by(self.direction))
        # if dest is not None:
        #     return []
        return [MoveEntity(target, self.direction, force=False)]

    def handle_moves(
        self,
        state: State,
        moves: list[MoveEntity],
        ignore_collisions: bool = False,
        dry_run: bool = False,
    ) -> Optional[MoveEntity]:
        if not (state.get_entity(self.floor_position) is None or ignore_collisions):
            return None
        priority = [
            RelativeDirection.BACK,
            RelativeDirection.RIGHT,
            RelativeDirection.LEFT,
            RelativeDirection.FRONT,
        ]
        move = min(
            moves,
            key=lambda m: priority.index(
                m.direction.back().relative_to(self.direction)
            ),
        )
        return move


class Output(Module):
    _MODULE_IDS = [ModuleId.OUTPUT]
    on_rack = False
    price = 0

    def check(self) -> None:
        if self.floor_position.row != 0:
            raise InvalidSolutionError("Output must be on the bottom row")
        if self.direction is not Direction.DOWN:
            raise InvalidSolutionError("Output must face down")

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 1:
            return []
        target = state.get_entity(self.floor_position)
        if target is None:
            return []
        expected = state.level.order_products[state.order_index]
        if target != expected:
            print("expected:", expected)
            print("got:     ", target)
            raise self.emergency_stop("This product does not match the order.")
        return [MoveEntity(target, self.direction)]


@dataclass
class Router(Module):
    _MODULE_IDS = [ModuleId.ROUTER]
    price = 10
    jacks = [InJack(name) for name in ["LEFT", "THRU", "RIGHT"]]

    current_direction: Direction = field(init=False)

    __hash__ = Module.__hash__

    def __post_init__(self, level: Level) -> None:
        super().__post_init__(level)
        self.current_direction = self.direction

    def debug_str(self) -> str:
        return self.current_direction.name

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 1:
            return []
        if self._get_signal_count() > 1:
            raise TooManyActiveInputs(self)
        old_direction = self.current_direction
        if self._get_signal("THRU"):
            self.current_direction = self.direction
        elif self._get_signal("LEFT"):
            self.current_direction = self.direction.left()
        elif self._get_signal("RIGHT"):
            self.current_direction = self.direction.right()
        target = state.get_entity(self.floor_position)
        if target is not None:
            return [MoveEntity(target, old_direction, force=False)]
        return []


class Sensor(Module):
    _MODULE_IDS = [ModuleId.SENSOR]
    _input_directions = set()  # type: ignore
    price = 5
    jacks = [OutJack("SENSE")]

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 2:
            return []
        target = state.get_entity(self.floor_position.shift_by(self.direction))
        if target is not None:
            self._set_signal("SENSE", True, state)
        return []


class EjectingModule(Module):
    """Common code shared between Sorter, Cooker, and Espresso."""

    def handle_moves(
        self,
        state: State,
        moves: list[MoveEntity],
        ignore_collisions: bool = False,
        dry_run: bool = False,
    ) -> Optional[MoveEntity]:
        # does not handle collisions with stopped entities
        super().handle_moves(state, moves, ignore_collisions, dry_run)
        priority = [
            RelativeDirection.BACK,
            RelativeDirection.RIGHT,
            RelativeDirection.LEFT,
            RelativeDirection.FRONT,
        ]
        move = min(
            moves,
            key=lambda m: priority.index(
                m.direction.back().relative_to(self.direction)
            ),
        )

        available = state.get_entity(self.floor_position) is None or ignore_collisions
        if not available:
            if any(jack.name == "EJECT" for jack in self.jacks):
                # Cooker and Espresso
                will_eject = self._get_signal("EJECT")
            else:
                # Sorter
                will_eject = self._get_signal_count() == 1
            if will_eject:
                # we're going to move the current entity away this tick, which should
                # have been processed already
                raise InternalSimulationError(
                    "move evaluation order is incorrect", self.floor_position
                )
        if not available:
            if move.force:
                raise self.emergency_stop("These products have collided.", move.source)
            return None
        return move


class Sorter(EjectingModule):
    _MODULE_IDS = [ModuleId.SORTER]
    _input_directions = set(RelativeDirection)
    price = 10
    jacks = [OutJack("SENSE"), InJack("LEFT"), InJack("THRU"), InJack("RIGHT")]

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        target = state.get_entity(self.floor_position)
        if stage == 1:
            if self._get_signal_count() > 1:
                raise TooManyActiveInputs(self)
            if target is None:
                return []
            direction = None
            if self._get_signal("THRU"):
                direction = self.direction
            elif self._get_signal("LEFT"):
                direction = self.direction.left()
            elif self._get_signal("RIGHT"):
                direction = self.direction.right()
            if direction is not None:
                return [MoveEntity(target, direction)]
        elif stage == 2 and target is not None:
            self._set_signal("SENSE", True, state)
        return []


class Stacker(Module):
    _MODULE_IDS = [ModuleId.STACKER]
    price = 20
    jacks = [OutJack("STACK"), InJack("EJECT")]

    __hash__ = Module.__hash__

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 1:
            return []
        target = state.get_entity(self.floor_position)
        if target is None or not self._get_signal("EJECT"):
            return []
        return [MoveEntity(target, self.direction)]

    def handle_moves(
        self,
        state: State,
        moves: list[MoveEntity],
        ignore_collisions: bool = False,
        dry_run: bool = False,
    ) -> Optional[MoveEntity]:
        # does not handle collisions with stopped entities
        super().handle_moves(state, moves, ignore_collisions, dry_run)
        assert len(moves) == 1, "Stacker only handles one move"
        move = moves[0]
        base = state.get_entity(self.floor_position)
        if base is None or ignore_collisions:
            return move

        if not dry_run:
            stack_error = self.emergency_stop(
                "These products cannot be stacked.", move.source
            )
            # stacking logic
            base.add_to_stack(state, move.entity, stack_error)
            self._set_signal("STACK", True, state)
        return None


class Cooker(EjectingModule):
    _MODULE_IDS = [ModuleId.GRILL, ModuleId.FRYER, ModuleId.MICROWAVE]
    _input_directions = {RelativeDirection.FRONT, RelativeDirection.BACK}
    price = 20
    jacks = [OutJack("SENSE"), InJack("EJECT")]

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        target = state.get_entity(self.floor_position)
        if stage == 1:
            first_tick = not self.signals.values[0]
            if target is None:
                return []
            if self._get_signal("EJECT"):
                return [MoveEntity(target, self.direction)]
            if not first_tick:
                op = Operation(
                    {
                        ModuleId.GRILL: OperationId.COOK_GRILL,
                        ModuleId.FRYER: OperationId.COOK_FRYER,
                        ModuleId.MICROWAVE: OperationId.COOK_MICROWAVE,
                    }[self.id]
                )
                target.operations.append(op)
        elif stage == 2 and target is not None:
            self._set_signal("SENSE", True, state)
        return []


class SimpleMachine(Module):
    on_rack = False
    price = 20


@dataclass
class WasteBin(SimpleMachine):
    _MODULE_IDS = [ModuleId.WASTE_BIN]

    is_full: bool = False

    __hash__ = Module.__hash__

    def debug_str(self) -> str:
        return "full" if self.is_full else "empty"

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 1:
            return []
        target = state.get_entity(self.floor_position)
        if target is None:
            return []
        if self.is_full:
            raise self.emergency_stop("This waste bin has already been used.")
        self.is_full = True
        state.remove_entity(target)
        return []


class DoubleSlicer(SimpleMachine):
    _MODULE_IDS = [ModuleId.DOUBLE_SLICER]
    _LOOKUP = {
        LevelId.CAFE_TRISTE: {
            EntityId.CIGARETTE_4X: EntityId.CIGARETTE_2X,
            EntityId.CIGARETTE_2X: EntityId.CIGARETTE,
        },
        LevelId.SWEET_HEAT_BBQ: {
            EntityId.ROAST: EntityId.ROAST_SLICE,
            EntityId.RIBS: EntityId.RIBS_SLICE,
        },
        LevelId.SUSHI_YEAH: {
            EntityId.TUNA_MAKI_4X: EntityId.TUNA_MAKI_2X,
            EntityId.TUNA_MAKI_2X: EntityId.TUNA_MAKI,
            EntityId.SALMON_MAKI_4X: EntityId.SALMON_MAKI_2X,
            EntityId.SALMON_MAKI_2X: EntityId.SALMON_MAKI,
        },
    }

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 1:
            return []
        target = state.get_entity(self.floor_position)
        if target is None:
            return []
        eid = self._LOOKUP[state.level.id][target.id]
        if state.level.id in (LevelId.CAFE_TRISTE, LevelId.SUSHI_YEAH):
            state.remove_entity(target)
            entity_r = Entity(eid, position=self.floor_position)
            entity_l = Entity(eid, position=self.floor_position)
            state.add_entity(entity_r)
            state.add_entity(entity_l)
        elif state.level.id is LevelId.SWEET_HEAT_BBQ:
            entity_r = Entity(eid, position=self.floor_position)
            entity_l = target
            state.add_entity(entity_r)
        return [
            MoveEntity(entity_r, direction=self.direction.right()),
            MoveEntity(entity_l, direction=self.direction.left()),
        ]

    def handle_moves(
        self,
        state: State,
        moves: list[MoveEntity],
        ignore_collisions: bool = False,
        dry_run: bool = False,
    ) -> Optional[MoveEntity]:
        move = super().handle_moves(state, moves)
        if move is None:
            return None
        target = move.entity
        error = self.emergency_stop("This product cannot be sliced.", move.source)
        if target.operations or target.stack:
            raise error
        if state.level.id not in self._LOOKUP:
            raise error
        if target.id not in self._LOOKUP[state.level.id]:
            raise error
        return move


class TripleSlicer(SimpleMachine):
    _MODULE_IDS = [ModuleId.TRIPLE_SLICER]

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 1:
            return []
        target = state.get_entity(self.floor_position)
        if target is None:
            return []
        actions: list[MoveEntity]
        if target not in (Entity(EntityId.CHICKEN), Entity(EntityId.CHICKEN_HALF)):
            raise self.emergency_stop("This product cannot be sliced.")
        state.remove_entity(target)
        leg = Entity(EntityId.CHICKEN_LEG, position=self.floor_position)
        cutlet = Entity(EntityId.CHICKEN_CUTLET, position=self.floor_position)
        if state.level.id is LevelId.DA_WINGS and target.id is EntityId.CHICKEN_HALF:
            entity_r = cutlet
            entity_t = leg
        else:
            entity_r = leg
            entity_t = cutlet
        state.add_entity(entity_r)
        state.add_entity(entity_t)
        actions = [
            MoveEntity(entity_r, direction=self.direction.right()),
            MoveEntity(entity_t, direction=self.direction),
        ]
        if target.id == EntityId.CHICKEN:
            entity_l = Entity(EntityId.CHICKEN_HALF, position=self.floor_position)
            state.add_entity(entity_l)
            actions.append(MoveEntity(entity_l, direction=self.direction.left()))
        return actions


class HorizontalSlicer(SimpleMachine):
    _MODULE_IDS = [ModuleId.HORIZONTAL_SLICER]

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 1:
            return []
        target = state.get_entity(self.floor_position)
        if target is None:
            return []
        if target == Entity(EntityId.BUN):
            state.remove_entity(target)
            entity_r = Burger(position=self.floor_position)
            entity_l = Entity(EntityId.BUN_TOP, position=self.floor_position)
            state.add_entity(entity_r)
            state.add_entity(entity_l)
            return [
                MoveEntity(entity_r, direction=self.direction.right()),
                MoveEntity(entity_l, direction=self.direction.left()),
            ]
        raise self.emergency_stop("This product cannot be sliced.")


class Roller(SimpleMachine):
    _MODULE_IDS = [ModuleId.ROLLER]

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 1:
            return []
        target = state.get_entity(self.floor_position)
        if target is None:
            return []
        error = self.emergency_stop("This product cannot be rolled.")
        if target.id is EntityId.PAPER:
            if target.operations != [DispenseTopping(ToppingId.LEAVES)]:
                raise error
            state.remove_entity(target)
            entity = Entity(EntityId.CIGARETTE_4X, position=self.floor_position)
            state.add_entity(entity)
            return [MoveEntity(entity, self.direction)]
        if isinstance(target, Nori):
            if not (
                len(target.multistack) == 2
                and target.multistack[0] == target.multistack[1]
                and target.multistack[0]
                in [
                    Entity(EntityId.RICE, stack=Entity(fish))
                    for fish in [EntityId.TUNA, EntityId.SALMON]
                ]
            ):
                raise error
            if target.multistack[0].stack.id is EntityId.TUNA:  # type: ignore
                roll_type = EntityId.TUNA_MAKI_4X
            else:
                roll_type = EntityId.SALMON_MAKI_4X
            state.remove_entity(target)
            entity = Entity(roll_type, position=self.floor_position)
            state.add_entity(entity)
            return [MoveEntity(entity, self.direction)]
        raise error


class Docker(SimpleMachine):
    _MODULE_IDS = [ModuleId.DOCKER]

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 1:
            return []
        target = state.get_entity(self.floor_position)
        if target is None:
            return []
        if not isinstance(target, ChaatDough):
            raise self.emergency_stop("This product cannot be rolled.")
        target.operations.append(Dock())
        return [MoveEntity(target, self.direction)]


class Flattener(SimpleMachine):
    _MODULE_IDS = [ModuleId.FLATTENER]

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 1:
            return []
        entity = state.get_entity(self.floor_position)
        if entity is None:
            return []
        target = entity
        # can operate on top of tray
        if target.id is EntityId.TRAY and target.stack is not None:
            target = target.stack
        if not isinstance(target, PizzaDough):
            raise self.emergency_stop("This product cannot be rolled.")
        target.operations.append(Flatten())
        return [MoveEntity(entity, self.direction)]


class Rotator(SimpleMachine):
    _MODULE_IDS = [ModuleId.ROTATOR]
    _input_directions = {RelativeDirection.FRONT, RelativeDirection.BACK}

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 1:
            return []
        entity = state.get_entity(self.floor_position)
        if entity is None:
            return []
        target = entity
        # can operate on top of tray
        if target.id is EntityId.TRAY and target.stack is not None:
            target = target.stack
        if not isinstance(target, PizzaDough):
            raise self.emergency_stop("This product cannot be rotated.")
        # swap left and right toppings
        target.left_toppings, target.right_toppings = (
            target.right_toppings,
            target.left_toppings,
        )
        return [MoveEntity(entity, self.direction)]


@dataclass
class Painter(Module):
    _MODULE_IDS = [ModuleId.PAINTER]
    _input_directions = {RelativeDirection.FRONT, RelativeDirection.BACK}
    price = 40

    color: PaintColor
    mask: PaintMask

    __hash__ = Module.__hash__

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 1:
            return []
        target = state.get_entity(self.floor_position)
        if target is None:
            return []
        if not isinstance(target, PaintableCup):
            raise self.emergency_stop("This product cannot be painted.")
        # paint colors go from top to bottom
        indices = {
            PaintMask.UPPER_2: [0, 1],
            PaintMask.UPPER_1: [0],
            PaintMask.LOWER_1: [2],
            PaintMask.LOWER_2: [1, 2],
        }[self.mask]
        for i in indices:
            target.colors[i] = self.color
        return [MoveEntity(target, self.direction)]


@dataclass
class Espresso(EjectingModule):
    _MODULE_IDS = [ModuleId.ESPRESSO]
    _input_directions = {RelativeDirection.FRONT, RelativeDirection.BACK}
    price = 40
    jacks = [InJack(name) for name in ["GRIND", "XTRACT", "STEAM", "EJECT"]]

    grind_count: int = 0

    __hash__ = Module.__hash__

    def check(self) -> None:
        super().check()
        if self.direction not in (
            Direction.RIGHT,
            Direction.LEFT,
        ):
            raise InvalidSolutionError("Espresso machine can only face right or left")

    def debug_str(self) -> str:
        return f"grind_count={self.grind_count}"

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 1:
            return []
        if self._get_signal_count() > 1:
            raise TooManyActiveInputs(self)
        if self._get_signal("GRIND"):
            if self.grind_count >= 4:
                raise self.emergency_stop("The espresso filter is already full.")
            self.grind_count += 1
            return []
        target = state.get_entity(self.floor_position)
        if self._get_signal("EJECT"):
            if target is not None:
                return [MoveEntity(target, self.direction)]
            return []
        if self._get_signal("XTRACT"):
            error = self.emergency_stop("Extraction requires a proper target product.")
            if not isinstance(target, Cup):
                raise error
            if self.grind_count != 4:
                raise self.emergency_stop("The espresso filter is not yet full.")
            self.grind_count = 0
            target.add_fluid(ToppingId.COFFEE, error)
            return []
        if self._get_signal("STEAM"):
            error = self.emergency_stop("Steaming requires a proper target product.")
            if not isinstance(target, Cup):
                raise error
            # milk can be foamed as long as there's only milk and foam in the cup
            if not (+target.contents).keys() <= {ToppingId.MILK, ToppingId.FOAM}:
                raise error
            target.remove_fluid(ToppingId.MILK)
            target.add_fluid(ToppingId.FOAM, error)
        return []


@dataclass
class Animatronic(Module):
    _MODULE_IDS = [ModuleId.ANIMATRONIC]
    _input_directions = set()  # type: ignore
    rack_width = 2
    price = 40
    jacks = [
        InJack(name) for name in ["DANCE", "SING", "GLASSES", "I", "IV", "V", "I'"]
    ]

    music_mode: MusicMode

    __hash__ = Module.__hash__


class Multimixer(Module):
    _MODULE_IDS = [ModuleId.MULTIMIXER]
    on_floor = False
    price = 1
    jacks = [
        *[InJack(f"IN_{i+1}") for i in range(4)],
        *[OutJack(f"OUT_{i+1}") for i in range(4)],
    ]

    def _set_input_signal(
        self, idx: int, value: bool, state: State, seen: set[tuple[Module, int]]
    ) -> None:
        super()._set_input_signal(idx, value, state, seen)
        # propagate to all connected outputs
        value = any(self.signals.next_values[:4])
        self._set_signals([value] * 4, state, seen)


class MultimixerEnable(Module):
    _MODULE_IDS = [ModuleId.MULTIMIXER_ENABLE]
    on_floor = False
    price = 1
    jacks = [
        InJack("ENABLE"),
        *[InJack(f"IN_{i+1}") for i in range(3)],
        *[OutJack(f"OUT_{i+1}") for i in range(3)],
    ]

    def _set_input_signal(
        self, idx: int, value: bool, state: State, seen: set[tuple[Module, int]]
    ) -> None:
        super()._set_input_signal(idx, value, state, seen)
        # propagate to all connected outputs
        value = self.signals.next_values[0] and any(self.signals.next_values[1:4])
        self._set_signals([value] * 3, state, seen)


@dataclass
class SmallCounter(Module):
    _MODULE_IDS = [ModuleId.SMALL_COUNTER]
    on_floor = False
    price = 3
    jacks = [OutJack("ZERO"), InJack("IN_1"), InJack("IN_2")]

    values: list[int]
    count: int = 0

    __hash__ = Module.__hash__

    def check(self) -> None:
        super().check()
        assert len(self.values) == 2, "Invalid values length for SmallCounter"
        if not all(-9 <= x <= 9 for x in self.values):
            raise InvalidSolutionError(
                "Small counter increment values must be between -9 and +9"
            )

    def debug_str(self) -> str:
        return f"count={self.count}"

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage == 1:
            for signal, increment in zip(self._get_signals(), self.values):
                if signal:
                    self.count = max(-99, min(self.count + increment, 99))
        elif stage == 2 and self.count == 0:
            self._set_signal("ZERO", True, state)
        return []


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

    __hash__ = Module.__hash__

    def check(self) -> None:
        super().check()
        assert len(self.values) == 4, "Invalid values length for BigCounter"
        if not all(-99 <= x <= 99 for x in self.values):
            raise InvalidSolutionError(
                "Big counter increment values must be between -99 and +99"
            )

    def debug_str(self) -> str:
        return f"count={self.count}"

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage == 1:
            for signal, increment in zip(self._get_signals(), self.values):
                if signal:
                    self.count = max(-99, min(self.count + increment, 99))
        elif stage == 2:
            if self.count == 0:
                self._set_signal("ZERO", True, state)
            elif self.count > 0:
                self._set_signal("POS", True, state)
        return []


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

    __hash__ = Module.__hash__

    def check(self) -> None:
        super().check()
        assert len(self.rows) == 12, "Invalid rows for Sequencer"
        assert all(len(r) == 4 for r in self.rows), "Invalid rows for Sequencer"

    def debug_str(self) -> str:
        return f"row={self.current_row}"

    def update(self, stage: int, state: State) -> list[MoveEntity]:
        if stage != 1:
            return []
        if self._get_signal("STOP"):
            self.current_row = -1
        if self.current_row == -1 and self._get_signal("START"):
            self.current_row = 0
        if 0 <= self.current_row < 12:
            self._set_signals(self.rows[self.current_row], state)
            self.current_row += 1
        if self.current_row == 12:
            self.current_row = -1
        return []


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
                assert isinstance(module_id, ModuleId), f"bad _MODULE_IDS for {value}"
                assert (
                    module_id not in lookup
                ), f"{module_id} is claimed by {lookup[module_id]} and {value}"
                lookup[module_id] = value

    valid_ids = set(ModuleId) - {
        ModuleId.MAIN_INPUT_BASE,
        ModuleId.SCANNER_BASE,
    }
    assert (
        lookup.keys() == valid_ids
    ), f"unhandled module ids: {valid_ids - lookup.keys()}"
    return lookup


MODULE_LOOKUP = populate_module_table()
