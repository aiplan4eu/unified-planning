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

import upf
from upf.shortcuts import *
from upf.test import TestCase, main
from upf.environment import get_env


class TestPyperplan(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.env = get_env()

    def test_pyperplan(self):
        x = upf.Fluent('x')
        y = upf.Fluent('y')
        a = upf.Action('a')
        a.add_precondition(y)
        a.add_effect(x, True)
        problem = upf.Problem('basic')
        problem.add_fluent(x)
        problem.add_fluent(y)
        problem.add_action(a)
        problem.set_initial_value(x, False)
        problem.set_initial_value(y, True)
        problem.add_goal(x)
        plan = upf.SequentialPlan([upf.ActionInstance(a)])
        self.env.factory.add_solver('pyperplan', 'upf_pyperplan', 'SolverImpl')

        with OneshotPlanner(name='pyperplan') as planner:
            self.assertNotEqual(planner, None)
            new_plan = planner.solve(problem)
            self.assertEqual(str(plan), str(new_plan))
