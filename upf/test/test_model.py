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
                self.assertNotEqual(action_1, action_1_clone)
            self.assertEqual(problem_clone_1, problem)
            assert problem != problem_clone_2
            #self.assertNotEqual(problem_clone_2, problem)

    def test_clone_action_parameter(self):
        ap = ActionParameter('semaphore', Bool)
        ap_clone_1 = ap.clone()
        ap_clone_2 = ap.clone()
        ap_clone_2._name = 'lock'
        self.assertEqual(ap_clone_1, ap)
        self.assertNotEqual(ap_clone_2, ap)

    def test_clone_variable(self):
        var = Variable('semaphore', Bool)
        var_clone_1 = var.clone()
        var_clone_2 = var.clone()
        var_clone_2._name = 'lock'
        self.assertEqual(var_clone_1, var)
        self.assertNotEqual(var_clone_2, var)
