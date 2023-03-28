# Copyright 2021 AIPlan4EU project
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
import unified_planning.engines
from unified_planning.model.problem_kind import ProblemKind
from unified_planning.engines import PlanGenerationResult, PlanGenerationResultStatus
from unified_planning.environment import get_environment
from typing import List, Optional, Union, IO, Iterator


FILE_PATH = os.path.dirname(os.path.abspath(__file__))


class ENHSP(up.engines.PDDLPlanner, up.engines.mixins.AnytimePlannerMixin):
    def __init__(self):
        up.engines.PDDLPlanner.__init__(self, False)
        self._options = ["-planner", "opt-hrmax"]

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
        ] + self._options

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

    def _get_solutions(
        self,
        problem: "up.model.AbstractProblem",
        timeout: Optional[float] = None,
        output_stream: Optional[IO[str]] = None,
    ) -> Iterator["up.engines.results.PlanGenerationResult"]:
        import threading
        import queue

        opts = self._options

        self._options = [
            "-h",
            "hadd",
            "-s",
            "gbfs",
            "-anytime",
        ]

        if timeout is not None:
            self._options.extend(["-timeout", str(timeout)])

        q: queue.Queue = queue.Queue()

        class Writer(up.AnyBaseClass):
            def __init__(self, os, q, engine):
                self._os = os
                self._q = q
                self._engine = engine
                self._plan = []
                self._storing = False

            def write(self, txt: str):
                if self._os is not None:
                    self._os.write(txt)
                for l in txt.splitlines():
                    if "Found Plan:" in l:
                        self._storing = True
                    elif "Plan-Length:" in l:
                        plan_str = "\n".join(self._plan)
                        plan = self._engine._plan_from_str(
                            problem, plan_str, self._engine._writer.get_item_named
                        )
                        res = PlanGenerationResult(
                            PlanGenerationResultStatus.INTERMEDIATE,
                            plan=plan,
                            engine_name=self._engine.name,
                        )
                        self._q.put(res)
                        self._plan = []
                        self._storing = False
                    elif self._storing and l:
                        self._plan.append(l.split(":")[1])

        def run():
            writer: IO[str] = Writer(output_stream, q, self)
            res = self._solve(problem, output_stream=writer)
            q.put(res)

        try:
            t = threading.Thread(target=run, daemon=True)
            t.start()
            status = PlanGenerationResultStatus.INTERMEDIATE
            while status == PlanGenerationResultStatus.INTERMEDIATE:
                res = q.get()
                status = res.status
                yield res
        finally:
            if self._process is not None:
                try:
                    self._process.kill()
                except OSError:
                    pass  # This can happen if the process is already terminated
            t.join()
            self._options = opts

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
        supported_kind = ProblemKind()
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_numbers("DISCRETE_NUMBERS")
        supported_kind.set_numbers("CONTINUOUS_NUMBERS")
        supported_kind.set_numbers("BOUNDED_TYPES")
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
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_fluents_type("NUMERIC_FLUENTS")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_quality_metrics("FINAL_VALUE")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
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
