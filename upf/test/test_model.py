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
from upf.test.examples import get_example_problems
from upf.test import TestCase, main


class TestModel(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_clone_problem_and_action(self):
        for _, (problem, _) in self.problems.items():
            problem_clone_1 = problem.clone()
            problem_clone_2 = problem.clone()
            for action_1, action_2 in zip(problem_clone_1.actions().values(), problem_clone_2.actions().values()):
                if isinstance(action_2, InstantaneousAction):
                    action_2._effects = []
                    action_1_clone = action_1.clone()
                    action_1_clone._effects = []
                elif isinstance(action_2, DurativeAction):
                    action_2._effects = {}
                    action_1_clone = action_1.clone()
                    action_1_clone._effects = {}
                else:
                    raise NotImplementedError
                self.assertEqual(action_2, action_1_clone)
                self.assertEqual(action_1_clone, action_2)
                self.assertNotEqual(action_1, action_1_clone)
                self.assertNotEqual(action_1_clone, action_1)
                self.assertNotEqual(action_1, action_1_clone.name)
                self.assertNotEqual(action_1_clone.name, action_1)
            self.assertEqual(problem_clone_1, problem)
            self.assertEqual(problem, problem_clone_1)
            self.assertNotEqual(problem_clone_2, problem)
            self.assertNotEqual(problem, problem_clone_2)

    def test_clone_action(self):
        Location = UserType('Location')
        a = Action('move', l_from=Location, l_to=Location)
        with self.assertRaises(NotImplementedError):
            a.clone()
        with self.assertRaises(NotImplementedError):
            hash(a)
        with self.assertRaises(NotImplementedError):
            a == a.name
        with self.assertRaises(NotImplementedError):
            a.is_conditional()

    def test_clone_effect(self):
        x = FluentExp(Fluent('x'))
        y = FluentExp(Fluent('y'))
        z = FluentExp(Fluent('z'))
        e = Effect(x, z, y, upf.model.effect.ASSIGN)
        e_clone_1 = e.clone()
        e_clone_2 = e.clone()
        e_clone_2._condition = TRUE()
        self.assertEqual(e_clone_1, e)
        self.assertEqual(e, e_clone_1)
        self.assertNotEqual(e_clone_2, e)
        self.assertNotEqual(e, e_clone_2)
        self.assertNotEqual(e, e.value())
        self.assertNotEqual(e.value(), e)
