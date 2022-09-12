import io
from pathlib import Path

import pytest
from foodcourt_sim import read_solution, write_solution

solutions_dir = Path(__file__).parent / "solutions"

SOLUTION_FILES = list(solutions_dir.glob("*/*.solution"))


@pytest.fixture(
    params=SOLUTION_FILES,
    ids=[f"{path.parent.name}-{path.stem}" for path in SOLUTION_FILES],
)
def raw_solution(request):
    with open(solutions_dir / request.param, "rb") as f:
        raw = f.read()
    return raw


def test_check(raw_solution):  # pylint: disable=redefined-outer-name
    solution = read_solution(raw_solution)[0]
    solution.check()


def test_roundtrip(raw_solution):  # pylint: disable=redefined-outer-name
    stream = io.BytesIO(raw_solution)
    solution_1 = read_solution(stream)[0]
    stream.seek(0)
    stream.truncate(0)
    write_solution(stream, solution_1)
    raw_2 = stream.getvalue()
    assert raw_solution == raw_2, "round-trip from bytes to Solution to bytes failed"
    stream.seek(0)
    solution_2 = read_solution(stream)[0]
    assert (
        solution_1 == solution_2
    ), "round-trip from Solution to bytes to Solution failed"
