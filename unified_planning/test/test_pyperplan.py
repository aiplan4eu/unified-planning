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

import unified_planning as up
from unified_planning.shortcuts import *
from unified_planning.solvers.results import POSITIVE_OUTCOMES
from unified_planning.test import TestCase, main, skipIfSolverNotAvailable
from unified_planning.environment import get_env
from unified_planning.test.examples import get_example_problems



class TestPyperplan(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.env = get_env()
        self.problems = get_example_problems()

    @skipIfSolverNotAvailable('pyperplan')
    def test_pyperplan(self):
        problem, plan = self.problems['robot_no_negative_preconditions']
        with OneshotPlanner(name='pyperplan') as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)
            self.assertIn(final_report.status(), POSITIVE_OUTCOMES)
            self.assertEqual(str(plan), str(final_report.plan()))

    @skipIfSolverNotAvailable('pyperplan')
    def test_basic_without_negative_preconditions(self):
        problem, plan = self.problems['basic_without_negative_preconditions']
        with OneshotPlanner(name='pyperplan') as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)
            self.assertIn(final_report.status(), POSITIVE_OUTCOMES)
            self.assertEqual(str(plan), str(final_report.plan()))


    @skipIfSolverNotAvailable('pyperplan')
    def test_basic_nested_conjunctions(self):
        problem, plan = self.problems['basic_nested_conjunctions']
        with OneshotPlanner(name='pyperplan') as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)
            self.assertIn(final_report.status(), POSITIVE_OUTCOMES)
            self.assertEqual(str(plan), str(final_report.plan()))


    @skipIfSolverNotAvailable('pyperplan')
    def test_hierarchical_blocks_world(self):
        problem, plan = self.problems['hierarchical_blocks_world']
        with OneshotPlanner(name='pyperplan') as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)
            self.assertIn(final_report.status(), POSITIVE_OUTCOMES)
            self.assertEqual(str(plan), str(final_report.plan()))


    @skipIfSolverNotAvailable('pyperplan')
    def test_hierarchical_blocks_world_object_as_root(self):
        problem, plan = self.problems['hierarchical_blocks_world_object_as_root']
        with OneshotPlanner(name='pyperplan') as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)
            self.assertIn(final_report.status(), POSITIVE_OUTCOMES)
            self.assertEqual(str(plan), str(final_report.plan()))

    
    @skipIfSolverNotAvailable('pyperplan')
    def test_hierarchical_blocks_world_with_object(self):
        problem, plan = self.problems['hierarchical_blocks_world_with_object']
        with OneshotPlanner(name='pyperplan') as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)
            self.assertIn(final_report.status(), POSITIVE_OUTCOMES)
            self.assertEqual(str(plan), str(final_report.plan()))
