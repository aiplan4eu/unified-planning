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

from shutil import move
import warnings
import unified_planning as up
from unified_planning.shortcuts import *
from unified_planning.model.problem_kind import (
    classical_kind,
    basic_numeric_kind,
    quality_metrics_kind,
)
from unified_planning.test import TestCase, main, skipIfEngineNotAvailable
from unified_planning.test import skipIfNoOneshotPlannerForProblemKind
from unified_planning.test import skipIfNoOneshotPlannerSatisfiesOptimalityGuarantee
from unified_planning.test.examples import get_example_problems
from unified_planning.engines import PlanGenerationResultStatus, CompilationKind
from unified_planning.engines.results import POSITIVE_OUTCOMES


class TestPlanner(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfEngineNotAvailable("tamer")
    def test_basic(self):
        problem = self.problems["basic"].problem
        a = problem.action("a")

        with OneshotPlanner(name="tamer", params={"weight": 0.8}) as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)
            plan = final_report.plan
            self.assertEqual(
                final_report.status, PlanGenerationResultStatus.SOLVED_SATISFICING
            )
            self.assertEqual(len(plan.actions), 1)
            self.assertEqual(plan.actions[0].action, a)
            self.assertEqual(len(plan.actions[0].actual_parameters), 0)

    @skipIfEngineNotAvailable("tamer")
    def test_basic_with_timeout(self):
        problem = self.problems["basic"].problem
        a = problem.action("a")

        with OneshotPlanner(name="tamer", params={"weight": 0.8}) as planner:
            self.assertNotEqual(planner, None)
            with warnings.catch_warnings(record=True) as w:
                final_report = planner.solve(problem, timeout=0.001)
                self.assertIn(final_report.status, POSITIVE_OUTCOMES)
                plan = final_report.plan
                self.assertEqual(
                    final_report.status, PlanGenerationResultStatus.SOLVED_SATISFICING
                )
                self.assertEqual(len(plan.actions), 1)
                self.assertEqual(plan.actions[0].action, a)
                self.assertEqual(len(plan.actions[0].actual_parameters), 0)
                self.assertEqual(len(w), 1)
                self.assertEqual("Tamer does not support timeout.", str(w[-1].message))

    @skipIfEngineNotAvailable("tamer")
    def test_basic_parallel(self):
        problem = self.problems["basic"].problem
        a = problem.action("a")

        with OneshotPlanner(
            names=["tamer", "tamer"],
            params=[{"heuristic": "hadd"}, {"heuristic": "hmax"}],
        ) as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)
            plan = final_report.plan
            self.assertEqual(
                final_report.status, PlanGenerationResultStatus.SOLVED_SATISFICING
            )
            self.assertEqual(len(plan.actions), 1)
            self.assertEqual(plan.actions[0].action, a)
            self.assertEqual(len(plan.actions[0].actual_parameters), 0)

    @skipIfEngineNotAvailable("tamer")
    def test_timed_connected_locations_parallel(self):
        problem = self.problems["timed_connected_locations"].problem
        move = problem.action("move")
        with OneshotPlanner(
            names=["tamer", "tamer"],
            params=[{"heuristic": "hadd"}, {"heuristic": "hmax"}],
        ) as planner:
            self.assertNotEqual(planner, None)
            with self.assertRaises(up.exceptions.UPUsageError) as e:
                final_report = planner.solve(problem)
            self.assertIn("cannot solve this kind of problem", str(e.exception))
            with Compiler(name="up_quantifiers_remover") as quantifiers_remover:
                res = quantifiers_remover.compile(
                    problem, CompilationKind.QUANTIFIERS_REMOVING
                )
                suitable_problem = res.problem
                final_report = planner.solve(suitable_problem)
                plan = final_report.plan.replace_action_instances(
                    res.map_back_action_instance
                )
                self.assertEqual(
                    final_report.status, PlanGenerationResultStatus.SOLVED_SATISFICING
                )
                self.assertEqual(len(plan.timed_actions), 2)
                self.assertEqual((plan.timed_actions[0])[1].action, move)
                self.assertEqual((plan.timed_actions[1])[1].action, move)

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(quality_metrics_kind))
    @skipIfNoOneshotPlannerSatisfiesOptimalityGuarantee(
        PlanGenerationResultStatus.SOLVED_OPTIMALLY
    )
    def test_actions_cost(self):
        problem = self.problems["basic_with_costs"].problem
        opt_plan = self.problems["basic_with_costs"].plan
        with OneshotPlanner(
            problem_kind=problem.kind,
            optimality_guarantee=PlanGenerationResultStatus.SOLVED_OPTIMALLY,
        ) as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)
            plan = final_report.plan
            self.assertEqual(
                final_report.status, PlanGenerationResultStatus.SOLVED_OPTIMALLY
            )
            self.assertEqual(plan, opt_plan)

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(basic_numeric_kind))
    def test_robot(self):
        problem = self.problems["robot"].problem
        move = problem.action("move")

        with OneshotPlanner(problem_kind=problem.kind) as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)
            plan = final_report.plan
            self.assertIn(final_report.status, POSITIVE_OUTCOMES)
            self.assertNotEqual(plan, None)
            self.assertEqual(len(plan.actions), 1)
            self.assertEqual(plan.actions[0].action, move)
            self.assertEqual(len(plan.actions[0].actual_parameters), 2)

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    def test_robot_loader(self):
        problem = self.problems["robot_loader"].problem
        move = problem.action("move")
        load = problem.action("load")
        unload = problem.action("unload")

        with OneshotPlanner(problem_kind=problem.kind) as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)
            plan = final_report.plan
            self.assertIn(final_report.status, POSITIVE_OUTCOMES)
            self.assertEqual(len(plan.actions), 4)
            self.assertEqual(plan.actions[0].action, move)
            self.assertEqual(plan.actions[1].action, load)
            self.assertEqual(plan.actions[2].action, move)
            self.assertEqual(plan.actions[3].action, unload)
            self.assertEqual(len(plan.actions[0].actual_parameters), 2)
            self.assertEqual(len(plan.actions[1].actual_parameters), 1)
            self.assertEqual(len(plan.actions[2].actual_parameters), 2)
            self.assertEqual(len(plan.actions[3].actual_parameters), 1)

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    def test_robot_loader_adv(self):
        problem = self.problems["robot_loader_adv"].problem
        move = problem.action("move")
        load = problem.action("load")
        unload = problem.action("unload")

        with OneshotPlanner(
            problem_kind=problem.kind, optimality_guarantee="SOLVED_OPTIMALLY"
        ) as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)
            plan = final_report.plan
            self.assertIn(final_report.status, POSITIVE_OUTCOMES)
            self.assertEqual(len(plan.actions), 5)
            self.assertEqual(plan.actions[0].action, move)
            self.assertEqual(plan.actions[1].action, load)
            self.assertEqual(plan.actions[2].action, move)
            self.assertEqual(plan.actions[3].action, unload)
            self.assertEqual(plan.actions[4].action, move)
            self.assertEqual(len(plan.actions[0].actual_parameters), 3)
            self.assertEqual(len(plan.actions[1].actual_parameters), 3)
            self.assertEqual(len(plan.actions[2].actual_parameters), 3)
            self.assertEqual(len(plan.actions[3].actual_parameters), 3)
            self.assertEqual(len(plan.actions[4].actual_parameters), 3)


if __name__ == "__main__":
    main()
