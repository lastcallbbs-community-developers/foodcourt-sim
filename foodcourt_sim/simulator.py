from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from .enums import JackDirection
from .errors import EmergencyStop
from .models import Direction, MoveEntity, Position
from .modules import MainInput, Output

if TYPE_CHECKING:
    from .entities import Entity
    from .levels import Level
    from .models import Solution, Wire
    from .modules import Module


__all__ = [
    "MoveEntity",
    "State",
    "simulate_order",
    "simulate_solution",
]


@dataclass
class State:
    level: Level
    modules: list[Module]
    # bi-directional map of wire connections
    wire_map: dict[tuple[Module, int], tuple[Module, int]]
    order_index: int
    entities: dict[Position, list[Entity]] = field(
        init=False, repr=False, default_factory=dict
    )
    _modules_by_pos: dict[Position, Module] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._modules_by_pos = {
            module.floor_position: module for module in self.modules if module.on_floor
        }

    @classmethod
    def from_solution(cls, level: Level, solution: Solution, order_index: int) -> State:
        assert solution.level_id == level.id
        modules = deepcopy(solution.modules)
        # build wire map
        wire_map = {}
        for wire in solution.wires:
            module_1 = modules[wire.module_1]
            module_2 = modules[wire.module_2]
            wire_map[module_1, wire.jack_1] = (module_2, wire.jack_2)
            wire_map[module_2, wire.jack_2] = (module_1, wire.jack_1)
        return cls(level, modules, wire_map, order_index)

    @property
    def order_signals(self) -> tuple[bool, ...]:
        return self.level.order_signals[self.order_index]

    def get_module(self, pos: Position) -> Optional[Module]:
        return self._modules_by_pos.get(pos, None)

    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the position map."""
        if entity.position not in self.entities:
            self.entities[entity.position] = []
        self.entities[entity.position].append(entity)

    def remove_entity(self, entity: Entity) -> None:
        """Remove an entity from the position map. Also clears the entity's position."""
        self.entities[entity.position].remove(entity)
        if not self.entities[entity.position]:
            del self.entities[entity.position]
        entity.position = Position(-1, -1)

    def move_entity(self, entity: Entity, direction: Direction) -> None:
        """Move an entity from one position to the adjacent position in a direction."""
        new_pos = entity.position.shift_by(direction)
        self.remove_entity(entity)
        entity.position = new_pos
        self.add_entity(entity)

    def get_entity(self, pos: Position) -> Optional[Entity]:
        """Retrieve the entity at a specific position. Returns None if no entity is present."""
        if pos not in self.entities:
            return None
        ents = self.entities[pos]
        assert len(ents) == 1, f"multiple entities at {pos}"
        return ents[0]

    def dump(self, indent: str = "") -> None:
        """Pretty-print the simulation state for debugging."""
        for module in sorted(
            self.modules, key=lambda m: (-m.rack_position.row, m.rack_position.column)
        ):
            if not module.on_rack:
                continue
            print(
                f"{indent}{module.id.name} @ {module.rack_position}: {module.debug_str()}"
            )
            for i, (jack, value) in enumerate(zip(module.jacks, module.signals.values)):
                if not value:
                    continue
                if (module, i) not in self.wire_map:
                    continue
                if jack.direction is JackDirection.OUT:
                    print(f"{indent}  {jack.name} >")
                else:
                    print(f"{indent}  > {jack.name}")
        for pos, entities in self.entities.items():
            print(f"{indent}{pos}:")
            for entity in entities:
                print(f"{indent}  {entity}")


def update_modules(state: State, stage: int) -> list[MoveEntity]:
    moves = []
    # tick modules
    for module in state.modules:
        moves.extend(module.update(stage, state))
    if stage != 1:
        assert not moves, "only update stage 1 can make movements"
    return moves


def handle_moves_to_empty(
    dest: Position, state: State, moves: list[MoveEntity]
) -> Optional[MoveEntity]:
    """Handle moving entities onto an empty factory floor space."""
    force = moves[0].force
    assert all(
        m.force is force for m in moves
    ), "not all moves have the same force state"
    if state.get_entity(dest) is not None:
        if force:
            # collision with something already on the floor
            raise EmergencyStop(
                "These products have collided.", dest, moves[0].position
            )
        return None
    if force:
        if len(moves) > 1:
            # collision between entities moving onto the same empty space
            raise EmergencyStop(
                "These products have collided.", dest, *[m.position for m in moves]
            )
        return moves[0]
    # move priority: down, right, left, up
    priority = [Direction.DOWN, Direction.RIGHT, Direction.LEFT, Direction.UP]
    return min(moves, key=lambda m: priority.index(m.direction))


def update_entities(
    state: State, all_moves: list[MoveEntity], output_pos: Position
) -> bool:
    """Move entities around and handle collisions.

    Return True if the correct product exits through the output conveyor.
    """
    ret = False

    # TODO: evaluate movements in the right order, to avoid spurious backups
    # should be: move entities off a space, then move entities on
    # forced movements should be evaluated first
    by_dest: dict[Position, tuple[list[MoveEntity], list[MoveEntity]]] = defaultdict(
        lambda: ([], [])
    )
    for move in all_moves:
        pos = move.entity.position
        if pos == output_pos and move.direction is Direction.DOWN:
            ret = True
            state.remove_entity(move.entity)
            continue
        # group MoveEntity by destination
        if not (0 <= move.dest.row < 7 and 0 <= move.dest.column < 6):
            raise EmergencyStop("Products cannot leave the factory.", pos)
        idx = 0 if move.force else 1
        by_dest[move.dest][idx].append(move)
    for dest, (forced, optional) in by_dest.items():
        print(f"Moves to {dest}:\n  {forced=}\n  {optional=}")
        for moves in (forced, optional):
            if not moves:
                continue
            module = state.get_module(dest)
            if module is None:
                accepted = handle_moves_to_empty(dest, state, moves)
            else:
                accepted = module.handle_moves(state, moves)
            if accepted is not None:
                state.move_entity(accepted.entity, accepted.direction)
                break
    # check for collisions
    for dest in by_dest:
        # either one of the moves should have succeeded, or whatever blocked
        # the moves should still be there
        assert dest in state.entities
        if len(state.entities[dest]) > 1:
            raise EmergencyStop("Unhandled entity collision", dest)

    return ret


def propagate_signals(state: State) -> None:
    for module in state.modules:
        if not module.on_rack:
            continue
        # commit pending signal values
        module.signals.update()


""" Notes:
* multimixers wired to themselves don't stay on after the other inputs go off

processing order:
1. increment time
2. update module state/signals - "too many active inputs" triggers before movement (stage 1)
3. move entities - entity collision error triggers before level pass
4. update module sense signals (scanner, sensor, cooker, etc.) (stage 2)
5. end level if product has exited at bottom of output
6. propagate signals, light up jacks and wires

before first tick, do last step with main input signals turned on
"""


def simulate_order(
    level: Level,
    solution: Solution,
    order_index: int,
    tick_limit: int = -1,
    debug: bool = False,
) -> int:
    """Return the number of ticks the order took to complete."""
    if debug:
        print(solution)
    state = State.from_solution(level, solution, order_index)

    main_input = next(m for m in state.modules if isinstance(m, MainInput))
    output = next(m for m in state.modules if isinstance(m, Output))

    time = 0
    successful_output = False
    try:
        main_input.zeroth_tick(state)
        propagate_signals(state)
        if debug:
            print(f"Tick {time}:")
            state.dump(indent="  ")
        while True:
            time += 1
            actions = update_modules(state, stage=1)
            successful_output |= update_entities(state, actions, output.floor_position)
            update_modules(state, stage=2)
            # keep simulating until all entities are removed
            if successful_output and not state.entities:
                return time
            propagate_signals(state)
            # pause here in single-step mode
            if debug:
                print(f"Tick {time}:")
                state.dump(indent="  ")
            if tick_limit != -1 and time > tick_limit:
                raise EmergencyStop("Tick limit reached.", Position(-1, -1))
    except EmergencyStop as e:
        # annotate exception with the current time
        e.time = time
        print(f"\n! EMERGENCY STOP !\nTick {time}:")
        state.dump(indent="  ")
        raise

    assert False


def simulate_solution(level: Level, solution: Solution) -> int:
    """Return the max number of ticks any order took to complete."""
    max_time = 0
    for order_index in range(len(level)):
        max_time = max(simulate_order(level, solution, order_index), max_time)
    return max_time
