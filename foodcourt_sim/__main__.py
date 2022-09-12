#!/usr/bin/env python3

import argparse
import dataclasses
import json
import sys
from pathlib import Path
from typing import Any

from .errors import EmergencyStop, InvalidSolutionError, TimeLimitExceeded
from .models import Solution
from .savefile import read_solution
from .simulator import Metrics, simulate_solution


def to_json(solution: Solution, metrics: Metrics) -> dict[str, Any]:
    return dict(
        level_number=solution.level.number,
        level_name=solution.level.name,
        level_slug=solution.level.internal_name,
        solution_name=solution.name,
        **dataclasses.asdict(metrics),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m foodcourt_sim",
        description="Simulate 20th Century Food Court solutions",
    )
    subparsers = parser.add_subparsers(required=True)

    parser_validate_all = subparsers.add_parser(
        "validate_all", help="Validate all solved solution files in a directory"
    )
    parser_validate_all.add_argument(
        "solution_dir",
        type=Path,
        help="Path to solution directory",
    )
    parser_validate_all.add_argument(
        "--json", action="store_true", help="Use JSON output mode"
    )

    def run_validate_all(args: argparse.Namespace) -> int:
        """Returns an exit code."""
        json_result = []
        solutions = []
        for path in args.solution_dir.glob("*.solution"):
            with path.open("rb") as f:
                solution = read_solution(f)
            solution.check()
            if not solution.solved:
                continue
            solutions.append(((solution.level.number, path.name), solution))
        solutions.sort()
        for _, solution in solutions:
            try:
                metrics = simulate_solution(solution)
            except (InvalidSolutionError, EmergencyStop, TimeLimitExceeded):
                continue
            if args.json:
                json_result.append(to_json(solution, metrics))
            else:
                print(f'{solution.level.name} ("{solution.name}"): {metrics}')
        if args.json:
            print(json.dumps(json_result))
        return 0

    parser_validate_all.set_defaults(func=run_validate_all)

    parser_validate = subparsers.add_parser(
        "validate", help="Validate a solution file (must already be solved)"
    )
    parser_validate.add_argument(
        "solution_file",
        type=argparse.FileType("rb"),
        help="Solution file path (or - for stdin)",
    )
    parser_validate.add_argument(
        "--json", action="store_true", help="Use JSON output mode"
    )

    def run_validate(args: argparse.Namespace) -> int:
        """Returns an exit code."""
        solution = read_solution(args.solution_file)
        solution.check()
        if not solution.solved:
            sys.stderr.write(
                "ERROR: the given solution has not been marked as solved in-game\n"
            )
            return 1
        metrics = simulate_solution(solution)
        if args.json:
            print(json.dumps([to_json(solution, metrics)]))
        else:
            print(f'{solution.level.name} ("{solution.name}")')
            for field in dataclasses.fields(metrics):
                print(field.name, "=", getattr(metrics, field.name))
        return 0

    parser_validate.set_defaults(func=run_validate)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
