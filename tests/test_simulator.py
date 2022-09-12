from pathlib import Path
from typing import Any

import pytest
from foodcourt_sim import read_solution, simulate_order
from foodcourt_sim.errors import EmergencyStop, TimeLimitExceeded
from foodcourt_sim.models import Position, Solution

solutions_dir = Path(__file__).parent / "solutions"

DEBUG = True


def pytest_generate_tests(metafunc):
    if metafunc.function not in (test_solved, test_unsolved):
        return
    # first entry is a sorting key
    entries: list[tuple[tuple[Any, ...], tuple[Solution, int], str]] = []
    for filepath in sorted(solutions_dir.glob("*/*.solution")):
        with open(filepath, "rb") as f:
            solution = read_solution(f)
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
    ticks = simulate_order(solution, order_index, time_limit=solution.time, debug=DEBUG)
    assert ticks <= solution.time


def test_unsolved(solution: Solution, order_index: int) -> None:
    assert not solution.solved
    try:
        simulate_order(solution, order_index, time_limit=100, debug=DEBUG)
    except (TimeLimitExceeded, EmergencyStop):
        pass


@pytest.mark.parametrize(
    "solution_name", [f"movement-testing-{n}.solution" for n in range(1, 9)]
)
def test_movement(solution_name: str) -> None:
    with open(solutions_dir / "yut23" / solution_name, "rb") as f:
        solution = read_solution(f)

    with pytest.raises(TimeLimitExceeded):
        simulate_order(solution, 0, time_limit=20, debug=DEBUG)


def test_loops() -> None:
    with open(solutions_dir / "yut23" / "loop-testing-1.solution", "rb") as f:
        solution = read_solution(f)

    ticks = simulate_order(solution, 0, time_limit=22, debug=DEBUG)
    assert ticks == 22

    with open(solutions_dir / "yut23" / "loop-testing-2.solution", "rb") as f:
        solution = read_solution(f)

    with pytest.raises(EmergencyStop) as excinfo:
        ticks = simulate_order(solution, 0, time_limit=12, debug=DEBUG)
    assert excinfo.value.message == "This product cannot be sliced."
    assert Position(3, 3) in excinfo.value.positions


def test_2twelve():
    with open(solutions_dir / "yut23" / "2twelve-1.solution", "rb") as f:
        solution = read_solution(f)

    ticks = simulate_order(solution, 1, time_limit=8, debug=DEBUG)
    assert ticks == 8
    ticks = simulate_order(solution, 0, time_limit=8, debug=DEBUG)
    assert ticks == 8
