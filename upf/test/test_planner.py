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
from upf.test.examples import get_example_problems


class TestPlanner(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_basic(self):
        problem = self.problems['basic'].problem
        a = problem.action('a')

        with OneshotPlanner(problem_kind=problem.kind()) as planner:
            self.assertNotEqual(planner, None)
            plan = planner.solve(problem)
            self.assertEqual(len(plan.actions()), 1)
            self.assertEqual(plan.actions()[0].action(), a)
            self.assertEqual(len(plan.actions()[0].parameters()), 0)

    def test_robot(self):
        problem = self.problems['robot'].problem
        move = problem.action('move')

        with OneshotPlanner(problem_kind=problem.kind()) as planner:
            self.assertNotEqual(planner, None)
            plan = planner.solve(problem)
            self.assertNotEqual(plan, None)
            self.assertEqual(len(plan.actions()), 1)
            self.assertEqual(plan.actions()[0].action(), move)
            self.assertEqual(len(plan.actions()[0].parameters()), 2)

    def test_robot_loader(self):
        problem = self.problems['robot_loader'].problem
        move = problem.action('move')
        load = problem.action('load')
        unload = problem.action('unload')

        with OneshotPlanner(problem_kind=problem.kind()) as planner:
            self.assertNotEqual(planner, None)
            plan = planner.solve(problem)
            self.assertEqual(len(plan.actions()), 4)
            self.assertEqual(plan.actions()[0].action(), move)
            self.assertEqual(plan.actions()[1].action(), load)
            self.assertEqual(plan.actions()[2].action(), move)
            self.assertEqual(plan.actions()[3].action(), unload)
            self.assertEqual(len(plan.actions()[0].parameters()), 2)
            self.assertEqual(len(plan.actions()[1].parameters()), 1)
            self.assertEqual(len(plan.actions()[2].parameters()), 2)
            self.assertEqual(len(plan.actions()[3].parameters()), 1)

    def test_robot_loader_adv(self):
        problem = self.problems['robot_loader_adv'].problem
        move = problem.action('move')
        load = problem.action('load')
        unload = problem.action('unload')

        with OneshotPlanner(problem_kind=problem.kind()) as planner:
            self.assertNotEqual(planner, None)
            plan = planner.solve(problem)
            self.assertEqual(len(plan.actions()), 5)
            self.assertEqual(plan.actions()[0].action(), move)
            self.assertEqual(plan.actions()[1].action(), load)
            self.assertEqual(plan.actions()[2].action(), move)
            self.assertEqual(plan.actions()[3].action(), unload)
            self.assertEqual(plan.actions()[4].action(), move)
            self.assertEqual(len(plan.actions()[0].parameters()), 3)
            self.assertEqual(len(plan.actions()[1].parameters()), 3)
            self.assertEqual(len(plan.actions()[2].parameters()), 3)
            self.assertEqual(len(plan.actions()[3].parameters()), 3)
            self.assertEqual(len(plan.actions()[4].parameters()), 3)

if __name__ == "__main__":
    main()
