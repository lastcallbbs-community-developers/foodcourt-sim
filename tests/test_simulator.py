from pathlib import Path

import pytest
from foodcourt_sim import BY_ID, read_solution, simulate_order
from foodcourt_sim.errors import EmergencyStop, TimeLimitExceeded
from foodcourt_sim.models import Position, Solution

solutions_dir = Path(__file__).parent / "solutions"


def pytest_generate_tests(metafunc):
    if metafunc.function not in (test_solved, test_unsolved):
        return
    entries: list[tuple[tuple[Solution, int], str]] = []
    for filepath in sorted(solutions_dir.glob("*.solution")):
        with open(filepath, "rb") as f:
            solution, level = read_solution(f)
        if (metafunc.function is test_solved) != solution.solved:
            continue
        for i in range(len(level.order_signals)):
            # if i != 0:
            #     continue
            entries.append(((solution, i), f"{filepath.stem}-{i+1}"))

    def sort_key(entry):
        sol = entry[0][0]
        return (BY_ID[sol.level_id].number, entry[0][1])

    args, ids = zip(*sorted(entries, key=sort_key))
    metafunc.parametrize(("solution", "order_index"), args, ids=ids)


def test_solved(solution: Solution, order_index: int) -> None:
    level = BY_ID[solution.level_id]
    assert solution.solved
    ticks = simulate_order(
        level, solution, order_index, time_limit=solution.time, debug=True
    )
    assert ticks <= solution.time


def test_unsolved(solution: Solution, order_index: int) -> None:
    level = BY_ID[solution.level_id]
    assert not solution.solved
    try:
        simulate_order(level, solution, order_index, time_limit=100, debug=True)
    except (TimeLimitExceeded, EmergencyStop):
        pass


@pytest.mark.parametrize(
    "solution_name", [f"movement-testing-{n}.solution" for n in range(1, 9)]
)
def test_movement(solution_name: str) -> None:
    with open(solutions_dir / solution_name, "rb") as f:
        solution, level = read_solution(f)

    with pytest.raises(TimeLimitExceeded):
        simulate_order(level, solution, 0, time_limit=20, debug=True)


def test_loops() -> None:
    with open(solutions_dir / "loop-testing-1.solution", "rb") as f:
        solution, level = read_solution(f)

    ticks = simulate_order(level, solution, 0, time_limit=22, debug=True)
    assert ticks == 22

    with open(solutions_dir / "loop-testing-2.solution", "rb") as f:
        solution, level = read_solution(f)

    with pytest.raises(EmergencyStop) as excinfo:
        ticks = simulate_order(level, solution, 0, time_limit=12, debug=True)
    assert excinfo.value.message == "This product cannot be sliced."
    assert Position(3, 3) in excinfo.value.positions


def test_2twelve():
    with open(solutions_dir / "2twelve-1.solution", "rb") as f:
        solution, level = read_solution(f)

    ticks = simulate_order(level, solution, 1, time_limit=8, debug=True)
    assert ticks == 8
    ticks = simulate_order(level, solution, 0, time_limit=8, debug=True)
    assert ticks == 8
