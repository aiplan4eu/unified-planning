#!/usr/bin/env python

import argparse
import warnings
from typing import List, Optional, Tuple
import unified_planning as up
from unified_planning.cmd.arg_parser import create_up_parser
from unified_planning.shortcuts import *
from unified_planning.engines import (
    OperationMode,
    AnytimeGuarantee,
    OptimalityGuarantee,
    CompilationKind,
    CompilerResult,
    PlanGenerationResult,
    ValidationResult,
)
from unified_planning.io import PDDLReader, PDDLWriter, ANMLReader, ANMLWriter

# TODO in anytime_planning decide if use this handling or the KeyboardException Handler
# import signal
# import sys
# def signal_handler(sig, frame):
#     print('You pressed Ctrl+C!')
#     sys.exit(0)

# signal.signal(signal.SIGINT, signal_handler)
# print('Press Ctrl+C')
# signal.pause()


def main():
    parser = create_up_parser()
    args = parser.parse_args()

    engine_name, engine_names = args.engine_name, args.engine_names
    if engine_name is not None and engine_names is not None:
        parser.error("--engine (or -e) and --engines are mutually exclusive")

    if args.mode == "oneshot-planning":
        oneshot_planning(parser, args)
    elif args.mode == "anytime-planning":
        anytime_planning(parser, args)
    elif args.mode == "plan-validation":
        plan_validation(parser, args)
    elif args.mode == "compile":
        compile(parser, args)


def oneshot_planning(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
):
    original_problem = parse_problem(parser, args)
    problem = original_problem
    compilation_kind, compilation_kinds = args.compilation_kind, args.compilation_kinds
    compilation_res: Optional[CompilerResult] = None
    if compilation_kind is not None or compilation_kinds is not None:
        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=compilation_kind,
            compilation_kinds=compilation_kinds,
        ) as compiler:
            compilation_res = compiler.compile(problem)
            problem = compilation_res.problem
    with OneshotPlanner(
        name=args.engine_name,
        names=args.engine_names,
        optimality_guarantee=args.optimality_guarantee,
        problem_kind=problem.kind,
    ) as planner:
        plan_gen_res: PlanGenerationResult = planner.solve(
            problem, timeout=args.timeout
        )
        print(f"Status returned by {planner.name}: {plan_gen_res.status.name}")
        plan = plan_gen_res.plan
        plan_filename = args.plan_filename
        if plan is not None and compilation_res is not None:
            plan = plan.replace_action_instances(
                compilation_res.map_back_action_instance
            )
        if plan is None:
            print("No plan found!")
            exit(1)
        else:
            print("Plan found:", plan, sep="\n")
            if plan_filename is not None:
                writer = PDDLWriter(original_problem)
                writer.write_plan(plan, plan_filename)
    unused_options: List[str] = []
    if args.anytime_guarantee is not None:
        unused_options.append("--anytime-guarantee")
    if args.pddl_out is not None:
        unused_options.append("--pddl-output")
    if args.anml_out is not None:
        unused_options.append("--anml-output")
    if args.kind is not None:
        unused_options.append("--kind")
    if args.kinds is not None:
        unused_options.append("--kinds")
    if unused_options:
        warnings.warn(
            f"With oneshot-planning mode the following specified options are ignored: {unused_options}",
            stacklevel=4,
        )


def anytime_planning(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
):
    original_problem = parse_problem(parser, args)
    problem = original_problem
    compilation_kind, compilation_kinds = args.compilation_kind, args.compilation_kinds
    compilation_res: Optional[CompilerResult] = None
    if compilation_kind is not None or compilation_kinds is not None:
        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=compilation_kind,
            compilation_kinds=compilation_kinds,
        ) as compiler:
            compilation_res = compiler.compile(problem)
            problem = compilation_res.problem
    with AnytimePlanner(
        name=args.engine_name,
        anytime_guarantee=args.anytime_guarantee,
        problem_kind=problem.kind,
    ) as anytime_planner:
        last_plan_found = None
        try:
            for plan_gen_res in anytime_planner.get_solutions(
                problem, timeout=args.timeout
            ):
                print(
                    f"Status returned by {anytime_planner.name}: {plan_gen_res.status.name}"
                )
                plan = plan_gen_res.plan
                plan_filename = args.plan_filename
                if plan is not None and compilation_res is not None:
                    plan = plan.replace_action_instances(
                        compilation_res.map_back_action_instance
                    )
                if plan is not None:
                    last_plan_found = plan
                    print("Plan found:", plan, sep="\n")
        except KeyboardInterrupt:
            pass
        finally:
            if last_plan_found is None:
                print("No plan found!")
                exit(1)
            if plan_filename is not None:
                writer = PDDLWriter(original_problem)
                writer.write_plan(last_plan_found, plan_filename)
    unused_options: List[str] = []
    if args.engine_names is not None:
        unused_options.append("--engines")
    if args.optimality_guarantee is not None:
        unused_options.append("--optimality-guarantee")
    if args.pddl_out is not None:
        unused_options.append("--pddl-output")
    if args.anml_out is not None:
        unused_options.append("--anml-output")
    if args.kind is not None:
        unused_options.append("--kind")
    if args.kinds is not None:
        unused_options.append("--kinds")
    if unused_options:
        warnings.warn(
            f"With oneshot-planning mode the following specified options are ignored: {unused_options}",
            stacklevel=4,
        )


def plan_validation(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
):
    problem = parse_problem(parser, args)
    engine_name, engine_names = args.engine_name, args.engine_names
    plan_filename = args.plan_filename
    if plan_filename is None:
        parser.error("plan-validation mode requires the --plan option")
    problem_kind = problem.kind
    reader = PDDLReader()
    plan = reader.parse_plan(problem, plan_filename)

    with PlanValidator(
        name=engine_name,
        names=engine_names,
        problem_kind=problem_kind,
        plan_kind=plan.kind,
    ) as validator:
        val_res: ValidationResult = validator.validate(problem, plan)
        print(val_res)

    unused_options: List[str] = []
    if args.optimality_guarantee is not None:
        unused_options.append("--optimality-guarantee")
    if args.anytime_guarantee is not None:
        unused_options.append("--anytime-guarantee")
    if args.pddl_out is not None:
        unused_options.append("--pddl-output")
    if args.anml_out is not None:
        unused_options.append("--anml-output")
    if args.timeout is not None:
        unused_options.append("--timeout")
    if args.kind is not None:
        unused_options.append("--kind")
    if args.kinds is not None:
        unused_options.append("--kinds")
    if unused_options:
        warnings.warn(
            "With plan-validation mode the following specified options are ignored:",
            *unused_options,
            stacklevel=4,
        )


def plan_repair(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
):
    problem = parse_problem(parser, args)
    engine_name = args.engine_name
    plan_filename = args.plan_filename
    if plan_filename is None:
        parser.error("plan-repair mode requires the --plan option")
    problem_kind = problem.kind
    reader = PDDLReader()
    plan = reader.parse_plan(problem, plan_filename)

    with PlanRepairer(
        name=engine_name,
        problem_kind=problem_kind,
        plan_kind=plan.kind,
        optimality_guarantee=args.optimality_guarantee,
    ) as repairer:
        plan_gen_res: PlanGenerationResult = repairer.repair(problem, plan)
        print(f"Status returned by {repairer.name}: {plan_gen_res.status.name}")
        plan = plan_gen_res.plan
        plan_filename = args.plan_filename
        if plan is None:
            print("No plan found!")
            exit(1)
        else:
            print("Plan found:", plan, sep="\n")
            if plan_filename is not None:
                writer = PDDLWriter(problem)
                writer.write_plan(plan, plan_filename)

    unused_options: List[str] = []
    if args.engine_names is not None:
        unused_options.append("--engines")
    if args.optimality_guarantee is not None:
        unused_options.append("--optimality-guarantee")
    if args.anytime_guarantee is not None:
        unused_options.append("--anytime-guarantee")
    if args.pddl_out is not None:
        unused_options.append("--pddl-output")
    if args.anml_out is not None:
        unused_options.append("--anml-output")
    if args.timeout is not None:
        unused_options.append("--timeout")
    if args.kind is not None:
        unused_options.append("--kind")
    if args.kinds is not None:
        unused_options.append("--kinds")
    if unused_options:
        warnings.warn(
            "With plan-repair mode the following specified options are ignored:",
            *unused_options,
            stacklevel=4,
        )


def compile(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
):
    problem = parse_problem(parser, args)
    compilation_kind, compilation_kinds = args.kind, args.kinds
    engine_name = args.engine_name
    if compilation_kind is None and compilation_kinds is None and engine_name is None:
        parser.error(
            "with compile mode one between --engine (or -e), --kind and --kinds is required"
        )
    if compilation_kind is not None and compilation_kinds is not None:
        parser.error("with compile mode --kind and --kinds are mutually exclusive")
    with Compiler(
        name=args.engine_name,
        problem_kind=problem.kind,
        compilation_kind=compilation_kind,
        compilation_kinds=compilation_kinds,
    ) as compiler:
        compilation_res = compiler.compile(problem)
        problem = compilation_res.problem
        print(problem)

    unused_options: List[str] = []
    if args.anytime_guarantee is not None:
        unused_options.append("--anytime-guarantee")
    if args.pddl_out is not None:
        unused_options.append("--pddl-output")
    if args.anml_out is not None:
        unused_options.append("--anml-output")
    if args.timeout is not None:
        unused_options.append("--timeout")
    if args.kind is not None:
        unused_options.append("--kind")
    if args.kinds is not None:
        unused_options.append("--kinds")
    if unused_options:
        warnings.warn(
            f"With oneshot-planning mode the following specified options are ignored: {unused_options}",
            stacklevel=4,
        )


def parse_problem(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> Problem:
    pddl, anml = args.pddl, args.anml
    if (pddl is None and anml is None) or (pddl is not None and anml is not None):
        parser.error(
            f"{args.mode} mode requires ONE and ONLY ONE of --pddl or --anml options"
        )
    if pddl is not None:
        assert len(pddl) == 2, "ArgParsing error"
        reader = PDDLReader()
        problem = reader.parse_problem(*pddl)
        return problem
    elif anml is not None:
        assert (
            len(anml) == 1
        ), "For now only 1 anml file can be parsed"  # TODO remove this when ANMLReader can parse multiple files
        reader = ANMLReader()
        problem = reader.parse_problem(*anml)
        return problem

    # engine_name: Optional[str],
    # engine_names: Optional[List[str]],
    # pddl: Optional[List[str]],
    # anml: Optional[List[str]],
    # optimality_guarantee: Optional[str],
    # anytime_guarantee: Optional[str],
    # plan_filename: Optional[str],
    # pddl_out: Optional[List[str]],
    # anml_out: Optional[str],
    # kind: Optional[str],
    # kinds: Optional[List[str]],


if __name__ == "__main__":
    main()
