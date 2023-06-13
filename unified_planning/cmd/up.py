#!/usr/bin/env python

import argparse
from typing import Optional, cast
import unified_planning as up
from unified_planning.cmd.arg_parser import create_up_parser
from unified_planning.shortcuts import *
from unified_planning.engines import (
    CompilerResult,
    PlanGenerationResult,
    ValidationResult,
)
from unified_planning.io import PDDLReader, PDDLWriter, ANMLReader, ANMLWriter


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parser = create_up_parser()
    parsed_args = parser.parse_args(args)

    if parsed_args.mode == "oneshot-planning":
        oneshot_planning(parser, parsed_args)
    elif parsed_args.mode == "anytime-planning":
        anytime_planning(parser, parsed_args)
    elif parsed_args.mode == "plan-validation":
        plan_validation(parser, parsed_args)
    elif parsed_args.mode == "compile":
        compile(parser, parsed_args)
    elif parsed_args.mode == "list-engines":
        print_engines_info(
            operation_mode=parsed_args.operation_mode,
            show_supported_kind=parsed_args.show_kind,
        )
    else:
        raise NotImplementedError


def oneshot_planning(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
):
    original_problem = parse_problem(parser, args)
    problem: AbstractProblem = original_problem
    compilation_kind, compilation_kinds = args.compilation_kind, args.compilation_kinds
    compilation_res: Optional[CompilerResult] = None
    if compilation_kind is not None or compilation_kinds is not None:
        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=compilation_kind,
            compilation_kinds=compilation_kinds,
        ) as compiler:
            compilation_res = compiler.compile(problem)
            assert compilation_res is not None
            assert compilation_res.problem is not None
            problem = cast(AbstractProblem, compilation_res.problem)
    with OneshotPlanner(
        name=args.engine_name,
        names=args.engine_names,
        optimality_guarantee=args.optimality_guarantee,
        problem_kind=problem.kind,
    ) as planner:
        plan_gen_res: PlanGenerationResult = planner.solve(
            problem,
            timeout=args.timeout,
            output_stream=sys.stdout if args.show_log else None,
        )
        print(f"Status returned by {planner.name}: {plan_gen_res.status.name}")
        plan = plan_gen_res.plan
        plan_filename = args.plan_filename
        if plan is not None and compilation_res is not None:
            map_back_action_instance = compilation_res.map_back_action_instance
            assert map_back_action_instance is not None
            plan = plan.replace_action_instances(map_back_action_instance)
        if plan is None:
            print("No plan found!")
            exit(1)
        else:
            print("Plan found:", plan, sep="\n")
            if plan_filename is not None:
                writer = PDDLWriter(original_problem)
                writer.write_plan(plan, plan_filename)


def anytime_planning(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
):
    original_problem = parse_problem(parser, args)
    problem: AbstractProblem = original_problem
    compilation_kind, compilation_kinds = args.compilation_kind, args.compilation_kinds
    compilation_res: Optional[CompilerResult] = None
    if compilation_kind is not None or compilation_kinds is not None:
        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=compilation_kind,
            compilation_kinds=compilation_kinds,
        ) as compiler:
            compilation_res = compiler.compile(problem)
            assert compilation_res is not None
            assert compilation_res.problem is not None
            problem = cast(AbstractProblem, compilation_res.problem)
    with AnytimePlanner(
        name=args.engine_name,
        anytime_guarantee=args.anytime_guarantee,
        problem_kind=problem.kind,
    ) as anytime_planner:
        last_plan_found = None
        try:
            for plan_gen_res in anytime_planner.get_solutions(
                problem,
                timeout=args.timeout,
                output_stream=sys.stdout if args.show_log else None,
            ):
                print(
                    f"Status returned by {anytime_planner.name}: {plan_gen_res.status.name}"
                )
                plan = plan_gen_res.plan
                plan_filename = args.plan_filename
                if plan is not None and compilation_res is not None:
                    map_back_action_instance = compilation_res.map_back_action_instance
                    assert map_back_action_instance is not None
                    plan = plan.replace_action_instances(map_back_action_instance)
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
    plan_to_repair = reader.parse_plan(problem, plan_filename)

    with PlanRepairer(
        name=engine_name,
        problem_kind=problem_kind,
        plan_kind=plan_to_repair.kind,
        optimality_guarantee=args.optimality_guarantee,
    ) as repairer:
        plan_gen_res: PlanGenerationResult = repairer.repair(
            problem, plan_to_repair, optimality_guarantee=args.optimality_guarantee
        )
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
        written_to_file = False
        if args.anml_out is not None:
            anml_writer = ANMLWriter(problem)
            anml_writer.write_problem(args.anml_out)
            written_to_file = True
        if args.pddl_out is not None:
            domain_filename, problem_filename = args.pddl_out
            pddl_writer = PDDLWriter(problem)
            pddl_writer.write_domain(domain_filename)
            pddl_writer.write_problem(problem_filename)
            written_to_file = True
        if not written_to_file:
            print(problem)


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
        p_reader = PDDLReader()
        problem = p_reader.parse_problem(*pddl)
    elif anml is not None:
        if len(anml) == 1:
            anml = anml[0]
        a_reader = ANMLReader()
        problem = a_reader.parse_problem(anml)
    return problem


if __name__ == "__main__":
    main(sys.argv[1:])
