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
from upf.test import TestCase, main
from upf.test.examples import get_example_problems
from upf.negative_preconditions_remover import NegativePreconditionsRemover
from upf.plan_validator import PlanValidator as PV


class TestNegativePreconditionsRemover(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.env = get_env()
        self.problems = get_example_problems()
        self.env.factory.add_solver('pyperplan', 'upf_pyperplan', 'SolverImpl')

    def test_basic(self):
        problem = self.problems['basic'].problem
        npr = NegativePreconditionsRemover(problem)
        positive_problem = npr.get_rewritten_problem()
        with OneshotPlanner(name='tamer') as planner:
            self.assertNotEqual(planner, None)
            plan = planner.solve(problem)
            positive_plan = planner.solve(positive_problem)
            self.assertNotEqual(plan, positive_plan)
            self.assertEqual(str(plan), str(positive_plan))
            new_plan = npr.rewrite_back_plan(positive_plan)
            self.assertEqual(str(plan), str(new_plan))


    def test_robot_loader_mod(self):
        problem = self.problems['robot_loader_mod'].problem
        plan = self.problems['robot_loader_mod'].plan
        npr = NegativePreconditionsRemover(problem)
        positive_problem = npr.get_rewritten_problem()
        with OneshotPlanner(name='pyperplan') as planner:
            self.assertNotEqual(planner, None)
            positive_plan = planner.solve(positive_problem)
            self.assertNotEqual(plan, positive_plan)
            new_plan = npr.rewrite_back_plan(positive_plan)
            self.assertEqual(str(plan), str(new_plan))

    def test_ad_hoc(self):
        x = upf.Fluent('x')
        a = upf.Action('a')
        a.add_precondition(Not(x))
        a.add_effect(x, True)
        problem = upf.Problem('basic')
        problem.add_fluent(x)
        problem.add_action(a)
        problem.set_initial_value(x, False)
        problem.add_goal(x)
