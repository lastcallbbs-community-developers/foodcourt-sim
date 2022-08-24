#!/usr/bin/env python3

import io
import sys

from .savefile import read_solution, write_solution


def test_roundtrip(data: bytes) -> None:
    raw_1 = data
    stream = io.BytesIO(raw_1)
    solution_1, _ = read_solution(stream)
    stream.seek(0)
    stream.truncate(0)
    write_solution(stream, solution_1)
    raw_2 = stream.getvalue()
    assert raw_1 == raw_2, "round-trip from bytes to Solution to bytes failed"
    stream.seek(0)
    solution_2, _ = read_solution(stream)
    assert (
        solution_1 == solution_2
    ), "round-trip from Solution to bytes to Solution failed"


if __name__ == "__main__":
    with open(sys.argv[1], "rb") as f:
        raw = f.read()
    sol, level_ = read_solution(raw)
    sol.check(level_)

    test_roundtrip(raw)

    print(sol)
