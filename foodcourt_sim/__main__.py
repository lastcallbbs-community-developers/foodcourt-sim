#!/usr/bin/env python3

import argparse
import dataclasses
import json
import sys

from .savefile import read_solution
from .simulator import simulate_solution


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m foodcourt_sim",
        description="Simulate 20th Century Food Court solutions",
    )
    subparsers = parser.add_subparsers(required=True)

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
        level = solution.level
        solution.check()
        if not solution.solved:
            sys.stderr.write(
                "ERROR: the given solution has not been marked as solved in-game\n"
            )
            return 1
        metrics = simulate_solution(solution, time_limit=solution.time)
        json_result = [
            dict(
                level_number=level.number,
                level_name=level.name,
                level_slug=level.internal_name,
                solution_name=solution.name,
                **dataclasses.asdict(metrics),
            )
        ]
        if args.json:
            print(json.dumps(json_result))
        else:
            print(f'{level.name} ("{solution.name}")')
            for field in dataclasses.fields(metrics):
                print(field.name, "=", getattr(metrics, field.name))
        return 0

    parser_validate.set_defaults(func=run_validate)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
