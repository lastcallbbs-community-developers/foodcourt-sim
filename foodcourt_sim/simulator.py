from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

import networkx as nx

from .enums import JackDirection
from .errors import (
    EmergencyStop,
    InternalSimulationError,
    SimulationError,
    TimeLimitExceeded,
)
from .models import Direction, MoveEntity, Position
from .modules import MainInput, Output

if TYPE_CHECKING:
    from .entities import Entity
    from .levels import Level
    from .models import Solution, Wire
    from .modules import Module


__all__ = [
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
        for pos, entities in sorted(
            self.entities.items(), key=lambda x: (-x[0].row, x[0].column)
        ):
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
            raise EmergencyStop("These products have collided.", dest, moves[0].source)
        return None
    if force:
        if len(moves) > 1:
            # collision between entities moving onto the same empty space
            raise EmergencyStop(
                "These products have collided.", dest, *[m.source for m in moves]
            )
        return moves[0]
    # move priority: down, right, left, up
    priority = [Direction.DOWN, Direction.RIGHT, Direction.LEFT, Direction.UP]
    return min(moves, key=lambda m: priority.index(m.direction))


def order_moves(all_moves: list[MoveEntity]) -> list[set[Position]]:
    """
    Return a list of groups of destination positions in the order their movements
    should be evaluated.
    """

    """General approach:
    1. Construct DAGs from groups of potentially conflicting movements, where `dest` of
       one or more MoveEntity is `position` of another MoveEntity.
    2. Get the topological ordering of the DAGs.
    """

    graph = nx.DiGraph()
    dests = set()
    for move in all_moves:
        dests.add(move.dest)
        graph.add_edge(move.dest, move.source)

    # condense any loops to a single node
    cond = nx.condensation(graph)

    # get the topological order of the condensed graph
    return [
        {pos for pos in cond.nodes[n]["members"] if pos in dests}
        for n in nx.topological_sort(cond)
    ]


def resolve_movement(
    state: State,
    dest: Position,
    moves: list[MoveEntity],
    debug: bool,
) -> None:
    forced = [m for m in moves if m.force]
    optional = [m for m in moves if not m.force]
    if debug:
        print(f"Moves to {dest}:")
        if forced:
            print(f"  {forced=}")
        if optional:
            print(f"  {optional=}")
    for move_group in (forced, optional):
        if not move_group:
            continue
        module = state.get_module(dest)
        if module is None:
            accepted = handle_moves_to_empty(dest, state, move_group)
        else:
            accepted = module.handle_moves(state, move_group)
        if debug and (len(forced) + len(optional) > 1 or accepted is None):
            print(f"    accepted: {accepted}")
        if accepted is not None:
            state.move_entity(accepted.entity, accepted.direction)
            # don't need to try next move group
            break
    assert len(forced) <= 1


def resolve_loop(
    state: State,
    dests: set[Position],
    by_dest: dict[Position, list[MoveEntity]],
    loop_moves: list[MoveEntity],
    debug: bool,
) -> None:
    assert len(set(m.dest for m in loop_moves)) == len(dests)
    accepted_moves = []
    # For each position, see if the move that would be accepted will
    # keep the entity in the loop. If true for all positions, then all
    # moves will be performed, else none will.
    do_loop = True
    if debug:
        print(f"\n*** Loop detected at {dests} ***")
    for dest in dests:
        forced = [m for m in by_dest[dest] if m.force]
        optional = [m for m in by_dest[dest] if not m.force]
        if debug:
            print(f"Moves to {dest}:")
            if forced:
                print(f"  {forced=}")
            if optional:
                print(f"  {optional=}")
        for move_group in (forced, optional):
            if not move_group:
                continue
            module = state.get_module(dest)
            assert module is not None, "impossible move off an empty space"
            accepted = module.handle_moves(
                state, move_group, ignore_collisions=True, dry_run=True
            )
            if debug and (len(forced) + len(optional) > 1 or accepted is None):
                print(f"    accepted: {accepted}")
            if accepted not in loop_moves:
                do_loop = False
                break
            accepted_moves.append(accepted)
            if accepted is not None:
                # don't need to try next move group
                break
        assert len(forced) <= 1
    if do_loop:
        assert sorted(accepted_moves) == sorted(
            loop_moves
        ), "accepted_moves doesn't match loop_moves"
        for move in accepted_moves:
            assert module is not None
            accepted = module.handle_moves(state, [move], ignore_collisions=True)
            assert accepted is move
            state.move_entity(move.entity, move.direction)


def move_entities(
    state: State, all_moves: list[MoveEntity], output_pos: Position, debug: bool
) -> bool:
    """Move entities around and handle collisions.

    Return True if the correct product exits through the output conveyor.
    """
    ret = False

    by_dest: dict[Position, list[MoveEntity]] = defaultdict(list)

    for move in all_moves:
        if move.source == output_pos and move.direction is Direction.DOWN:
            ret = True
            state.remove_entity(move.entity)
            continue
        if not (0 <= move.dest.row < 7 and 0 <= move.dest.column < 6):
            raise EmergencyStop(
                "Products cannot leave the factory.", move.source, move.dest
            )
        # group moves by destination
        by_dest[move.dest].append(move)

    order = order_moves([m for m in all_moves if m.dest in by_dest])
    for dests in order:
        if not dests:
            continue
        if len(dests) == 1:
            # single destination, not a loop
            dest = next(iter(dests))
            resolve_movement(state, dest, by_dest[dest], debug)
        else:
            # entity movements make a closed loop
            loop_moves = [m for m in all_moves if m.dest in dests and m.source in dests]
            resolve_loop(state, dests, by_dest, loop_moves, debug)

    # check for collisions
    for dest in by_dest:
        # either one of the moves should have succeeded, or whatever blocked
        # the moves should still be there
        assert dest in state.entities
        if len(state.entities[dest]) > 1:
            raise InternalSimulationError("Unhandled entity collision", dest)

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
    time_limit: int = -1,
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
        try:
            main_input.zeroth_tick(state)
            propagate_signals(state)
            if debug:
                print(f"Tick {time}:")
                state.dump(indent="  ")
            while True:
                time += 1
                moves = update_modules(state, stage=1)
                successful_output |= move_entities(
                    state, moves, output.floor_position, debug=debug
                )
                update_modules(state, stage=2)
                # keep simulating until all entities are removed
                if successful_output and not state.entities:
                    return time
                propagate_signals(state)
                # pause here in single-step mode
                if debug:
                    print(f"Tick {time}:")
                    state.dump(indent="  ")
                if time_limit != -1 and time >= time_limit:
                    raise TimeLimitExceeded()
        except AssertionError as e:
            # reraise assertion errors as InternalSimulationErrors
            raise InternalSimulationError(str(e)) from e
    except SimulationError as e:
        # annotate error with the current time
        e.time = time
        if debug:
            if isinstance(e, EmergencyStop):
                desc = "*** EMERGENCY STOP ***"
            elif isinstance(e, InternalSimulationError):
                desc = "*** INTERNAL SIMULATION ERROR ***"
            else:
                desc = "*** SIMULATION ERROR ***"
            print(f"\n{desc}\nTick {time}:")
            state.dump(indent="  ")
        raise

    assert False


def simulate_solution(level: Level, solution: Solution) -> int:
    """Return the max number of ticks any order took to complete."""
    max_time = 0
    for order_index in range(len(level)):
        max_time = max(simulate_order(level, solution, order_index), max_time)
    return max_time
