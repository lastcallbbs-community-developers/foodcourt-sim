import io
from pathlib import Path

import pytest
from foodcourt_sim.errors import InvalidSolutionError
from foodcourt_sim.savefile import (
    dump_solution,
    read_solution,
    read_solutions,
    write_solution,
)

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
    solution = read_solution(raw_solution)
    solution.check()


def test_check_illegal():
    solution = read_solution(solutions_dir / "wine-oclock-illegal.solution")
    with pytest.raises(InvalidSolutionError):
        solution.check()


def test_roundtrip(raw_solution):  # pylint: disable=redefined-outer-name
    stream = io.BytesIO(raw_solution)
    solution_1 = read_solution(stream)
    stream.seek(0)
    stream.truncate(0)
    write_solution(stream, solution_1)
    raw_2 = stream.getvalue()
    assert raw_solution == raw_2, "round-trip from bytes to Solution to bytes failed"
    stream.seek(0)
    solution_2 = read_solution(stream)
    assert (
        solution_1 == solution_2
    ), "round-trip from Solution to bytes to Solution failed"


def test_concat():
    solution_1 = read_solution(solutions_dir / "yut23/2twelve-1.solution")
    solution_2 = read_solution(solutions_dir / "yut23/bellys-1.solution")

    stream = io.BytesIO()
    solutions = list(read_solutions(stream))
    assert len(solutions) == 0

    stream = io.BytesIO()
    write_solution(stream, solution_1)
    stream.seek(0)
    solutions = list(read_solutions(stream))
    assert len(solutions) == 1
    assert solutions[0] == solution_1

    stream = io.BytesIO()
    write_solution(stream, solution_1)
    write_solution(stream, solution_2)
    stream.seek(0)
    solutions = list(read_solutions(stream))
    assert len(solutions) == 2
    assert solutions[0] == solution_1
    assert solutions[1] == solution_2


def test_normalize():
    orig = read_solution(solutions_dir / "yut23/mr.-chilly-1.solution")
    dup = read_solution(solutions_dir / "yut23/mr.-chilly-1-duplicate.solution")
    # discard the solution names
    orig.name = ""
    dup.name = ""
    assert orig != dup

    norm_orig = orig.normalize()
    norm_dup = dup.normalize()
    norm_orig.name = ""
    norm_dup.name = ""
    assert norm_orig == norm_dup, "normalized solutions differ"

    assert dump_solution(norm_orig) == dump_solution(
        norm_dup
    ), "exported normalized solutions differ"


def test_normalize_idem(raw_solution):  # pylint: disable=redefined-outer-name
    orig = read_solution(raw_solution)
    norm_1 = orig.normalize()
    norm_2 = norm_1.normalize()
    assert norm_1 == norm_2, "Solution.normalize() is not idempotent"
