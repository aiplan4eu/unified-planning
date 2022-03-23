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
from unified_planning.test import TestCase


class TestSimulatedEffects(TestCase):
    def setUp(self):
        TestCase.setUp(self)

    def test_basic(self):
        x = Fluent('x')
        a = InstantaneousAction('a')
        a.add_precondition(Not(x))
        def fun(p, s):
            if s.get_value(FluentExp(x)).is_false():
                return [TRUE()]
            else:
                return [FALSE()]
        a.add_simulated_effects(SimulatedEffects([FluentExp(x)], fun))
        problem = Problem('basic')
        problem.add_fluent(x)
        problem.add_action(a)
        problem.set_initial_value(x, False)
        problem.add_goal(x)

        with OneshotPlanner(name='tamer', params={'heuristic': 'blind'}) as planner:
            self.assertNotEqual(planner, None)
            plan = planner.solve(problem)
            self.assertEqual(len(plan.actions()), 1)
