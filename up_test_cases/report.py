import importlib
import sys
import time
from functools import partial
from itertools import chain
from typing import List, Tuple
import warnings

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
    PlanRepairerMixin,
)

from unified_planning.plans import Plan

from unified_planning.shortcuts import *
from unified_planning.environment import get_environment
from unified_planning.exceptions import UPNoSuitableEngineAvailableException
from unified_planning.test import TestCase

from utils import Ok, Err, ResultSet, Warn, bcolors, Void, get_report_parser, _get_test_cases  # type: ignore


get_environment().credits_stream = None  # silence credits
factory = get_environment().factory
# Move the sequential_plan_validator to the top of the list
preference_list: List[str] = ["sequential_plan_validator"]
preference_list.extend(
    filter(lambda name: name != "sequential_plan_validator", factory.preference_list)
)
factory.preference_list = preference_list


def get_test_cases_from_packages(packages: List[str]) -> Dict[str, TestCase]:
    res = {}

    for package in packages:
        try:
            module = importlib.import_module(package)
            to_add = module.get_test_cases()
        except AttributeError:
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


def report_runtime(
    metrics: Optional[Dict[str, str]],
    total_time: float,
    max_overhead: float,
    adjust_docker_overhead: bool = True,
) -> str:
    internal_time_str = None
    if metrics is not None:
        internal_time_str = metrics.get("engine_internal_time", None)
        docker_overhead_time_str = metrics.get("docker_overhead_time", None)
    if internal_time_str is not None:
        internal_time = float(internal_time_str)
        docker_overhead_time = 0.0
        if adjust_docker_overhead and docker_overhead_time_str is not None:
            docker_overhead_time = float(docker_overhead_time_str)
        overhead_percentage = (
            total_time - docker_overhead_time - internal_time
        ) / internal_time
    else:
        overhead_percentage = None
    if total_time > 1 and overhead_percentage is not None:
        overhead_str = "{:.0%}".format(overhead_percentage)
        overhead = (
            Ok(overhead_str)
            if overhead_percentage < max_overhead
            else Warn(overhead_str)
        )
        runtime_report = "{:.3f}s {}".format(total_time, overhead).ljust(30)
    elif total_time < 1:
        runtime_report = "{:.3f}s {}".format(total_time, Ok("<1s")).ljust(30)
    else:
        runtime_report = "{:.3f}s".format(total_time).ljust(21)
    return runtime_report


def validate_plan(
    plan: Plan, problem: AbstractProblem
) -> Tuple[ResultSet, Optional[Dict[PlanQualityMetric, Union[int, Fraction]]]]:
    """Validates a plan produced by a planner."""
    try:
        with PlanValidator(problem_kind=problem.kind, plan_kind=plan.kind) as validator:
            check = validator.validate(problem, plan)
            if check.status is ValidationResultStatus.VALID:
                return Ok("Valid"), check.metric_evaluations
            else:
                return Err("Invalid plan generated"), None
    except unified_planning.exceptions.UPNoSuitableEngineAvailableException:
        return Warn("No validator for problem"), None
    except Exception as e:
        return Warn(f"Validator crash ({e})"), None


def verify(cond: bool, error_tag: str, ok_tag: str = "") -> ResultSet:
    """Returns an Error if the condition passed in parameter does not hold."""
    if cond:
        return Ok(ok_tag)
    else:
        return Err(error_tag)


def check_result(
    test: TestCase, result: PlanGenerationResult, planner
) -> Tuple[ResultSet, Optional[Dict[PlanQualityMetric, Union[int, Fraction]]]]:
    output = Void()
    metrics_evaluation = None

    if result.plan:
        if not test.solvable:
            return Err("Solved unsolvable problem")
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
                f"Returned {result.status.name} on Problem without metric",
            )
        else:
            if planner.satisfies(OptimalityGuarantee.SOLVED_OPTIMALLY):
                output += verify(
                    result.status is PlanGenerationResultStatus.SOLVED_OPTIMALLY,
                    f"Planner guarantees optimality but returned {result.status.name}",
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
                    f"Plan generated, but invalid status: {result.status.name}",
                )
        validation_res, metrics_evaluation = validate_plan(result.plan, test.problem)
        output += validation_res
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
                PlanGenerationResultStatus.INTERMEDIATE,
                PlanGenerationResultStatus.UNSOLVABLE_PROVEN,
            ),
            f"error status: {result.status.name}",
        )
        if result.status == PlanGenerationResultStatus.UNSOLVABLE_INCOMPLETELY:
            output += Warn(f"Solvable problem, returned {result.status.name}")
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
            "Invalid",
        )

    return output, metrics_evaluation


def check_grounding_result(test: TestCase, result: CompilerResult) -> ResultSet:
    compiled_problem = result.problem
    if compiled_problem is None:
        return Err("No compiled problem returned")
    if any(a.parameters for a in compiled_problem.actions):  # type: ignore [attr-defined]
        return Err("compiled_problem not grounded")

    planners = get_all_applicable_engines(problem_kind=compiled_problem.kind)
    if not planners:
        return Warn("No engine to solve compiled problem")
    plan = None
    for planner in map(lambda n: OneshotPlanner(name=n), planners):
        assert isinstance(planner, OneshotPlannerMixin)
        try:
            res = planner.solve(compiled_problem)
        except:
            pass
        if test.solvable and res.plan is not None:
            plan = res.plan
            break
        if not test.solvable and res.plan is None:
            return Ok("Compiled problem unsolvable")
    if plan is None and test.solvable:
        return Warn("No engine to solve compiled problem")
    elif plan is None:
        return Warn("No engine to prove compiled problem is unsolvable")

    assert test.solvable and plan is not None
    mbai = result.map_back_action_instance
    if mbai is None:
        return Err("The mapping back function is None")
    original_plan = plan.replace_action_instances(mbai)
    validation_res, _ = validate_plan(original_plan, test.problem)
    return validation_res


def report_oneshot(
    engines: List[str], problems: Dict[str, TestCase], timeout: Optional[float]
) -> List[Tuple[str, str]]:
    """Run all oneshot planners on all the given problems"""

    factory = get_environment().factory
    # filter OneshotPlanners
    planners = list(filter(lambda name: factory.engine(name).is_oneshot_planner(), engines))  # type: ignore [attr-defined, arg-type]

    print("\n\nONESHOT PLANNING:")
    errors = []
    problems_skipped = []
    for name, test_case in problems.items():
        name_printed = False
        pb = test_case.problem

        for planner_id in planners:
            planner = OneshotPlanner(name=planner_id)
            if planner.supports(pb.kind):

                if not name_printed:
                    name_printed = True
                    print()
                    print(name.ljust(40), end="\n")

                print("|  ", planner_id.ljust(40), end="")
                try:
                    assert isinstance(
                        planner, OneshotPlannerMixin
                    ), "Error in oneshot planners selection"
                    start = time.time()
                    result = planner.solve(pb, timeout=timeout)
                    total_execution_time = time.time() - start
                    status = str(result.status.name).ljust(25)
                    outcome, metrics_evaluation = check_result(
                        test_case, result, planner
                    )
                    if (
                        result.status is PlanGenerationResultStatus.SOLVED_OPTIMALLY
                        and metrics_evaluation
                    ):
                        assert (
                            len(metrics_evaluation) == 1
                        ), "Can't support more than 1 metric in the problem"
                        value = tuple(metrics_evaluation.values())[0]
                        expected_value = test_case.optimum
                        if expected_value is not None:
                            outcome += verify(
                                value == expected_value,
                                f"Expected OPT but metric evaluation = {value} and expected optimum = {expected_value}",
                            )
                        else:
                            outcome = (
                                Warn("The optimum is not defined in the test_case")
                                + outcome
                            )
                    if not outcome.ok():
                        errors.append((planner_id, name))
                    runtime_report = report_runtime(
                        result.metrics, total_execution_time, 0.10
                    )
                    print(status, "    ", runtime_report, outcome)

                except Exception as e:
                    print(f"{bcolors.ERR}CRASH{bcolors.ENDC}", e)
                    errors.append((planner_id, name))
        if not name_printed:
            problems_skipped.append(name)

    if len(problems_skipped) == len(problems):
        print("\n\nOneshot problems skipped: ALL")
    elif problems_skipped:
        print("\n\nOneshot problems skipped:")
        print("   ", "\n    ".join(problems_skipped))

    return errors


def report_plan_repair(
    engines: List[str], problems: Dict[str, TestCase]
) -> List[Tuple[str, str]]:
    """Run all plan repairer on all the given problems"""

    factory = get_environment().factory
    # filter PlanRepairer
    planners = list(filter(lambda name: factory.engine(name).is_plan_repairer(), engines))  # type: ignore [attr-defined, arg-type]

    print("\n\nPLAN REPAIR:")
    errors = []
    problems_skipped = []
    problems_run = 0
    for name, test_case in problems.items():
        pb = test_case.problem
        for i, plan in enumerate(test_case.invalid_plans):
            name_printed = False
            for planner_id in planners:
                planner = PlanRepairer(name=planner_id)
                if planner.supports(pb.kind) and planner.supports_plan(plan.kind):

                    if not name_printed:
                        problems_run += 1
                        name_printed = True
                        print()
                        print(f"{name} [{i}]".ljust(40), end="\n")

                    print("|  ", planner_id.ljust(40), end="")
                    try:
                        assert isinstance(
                            planner, PlanRepairerMixin
                        ), "Error in plan repairer selection"
                        start = time.time()
                        result = planner.repair(pb, plan)
                        total_execution_time = time.time() - start
                        status = str(result.status.name).ljust(25)
                        outcome, metrics_evaluation = check_result(
                            test_case, result, planner
                        )
                        if not outcome.ok():
                            errors.append((planner_id, f"{name} [{i}]"))
                        runtime_report = report_runtime(
                            result.metrics, total_execution_time, 0.10
                        )
                        print(status, "    ", runtime_report, outcome)

                    except Exception as e:
                        print(f"{bcolors.ERR}CRASH{bcolors.ENDC}", e)
                        errors.append((planner_id, f"{name} [{i}]"))
            if not name_printed:
                problems_skipped.append(f"{name} [{i}]")

    if problems_run == 0:
        print("\n\nPlan Repair problems skipped: ALL")
    elif problems_skipped:
        print("\n\nPlan Repair problems skipped:")
        print("   ", "\n    ".join(problems_skipped))

    return errors


def check_anytime_solution_improvement(
    problem: AbstractProblem,
    metrics_evaluations: List[Dict[PlanQualityMetric, Union[int, Fraction]]],
) -> ResultSet:
    if not hasattr(problem, "quality_metrics") or not problem.quality_metrics:  # type: ignore [attr-defined]
        if any(m for m in metrics_evaluations):
            return Warn(
                "Validator returned metric evaluations when the problem has no quality metrics"
            )
        return Ok()
    if len(problem.quality_metrics) != 1:
        return Warn("Problem has more that 1 quality metric")
    metric_values: Dict[PlanQualityMetric, List[Union[int, Fraction]]] = {}

    for element in metrics_evaluations:
        for metric, value in element.items():
            metric_values.setdefault(metric, []).append(value)

    output = Void()
    for metric, values in metric_values.items():
        metric_class_name = metric.__class__.__name__.lower()
        must_be_reversed = "minimize" in metric_class_name
        if values != sorted(values, reverse=must_be_reversed):
            output += Err(f"Metric: {metric}, values: {values}")
    return output


def check_all_optimal_solutions(
    test_case: TestCase,
    metrics_evaluations: List[Dict[PlanQualityMetric, Union[int, Fraction]]],
) -> ResultSet:
    if test_case.optimum is None:
        return Void()
    for metrics_evaluation in metrics_evaluations:
        assert len(metrics_evaluation) == 1, "Multiple metric not implemented"
        if any(v != test_case.optimum for v in metrics_evaluation.values()):
            return Err("Non optimal plan returned")
    return Ok()


def report_anytime(
    engines: List[str], problems: Dict[str, TestCase], timeout: Optional[float]
) -> List[Tuple[str, str]]:
    """Run all anytime planners on all problems that start with the given prefix"""

    factory = get_environment().factory
    # filter AnytimePlanners
    planners = list(filter(lambda name: factory.engine(name).is_anytime_planner(), engines))  # type: ignore [attr-defined, arg-type]

    print("\n\nANYTIME PLANNING:")
    errors = []
    problems_skipped = []
    for name, test_case in problems.items():
        name_printed = False
        pb = test_case.problem

        for planner_id in planners:
            planner = AnytimePlanner(name=planner_id)
            if planner.supports(pb.kind):

                if not name_printed:
                    name_printed = True
                    print()
                    print(name.ljust(40), end="\n")

                print("|  ", planner_id.ljust(40), end="")
                try:
                    outcome = Void()
                    metrics_evaluations: List[
                        Dict[PlanQualityMetric, Union[int, Fraction]]
                    ] = []
                    assert isinstance(
                        planner, AnytimePlannerMixin
                    ), "Error in Anytime selection"
                    results = []
                    start = time.time()
                    for result in planner.get_solutions(pb, timeout=timeout):
                        results.append(result)
                    total_execution_time = time.time() - start
                    for result in results:
                        status = str(result.status.name).ljust(25)
                        validity, metrics_evaluation = check_result(
                            test_case, result, planner
                        )
                        outcome += validity
                        if metrics_evaluation:
                            metrics_evaluations.append(metrics_evaluation)
                    if not outcome.ok():
                        errors.append((planner_id, name))
                    if test_case.solvable and planner.ensures(
                        AnytimeGuarantee.INCREASING_QUALITY
                    ):
                        outcome += check_anytime_solution_improvement(
                            test_case.problem, metrics_evaluations
                        )
                    if test_case.solvable and planner.ensures(
                        AnytimeGuarantee.OPTIMAL_PLANS
                    ):
                        outcome += check_all_optimal_solutions(
                            test_case, metrics_evaluations
                        )
                    runtime_report = report_runtime(
                        result.metrics, total_execution_time, 0.15
                    )
                    print(status, "    ", runtime_report, outcome)

                except Exception as e:
                    print(f"{bcolors.ERR}CRASH{bcolors.ENDC}", e)
                    errors.append((planner_id, name))

        if not name_printed:
            problems_skipped.append(name)

    if len(problems_skipped) == len(problems):
        print("\n\nAnytime problems skipped: ALL")
    elif problems_skipped:
        print("\n\nAnytime problems skipped:")
        print("   ", "\n    ".join(problems_skipped))

    return errors


def report_validation(
    engines: List[str], problems: Dict[str, TestCase]
) -> List[Tuple[str, str]]:
    """Checks that all given plan validators produce the correct output on test-cases."""
    factory = get_environment().factory
    # filter PlanValidators
    validators = list(filter(lambda name: factory.engine(name).is_plan_validator(), engines))  # type: ignore [attr-defined, arg-type]

    def applicable_validators(pb, plan):
        vals = [PlanValidator(name=validator_name) for validator_name in validators]
        return filter(
            lambda e: e.supports(pb.kind) and e.supports_plan(plan.kind), vals
        )

    print("\n\nVALIDATION")
    errors: List[Tuple[str, str]] = []  # all errors encountered
    problems_skipped = []
    problems_run = 0
    for name, test_case in problems.items():
        result: ValidationResult
        for i, valid_plan in enumerate(test_case.valid_plans):
            problem_name_printed = False
            for validator in applicable_validators(test_case.problem, valid_plan):
                if not problem_name_printed:
                    problems_run += 1
                    problem_name_printed = True
                    print()
                    print(f"{name} valid[{i}]".ljust(40), end="\n")

                print("|  ", validator.name.ljust(40), end="")
                start = time.time()
                result = validator.validate(test_case.problem, valid_plan)
                total_execution_time = time.time() - start
                print(str(result.status.name).ljust(25), end="      ")
                runtime_report = report_runtime(
                    result.metrics, total_execution_time, 0.05
                )
                print(runtime_report, end="")
                if result.status == ValidationResultStatus.VALID:
                    print(Ok("Valid"))
                else:
                    print(Err(f"Incorrectly flagged as {result.status.name}"))
                    errors.append((name, validator.name))
            if not problem_name_printed:
                problems_skipped.append(f"{name} valid[{i}]")

        for i, invalid_plan in enumerate(test_case.invalid_plans):
            problem_name_printed = False
            for validator in applicable_validators(test_case.problem, invalid_plan):
                if not problem_name_printed:
                    problems_run += 1
                    problem_name_printed = True
                    print()
                    print(f"{name} invalid[{i}]".ljust(40), end="\n")
                print("|  ", validator.name.ljust(40), end="")
                start = time.time()
                result = validator.validate(test_case.problem, invalid_plan)
                total_execution_time = time.time() - start
                print(str(result.status.name).ljust(25), end="      ")
                runtime_report = report_runtime(
                    result.metrics, total_execution_time, 0.05
                )
                print(runtime_report, end="")
                if result.status == ValidationResultStatus.INVALID:
                    print(Ok("Invalid"))
                else:
                    print(Err(f"Incorrectly flagged as {result.status.name}"))
                    errors.append((name, validator.name))
            if not problem_name_printed:
                problems_skipped.append(f"{name} invalid[{i}]")

    if problems_run == 0:
        print("\n\nValidation problems skipped: ALL")
    elif problems_skipped:
        print("\n\nValidation test cases skipped:")
        print("   ", "\n    ".join(problems_skipped))

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

    print("\n\nGROUNDING:")
    errors: List[Tuple[str, str]] = []
    problems_skipped = []
    problems_run = 0
    for name, test_case in problems.items():
        pb = test_case.problem
        kind = pb.kind
        # if the problem is not action based or has no parameters in the actions, skip it
        if not kind.has_action_based() or not any(a.parameters for a in pb.actions):  # type: ignore [attr-defined] # If the kind has action_based, the pb.actions is defined
            continue

        name_printed = False

        for engine_id in grounders:
            compiler = Compiler(name=engine_id)
            if compiler.supports(kind):

                if not name_printed:
                    name_printed = True
                    problems_run += 1
                    print()
                    print(name.ljust(40), end="\n")

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
                    runtime = "{:.3f}s".format(end - start).ljust(15)
                    print(status, "    ", runtime, outcome)

                except Exception as e:
                    print(f"{bcolors.ERR}CRASH{bcolors.ENDC}", e)
                    errors.append((engine_id, name))
        if not name_printed:
            problems_skipped.append(name)

    if problems_run == 0:
        print("\n\nGrounding problems skipped: ALL")
    elif problems_skipped:
        print("\n\nGrounding problems skipped:")
        print("   ", "\n    ".join(problems_skipped))

    return errors


def main():
    parser = get_report_parser()
    parsed_args = parser.parse_args()
    engines = parsed_args.engines
    if not engines:
        engines = get_environment().factory.engines

    if parsed_args.packages:
        packages = parsed_args.packages
    else:
        packages = ["builtin", "unified_planning.test"]
        packages.extend(parsed_args.extra_packages)

    problem_test_cases = get_test_cases_from_packages(packages)

    filters = parsed_args.filters
    if filters:
        # Filter only the names that have at least one of the given filters in them
        problem_test_cases = dict(
            filter(
                lambda name_value: any(p in name_value[0] for p in filters),
                problem_test_cases.items(),
            )
        )

    timeout: Optional[float] = parsed_args.timeout
    assert timeout is not None
    if timeout <= 0:
        timeout = None

    modes = parsed_args.modes
    oneshot_errors = []
    validation_errors = []
    anytime_errors = []
    grounding_errors = []
    repair_errors = []

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        if "oneshot" in modes:
            oneshot_errors = report_oneshot(engines, problem_test_cases, timeout)
        if "anytime" in modes:
            anytime_errors = report_anytime(engines, problem_test_cases, timeout)
        if "repair" in modes:
            repair_errors = report_plan_repair(engines, problem_test_cases)
        if "validation" in modes:
            validation_errors = report_validation(engines, problem_test_cases)
        if "grounding" in modes:
            grounding_errors = report_grounding(engines, problem_test_cases)

    print()
    if oneshot_errors:
        print(
            "Oneshot errors:\n   ", "\n    ".join(map(str, oneshot_errors)), end="\n\n"
        )
    if anytime_errors:
        print(
            "Anytime errors:\n   ", "\n    ".join(map(str, anytime_errors)), end="\n\n"
        )
    if repair_errors:
        print(
            "Plan Repair errors:\n   ",
            "\n    ".join(map(str, repair_errors)),
            end="\n\n",
        )
    if validation_errors:
        print(
            "Validation errors:\n   ",
            "\n    ".join(map(str, validation_errors)),
            end="\n\n",
        )
    if grounding_errors:
        print(
            "Grounding errors:\n   ",
            "\n    ".join(map(str, grounding_errors)),
            end="\n\n",
        )
    errors = list(
        chain(
            oneshot_errors,
            validation_errors,
            anytime_errors,
            repair_errors,
            grounding_errors,
        )
    )

    if len(errors) > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
