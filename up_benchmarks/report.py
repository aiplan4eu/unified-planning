from functools import partial
from itertools import chain
import typing
import test_cases  # type: ignore
from test_cases import get_test_cases
import os
import sys
import time
from typing import Set, Tuple

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

from utils import Ok, Err, ResultSet, Warn, bcolors, Void, get_report_parser, _get_test_cases  # type: ignore

USAGE = """Validates the results of solvers on a set of planning problems.
Usage (default operation mode: oneshot):
 - python report.py                          # will run all solvers on all problems
 - python report.py aries tamer              # will run aries an tamer on all problems they support
 - python report.py aries --prefix up:basic  # will run aries on all problems whose name starts with "up:basic"

The test operation can be changed with `--mode plan-validation`, `--mode oneshot`, `--mode anytime`, `--mode grounding` and `--mode all` that reports all the previous modes.
"""

get_environment().credits_stream = None  # silence credits


def get_test_cases_from_packages(packages: List[str]) -> Dict[str, TestCase]:
    res = {}

    for package in packages:
        if hasattr(package, "get_test_cases"):
            to_add = package.get_test_cases
        else:
            # If the package does not have a top-level get_test_cases method, run the "discover" method on the whole package
            package_get_test_cases = partial(_get_test_cases, package)
            to_add = package_get_test_cases()
        for test_case_name, test_case in to_add.items():
            test_case_name = f"{package}:{test_case_name}"
            count = 0
            # If the name is already in the results, add a counter to guarantee unicity
            while test_case_name in res:
                test_case_name = f"{test_case_name}_{count}"
                count += 1
            res[test_case_name] = test_case
    return res


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


def report_oneshot(
    engines: List[str], problems: Dict[str, TestCase], timeout: Optional[float]
) -> List[Tuple[str, str]]:
    """Run all oneshot planners on all the given problems"""

    factory = get_environment().factory
    # filter OneshotPlanners
    planners = list(filter(lambda name: factory.engine(name).is_oneshot_planner(), engines))  # type: ignore [attr-defined]

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


def report_anytime(
    engines: List[str], problems: Dict[str, TestCase], timeout: Optional[float]
) -> List[Tuple[str, str]]:
    """Run all anytime planners on all problems that start with the given prefix"""

    factory = get_environment().factory
    # filter AnytimePlanners
    planners = list(filter(lambda name: factory.engine(name).is_anytime_planner(), engines))  # type: ignore [attr-defined]

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


def report_validation(
    engines: List[str], problems: Dict[str, TestCase]
) -> List[Tuple[str, str]]:
    """Checks that all given plan validators produce the correct output on test-cases."""
    errors: List[Tuple[str, str]] = []  # all errors encountered
    factory = get_environment().factory
    # filter PlanValidators
    validators = list(filter(lambda name: factory.engine(name).is_plan_validator(), engines))  # type: ignore [attr-defined]

    def applicable_validators(pb, plan):
        vals = [PlanValidator(name=validator_name) for validator_name in validators]
        return filter(
            lambda e: e.supports(pb.kind) and e.supports_plan(plan.kind), vals
        )

    for test_case in problems.values():
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
    return errors


def report_grounding(
    engines: List[str], problems: Dict[str, TestCase]
) -> List[Tuple[str, str]]:
    """Checks that all given grounders produce the correct output on test-cases."""
    factory = get_environment().factory

    # filter grounders
    def is_grounder(engine_name):
        e = factory.engine(engine_name)
        return e.is_compiler() and e.supports_compilation(CompilationKind.GROUNDING)  # type: ignore [attr-defined]

    grounders = list(filter(is_grounder, engines))

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

        for engine_id in grounders:
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


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parser = get_report_parser()
    parsed_args = parser.parse_args(args)
    engines = parsed_args.engines
    if not engines:
        engines = get_environment().factory.engines

    if parsed_args.packages:
        packages = parsed_args.packages
    else:
        packages = ["test_cases", "unified_planning.test"]
        packages.extend(parsed_args.extra_packages)

    problem_test_cases = get_test_cases_from_packages(packages)
    prefixes = parsed_args.prefixes
    if prefixes:
        # Filter only the names that have at least one of the prefixes in them
        problem_test_cases = dict(
            filter(
                lambda name_value: any(p in name_value[0] for p in prefixes),
                problem_test_cases.items(),
            )
        )

    timeout: Optional[float] = parsed_args.timeout
    if timeout <= 0:
        timeout = None

    modes = parsed_args.modes
    oneshot_errors = []
    validation_errors = []
    anytime_errors = []
    grounding_errors = []

    if "oneshot" in modes:
        oneshot_errors = report_oneshot(engines, problem_test_cases, timeout)
    if "anytime" in modes:
        anytime_errors = report_anytime(engines, problem_test_cases, timeout)
    if "validation" in modes:
        validation_errors = report_validation(engines, problem_test_cases)
    if "grounding" in modes:
        grounding_errors = report_grounding(engines, problem_test_cases)

    print()
    if oneshot_errors:
        print("Oneshot errors:\n ", "\n  ".join(map(str, oneshot_errors)))
    if anytime_errors:
        print("Anytime errors:\n ", "\n  ".join(map(str, anytime_errors)))
    if validation_errors:
        print("Validation errors:\n ", "\n  ".join(map(str, validation_errors)))
    if grounding_errors:
        print("Grounding errors:\n ", "\n  ".join(map(str, grounding_errors)))
    errors = list(
        chain(oneshot_errors, validation_errors, anytime_errors, grounding_errors)
    )

    if len(errors) > 0:
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
