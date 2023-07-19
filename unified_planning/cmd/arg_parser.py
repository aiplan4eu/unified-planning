# Copyright 2021-2023 AIPlan4EU project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import argparse
from unified_planning.engines import (
    AnytimeGuarantee,
    OptimalityGuarantee,
    CompilationKind,
    OperationMode,
)


def create_up_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Perform a Unified Planning Operation mode.",
        allow_abbrev=False,
    )
    compilation_kind_explaination = f"COMPILATION_KIND is one of {{{','.join((ck.name.lower() for ck in CompilationKind))}}}"
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
    )
    plan_validation_parser.set_defaults(cmd="plan-validation")

    plan_repair_parser = subparsers.add_parser(
        "plan-repair",
    )
    plan_repair_parser.set_defaults(cmd="plan-repair")

    compile_parser = subparsers.add_parser(
        "compile",
        epilog=compilation_kind_explaination,
    )
    compile_parser.set_defaults(cmd="compile")

    list_engines_parser = subparsers.add_parser(
        "list-engines",
    )
    compile_parser.set_defaults(cmd="list-engines")

    # Options:
    # --engine, -e
    # --engines
    # --pddl
    # --anml
    # --timeout
    # --plan
    # --compilation-kind
    # --compilation-kinds
    # --optimality-guarantee
    # --anytime-guarantee
    # --pddl-output
    # --anml-output
    # --kind
    # --kinds
    # --operation-mode
    # --log, -l

    for sub_parser in (
        oneshot_planning_parser,
        anytime_planning_parser,
        plan_validation_parser,
        plan_repair_parser,
        compile_parser,
    ):
        mutually_exclusive = sub_parser.add_mutually_exclusive_group()
        mutually_exclusive.add_argument(
            "--pddl",
            type=str,
            nargs=2,
            help="The path of the pddl domain and pddl problem file",
            dest="pddl",
            metavar="PDDL_FILENAME",
        )
        mutually_exclusive.add_argument(
            "--anml",
            type=str,
            nargs="+",
            help="The path of the anml file",
            dest="anml",
            metavar="ANML_FILENAME",
        )
        # skip oneshot-planning, defined later mutually exclusive with --engines
        if sub_parser != oneshot_planning_parser:
            sub_parser.add_argument(
                "--engine",
                "-e",
                type=str,
                help="The name of the engine to use",
                dest="engine_name",
            )

    mutually_exclusive = oneshot_planning_parser.add_mutually_exclusive_group()
    mutually_exclusive.add_argument(
        "--engine",
        "-e",
        type=str,
        help="The name of the engine to use",
        dest="engine_name",
    )
    mutually_exclusive.add_argument(
        "--engines",
        type=str,
        nargs="+",
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
            help="The filename where to write the plan",
            dest="plan_filename",
            metavar="PLAN_FILENAME",
        )
        sub_parser.add_argument(
            "--logs",
            "-l",
            action="store_true",
            help="If set shows the logs of the planner",
            dest="show_log",
            default=False,
        )
        mutually_exclusive = sub_parser.add_mutually_exclusive_group()
        mutually_exclusive.add_argument(
            "--compilation-kind",
            type=str,
            help="The compilation to apply before the engine",
            dest="compilation_kind",
            metavar="COMPILATION_KIND",
        )
        mutually_exclusive.add_argument(
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
            help="The filename where to read the plan",
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

    compile_parser_mutually_exclusive = compile_parser.add_mutually_exclusive_group()
    compile_parser_mutually_exclusive.add_argument(
        "--kind",
        type=str,
        help="The compilation to apply to the problem",
        dest="kind",
        metavar="COMPILATION_KIND",
    )

    compile_parser_mutually_exclusive.add_argument(
        "--kinds",
        type=str,
        nargs="+",
        help="The sequence of compilations to apply to the problem",
        dest="kinds",
        metavar="COMPILATION_KIND",
    )

    list_engines_parser.add_argument(
        "--operation-mode",
        type=str,
        help="Only the engines capable of handling this operation mode are listed",
        dest="operation_mode",
        choices=[om.name.lower() for om in OperationMode],
    )

    list_engines_parser.add_argument(
        "--show-kind",
        action="store_true",
        help="If specified, shows the engine's supported kind",
        dest="show_kind",
        default=False,
    )
    return parser
