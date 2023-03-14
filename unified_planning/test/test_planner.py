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


import warnings
import unified_planning as up
from unified_planning.shortcuts import *
from unified_planning.model.problem_kind import (
    basic_classical_kind,
    classical_kind,
    general_numeric_kind,
    bounded_types_kind,
    quality_metrics_kind,
    oversubscription_kind,
)
from unified_planning.test import TestCase, main, skipIfEngineNotAvailable
from unified_planning.test import skipIfNoOneshotPlannerForProblemKind
from unified_planning.test.examples import get_example_problems
from unified_planning.engines import PlanGenerationResultStatus, CompilationKind
from unified_planning.engines.results import POSITIVE_OUTCOMES
from unified_planning.exceptions import UPUsageError
from unified_planning.model.metrics import MinimizeSequentialPlanLength


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
    def test_basic_with_custom_heuristic(self):
        problem = self.problems["basic"].problem
        x = problem.fluent("x")

        with OneshotPlanner(name="tamer") as planner:
            self.assertNotEqual(planner, None)

            def h(state):
                v = state.get_value(x()).bool_constant_value()
                return 0 if v else 1

            final_report = planner.solve(problem, heuristic=h)
            plan = final_report.plan
            self.assertEqual(
                final_report.status, PlanGenerationResultStatus.SOLVED_SATISFICING
            )

    @skipIfNoOneshotPlannerForProblemKind(
        basic_classical_kind.union(oversubscription_kind)
    )
    def test_basic_oversubscription(self):
        problem = self.problems["basic_oversubscription"].problem
        a = problem.action("a")

        with OneshotPlanner(problem_kind=problem.kind) as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)
            plan = final_report.plan
            self.assertEqual(
                final_report.status, PlanGenerationResultStatus.SOLVED_OPTIMALLY
            )
            self.assertEqual(len(plan.actions), 1)
            self.assertEqual(plan.actions[0].action, a)
            self.assertEqual(len(plan.actions[0].actual_parameters), 0)

    @skipIfEngineNotAvailable("tamer")
    def test_basic_oversubscription_parallel(self):
        problem = self.problems["basic_oversubscription"].problem
        a = problem.action("a")

        with OneshotPlanner(
            names=["oversubscription[tamer]", "oversubscription[tamer]"],
            params=[{"heuristic": "hadd"}, {"heuristic": "hmax"}],
        ) as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)
            plan = final_report.plan
            self.assertEqual(
                final_report.status, PlanGenerationResultStatus.SOLVED_OPTIMALLY
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
            planner.error_on_failed_checks = True
            with self.assertRaises(up.exceptions.UPUsageError) as e:
                final_report = planner.solve(problem)
            self.assertIn("cannot establish whether", str(e.exception))
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

    @skipIfNoOneshotPlannerForProblemKind(
        classical_kind.union(quality_metrics_kind), OptimalityGuarantee.SOLVED_OPTIMALLY
    )
    def test_actions_cost(self):
        problem = self.problems["basic_with_costs"].problem
        opt_plan = self.problems["basic_with_costs"].plan
        with OneshotPlanner(
            problem_kind=problem.kind,
            optimality_guarantee=OptimalityGuarantee.SOLVED_OPTIMALLY,
        ) as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)
            plan = final_report.plan
            self.assertEqual(
                final_report.status, PlanGenerationResultStatus.SOLVED_OPTIMALLY
            )
            self.assertEqual(plan, opt_plan)

    @skipIfNoOneshotPlannerForProblemKind(
        classical_kind.union(general_numeric_kind).union(bounded_types_kind)
    )
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

    @skipIfNoOneshotPlannerForProblemKind(
        classical_kind.union(quality_metrics_kind), OptimalityGuarantee.SOLVED_OPTIMALLY
    )
    def test_robot_loader_adv(self):
        problem = self.problems["robot_loader_adv"].problem.clone()
        problem.add_quality_metric(MinimizeSequentialPlanLength())

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

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_check_flags(self):
        problem = self.problems["robot"].problem
        error_msg = "We cannot establish whether ENHSP can solve this problem!"
        with OneshotPlanner(name="opt-pddl-planner") as planner:

            # By default, when getting an Engine by name, we get a warning if the problem is not
            # supported
            with warnings.catch_warnings(record=True) as w:
                plan = planner.solve(problem).plan
                self.assertIsNotNone(plan)
                self.assertEqual(len(w), 1)
                self.assertEqual(error_msg, str(w[-1].message))

            # We can set the Engine to give an error when the problem is not supported
            planner.error_on_failed_checks = True
            with self.assertRaises(UPUsageError) as e:
                planner.solve(problem)
            self.assertEqual(error_msg, str(e.exception))

            # Or we can set the check to be completely skipped
            planner.skip_checks = True
            plan = planner.solve(problem).plan
            self.assertIsNotNone(plan)


if __name__ == "__main__":
    main()
