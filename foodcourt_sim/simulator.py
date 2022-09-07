from typing import Optional

from .models import Action, Entity, EntityId, FinishLevel, Level, Solution, State
from .modules import MainInput, Output, TargetsFront, TargetsSelf

""" Notes:
* multimixers wired to themselves don't stay on after the other inputs go off

processing order:
1. increment time
2. update module state/signals - "too many active inputs" triggers before movement
3. move entities - entity collision error triggers before level pass
4. end level if product has exited at bottom of output
5. propagate signals, light up jacks and wires

before first tick, do step 5 with main input signals turned on
"""


def update_modules(state: State) -> list[Action]:
    entities_by_pos: dict[tuple[int, int], Entity] = {}
    for entity in state.entities:
        key = entity.position.astuple()
        assert key not in entities_by_pos, f"unhandled collision at {entity.position}"
        entities_by_pos[entity.position.astuple()] = entity

    actions = []
    # tick modules
    for module in state.modules:
        args = {}
        if isinstance(module, (TargetsSelf, TargetsFront)):
            key = module.target_pos().astuple()
            args["target"] = entities_by_pos.get(key, None)
        actions.extend(module.update(**args))
    return actions


def update_entities(state: State, actions: list[Action]) -> Optional[bool]:
    """Move entities around and handle collisions.

    If the correct product exits through the output conveyor and there are no
    remaining entities, return True.
    If there are remaining entities, return False.
    Otherwise, return None.
    """
    finished = False
    for action in actions:
        if isinstance(action, FinishLevel):
            finished = True
    if finished:
        return not state.entities
    return None


def propagate_signals(state: State) -> None:
    pass


def simulate_order(level: Level, solution: Solution, order_index: int) -> bool:
    target_product = level.order_products[order_index]
    state = State.from_solution(level, solution, order_index)

    main_input = next(m for m in state.modules if isinstance(m, MainInput))
    output = next(m for m in state.modules if isinstance(m, Output))
    tray = Entity(EntityId.TRAY, position=main_input.floor_position.copy())
    state.add_entity(tray)

    time = 0
    # TODO: main input signals
    propagate_signals(state)
    while True:
        time += 1
        # pause here in single-step mode
        actions = update_modules(state)
        result = update_entities(state, actions)
        if result is not None:
            return result
        propagate_signals(state)

    assert False


def simulate_solution(level: Level, solution: Solution) -> bool:
    bad_orders = []
    for order_index in range(len(level)):
        result = simulate_order(level, solution, order_index)
        if not result:
            bad_orders.append(order_index)
    return not bad_orders
