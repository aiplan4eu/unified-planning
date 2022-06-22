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


from collections import OrderedDict
from unified_planning.shortcuts import *
from unified_planning.test import TestCase, main
from unified_planning.test.examples import get_example_problems
from unified_planning.io import PythonWriter

class TestPythonWriter(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_all(self):
        for p in self.problems.values():
            original_problem = p.problem
            pw = PythonWriter(original_problem)
            _locals = {}
            exec(pw.write_problem_code(), {}, _locals)
            self.assertEqual(original_problem, _locals['problem'])
            self.assertEqual(hash(original_problem), hash(_locals['problem']))

    def test_ad_hoc_1(self):
        xd = Fluent('x-$')
        xe = Fluent('x-&')
        nop = Fluent('')
        a = InstantaneousAction('3')
        a.add_precondition(Not(xd))
        a.add_effect(xd, True)
        a.add_precondition(Not(xe))
        a.add_effect(xe, True)
        a.add_precondition(Not(nop))
        a.add_effect(nop, True)
        problem = Problem('basic')
        problem.add_fluent(xd)
        problem.add_fluent(xe)
        problem.add_fluent(nop)
        problem.add_action(a)
        problem.set_initial_value(xd, False)
        problem.set_initial_value(xe, False)
        problem.set_initial_value(nop, False)
        problem.add_goal(xd)
        problem.add_goal(xe)
        problem.add_goal(nop)
        pw = PythonWriter(problem)
        _locals = {}
        exec(pw.write_problem_code(), {}, _locals)
        self.assertEqual(problem, _locals['problem'])

    def test_ad_hoc_2(self):
        Location = UserType('Location')
        robot_at = Fluent('robot_at', BoolType(), OrderedDict([('if', Location)]))
        battery_charge = Fluent('battery_charge', RealType(0, 100))
        move = InstantaneousAction('move', OrderedDict([('from', Location), ('to', Location)]))
        l_from = move.parameter('from')
        to = move.parameter('to')
        move.add_precondition(GE(battery_charge, 10))
        move.add_precondition(Not(Equals(l_from, to)))
        move.add_precondition(robot_at(l_from))
        move.add_precondition(Not(robot_at(to)))
        move.add_effect(robot_at(l_from), False)
        move.add_effect(robot_at(to), True)
        move.add_effect(battery_charge, Minus(battery_charge, 10))
        l1 = Object('l1', Location)
        l2 = Object('l2', Location)
        problem = Problem('robot')
        problem.add_fluent(robot_at)
        problem.add_fluent(battery_charge)
        problem.add_action(move)
        problem.add_object(l1)
        problem.add_object(l2)
        problem.set_initial_value(robot_at(l1), True)
        problem.set_initial_value(robot_at(l2), False)
        problem.set_initial_value(battery_charge, 100)
        problem.add_goal(robot_at(l2))
        pw = PythonWriter(problem)
        _locals = {}
        exec(pw.write_problem_code(), {}, _locals)
        self.assertEqual(problem, _locals['problem'])
