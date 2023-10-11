from itertools import chain
import typing
import test_cases  # type: ignore
from test_cases import get_test_cases
import os
import sys
import time
from typing import Tuple

from unified_planning.engines import (
    CompilerResult,
    PlanGenerationResultStatus,
    ValidationResultStatus,
    PlanGenerationResult,
    ValidationResult,
)
from unified_planning.engines.mixins import (
    CompilerMixin,
    AnytimePlannerMixin,
    PlanValidatorMixin,
    OneshotPlannerMixin,
)

from unified_planning.plans import Plan

from unified_planning.shortcuts import *
from unified_planning.environment import get_environment
from unified_planning.exceptions import UPNoSuitableEngineAvailableException
from unified_planning.test import TestCase

from test_cases.results import Ok, Err, ResultSet, Warn, bcolors, Void  # type: ignore

USAGE = """Validates the results of solvers on a set of planning problems.
Usage (default operation mode: oneshot):
 - python report.py                          # will run all solvers on all problems
 - python report.py aries tamer              # will run aries an tamer on all problems they support
 - python report.py aries --prefix up:basic  # will run aries on all problems whose name starts with "up:basic"

The test operation can be changed with `--mode plan-validation`, `--mode oneshot`, `--mode anytime`, `--mode grounding` and `--mode all` that reports all the previous modes.
"""

get_environment().credits_stream = None  # silence credits


def all_test_cases():
    """Returns all test cases of this repository"""
    res = up_tests()
    res.update(test_cases.get_test_cases())
    return res


def engines() -> List[Tuple[str, typing.Type[Engine]]]:
    """Returns all available engines."""
    factory = get_environment().factory
    return [(name, factory.engine(name)) for name in factory.engines]


def oneshot_planners():
    """All available oneshot planners."""
    return [t for t, e in engines() if e.is_oneshot_planner()]  # type: ignore [attr-defined]


def anytime_planners():
    """All available anytime planners."""
    return [t for t, e in engines() if e.is_anytime_planner()]  # type: ignore [attr-defined]


def validators():
    """All available plan validators"""
    return [t for t, e in engines() if e.is_plan_validator()]  # type: ignore [attr-defined]


def grounders():
    """All available grounders"""
    return [t for t, e in engines() if e.is_compiler() and e.supports_compilation(CompilationKind.GROUNDING)]  # type: ignore [attr-defined]


def up_tests():
    """All test cases defined in the `unified_planning.test` module. All are assumed to be solvable."""
    from unified_planning.test.examples import get_example_problems

    return get_example_problems()


def validate_plan(plan: Plan, problem: AbstractProblem) -> ResultSet:
    """Validates a plan produced by a planner."""
    try:
        with PlanValidator(problem_kind=problem.kind, plan_kind=plan.kind) as validator:
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
        metrics: Iterable[Any] = getattr(test.problem, "quality_metrics", tuple())
        if not metrics:
            output += verify(
                result.status
                in (
                    PlanGenerationResultStatus.SOLVED_SATISFICING,
                    PlanGenerationResultStatus.INTERMEDIATE,
                    PlanGenerationResultStatus.TIMEOUT,
                ),
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
                        PlanGenerationResultStatus.INTERMEDIATE,
                        PlanGenerationResultStatus.TIMEOUT,
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


def check_grounding_result(test: TestCase, result: CompilerResult) -> ResultSet:
    output = Void()
    compiled_problem = result.problem
    if compiled_problem is None:
        output += Err("No compiled problem returned")
        return output
    output += verify(all(not a.parameters for a in compiled_problem.actions), "compiled_problem not grounded")  # type: ignore [attr-defined]

    # TODO understand how to handle quality metrics
    if hasattr(test.problem, "quality_metrics") and test.problem.quality_metrics:  # type: ignore [attr-defined]
        output += Warn("Still to implemented how to deal with quality metrics")
        return output

    try:
        with OneshotPlanner(problem_kind=compiled_problem.kind) as planner:
            res = planner.solve(compiled_problem)
    except UPNoSuitableEngineAvailableException:
        output += Warn("No engine to solve compiled problem")
        return output
    if res.plan is not None:
        output += verify(test.solvable, "expected SAT/OPT")
        if test.solvable:
            original_plan = res.plan.replace_action_instances(
                result.map_back_action_instance
            )
            output += validate_plan(original_plan, test.problem)
    else:
        output += verify(not test.solvable, "expected UNSAT")

    return output


def run_oneshot(
    planners: Iterable[str], problems: Dict[str, TestCase], timeout=1
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
                    assert isinstance(
                        planner, OneshotPlannerMixin
                    ), "Error in oneshot planners selection"
                    result = planner.solve(pb, timeout=timeout)
                    end = time.time()
                    status = str(result.status.name).ljust(25)
                    outcome = check_result(test_case, result, planner)
                    if not outcome.ok():
                        errors.append((planner_id, name))
                    runtime = "{:.3f}s".format(end - start).ljust(10)
                    print(status, "    ", runtime, outcome)

                except Exception as e:
                    print(f"{bcolors.ERR}CRASH{bcolors.ENDC}", e)
                    errors.append((planner_id, name))
    return errors


def run_anytime(
    planners: Iterable[str], problems: Dict[str, TestCase], timeout=10
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
            planner = AnytimePlanner(name=planner_id)
            if planner.supports(pb.kind):

                print("|  ", planner_id.ljust(40), end="")
                start = time.time()
                try:
                    outcome = Void()
                    assert isinstance(
                        planner, AnytimePlannerMixin
                    ), "Error in Anytime selection"
                    for result in planner.get_solutions(pb, timeout=timeout):
                        status = str(result.status.name).ljust(25)
                        outcome += check_result(test_case, result, planner)
                    if not outcome.ok():
                        errors.append((planner_id, name))
                    end = time.time()
                    runtime = "{:.3f}s".format(end - start).ljust(10)
                    print(status, "    ", runtime, outcome)

                except Exception as e:
                    print(f"{bcolors.ERR}CRASH{bcolors.ENDC}", e)
                    errors.append((planner_id, name))
    return errors


def run_grounding(
    engines: Iterable[str], problems: Dict[str, TestCase], timeout=1
) -> List[Tuple[str, str]]:
    errors: List[Tuple[str, str]] = []
    for test_case in problems.values():
        pb = test_case.problem
        kind = pb.kind
        # if the problem is not action based or has no parameters in the actions, skip it
        if not kind.has_action_based() or not any(a.parameters for a in pb.actions):  # type: ignore [attr-defined] # If the kind has action_based, the pb.actions is defined
            continue
        print()
        name = pb.name
        if name is None:
            name = "None"
        print(name.ljust(40), end="\n")

        for engine_id in engines:
            compiler = Compiler(name=engine_id)
            if compiler.supports(kind):

                print("|  ", engine_id.ljust(40), end="")
                start = time.time()
                try:
                    assert isinstance(compiler, CompilerMixin)
                    result = compiler.compile(
                        pb, compilation_kind=CompilationKind.GROUNDING
                    )
                    end = time.time()
                    status = str("COMPILED").ljust(25)
                    outcome = check_grounding_result(test_case, result)
                    if not outcome.ok():
                        errors.append((engine_id, name))
                    runtime = "{:.3f}s".format(end - start).ljust(10)
                    print(status, "    ", runtime, outcome)

                except Exception as e:
                    print(f"{bcolors.ERR}CRASH{bcolors.ENDC}", e)
                    errors.append((engine_id, name))
    return errors


def report_oneshot(*planners: str, problem_prefix: str = "", silent: bool = False):
    """Run all oneshot planners on all problems that start with the given prefix"""

    if len(planners) == 0:
        planners = oneshot_planners()

    problems = all_test_cases()
    problems = dict(
        (name, tc) for name, tc in problems.items() if name.startswith(problem_prefix)
    )

    errors = run_oneshot(planners, problems)
    if len(errors) > 0 and not silent:
        print("Errors:\n ", "\n  ".join(map(str, errors)))
    return errors


def report_anytime(*planners: str, problem_prefix: str = "", silent: bool = False):
    """Run all anytime planners on all problems that start with the given prefix"""

    if len(planners) == 0:
        planners = anytime_planners()

    problems = all_test_cases()
    problems = dict(
        (name, tc) for name, tc in problems.items() if name.startswith(problem_prefix)
    )

    errors = run_anytime(planners, problems)
    if len(errors) > 0 and not silent:
        print("Errors:\n ", "\n  ".join(map(str, errors)))
    return errors


def report_validation(*engines: str, problem_prefix: str = "", silent: bool = False):
    """Checks that all given plan validators produce the correct output on test-cases."""
    errors: List[Tuple[str, str]] = []  # all errors encountered
    if len(engines) == 0:
        engines = validators()
    test_cases = all_test_cases()
    test_cases = dict(
        (name, tc) for name, tc in test_cases.items() if name.startswith(problem_prefix)
    )

    def applicable_validators(pb, plan):
        vals = [PlanValidator(name=validator_name) for validator_name in engines]
        return filter(
            lambda e: e.supports(pb.kind) and e.supports_plan(plan.kind), vals
        )

    for test_case in test_cases.values():
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

    if len(errors) > 0 and not silent:
        print("Errors:\n ", "\n  ".join(map(str, errors)))
    return errors


def report_grounding(*engines: str, problem_prefix: str = "", silent: bool = False):
    """Checks that all given grounders produce the correct output on test-cases."""
    if len(engines) == 0:
        engines = grounders()

    problems = all_test_cases()
    problems = dict(
        (name, tc) for name, tc in problems.items() if name.startswith(problem_prefix)
    )

    errors = run_grounding(engines, problems)
    if len(errors) > 0 and not silent:
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
    elif mode in ["anytime", "anytime-planning", "anytime_planning"]:
        errors = report_anytime(*planners, problem_prefix=prefix)
    elif mode in ["grounding", "ground"]:
        errors = report_grounding(*planners, problem_prefix=prefix)
    elif mode == "all":
        oneshot_errors = report_oneshot(*planners, problem_prefix=prefix, silent=True)
        validation_errors = report_validation(
            *planners, problem_prefix=prefix, silent=True
        )
        anytime_errors = report_anytime(*planners, problem_prefix=prefix, silent=True)
        grounding_errors = report_grounding(
            *planners, problem_prefix=prefix, silent=True
        )

        print()
        if len(oneshot_errors) > 0:
            print("Oneshot errors:\n ", "\n  ".join(map(str, oneshot_errors)))
        if len(validation_errors) > 0:
            print("Validation errors:\n ", "\n  ".join(map(str, validation_errors)))
        if len(anytime_errors) > 0:
            print("Anytime errors:\n ", "\n  ".join(map(str, anytime_errors)))
        if len(grounding_errors) > 0:
            print("Grounding errors:\n ", "\n  ".join(map(str, grounding_errors)))
        errors = list(
            chain(oneshot_errors, validation_errors, anytime_errors, grounding_errors)
        )

    else:
        print(f"Unrecognized operation mode {mode}")
        sys.exit(1)

    if len(errors) > 0:
        sys.exit(1)
