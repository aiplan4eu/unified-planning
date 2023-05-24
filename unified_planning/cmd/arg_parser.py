import argparse
from unified_planning.engines import (
    AnytimeGuarantee,
    OptimalityGuarantee,
    CompilationKind,
)


def create_up_parser() -> argparse.ArgumentParser:
    epilog_str = ",".join((ck.name.lower() for ck in CompilationKind))
    parser = argparse.ArgumentParser(
        description=f"Perform a Unified Planning Operation mode. COMPILATION_KIND is one of {{{epilog_str}}}",
        allow_abbrev=False,
        epilog=f"COMPILATION_KIND is one of {{{epilog_str}}}",  # TODO decide if leave this part in epilog or description, and maybe play a bit with formatters
    )
    parser.add_argument(
        "mode",
        type=str,
        choices=[
            "oneshot-planning",
            "anytime-planning",
            "plan-validation",
            "plan-repair",
            "compile",
        ],
        help="the operation mode to perform",
    )
    parser.add_argument(
        "--engine",
        "-e",
        type=str,
        # choices=[available engines], #TODO decide if put choices here
        help="The name of the engine to use",
        dest="engine_name",
    )
    parser.add_argument(
        "--engines",
        type=str,
        # choices=[available engines], #TODO decide if put choices here
        help="The names of the engines to put in parallel; compatible only if the mode is oneshot-planning",
        dest="engine_names",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        help="The timeout in seconds for the engine; compatible with: oneshot-planning and anytime-planning",
        dest="timeout",
    )
    parser.add_argument(
        "--pddl",
        type=str,
        nargs=2,
        help="The path of the pddl domain and pddl problem file",
        dest="pddl",
        metavar="PDDL_FILENAME",
    )
    parser.add_argument(
        "--anml",
        type=str,
        nargs="+",
        help="The path of the anml file",
        dest="anml",
        metavar="ANML_FILENAME",
    )
    parser.add_argument(
        "--optimality-guarantee",
        "-o",
        type=str,
        choices=[og.name.lower() for og in OptimalityGuarantee],
        help="The required optimality guarantee; compatible with: oneshot-planning and plan-repair",
        dest="optimality_guarantee",
    )
    parser.add_argument(
        "--anytime-guarantee",
        "-a",
        type=str,
        choices=[ag.name.lower() for ag in AnytimeGuarantee],
        help="The required anytime guarantee; compatible with: anytime-planning",
        dest="anytime_guarantee",
    )
    parser.add_argument(
        "--plan",
        type=str,
        help="The filename where to write or read the plan; compatible with: oneshot-planning, anytime-planning, plan-validation and plan-repair",
        dest="plan_filename",
        metavar="PLAN_FILENAME",
    )
    parser.add_argument(
        "--pddl-output",
        type=str,
        nargs=2,
        help="The path of the pddl domain and pddl problem file where the compiled problem is written; compatible with: compiler",
        dest="pddl_out",
        metavar="PDDL_OUT_FILENAME",
    )
    parser.add_argument(
        "--anml-output",
        type=str,
        help="The path of the anml file where the compiled problem is written; compatible with: compiler",
        dest="anml_out",
        metavar="ANML_FILENAME",
    )
    parser.add_argument(
        "--kind",
        type=str,
        help="The compilation to apply to the problem; compatible with: compiler",
        dest="kind",
        metavar="COMPILATION_KIND",
    )
    parser.add_argument(
        "--kinds",
        type=str,
        nargs="+",
        help="The sequence of compilations to apply to the problem; compatible with: compiler",
        dest="kinds",
        metavar="COMPILATION_KIND",
    )
    parser.add_argument(
        "--compilation-kind",
        type=str,
        help="The compilation to apply before the engine; compatible with: oneshot-planning and anytime-planning",
        dest="compilation_kind",
        metavar="COMPILATION_KIND",
    )
    parser.add_argument(
        "--compilation-kinds",
        type=str,
        nargs="+",
        help="The Sequence of compilations to apply before the engine; compatible with: oneshot-planning and anytime-planning",
        dest="compilation_kinds",
        metavar="COMPILATION_KIND",
    )
    return parser
