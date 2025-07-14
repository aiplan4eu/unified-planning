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


from io import StringIO
import unified_planning as up
from unified_planning.shortcuts import *
from unified_planning.engines import PlanGenerationResultStatus
from unified_planning.test import unittest_TestCase, main, skipIfEngineNotAvailable
from unified_planning.test.examples import get_example_problems

VERYSMALL_TIMEOUT = 0.0001


class TestPDDLPlanner(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_basic(self):
        problem = self.problems["basic"].problem
        a = problem.action("a")

        with OneshotPlanner(name="opt-pddl-planner") as planner:
            self.assertNotEqual(planner, None)

            import sys

            final_report = planner.solve(problem, output_stream=sys.stdout)
            plan = final_report.plan
            self.assertEqual(
                final_report.status, PlanGenerationResultStatus.SOLVED_OPTIMALLY
            )
            self.assertEqual(len(plan.actions), 1)
            self.assertEqual(plan.actions[0].action, a)
            self.assertEqual(len(plan.actions[0].actual_parameters), 0)

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_basic_conditional(self):
        problem = self.problems["basic_conditional"].problem
        a_x = problem.action("a_x")
        a_y = problem.action("a_y")

        with OneshotPlanner(name="opt-pddl-planner") as planner:
            self.assertNotEqual(planner, None)

            final_report = planner.solve(problem)
            plan = final_report.plan
            self.assertEqual(
                final_report.status, PlanGenerationResultStatus.SOLVED_OPTIMALLY
            )
            self.assertEqual(len(plan.actions), 2)
            self.assertEqual(plan.actions[0].action, a_y)
            self.assertEqual(plan.actions[1].action, a_x)
            self.assertEqual(len(plan.actions[0].actual_parameters), 0)
            self.assertEqual(len(plan.actions[1].actual_parameters), 0)

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_robot_decrease(self):
        problem = self.problems["robot_decrease"].problem
        move = problem.action("move")

        with OneshotPlanner(name="opt-pddl-planner") as planner:
            self.assertNotEqual(planner, None)

            final_report = planner.solve(problem)
            plan = final_report.plan
            self.assertEqual(
                final_report.status, PlanGenerationResultStatus.SOLVED_OPTIMALLY
            )
            self.assertNotEqual(plan, None)
            self.assertEqual(len(plan.actions), 1)
            self.assertEqual(plan.actions[0].action, move)
            self.assertEqual(len(plan.actions[0].actual_parameters), 2)

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_robot_loader(self):
        problem = self.problems["robot_loader"].problem
        move = problem.action("move")
        load = problem.action("load")
        unload = problem.action("unload")

        with OneshotPlanner(name="opt-pddl-planner") as planner:
            self.assertNotEqual(planner, None)

            final_report = planner.solve(problem)
            plan = final_report.plan
            self.assertEqual(
                final_report.status, PlanGenerationResultStatus.SOLVED_OPTIMALLY
            )
            self.assertEqual(len(plan.actions), 4)
            self.assertEqual(plan.actions[0].action, move)
            self.assertEqual(plan.actions[1].action, load)
            self.assertEqual(plan.actions[2].action, move)
            self.assertEqual(plan.actions[3].action, unload)
            self.assertEqual(len(plan.actions[0].actual_parameters), 2)
            self.assertEqual(len(plan.actions[1].actual_parameters), 1)
            self.assertEqual(len(plan.actions[2].actual_parameters), 2)
            self.assertEqual(len(plan.actions[3].actual_parameters), 1)

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_robot_loader_adv(self):
        problem = self.problems["robot_loader_adv"].problem
        move = problem.action("move")
        load = problem.action("load")
        unload = problem.action("unload")

        with OneshotPlanner(name="opt-pddl-planner") as planner:
            self.assertNotEqual(planner, None)
            output = StringIO()
            final_report = planner.solve(problem, output_stream=output)
            plan = final_report.plan
            planner_output = output.getvalue()
            self.assertEqual(
                final_report.status, PlanGenerationResultStatus.SOLVED_OPTIMALLY
            )
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

            self.assertIn("Domain parsed\nProblem parsed", planner_output)
            self.assertIn("Problem Solved", planner_output)
            self.assertIn("Found Plan", planner_output)
            self.assertIn("Heuristic Time (msec):", planner_output)
            self.assertIn("Search Time (msec):", planner_output)
            self.assertIn("Expanded Nodes:", planner_output)

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_robot_loader_adv_with_timeout(self):
        problem, right_plan = (
            self.problems["robot_loader_adv"].problem,
            self.problems["robot_loader_adv"].valid_plans[0],
        )
        with OneshotPlanner(name="opt-pddl-planner") as planner:
            self.assertNotEqual(planner, None)

            final_report = planner.solve(problem, timeout=VERYSMALL_TIMEOUT)
            self.assertIn(
                final_report.status,
                [
                    PlanGenerationResultStatus.TIMEOUT,
                    PlanGenerationResultStatus.SOLVED_OPTIMALLY,
                ],
            )  # It could happen that the PDDL planner manages to solve the problem
            self.assertTrue(
                final_report.plan is None or final_report.plan == right_plan
            )

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_robot_loader_adv_with_long_timeout(self):
        problem = self.problems["robot_loader_adv"].problem
        move = problem.action("move")
        load = problem.action("load")
        unload = problem.action("unload")
        with OneshotPlanner(name="opt-pddl-planner") as planner:
            self.assertNotEqual(planner, None)

            final_report = planner.solve(problem, timeout=100)
            plan = final_report.plan
            self.assertEqual(
                final_report.status, PlanGenerationResultStatus.SOLVED_OPTIMALLY
            )
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

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_robot_loader_adv_with_long_timeout_and_output_stream(self):
        problem = self.problems["robot_loader_adv"].problem
        move = problem.action("move")
        load = problem.action("load")
        unload = problem.action("unload")
        output_stream = StringIO()
        with OneshotPlanner(name="opt-pddl-planner") as planner:
            self.assertNotEqual(planner, None)

            final_report = planner.solve(
                problem, timeout=100, output_stream=output_stream
            )
            plan = final_report.plan
            planner_output = output_stream.getvalue()
            self.assertEqual(
                final_report.status, PlanGenerationResultStatus.SOLVED_OPTIMALLY
            )
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

            self.assertIn("Domain parsed\nProblem parsed", planner_output)
            self.assertIn("Problem Solved", planner_output)
            self.assertIn("Found Plan", planner_output)
            self.assertIn("Heuristic Time (msec):", planner_output)
            self.assertIn("Search Time (msec):", planner_output)
            self.assertIn("Expanded Nodes:", planner_output)

            for lm in final_report.log_messages:
                if lm.level == up.engines.LogLevel.INFO:
                    self.assertEqual(planner_output, lm.message)
                else:
                    self.assertEqual(lm.level, up.engines.LogLevel.ERROR)
                    self.assertEqual(lm.message, "")

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_robot_loader_adv_with_short_timeout_and_output_stream(self):
        problem, right_plan = (
            self.problems["robot_loader_adv"].problem,
            self.problems["robot_loader_adv"].valid_plans[0],
        )
        output_stream = StringIO()
        with OneshotPlanner(name="opt-pddl-planner") as planner:
            self.assertNotEqual(planner, None)

            final_report = planner.solve(
                problem, timeout=VERYSMALL_TIMEOUT, output_stream=output_stream
            )
            plan = final_report.plan
            planner_output = output_stream.getvalue()
            self.assertTrue(plan is None or plan == right_plan)

            for lm in final_report.log_messages:
                if lm.level == up.engines.LogLevel.INFO:
                    self.assertEqual(planner_output, lm.message)
                else:
                    self.assertEqual(lm.level, up.engines.LogLevel.ERROR)
                    self.assertEqual(lm.message, "")
