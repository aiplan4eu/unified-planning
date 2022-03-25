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
from unified_planning.test import TestCase, skipIfSolverNotAvailable


class TestSimulatedEffects(TestCase):
    def setUp(self):
        TestCase.setUp(self)

    @skipIfSolverNotAvailable('tamer')
    def test_basic(self):
        x = Fluent('x')
        a = InstantaneousAction('a')
        a.add_precondition(Not(x))
        def fun(problem, state, actual_params):
            if state.get_value(FluentExp(x)).is_false():
                return [TRUE()]
            else:
                return [FALSE()]
        a.add_simulated_effects(SimulatedEffects([FluentExp(x)], fun))
        problem = Problem('basic_with_simulated_effects')
        problem.add_fluent(x)
        problem.add_action(a)
        problem.set_initial_value(x, False)
        problem.add_goal(x)

        with OneshotPlanner(name='tamer', params={'heuristic': 'blind'}) as planner:
            self.assertNotEqual(planner, None)
            plan = planner.solve(problem)
            self.assertEqual(len(plan.actions()), 1)

    @skipIfSolverNotAvailable('tamer')
    def test_with_parameters(self):
        Location = UserType('Location')
        Robot = UserType('Robot')
        at = Fluent('at', Location, robot=Robot)
        battery_charge = Fluent('battery_charge', IntType(0, 100), robot=Robot)
        move = InstantaneousAction('move', robot=Robot, l_from=Location, l_to=Location)
        robot = move.parameter('robot')
        l_from = move.parameter('l_from')
        l_to = move.parameter('l_to')
        move.add_precondition(Equals(at(robot), l_from))
        move.add_precondition(GE(battery_charge(robot), 10))
        move.add_precondition(Not(Equals(l_from, l_to)))
        move.add_effect(at(robot), l_to)
        def fun(problem, state, actual_params):
            value = state.get_value(battery_charge(actual_params.get(robot))).constant_value()
            return [Int(value - 10)]
        move.add_simulated_effects(SimulatedEffects([battery_charge(robot)], fun))
        l1 = Object('l1', Location)
        l2 = Object('l2', Location)
        r1 = Object('r1', Robot)
        problem = Problem('robot_with_simulated_effects')
        problem.add_fluent(at)
        problem.add_fluent(battery_charge)
        problem.add_action(move)
        problem.add_object(l1)
        problem.add_object(l2)
        problem.add_object(r1)
        problem.set_initial_value(at(r1), l1)
        problem.set_initial_value(battery_charge(r1), 100)
        problem.add_goal(Equals(at(r1), l2))

        with OneshotPlanner(name='tamer', params={'heuristic': 'blind'}) as planner:
            self.assertNotEqual(planner, None)
            plan = planner.solve(problem)
            self.assertEqual(len(plan.actions()), 1)
