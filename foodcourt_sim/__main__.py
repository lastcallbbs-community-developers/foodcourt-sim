#!/usr/bin/env python3

import argparse
import dataclasses
import json
import sys
from pathlib import Path
from typing import Any

from .errors import (
    EmergencyStop,
    InternalSimulationError,
    InvalidSolutionError,
    SimulationError,
    TimeLimitExceeded,
)
from .models import Solution
from .savefile import read_solution
from .simulator import Metrics, simulate_solution

INTERNAL_ERROR_MESSAGE = """Internal simulation error encountered. Please open an issue at
https://github.com/lastcallbbs-community-developers/foodcourt-sim/issues/new
or contact yut23#9382 on the Zachtronics discord.
Extra details: {}
"""


def to_json(solution: Solution, **kwargs: Any) -> dict[str, Any]:
    return dict(
        level_number=solution.level.number,
        level_name=solution.level.name,
        level_slug=solution.level.internal_name,
        solution_name=solution.name,
        **kwargs,
    )


def metrics_to_json(solution: Solution, metrics: Metrics) -> dict[str, Any]:
    return to_json(solution, is_correct=True, **dataclasses.asdict(metrics))


def error_to_json(solution: Solution, ex: Exception) -> dict[str, Any]:
    return to_json(
        solution,
        is_correct=False,
        error_type=type(ex).__name__,
        error_message=str(ex),
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
            if not solution.solved:
                continue
            solutions.append(((solution.level.number, path.name), solution))
        solutions.sort()
        for (_, filename), solution in solutions:
            try:
                solution.check()
                metrics = simulate_solution(solution)
            except (InvalidSolutionError, EmergencyStop, TimeLimitExceeded) as ex:
                json_result.append(error_to_json(solution, ex))
                continue
            except InternalSimulationError as ex:
                sys.stderr.write(
                    INTERNAL_ERROR_MESSAGE.format(f"file={filename}; {ex}")
                )
                return 127
            json_result.append(metrics_to_json(solution, metrics))
            if not args.json:
                print(f'{solution.level.name} ("{solution.name}"): {metrics}')
        if args.json:
            print(json.dumps(json_result))
        return 0

    parser_validate_all.set_defaults(func=run_validate_all)

    parser_simulate = subparsers.add_parser(
        "simulate", help="Simulate a solution file (may be unsolved)"
    )
    parser_simulate.add_argument(
        "solution_file",
        type=argparse.FileType("rb"),
        help="Solution file path (or - for stdin)",
    )
    parser_simulate.add_argument(
        "--time-limit",
        type=int,
        default=1000,
        help="Maximum number of ticks to run each order before halting (default is 1000, pass -1 for no limit)",
    )
    output_group = parser_simulate.add_mutually_exclusive_group()
    output_group.add_argument(
        "--debug",
        action="store_true",
        help="Output lots of information about the simulation state while running",
    )
    output_group.add_argument(
        "--json", action="store_true", help="Use JSON output mode"
    )

    def run_simulate(args: argparse.Namespace) -> int:
        """Returns an exit code."""
        solution = read_solution(args.solution_file)
        if solution.solved and args.time_limit == -1:
            args.time_limit = solution.time
        exit_code = 0
        metrics = None
        if not args.json:
            print(f'{solution.level.name} ("{solution.name}")')
        try:
            solution.check()
            metrics = simulate_solution(
                solution, time_limit=args.time_limit, debug=args.debug
            )
        except (SimulationError, InvalidSolutionError) as ex:
            result = error_to_json(solution, ex)
            if isinstance(ex, EmergencyStop):
                exit_code = 1
            elif isinstance(ex, TimeLimitExceeded):
                exit_code = 2
            elif isinstance(ex, InvalidSolutionError):
                exit_code = 3
            elif isinstance(ex, InternalSimulationError):
                exit_code = 127
                sys.stderr.write(INTERNAL_ERROR_MESSAGE.format(str(ex)))
            if not args.json:
                print(f"Simulation failed:\n{ex}")
        else:
            result = metrics_to_json(solution, metrics)
        if args.json:
            print(json.dumps([result]))
        elif metrics is not None:
            for field in dataclasses.fields(metrics):
                print(field.name, "=", getattr(metrics, field.name))
        return exit_code

    parser_simulate.set_defaults(func=run_simulate)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
