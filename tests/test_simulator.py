from pathlib import Path
from typing import Any

import pytest
from foodcourt_sim import read_solution, simulate_order
from foodcourt_sim.errors import (
    EmergencyStop,
    InternalSimulationError,
    SimulationError,
    TimeLimitExceeded,
)
from foodcourt_sim.models import Position
from foodcourt_sim.solution import Solution

solutions_dir = Path(__file__).parent / "solutions"


def pytest_generate_tests(metafunc):
    if metafunc.function not in (test_solved, test_unsolved):
        return
    # first entry is a sorting key
    entries: list[tuple[tuple[Any, ...], tuple[Solution, int], str]] = []
    for filepath in sorted(solutions_dir.glob("*/*.solution")):
        solution = read_solution(filepath)
        if (metafunc.function is test_solved) != solution.solved:
            continue
        level = solution.level
        for i in range(len(level.order_signals)):
            entries.append(
                (
                    (filepath.parent.name, level.number, filepath.name, i),
                    (solution, i),
                    f"{filepath.parent.name}-{filepath.stem}-{i+1}",
                )
            )

    _, args, ids = zip(*sorted(entries))
    metafunc.parametrize(("solution", "order_index"), args, ids=ids)


def test_solved(solution: Solution, order_index: int) -> None:
    assert solution.solved
    error = False
    # run without debugging for speed, and only rerun with debugging if an error occurs
    try:
        ticks = simulate_order(solution, order_index, time_limit=solution.time).time
    except SimulationError:
        error = True
    if error:
        simulate_order(solution, order_index, time_limit=solution.time, debug=True)
    assert ticks <= solution.time


def test_unsolved(solution: Solution, order_index: int) -> None:
    assert not solution.solved
    error = False
    # run without debugging for speed, and only rerun with debugging if an unexpected
    # error occurs
    try:
        simulate_order(solution, order_index, time_limit=1000)
    except (TimeLimitExceeded, EmergencyStop):
        pass
    except InternalSimulationError:
        error = True
    if error:
        simulate_order(solution, order_index, time_limit=1000, debug=True)


@pytest.mark.parametrize(
    "solution_name", [f"movement-testing-{n}.solution" for n in range(1, 9)]
)
def test_movement(solution_name: str) -> None:
    solution = read_solution(solutions_dir / "yut23" / solution_name)
    with pytest.raises(TimeLimitExceeded) as excinfo:
        simulate_order(solution, 0, time_limit=20, debug=True)
    assert excinfo.value.time < 20


def test_loops() -> None:
    solution = read_solution(solutions_dir / "yut23" / "loop-testing-1.solution")
    ticks = simulate_order(solution, 0, time_limit=22, debug=True).time
    assert ticks == 22

    solution = read_solution(solutions_dir / "yut23" / "loop-testing-2.solution")
    with pytest.raises(EmergencyStop) as excinfo:
        simulate_order(solution, 0, time_limit=12, debug=True)
    assert excinfo.value.message == "Emergency stop: This product cannot be sliced."
    assert Position(3, 3) in excinfo.value.positions


def test_2twelve():
    solution = read_solution(solutions_dir / "yut23" / "2twelve-1.solution")
    state = simulate_order(solution, 1, time_limit=8, debug=True)
    assert state.time == 8
    state = simulate_order(solution, 0, time_limit=8, debug=True)
    assert state.time == 8
