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
import upf
from upf.environment import get_env
from upf.shortcuts import *
from upf.test import TestCase, skipIfNoPlanValidatorForProblemKind, skipIfNoOneshotPlannerForProblemKind
from upf.test import classical_kind, full_classical_kind, basic_temporal_kind, full_numeric_kind
from upf.test.examples import get_example_problems
from upf.transformers import QuantifiersRemover



class TestQuantifiersRemover(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    @skipIfNoPlanValidatorForProblemKind(full_classical_kind)
    def test_basic_exists(self):
        problem = self.problems['basic_exists'].problem
        qr = QuantifiersRemover(problem)
        uq_problem = qr.get_rewritten_problem()
        uq_problem_2 = qr.get_rewritten_problem()
        self.assertEqual(uq_problem, uq_problem_2)
        self.assertTrue(problem.kind().has_existential_conditions())
        self.assertFalse(uq_problem.kind().has_existential_conditions())
        self.assertEqual(len(problem.actions()), len(uq_problem.actions()))

        with OneshotPlanner(problem_kind=uq_problem.kind()) as planner:
            self.assertNotEqual(planner, None)
            uq_plan = planner.solve(uq_problem)
            new_plan = qr.rewrite_back_plan(uq_plan)
            with PlanValidator(problem_kind=problem.kind()) as pv:
                self.assertTrue(pv.validate(problem, new_plan))

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    @skipIfNoPlanValidatorForProblemKind(full_classical_kind)
    def test_basic_forall(self):
        problem = self.problems['basic_forall'].problem
        qr = QuantifiersRemover(problem)
        uq_problem = qr.get_rewritten_problem()
        self.assertTrue(problem.kind().has_universal_conditions())
        self.assertFalse(uq_problem.kind().has_universal_conditions())
        self.assertEqual(len(problem.actions()), len(uq_problem.actions()))

        with OneshotPlanner(problem_kind=uq_problem.kind()) as planner:
            self.assertNotEqual(planner, None)
            uq_plan = planner.solve(uq_problem)
            new_plan = qr.rewrite_back_plan(uq_plan)
            with PlanValidator(problem_kind=problem.kind()) as pv:
                self.assertTrue(pv.validate(problem, new_plan))

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(full_numeric_kind))
    @skipIfNoPlanValidatorForProblemKind(full_classical_kind.union(full_numeric_kind))
    def test_robot_locations_connected(self):
        problem = self.problems['robot_locations_connected'].problem
        qr = QuantifiersRemover(problem)
        uq_problem = qr.get_rewritten_problem()
        self.assertTrue(problem.kind().has_existential_conditions())
        self.assertFalse(uq_problem.kind().has_existential_conditions())
        self.assertEqual(len(problem.actions()), len(uq_problem.actions()))

        with OneshotPlanner(problem_kind=uq_problem.kind()) as planner:
            self.assertNotEqual(planner, None)
            uq_plan = planner.solve(uq_problem)
            new_plan = qr.rewrite_back_plan(uq_plan)
            with PlanValidator(problem_kind=problem.kind()) as pv:
                self.assertTrue(pv.validate(problem, new_plan))

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(full_numeric_kind))
    @skipIfNoPlanValidatorForProblemKind(full_classical_kind.union(full_numeric_kind))
    def test_robot_locations_visited(self):
        problem = self.problems['robot_locations_visited'].problem
        qr = QuantifiersRemover(problem)
        uq_problem = qr.get_rewritten_problem()
        self.assertTrue(problem.kind().has_existential_conditions())
        self.assertFalse(uq_problem.kind().has_existential_conditions())
        self.assertTrue(problem.kind().has_universal_conditions())
        self.assertFalse(uq_problem.kind().has_universal_conditions())
        self.assertEqual(len(problem.actions()), len(uq_problem.actions()))

        with OneshotPlanner(problem_kind=uq_problem.kind()) as planner:
            self.assertNotEqual(planner, None)
            uq_plan = planner.solve(uq_problem)
            new_plan = qr.rewrite_back_plan(uq_plan)
            with PlanValidator(problem_kind=problem.kind()) as pv:
                self.assertTrue(pv.validate(problem, new_plan))

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(basic_temporal_kind))
    def test_timed_connected_locations(self):
        problem = self.problems['timed_connected_locations'].problem
        plan = self.problems['timed_connected_locations'].plan
        qr = QuantifiersRemover(problem)
        uq_problem = qr.get_rewritten_problem()
        self.assertTrue(problem.has_quantifiers())
        self.assertFalse(uq_problem.has_quantifiers())
        self.assertEqual(len(problem.actions()), len(uq_problem.actions()))

        with OneshotPlanner(problem_kind=uq_problem.kind()) as planner:
            self.assertNotEqual(planner, None)
            uq_plan = planner.solve(uq_problem)
            new_plan = qr.rewrite_back_plan(uq_plan)
            for (s, a, d), (s_1, a_1, d_1) in zip(new_plan.actions(), uq_plan.actions()):
                self.assertEqual(s, s_1)
                self.assertEqual(d, d_1)
                self.assertIn(a.action(), problem.actions().values())
