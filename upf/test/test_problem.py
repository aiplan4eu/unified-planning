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


class TestProblem(TestCase):
    def test_basic(self):
        x = upf.Fluent('x')
        self.assertEqual(x.name(), 'x')
        self.assertEqual(x.arity(), 0)
        self.assertTrue(x.type().is_bool_type())

        a = upf.Action('a')
        a.add_precondition(Not(x))
        a.add_effect(x, True)
        self.assertEqual(a.name(), 'a')
        self.assertEqual(len(a.preconditions()), 1)
        self.assertEqual(len(a.effects()), 1)

        problem = upf.Problem('basic')
        problem.add_fluent(x)
        problem.add_action(a)
        problem.set_initial_value(x, False)
        problem.add_goal(x)
        self.assertEqual(problem.name(), 'basic')
        self.assertEqual(len(problem.fluents()), 1)
        self.assertEqual(problem.fluent('x'), x)
        self.assertEqual(len(problem.actions()), 1)
        self.assertEqual(problem.action('a'), a)
        self.assertTrue(problem.initial_value(x) is not None)
        self.assertEqual(len(problem.goals()), 1)

    def test_with_parameters(self):
        Location = UserType('Location')
        self.assertTrue(Location.is_user_type())
        self.assertEqual(Location.name(), 'Location')

        robot_at = upf.Fluent('robot_at', BOOL(), [Location])
        self.assertEqual(robot_at.name(), 'robot_at')
        self.assertEqual(robot_at.arity(), 1)
        self.assertEqual(robot_at.signature(), [Location])
        self.assertTrue(robot_at.type().is_bool_type())

        move = upf.Action('move', l_from=Location, l_to=Location)
        l_from = move.parameter('l_from')
        l_to = move.parameter('l_to')
        move.add_precondition(Not(Equals(l_from, l_to)))
        move.add_precondition(robot_at(l_from))
        move.add_precondition(Not(robot_at(l_to)))
        move.add_effect(robot_at(l_from), False)
        move.add_effect(robot_at(l_to), True)
        self.assertEqual(move.name(), 'move')
        self.assertEqual(len(move.parameters()), 2)
        self.assertEqual(l_from.name(), 'l_from')
        self.assertEqual(l_from.type(), Location)
        self.assertEqual(l_to.name(), 'l_to')
        self.assertEqual(l_to.type(), Location)
        self.assertEqual(len(move.preconditions()), 3)
        self.assertEqual(len(move.effects()), 2)

        l1 = upf.Object('l1', Location)
        l2 = upf.Object('l2', Location)
        self.assertEqual(l1.name(), 'l1')
        self.assertEqual(l1.type(), Location)
        self.assertEqual(l2.name(), 'l2')
        self.assertEqual(l2.type(), Location)

        p = upf.Problem('robot')
        p.add_fluent(robot_at)
        p.add_action(move)
        p.add_object(l1)
        p.add_object(l2)
        p.set_initial_value(robot_at(l1), True)
        p.set_initial_value(robot_at(l2), False)
        p.add_goal(robot_at(l2))
        self.assertEqual(p.name(), 'robot')
        self.assertEqual(len(p.fluents()), 1)
        self.assertEqual(p.fluent('robot_at'), robot_at)
        self.assertEqual(len(p.user_types()), 1)
        self.assertEqual(p.user_types()['Location'], Location)
        self.assertEqual(len(p.objects(Location)), 2)
        self.assertEqual(p.objects(Location), [l1, l2])
        self.assertEqual(len(p.actions()), 1)
        self.assertEqual(p.action('move'), move)
        self.assertTrue(p.initial_value(robot_at(l1)) is not None)
        self.assertTrue(p.initial_value(robot_at(l2)) is not None)
        self.assertEqual(len(p.goals()), 1)


if __name__ == "__main__":
    main()
