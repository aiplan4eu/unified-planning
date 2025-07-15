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

import os
import unified_planning as up
from unified_planning.model import ProblemKind
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.engines import (
    PlanGenerationResult,
    PlanGenerationResultStatus,
    PDDLAnytimePlanner,
)
from unified_planning.engines.pddl_anytime_planner import Writer
from unified_planning.environment import get_environment
from unified_planning.io import PDDLWriter
from typing import List, Optional


FILE_PATH = os.path.dirname(os.path.abspath(__file__))


class ENHSP(PDDLAnytimePlanner):
    def __init__(self):
        PDDLAnytimePlanner.__init__(self, False, True)

    @property
    def name(self) -> str:
        return "ENHSP"

    def _get_cmd(
        self, domanin_filename: str, problem_filename: str, plan_filename: str
    ) -> List[str]:
        return [
            "java",
            "-jar",
            os.path.join(
                FILE_PATH, "..", "..", "..", ".planners", "enhsp-20", "enhsp.jar"
            ),
            "-o",
            domanin_filename,
            "-f",
            problem_filename,
            "-sp",
            plan_filename,
            "-planner",
            "opt-hrmax",
            "-npm",
        ]

    def _get_anytime_cmd(
        self, domanin_filename: str, problem_filename: str, plan_filename: str
    ) -> List[str]:
        return [
            "java",
            "-jar",
            os.path.join(
                FILE_PATH, "..", "..", "..", ".planners", "enhsp-20", "enhsp.jar"
            ),
            "-o",
            domanin_filename,
            "-f",
            problem_filename,
            "-sp",
            plan_filename,
            "-h",
            "hadd",
            "-s",
            "gbfs",
            "-anytime",
        ]

    def _result_status(
        self,
        problem: "up.model.Problem",
        plan: Optional["up.plans.Plan"],
        retval: int,
        log_messages: Optional[List["up.engines.LogMessage"]] = None,
    ) -> "up.engines.results.PlanGenerationResultStatus":
        if retval != 0:
            return up.engines.results.PlanGenerationResultStatus.INTERNAL_ERROR
        elif plan is None:
            return up.engines.results.PlanGenerationResultStatus.UNSOLVABLE_PROVEN
        else:
            return up.engines.results.PlanGenerationResultStatus.SOLVED_OPTIMALLY

    def _starting_plan_str(self) -> str:
        return "Found Plan:"

    def _ending_plan_str(self) -> str:
        return "Plan-Length:"

    def _parse_plan_line(self, plan_line: str) -> str:
        return plan_line.split(":")[1]

    @staticmethod
    def satisfies(optimality_guarantee: up.engines.OptimalityGuarantee) -> bool:
        return True

    @staticmethod
    def ensures(anytime_guarantee: up.engines.AnytimeGuarantee) -> bool:
        if anytime_guarantee == up.engines.AnytimeGuarantee.INCREASING_QUALITY:
            return True
        return False

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITIES")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        supported_kind.set_effects_kind("INCREASE_EFFECTS")
        supported_kind.set_effects_kind("DECREASE_EFFECTS")
        supported_kind.set_effects_kind("FORALL_EFFECTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("INCREASE_CONTINUOUS_EFFECTS")
        supported_kind.set_effects_kind("DECREASE_CONTINUOUS_EFFECTS")
        supported_kind.set_fluents_type("INT_FLUENTS")
        supported_kind.set_fluents_type("REAL_FLUENTS")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_quality_metrics("FINAL_VALUE")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        supported_kind.set_actions_cost_kind("INT_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("REAL_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("STATIC_FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_time("PROCESSES")
        supported_kind.set_time("EVENTS")
        supported_kind.set_initial_state("UNDEFINED_INITIAL_NUMERIC")
        return supported_kind

    @staticmethod
    def supports(problem_kind: "ProblemKind") -> bool:
        return problem_kind <= ENHSP.supported_kind()

    @staticmethod
    def get_credits(**kwargs) -> Optional[up.engines.Credits]:
        return None


environment = get_environment()
if os.path.isfile(
    os.path.join(FILE_PATH, "..", "..", "..", ".planners", "enhsp-20", "enhsp.jar")
):
    environment.factory.add_engine(
        "opt-pddl-planner", "unified_planning.test.pddl.enhsp", "ENHSP"
    )
