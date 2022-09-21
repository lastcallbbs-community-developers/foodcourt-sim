from __future__ import annotations

import logging
from collections import OrderedDict, defaultdict, deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from . import logger
from .enums import JackDirection
from .errors import (
    EmergencyStop,
    InternalSimulationError,
    InvalidSolutionError,
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
    "Metrics",
    "simulate_order",
    "simulate_solution",
]


class LoggingContext:
    def __init__(self, logger_, level=None, handler=None, close=True):
        self.logger = logger_
        self.level = level
        self.handler = handler
        self.close = close

    def __enter__(self):
        if self.level is not None:
            # pylint: disable-next=attribute-defined-outside-init
            self.old_level = self.logger.level
            self.logger.setLevel(self.level)
        if self.handler:
            self.logger.addHandler(self.handler)

    def __exit__(self, et, ev, tb):
        if self.level is not None:
            self.logger.setLevel(self.old_level)
        if self.handler:
            self.logger.removeHandler(self.handler)
        if self.handler and self.close:
            self.handler.close()
        # implicit return of None => don't swallow exceptions


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

    time: int = 0
    # whether the target product has been sent to the output
    successful_output: bool = False

    def __post_init__(self) -> None:
        self._modules_by_pos = {
            module.floor_position: module for module in self.modules if module.on_floor
        }

    @classmethod
    def from_solution(cls, solution: Solution, order_index: int) -> State:
        modules = [m.copy(solution.level) for m in solution.modules]
        # build wire map
        wire_map = {}
        for wire in solution.wires:
            module_1 = modules[wire.module_1]
            module_2 = modules[wire.module_2]
            wire_map[module_1, wire.jack_1] = (module_2, wire.jack_2)
            wire_map[module_2, wire.jack_2] = (module_1, wire.jack_1)
        return cls(solution.level, modules, wire_map, order_index)

    @property
    def order_signals(self) -> tuple[bool, ...]:
        return self.level.order_signals[self.order_index]

    def dump(self) -> tuple[Any, ...]:
        """Return a hashable object representing the current simulation state.
        Used for detecting deadlocks and cycles.
        """
        module_states = []
        for module in self.modules:
            module_state = module.dump_state()
            if module_state:
                module_states.append(module_state)
        entity_states: dict[int, tuple[Any, ...]] = {}
        for entities in self.entities.values():
            for entity in entities:
                entity_states[id(entity)] = entity.dump_state()
        return (
            tuple(module_states),
            tuple(sorted(entity_states.items())),
            self.successful_output,
        )

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

    def debug_log(self) -> None:
        """Pretty-print the simulation state to the debug logger."""
        if not logger.isEnabledFor(logging.DEBUG):
            return
        logger.debug("Tick %d:", self.time)
        for module in sorted(
            self.modules, key=lambda m: (-m.rack_position.row, m.rack_position.column)
        ):
            if not module.on_rack:
                continue
            logger.debug(
                "  %s @ %s: %s",
                module.id.name,
                module.rack_position,
                module.debug_str(),
            )
            for i, (jack, value) in enumerate(zip(module.jacks, module.signals.values)):
                if not value:
                    continue
                if (module, i) not in self.wire_map:
                    continue
                if jack.direction is JackDirection.OUT:
                    logger.debug("    %s >", jack.name)
                else:
                    logger.debug("    > %s", jack.name)
        for pos, entities in sorted(
            self.entities.items(), key=lambda x: (-x[0].row, x[0].column)
        ):
            logger.debug("  %s:", pos)
            for entity in entities:
                logger.debug("    %s", entity)


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

    Uses a custom implementation of Tarjan's SCC algorithm, using Nuutila's
    modification. This produces the components in topological order.
    """
    if len(all_moves) == 1:
        return [{all_moves[0].dest}]

    dests = set()
    vertices: set[Position] = set()
    edges: dict[Position, list[Position]] = defaultdict(list)

    for move in all_moves:
        dests.add(move.dest)
        vertices.add(move.source)
        vertices.add(move.dest)
        edges[move.source].append(move.dest)

    # Nuutila's improved algorithm 1; pseudocode from Nuutila & Soisalon-Soininen 1994
    next_index = 0
    S: deque[Position] = deque()

    index: dict[Position, int] = {}
    root: dict[Position, Position] = {}
    in_component: dict[Position, bool] = {}

    components: list[set[Position]] = []

    def visit(v: Position) -> None:
        nonlocal next_index
        # keep track of when we entered visit with this node
        index[v] = next_index
        next_index += 1

        root[v] = v
        in_component[v] = False

        if v in edges:
            for w in edges[v]:
                if w not in index:
                    visit(w)
                if not in_component[w]:
                    root[v] = min(root[v], root[w], key=index.__getitem__)

        if root[v] == v:
            in_component[v] = True
            scc = set()
            if v in dests:
                scc.add(v)
            while S and index[S[-1]] > index[v]:
                w = S.pop()
                in_component[w] = True
                if w in dests:
                    scc.add(w)
            components.append(scc)
        else:
            S.append(v)

    for v in dests:
        if v not in index:
            visit(v)

    return components


def check_order(dest_order: list[set[Position]], all_moves: list[MoveEntity]) -> None:
    """Check that a move order is correct."""

    if not dest_order:
        return

    prev_dests: set[Position] = set()
    for dests in dest_order:
        prev_dests.update(dests)
        for dest in dests:
            # there can't be any moves that come after the current group whose source is dest
            for i, m in enumerate(all_moves):
                if m.dest in prev_dests:
                    continue
                assert (
                    m.source != dest
                ), f"check_order failed, {dests=}, move {i}: {m.source} -> {m.dest}"

    assert prev_dests == {
        m.dest for m in all_moves
    }, "check_order failed: missing some dests"


def resolve_movement(
    state: State,
    dest: Position,
    moves: list[MoveEntity],
) -> None:
    forced = [m for m in moves if m.force]
    optional = [m for m in moves if not m.force]
    logger.debug("Moves to %s:", dest)
    if forced:
        logger.debug("  forced=%s", forced)
    if optional:
        logger.debug("  optional=%s", optional)
    # check for forced collisions
    if len(forced) > 1:
        raise EmergencyStop(
            "These products have collided.", dest, *(m.source for m in forced)
        )
    for move_group in (forced, optional):
        if not move_group:
            continue
        module = state.get_module(dest)
        if module is None:
            accepted = handle_moves_to_empty(dest, state, move_group)
        else:
            accepted = module.handle_moves(state, move_group)
        if len(forced) + len(optional) > 1 or accepted is None:
            logger.debug("    accepted: %s", accepted)
        if accepted is not None:
            state.move_entity(accepted.entity, accepted.direction)
            # don't need to try next move group
            break


def resolve_loop(
    state: State,
    dests: set[Position],
    by_dest: dict[Position, list[MoveEntity]],
    loop_moves: list[MoveEntity],
) -> None:
    assert len(set(m.dest for m in loop_moves)) == len(dests)
    accepted_moves = []
    # For each position, see if the move that would be accepted will
    # keep the entity in the loop. If true for all positions, then all
    # moves will be performed, else none will.
    do_moves = True
    logger.debug("*** Loop detected at %s ***", dests)
    for dest in dests:
        forced = [m for m in by_dest[dest] if m.force]
        optional = [m for m in by_dest[dest] if not m.force]
        logger.debug("Moves to %s:", dest)
        if forced:
            logger.debug("  forced=%s", forced)
        if optional:
            logger.debug("  optional=%s", optional)
        # check for forced collisions
        if len(forced) > 1:
            raise EmergencyStop(
                "These products have collided.", dest, *(m.source for m in forced)
            )
        for move_group in (forced, optional):
            if not move_group:
                continue
            module = state.get_module(dest)
            assert module is not None, "impossible move off an empty space"
            accepted = module.handle_moves(
                state, move_group, ignore_collisions=True, dry_run=True
            )
            if len(forced) + len(optional) > 1 or accepted is None:
                logger.debug("    accepted: %s", accepted)
            if accepted not in loop_moves:
                do_moves = False
                break
            accepted_moves.append(accepted)
            if accepted is not None:
                # don't need to try next move group
                break
    if do_moves:
        assert sorted(accepted_moves) == sorted(
            loop_moves
        ), "accepted_moves doesn't match loop_moves"
        for move in accepted_moves:
            assert module is not None
            accepted = module.handle_moves(state, [move], ignore_collisions=True)
            assert accepted is move
            state.move_entity(move.entity, move.direction)


def move_entities(
    state: State, all_moves: list[MoveEntity], output_pos: Position
) -> None:
    """Move entities around and handle collisions."""
    by_dest: dict[Position, list[MoveEntity]] = defaultdict(list)

    to_discard: list[MoveEntity] = []
    for move in all_moves:
        if move.source == output_pos and move.direction is Direction.DOWN:
            state.successful_output = True
            state.remove_entity(move.entity)
            to_discard.append(move)
            continue
        if not (0 <= move.dest.row < 7 and 0 <= move.dest.column < 6):
            raise EmergencyStop(
                "Products cannot leave the factory.", move.source, move.dest
            )
        # group moves by destination
        by_dest[move.dest].append(move)
    for move in to_discard:
        all_moves.remove(move)

    order = order_moves(all_moves)
    # check_order(order, all_moves)
    for dests in order:
        if not dests:
            continue
        if len(dests) == 1:
            # single destination, not a loop
            dest = next(iter(dests))
            resolve_movement(state, dest, by_dest[dest])
        else:
            # entity movements make a closed loop
            loop_moves = [m for m in all_moves if m.dest in dests and m.source in dests]
            resolve_loop(state, dests, by_dest, loop_moves)

    # check for collisions
    for dest in by_dest:
        # either one of the moves should have succeeded, or whatever blocked
        # the moves should still be there
        assert dest in state.entities
        if len(state.entities[dest]) > 1:
            raise InternalSimulationError("Unhandled entity collision", dest)


def propagate_signals(state: State) -> None:
    for module in state.modules:
        if not module.jacks:
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


# maximum length of a cycle to detect (keeps memory usage bounded)
_MAX_CYCLE_LENGTH = 1000


def simulate_order(
    solution: Solution,
    order_index: int,
    time_limit: int = -1,
    debug: bool = False,
) -> State:
    """Return the number of ticks the order took to complete."""
    kwargs = {}
    if not logger.isEnabledFor(logging.DEBUG) and debug:
        # set logging level to DEBUG if it's not already enabled
        kwargs["level"] = logging.DEBUG
    with LoggingContext(logger, **kwargs):  # type: ignore
        logger.debug("%s", solution)
        state = State.from_solution(solution, order_index)
        seen_states: OrderedDict[tuple[Any, ...], int] = OrderedDict()

        main_input = next(m for m in state.modules if isinstance(m, MainInput))
        output = next(m for m in state.modules if isinstance(m, Output))

        try:
            try:
                main_input.zeroth_tick(state)
                propagate_signals(state)
                state.debug_log()
                while True:
                    state.time += 1
                    moves = []
                    for module in state.modules:
                        moves.extend(module.tick(state))
                    move_entities(state, moves, output.floor_position)
                    for module in state.modules:
                        module.update_signals(state)
                    # keep simulating until all entities are removed
                    if state.successful_output and not state.entities:
                        return state
                    propagate_signals(state)
                    # pause here in single-step mode
                    state.debug_log()
                    state_key = state.dump()
                    if state_key in seen_states:
                        raise TimeLimitExceeded(
                            loop=(seen_states[state_key], state.time)
                        )
                    seen_states[state_key] = state.time
                    if len(seen_states) > _MAX_CYCLE_LENGTH:
                        seen_states.popitem(last=False)
                    if time_limit != -1 and state.time >= time_limit:
                        raise TimeLimitExceeded()
            except AssertionError as e:
                # reraise assertion errors as InternalSimulationErrors
                raise InternalSimulationError(str(e)) from e
        except SimulationError as e:
            # annotate error with the current time
            e.time = state.time
            e.order = state.order_index
            if isinstance(e, EmergencyStop):
                desc = "*** EMERGENCY STOP ***"
            elif isinstance(e, InternalSimulationError):
                desc = "*** INTERNAL SIMULATION ERROR ***"
            else:
                desc = "*** SIMULATION ERROR ***"
            logger.debug(desc)
            if not isinstance(e, TimeLimitExceeded):
                state.debug_log()
                logger.debug("", exc_info=e)
            raise

    assert False


@dataclass
class Metrics:
    cost: int
    max_time: int
    total_time: int
    num_wires: int

    def __str__(self) -> str:
        return f"{self.max_time}T/{self.cost}k/{self.total_time}S/{self.num_wires}W"


def simulate_solution(
    solution: Solution, time_limit: int = -1, debug: bool = False
) -> Metrics:
    if time_limit == -1 and solution.solved:
        time_limit = solution.time
    times = []
    for order_index in range(len(solution.level.order_signals)):
        times.append(
            simulate_order(
                solution, order_index, time_limit=time_limit, debug=debug
            ).time
        )
    max_time = max(times)
    if solution.solved and max_time > solution.time:
        logger.warning(
            '%s, "%s": evaluated time (%d) doesn\'t match stored time (%d)',
            solution.level.name,
            solution.name,
            max_time,
            solution.time,
        )
    return Metrics(
        cost=solution.cost,
        max_time=max_time,
        total_time=sum(times),
        num_wires=len(solution.wires),
    )
