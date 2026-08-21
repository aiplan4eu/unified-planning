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


from unified_planning.environment import Environment
from unified_planning.engines.engine import Engine
from unified_planning.engines.mixins.oneshot_planner import OneshotPlannerMixin
from unified_planning.engines.results import (
    PlanGenerationResult,
    PlanGenerationResultStatus,
)
from unified_planning.model import Fluent, InstantaneousAction, Problem, ProblemKind
from unified_planning.plans import SequentialPlan
from unified_planning.test import unittest_TestCase, main


class ArgRecordingEngine(Engine, OneshotPlannerMixin):
    """Oneshot planner that reports the arguments it actually received back in the result metrics."""

    def __init__(self, **kwargs):
        Engine.__init__(self)
        OneshotPlannerMixin.__init__(self)

    @property
    def name(self) -> str:
        return "arg-recording-engine"

    @staticmethod
    def supported_kind() -> ProblemKind:
        return ProblemKind()

    @staticmethod
    def supports(problem_kind: ProblemKind) -> bool:
        return True

    def _solve(self, problem, heuristic=None, timeout=None, output_stream=None):
        return PlanGenerationResult(
            PlanGenerationResultStatus.UNSOLVABLE_INCOMPLETELY,
            None,
            self.name,
            metrics={"heuristic": repr(heuristic), "timeout": repr(timeout)},
        )


class TestParallel(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        # Use a dedicated Environment so registering the dummy engine does not
        # leak into the global factory used by the rest of the test suite.
        self.env = Environment()
        self.env.factory.add_engine(
            "arg-recording-engine", __name__, "ArgRecordingEngine"
        )

        a = Fluent("a", environment=self.env)
        act = InstantaneousAction("act", _env=self.env)
        act.add_effect(a, True)
        problem = Problem("test", self.env)
        problem.add_fluent(a, default_initial_value=False)
        problem.add_action(act)
        problem.add_goal(a)
        self.problem = problem
        self.act = act

    def test_solve_forwards_timeout_to_sub_engines(self):
        with self.env.factory.OneshotPlanner(
            names=["arg-recording-engine"], params=[{}]
        ) as planner:
            result = planner.solve(self.problem, timeout=42.0)
            self.assertEqual(result.metrics["timeout"], repr(42.0))
            self.assertEqual(result.metrics["heuristic"], repr(None))

    def test_solve_warns_on_ignored_heuristic(self):
        with self.env.factory.OneshotPlanner(
            names=["arg-recording-engine"], params=[{}]
        ) as planner:
            with self.assertWarns(UserWarning):
                result = planner.solve(self.problem, heuristic=lambda state: 0.0)
            self.assertEqual(result.metrics["heuristic"], repr(None))

    def test_validate_still_dispatches(self):
        plan = SequentialPlan([self.act()], environment=self.env)
        with self.env.factory.PlanValidator(
            names=["sequential_plan_validator", "sequential_plan_validator"]
        ) as validator:
            validation_result = validator.validate(self.problem, plan)
            self.assertTrue(validation_result)


if __name__ == "__main__":
    main()
