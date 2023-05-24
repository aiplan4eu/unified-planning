import argparse
from unified_planning.engines import (
    AnytimeGuarantee,
    OptimalityGuarantee,
    CompilationKind,
)


def create_up_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Perform a Unified Planning Operation mode.",
        allow_abbrev=False,
    )
    compilation_kind_explaination = f"COMPILATION_KIND is one of {{{','.join((ck.name.lower() for ck in CompilationKind))}}}"
    # parser.add_argument(
    #     "mode",
    #     type=str,
    #     choices=[
    #         "oneshot-planning",
    #         "anytime-planning",
    #         "plan-validation",
    #         "plan-repair",
    #         "compile",
    #     ],
    #     help="the operation mode to perform",
    # )
    subparsers = parser.add_subparsers(
        title="modes",
        description="valid modes",
        dest="mode",
    )
    oneshot_planning_parser = subparsers.add_parser(
        "oneshot-planning",
        epilog=compilation_kind_explaination,
    )
    oneshot_planning_parser.set_defaults(cmd="oneshot-planning")

    anytime_planning_parser = subparsers.add_parser(
        "anytime-planning",
        epilog=compilation_kind_explaination,
    )
    anytime_planning_parser.set_defaults(cmd="anytime-planning")

    plan_validation_parser = subparsers.add_parser(
        "plan-validation",
        epilog=compilation_kind_explaination,
    )
    plan_validation_parser.set_defaults(cmd="plan-validation")

    plan_repair_parser = subparsers.add_parser(
        "plan-repair",
        epilog=compilation_kind_explaination,
    )
    plan_repair_parser.set_defaults(cmd="plan-repair")

    compile_parser = subparsers.add_parser(
        "compile",
        epilog=compilation_kind_explaination,
    )
    compile_parser.set_defaults(cmd="compile")

    for sub_parser in (
        oneshot_planning_parser,
        anytime_planning_parser,
        plan_validation_parser,
        plan_repair_parser,
        compile_parser,
    ):
        sub_parser.add_argument(
            "--engine",
            "-e",
            type=str,
            # choices=[available engines], #TODO decide if put choices here
            help="The name of the engine to use",
            dest="engine_name",
        )
        sub_parser.add_argument(
            "--pddl",
            type=str,
            nargs=2,
            help="The path of the pddl domain and pddl problem file",
            dest="pddl",
            metavar="PDDL_FILENAME",
        )
        sub_parser.add_argument(
            "--anml",
            type=str,
            nargs="+",
            help="The path of the anml file",
            dest="anml",
            metavar="ANML_FILENAME",
        )

    oneshot_planning_parser.add_argument(
        "--engines",
        type=str,
        # choices=[available engines], #TODO decide if put choices here
        help="The names of the engines to put in parallel",
        dest="engine_names",
    )

    for sub_parser in (oneshot_planning_parser, anytime_planning_parser):
        sub_parser.add_argument(
            "--timeout",
            type=float,
            help="The timeout in seconds for the engine",
            dest="timeout",
        )
        sub_parser.add_argument(
            "--plan",
            type=str,
            help="The filename where to write or read the plan",
            dest="plan_filename",
            metavar="PLAN_FILENAME",
        )
        sub_parser.add_argument(
            "--compilation-kind",
            type=str,
            help="The compilation to apply before the engine",
            dest="compilation_kind",
            metavar="COMPILATION_KIND",
        )
        sub_parser.add_argument(
            "--compilation-kinds",
            type=str,
            nargs="+",
            help="The Sequence of compilations to apply before the engine",
            dest="compilation_kinds",
            metavar="COMPILATION_KIND",
        )

    for sub_parser in (plan_validation_parser, plan_repair_parser):
        sub_parser.add_argument(
            "--plan",
            type=str,
            help="The filename where to write or read the plan",
            dest="plan_filename",
            metavar="PLAN_FILENAME",
            required=True,
        )

    for sub_parser in (oneshot_planning_parser, plan_repair_parser):
        sub_parser.add_argument(
            "--optimality-guarantee",
            "-o",
            type=str,
            choices=[og.name.lower() for og in OptimalityGuarantee],
            help="The required optimality guarantee",
            dest="optimality_guarantee",
        )

    anytime_planning_parser.add_argument(
        "--anytime-guarantee",
        "-a",
        type=str,
        choices=[ag.name.lower() for ag in AnytimeGuarantee],
        help="The required anytime guarantee",
        dest="anytime_guarantee",
    )

    compile_parser.add_argument(
        "--pddl-output",
        type=str,
        nargs=2,
        help="The path of the pddl domain and pddl problem file where the compiled problem is written",
        dest="pddl_out",
        metavar="PDDL_OUT_FILENAME",
    )

    compile_parser.add_argument(
        "--anml-output",
        type=str,
        help="The path of the anml file where the compiled problem is written",
        dest="anml_out",
        metavar="ANML_FILENAME",
    )

    compile_parser.add_argument(
        "--kind",
        type=str,
        help="The compilation to apply to the problem",
        dest="kind",
        metavar="COMPILATION_KIND",
    )

    compile_parser.add_argument(
        "--kinds",
        type=str,
        nargs="+",
        help="The sequence of compilations to apply to the problem",
        dest="kinds",
        metavar="COMPILATION_KIND",
    )
    return parser
