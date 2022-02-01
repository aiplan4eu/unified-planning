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

import unified_planning
from unified_planning.shortcuts import *
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
        problem, plan = self.problems['robot_no_negative_preconditions'].problem, self.problems['robot_no_negative_preconditions'].plan
        with OneshotPlanner(name='pyperplan') as planner:
            self.assertNotEqual(planner, None)
            new_plan = planner.solve(problem)
            self.assertEqual(str(plan), str(new_plan))

    @skipIfSolverNotAvailable('pyperplan')
    def test_basic_without_negative_preconditions(self):
        problem, plan = self.problems['basic_without_negative_preconditions'].problem, self.problems['basic_without_negative_preconditions'].plan
        with OneshotPlanner(name='pyperplan') as planner:
            self.assertNotEqual(planner, None)
            new_plan = planner.solve(problem)
            self.assertEqual(str(plan), str(new_plan))

    @skipIfSolverNotAvailable('pyperplan')
    def test_basic_nested_conjunctions(self):
        problem, plan = self.problems['basic_nested_conjunctions'].problem, self.problems['basic_nested_conjunctions'].plan
        with OneshotPlanner(name='pyperplan') as planner:
            self.assertNotEqual(planner, None)
            new_plan = planner.solve(problem)
            self.assertEqual(str(plan), str(new_plan))
