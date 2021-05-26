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


class TestPlanner(TestCase):
    def test_basic(self):
        x = upf.Fluent('x')
        a = upf.Action('a')
        a.add_precondition(Not(x))
        a.add_effect(x, True)
        problem = upf.Problem('basic')
        problem.add_fluent(x)
        problem.add_action(a)
        problem.set_initial_value(x, False)
        problem.add_goal(x)

        with upf.Planner('upf_tamer') as p:
            plan = p.solve(problem)
            self.assertEqual(len(plan.actions()), 1)
            self.assertEqual(plan.actions()[0].action(), a)
            self.assertEqual(len(plan.actions()[0].parameters()), 0)

    def test_with_parameters(self):
        Location = UserType('Location')
        robot_at = upf.Fluent('robot_at', BoolType(), [Location])
        move = upf.Action('move', l_from=Location, l_to=Location)
        l_from = move.parameter('l_from')
        l_to = move.parameter('l_to')
        move.add_precondition(Not(Equals(l_from, l_to)))
        move.add_precondition(robot_at(l_from))
        move.add_precondition(Not(robot_at(l_to)))
        move.add_effect(robot_at(l_from), False)
        move.add_effect(robot_at(l_to), True)
        l1 = upf.Object('l1', Location)
        l2 = upf.Object('l2', Location)
        problem = upf.Problem('robot')
        problem.add_fluent(robot_at)
        problem.add_action(move)
        problem.add_object(l1)
        problem.add_object(l2)
        problem.set_initial_value(robot_at(l1), True)
        problem.set_initial_value(robot_at(l2), False)
        problem.add_goal(robot_at(l2))

        with upf.Planner('upf_tamer') as p:
            plan = p.solve(problem)
            self.assertEqual(len(plan.actions()), 1)
            self.assertEqual(plan.actions()[0].action(), move)
            self.assertEqual(len(plan.actions()[0].parameters()), 2)


if __name__ == "__main__":
    main()
