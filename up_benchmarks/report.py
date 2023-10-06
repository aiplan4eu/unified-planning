import test_cases
from test_cases import get_test_cases
import os
import sys
import time
from typing import Tuple

from unified_planning.engines import (
    PlanGenerationResultStatus,
    ValidationResultStatus,
    PlanGenerationResult,
    ValidationResult,
)

from unified_planning.plans import Plan

from unified_planning.shortcuts import *
from unified_planning.environment import get_environment
from unified_planning.test import TestCase

from test_cases.results import *

USAGE = """Validates the results of solvers on a set of planning problems.
Usage (default operation mode: oneshot):
 - python report.py                          # will run all solvers on all problems
 - python report.py aries tamer              # will run aries an tamer on all problems they support
 - python report.py aries --prefix up:basic  # will run aries on all problems whose name starts with "up:basic"

The test operation can be changed with `--mode plan-validation` or `--mode oneshot`.
"""

get_environment().credits_stream = None  # silence credits


def all_test_cases():
    """Returns all test cases of this repository"""
    res = up_tests()
    res.update(test_cases.get_test_cases())
    return res


def engines() -> List[Tuple[str, Engine]]:
    """Returns all available engines."""
    tags = [n for n in get_environment().factory.engines]
    return [(t, get_environment().factory.engine(t)) for t in tags]


def oneshot_planners():
    """All available oneshot planners."""
    return [t for t, e in engines() if e.is_oneshot_planner()]


def validators():
    """All available plan validators"""
    return [t for t, e in engines() if e.is_plan_validator()]


def up_tests():
    """All test cases defined in the `unified_planning.test` module. All are assumed to be solvable."""
    from unified_planning.test.examples import get_example_problems

    return get_example_problems()


def validate_plan(plan: Plan, problem: Problem) -> ResultSet:
    """Validates a plan produced by a planner."""
    try:
        with PlanValidator(problem_kind=problem.kind) as validator:
            if not validator.supports_plan(plan.kind):
                return Warn(f"Validator {validator.name} does not support plan")
            check = validator.validate(problem, plan)
            if check.status is ValidationResultStatus.VALID:
                return Ok("Valid")
            else:
                return Err("INVALID")
    except unified_planning.exceptions.UPNoSuitableEngineAvailableException:
        return Warn("No validator for problem")
    except Exception as e:
        return Warn(f"Validator crash ({e})")


def verify(cond: bool, error_tag: str, ok_tag: str = "") -> ResultSet:
    """Returns an Error if the condition passed in parameter does not hold."""
    if cond:
        return Ok(ok_tag)
    else:
        return Err(error_tag)


def check_result(test: TestCase, result: PlanGenerationResult, planner) -> ResultSet:
    output = Void()
    output += verify(
        result.status != PlanGenerationResultStatus.INTERNAL_ERROR,
        "forbidden internal error",
    )

    if result.plan:
        if not test.solvable:
            output += Err("Unsolvable problem")
        # if the planner guarantees optimality, this should be reflected in
        # the result status
        metrics = test.problem.quality_metrics
        if not metrics:
            output += verify(
                result.status is PlanGenerationResultStatus.SOLVED_SATISFICING,
                "expected SAT ",
            )
        else:
            if planner.satisfies(OptimalityGuarantee.SOLVED_OPTIMALLY):
                output += verify(
                    result.status is PlanGenerationResultStatus.SOLVED_OPTIMALLY,
                    "expected OPT",
                )
            else:
                output += verify(
                    result.status
                    in (
                        PlanGenerationResultStatus.SOLVED_OPTIMALLY,
                        PlanGenerationResultStatus.SOLVED_SATISFICING,
                    ),
                    "expected SAT/OPT",
                )
        output += validate_plan(result.plan, test.problem)
    elif test.solvable:
        output += verify(
            result.status != PlanGenerationResultStatus.UNSOLVABLE_PROVEN,
            "UNSOLVABLE on solvable problem",
        )
        # We are only running the test on solvable instances
        output += verify(
            result.status
            in (
                PlanGenerationResultStatus.TIMEOUT,
                PlanGenerationResultStatus.MEMOUT,
                PlanGenerationResultStatus.UNSUPPORTED_PROBLEM,
                PlanGenerationResultStatus.UNSOLVABLE_INCOMPLETELY,
            ),
            "invalid status",
        )
        output += Warn(f"Unsolved ({result.status.name})")
    else:
        output += verify(
            result.status
            in (
                PlanGenerationResultStatus.UNSOLVABLE_PROVEN,
                PlanGenerationResultStatus.TIMEOUT,
                PlanGenerationResultStatus.MEMOUT,
                PlanGenerationResultStatus.UNSUPPORTED_PROBLEM,
                PlanGenerationResultStatus.UNSOLVABLE_INCOMPLETELY,
            ),
            "invalid status",
        )

    return output


def run_oneshot(
    planners: List[str], problems: List[TestCase], timeout=1
) -> List[Tuple[str, str]]:
    errors = []
    for test_case in problems.values():
        print()
        name = test_case.problem.name
        if name is None:
            name = "None"
        print(name.ljust(40), end="\n")
        pb = test_case.problem

        for planner_id in planners:
            planner = OneshotPlanner(name=planner_id)
            if planner.supports(pb.kind):

                print("|  ", planner_id.ljust(40), end="")
                start = time.time()
                try:
                    result = planner.solve(pb, timeout=timeout)
                    end = time.time()
                    status = str(result.status.name).ljust(25)
                    outcome = check_result(test_case, result, planner)
                    if not outcome.ok():
                        errors.append((planner_id, test_case.problem.name))
                    runtime = "{:.3f}s".format(end - start).ljust(10)
                    print(status, "    ", runtime, outcome)

                except Exception as e:
                    print(f"{bcolors.ERR}CRASH{bcolors.ENDC}", e)
                    errors.append((planner_id, test_case.problem.name))
    return errors


def report_oneshot(*planners: str, problem_prefix: str = ""):
    """Run all oneshot planners on all problems that start with the given prefix"""

    if len(planners) == 0:
        planners = oneshot_planners()

    problems = all_test_cases()
    problems = dict(
        (name, tc) for name, tc in problems.items() if name.startswith(problem_prefix)
    )
    print("\n".join(problems.keys()))
    print(len(problems))
    errors = run_oneshot(planners, problems)
    if len(errors) > 0:
        print("Errors:\n ", "\n  ".join(map(str, errors)))
    return errors


def report_validation(*engines: str, problem_prefix: str = ""):
    """Checks that all given plan validators produce the correct output on test-caes."""
    errors: List[Tuple[str, str]] = []  # all errors encountered
    if len(engines) == 0:
        engines = validators()
    test_cases = all_test_cases()
    test_cases = [p for p in test_cases if p.name.startswith(problem_prefix)]

    def applicable_validators(pb, plan):
        vals = [PlanValidator(name=validator_name) for validator_name in engines]
        return filter(
            lambda e: e.supports(pb.kind) and e.supports_plan(plan.kind), vals
        )

    for test_case in test_cases:
        result: ValidationResult
        for i, valid_plan in enumerate(test_case.valid_plans):
            print()
            print(f"{test_case.problem.name} valid[{i}]".ljust(40), end="\n")
            for validator in applicable_validators(test_case.problem, valid_plan):
                print("|  ", validator.name.ljust(40), end="")
                result = validator.validate(test_case.problem, valid_plan)
                if result.status == ValidationResultStatus.VALID:
                    print(Ok("Valid"))
                else:
                    print(Err(f"Incorrectly flagged as {result.status.name}"))
                    errors.append((test_case.problem.name, validator.name))

        for i, invalid_plan in enumerate(test_case.invalid_plans):
            print()
            print(f"{test_case.problem.name} invalid[{i}]".ljust(40), end="\n")
            for validator in applicable_validators(test_case.problem, invalid_plan):
                print("|  ", validator.name.ljust(40), end="")
                result = validator.validate(test_case.problem, invalid_plan)
                if result.status == ValidationResultStatus.INVALID:
                    print(Ok("Invalid"))
                else:
                    print(Err(f"Incorrectly flagged as {result.status.name}"))
                    errors.append((test_case.problem.name, validator.name))

    if len(errors) > 0:
        print("Errors:\n ", "\n  ".join(map(str, errors)))
    return errors


if __name__ == "__main__":
    print(USAGE)
    planners = sys.argv[1:]
    try:  # extract "--prefix PREFIX"
        prefix_opt = planners.index("--prefix")
        planners.pop(prefix_opt)
        prefix = planners.pop(prefix_opt)
    except ValueError:
        prefix = ""
    try:  # extract "--mode MODE"
        prefix_opt = planners.index("--mode")
        planners.pop(prefix_opt)
        mode = planners.pop(prefix_opt).lower()
    except ValueError:
        mode = "oneshot"  # default mode is oneshot

    if mode == "oneshot":
        errors = report_oneshot(*planners, problem_prefix=prefix)
    elif mode in ["val", "plan-validation", "validation"]:
        errors = report_validation(*planners, problem_prefix=prefix)
    else:
        print(f"Unrecognized operation mode {mode}")
        sys.exit(1)

    if len(errors) > 0:
        sys.exit(1)
