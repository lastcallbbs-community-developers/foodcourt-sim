#!/usr/bin/env python3

import argparse
import base64
import dataclasses
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, BinaryIO, Union

from . import logger
from .errors import InternalSimulationError, InvalidSolutionError, SimulationError
from .levels import LEVELS
from .savefile import dump_solution, read_solution, read_solutions
from .simulator import Metrics, simulate_solution
from .solution import Solution

REPORT_MESSAGE = "Please contact @yut23#9382 on the Zachtronics discord or open an issue at https://github.com/lastcallbbs-community-developers/foodcourt-sim/issues/new."

# configure logging
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter("%(levelname)s|%(message)s"))
logger.addHandler(ch)


def to_json(solution: Solution, /, **kwargs: Any) -> dict[str, Any]:
    result = dict(
        level_number=solution.level.number,
        level_name=solution.level.name,
        level_slug=solution.level.internal_name,
        solution_name=solution.name,
        filename=solution.filename,
        marked_solved=solution.solved,
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


def error_to_json(solution: Solution, ex: Exception, **kwargs: Any) -> dict[str, Any]:
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
        nargs=argparse.ZERO_OR_MORE,
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
        for solution_file in args.solution_file or ["-"]:
            input_source: Union[Path, BinaryIO]
            if solution_file == "-":
                input_source = sys.stdin.buffer
            else:
                input_source = Path(solution_file)
            try:
                solutions.extend(read_solutions(input_source))
            except InvalidSolutionError as ex:
                logger.error("Unable to parse solution files: %s", ex)
                if args.json:
                    print(json.dumps([]))
                return 255
        nag_to_report = False
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
                if isinstance(ex, InternalSimulationError):
                    logger.error(
                        "Internal simulation error encountered%s: %s",
                        f' ({solution.level.name} "{solution.name}")'
                        if args.json
                        else "",
                        ex,
                    )
                    nag_to_report = True
                elif solution.solved:
                    logger.warning(
                        "%sSimulation error encountered in solved solution: %s",
                        f'{solution.level.name} "{solution.name}": '
                        if args.json
                        else "",
                        ex,
                    )
                if not args.json:
                    print(f"Simulation failed:\n{ex}")
            else:
                results.append(
                    metrics_to_json(solution, metrics, args.include_solution)
                )
            if not args.json and results[-1]["is_correct"]:
                print(metrics)
                if not solution.solved:
                    print(
                        "Note: this solution was not marked as solved in-game. If it doesn't actually work,"
                    )
                    print(REPORT_MESSAGE)
        if nag_to_report:
            logger.error(REPORT_MESSAGE)
        if args.json:
            print(json.dumps(results))
        return 0

    parser_simulate.set_defaults(func=run_simulate)

    parser_show_solution = subparsers.add_parser(
        "show_solution", help="Read solution files and print their metadata"
    )
    parser_show_solution.add_argument(
        "solution_file",
        nargs=argparse.ONE_OR_MORE,
        type=Path,
        help="Solution file path",
    )
    parser_show_solution.add_argument(
        "--dump", action="store_true", help="Dump the entire solution structure"
    )
    parser_show_solution.add_argument(
        "--normalize", action="store_true", help="Normalize the solution before dumping"
    )

    def run_show_solution(args: argparse.Namespace) -> int:
        for path in args.solution_file:
            try:
                solution = read_solution(path)
            except InvalidSolutionError as ex:
                print(f"Invalid solution file: {ex}")
                return 1
            print(f"{path.name}: ", end="")
            if args.dump:
                if args.normalize:
                    solution = solution.normalize()
                print(solution)
            else:
                out = []
                if not path.name.startswith(solution.level.internal_name):
                    out.append(solution.level.name)
                out.append(f'"{solution.name}",')
                if solution.solved:
                    out.append(f"{solution.time}T/{solution.cost}C")
                else:
                    out.append("unsolved")
                print(" ".join(out))
        return 0

    parser_show_solution.set_defaults(func=run_show_solution)

    # check for subcommands, default to simulate if none are found
    if set(subparsers.choices) & set(sys.argv[1:]):
        # one of the arguments matches a subparser name
        args = parser.parse_args()
    else:
        # default to simulate
        args = parser_simulate.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
