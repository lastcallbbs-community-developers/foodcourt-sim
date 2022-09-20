#!/usr/bin/env python3

import argparse
import base64
import dataclasses
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, BinaryIO, Optional, Union

from . import logger
from .errors import (
    EmergencyStop,
    InternalSimulationError,
    InvalidSolutionError,
    SimulationError,
    TimeLimitExceeded,
)
from .levels import LEVELS
from .models import Solution
from .savefile import dump_solution, read_solution, read_solutions
from .simulator import Metrics, simulate_solution

REPORT_MESSAGE = "Please contact @yut23#9382 on the Zachtronics discord or open an issue at https://github.com/lastcallbbs-community-developers/foodcourt-sim/issues/new."

EXIT_CODES = {
    EmergencyStop: 1,
    TimeLimitExceeded: 2,
    InvalidSolutionError: 3,
    InternalSimulationError: 127,
}

# configure logging
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)


def get_exit_code(ex: Exception) -> int:
    for error_class, code in EXIT_CODES.items():
        if isinstance(ex, error_class):
            return code
    return 255


def to_json(solution: Optional[Solution], /, **kwargs: Any) -> dict[str, Any]:
    result = {}
    if solution is not None:
        result.update(
            dict(
                level_number=solution.level.number,
                level_name=solution.level.name,
                level_slug=solution.level.internal_name,
                solution_name=solution.name,
                filename=solution.filename,
                marked_solved=solution.solved,
            )
        )
    result.update(**kwargs)
    return result


def metrics_to_json(
    solution: Solution, metrics: Metrics, include_solution: bool
) -> dict[str, Any]:
    kwargs = dataclasses.asdict(metrics)
    if include_solution:
        kwargs["solution"] = base64.b64encode(
            dump_solution(solution.normalize())
        ).decode()
    return to_json(solution, is_correct=True, **kwargs)


def error_to_json(
    solution: Optional[Solution], ex: Exception, **kwargs: Any
) -> dict[str, Any]:
    return to_json(
        solution,
        is_correct=False,
        error_type=type(ex).__name__,
        error_message=str(ex),
        **kwargs,
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
        "--include-solution",
        action="store_true",
        help="Include the normalized solution in the JSON output",
    )
    parser_validate_all.add_argument(
        "--json", action="store_true", help="Use JSON output mode"
    )

    def run_validate_all(args: argparse.Namespace) -> int:
        """Returns an exit code."""
        solutions = defaultdict(list)
        name_width = 0
        for path in args.solution_dir.glob("*.solution"):
            try:
                solution = read_solution(path)
            except InvalidSolutionError:
                continue
            if not solution.solved:
                continue
            solutions[solution.level.id].append(solution)
            name_width = max(name_width, len(solution.name))
        json_results = []
        exit_code = 0
        for level in LEVELS:
            if not solutions[level.id]:
                continue
            if not args.json:
                print(level.name)
            name_width = max(len(solution.name) for solution in solutions[level.id])
            for solution in sorted(solutions[level.id], key=lambda s: s.filename or ""):
                try:
                    solution.check()
                    metrics = simulate_solution(solution)
                except InvalidSolutionError as ex:
                    json_results.append(error_to_json(solution, ex))
                except SimulationError as ex:
                    json_results.append(error_to_json(solution, ex))
                    exit_code = get_exit_code(ex)
                else:
                    json_results.append(
                        metrics_to_json(solution, metrics, args.include_solution)
                    )
                if not args.json:
                    print(f"  {solution.name+':':{name_width+1}s} ", end="")
                    if json_results[-1]["is_correct"]:
                        print(metrics)
                    else:
                        print(f"Error: {json_results[-1]['error_message']}")
        if args.json:
            print(json.dumps(json_results))
        bad_results = [result for result in json_results if not result["is_correct"]]
        if bad_results:
            logger.error(
                "Unexpected simulation error%s occurred for:",
                "" if len(bad_results) == 1 else "s",
            )
            for result in bad_results:
                logger.error("  %s: %s", result["filename"], result["error_message"])
            logger.error(REPORT_MESSAGE)
        return exit_code

    parser_validate_all.set_defaults(func=run_validate_all)

    parser_simulate = subparsers.add_parser(
        "simulate", help="Simulate one or more solution files (may be unsolved)"
    )
    parser_simulate.add_argument(
        "solution_file",
        nargs=argparse.ONE_OR_MORE,
        type=str,
        help="Solution file path, or - to read from stdin",
    )
    parser_simulate.add_argument(
        "--time-limit",
        type=int,
        default=1000,
        help="Maximum number of ticks to run unsolved solutions before halting (default is 1000, pass -1 for no limit)",
    )
    parser_simulate.add_argument(
        "--include-solution",
        action="store_true",
        help="Include the normalized solution in the JSON output",
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
        if args.debug:
            logger.setLevel(logging.DEBUG)
        solutions: list[Solution] = []
        results = []
        for solution_file in args.solution_file:
            input_source: Union[Path, BinaryIO]
            if solution_file == "-":
                input_source = sys.stdin.buffer
            else:
                input_source = Path(solution_file)
            try:
                solutions.extend(read_solutions(input_source))
            except InvalidSolutionError as ex:
                if args.json:
                    print(json.dumps([error_to_json(None, ex, filename=solution_file)]))
                else:
                    print(f"Invalid solution file: {ex}")
                return get_exit_code(ex)
        exit_code = 0
        nagged_to_report = False
        for i, solution in enumerate(solutions):
            if solution.solved:
                time_limit = solution.time
            else:
                time_limit = args.time_limit
            if not args.json:
                if i != 0:
                    print()
                print(f'{solution.level.name} ("{solution.name}")')
            try:
                solution.check()
                metrics = simulate_solution(solution, time_limit=time_limit)
            except (SimulationError, InvalidSolutionError) as ex:
                results.append(error_to_json(solution, ex))
                exit_code = max(exit_code, get_exit_code(ex))
                if isinstance(ex, InternalSimulationError):
                    logger.error("Internal simulation error encountered: %s", ex)
                    if not nagged_to_report:
                        logger.error(REPORT_MESSAGE)
                        nagged_to_report = True
                elif solution.solved:
                    logger.error(
                        "Simulation error encountered in solved solution: %s", ex
                    )
                    if not nagged_to_report:
                        logger.error(REPORT_MESSAGE)
                        nagged_to_report = True
                if not args.json:
                    print(f"Simulation failed:\n{ex}")
            else:
                results.append(
                    metrics_to_json(solution, metrics, args.include_solution)
                )
            if not args.json and results[-1]["is_correct"]:
                for field in dataclasses.fields(metrics):
                    print(field.name, "=", getattr(metrics, field.name))
                if not solution.solved:
                    print(
                        "Note: this solution was not marked as solved in-game. If it doesn't actually work,"
                    )
                    print(REPORT_MESSAGE)
        if args.json:
            print(json.dumps(results))
        return exit_code

    parser_simulate.set_defaults(func=run_simulate)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
