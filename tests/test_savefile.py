import io
from pathlib import Path

import pytest
from foodcourt_sim.savefile import read_solution, write_solution

solutions_dir = Path(__file__).parent / "solutions"

SOLUTION_FILES = [path.name for path in solutions_dir.glob("*.solution")]


@pytest.fixture(scope="module", params=SOLUTION_FILES)
def raw_solution(request):
    with open(solutions_dir / request.param, "rb") as f:
        raw = f.read()
    return raw


def test_check(raw_solution):  # pylint: disable=redefined-outer-name
    solution = read_solution(raw_solution)[0]
    solution.check()


def test_roundtrip(raw_solution):  # pylint: disable=redefined-outer-name
    stream = io.BytesIO(raw_solution)
    solution_1, _ = read_solution(stream)
    stream.seek(0)
    stream.truncate(0)
    write_solution(stream, solution_1)
    raw_2 = stream.getvalue()
    assert raw_solution == raw_2, "round-trip from bytes to Solution to bytes failed"
    stream.seek(0)
    solution_2, _ = read_solution(stream)
    assert (
        solution_1 == solution_2
    ), "round-trip from Solution to bytes to Solution failed"
