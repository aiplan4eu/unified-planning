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
from upf.solvers.upf_tarski_converter import TarskiConverter
from upf.test import TestCase
from upf.test.examples import get_example_problems
from upf.interop.tarski import convert_tarski_problem


class TestGrounder(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()
        self.tc = TarskiConverter()

    def test_basic(self):
        problem = self.problems['basic'].problem
        tarski_problem = self.tc.upf_to_tarski(problem)
        new_problem = convert_tarski_problem(problem.env, tarski_problem)
        print(problem)
        print(new_problem)
        assert False

    # def test_basic_conditional(self):
    #     problem = self.problems['basic_conditional'].problem
    #     tarski_problem = self.tc.upf_to_tarski(problem)
    #     print(problem)
    #     print(tarski_problem)
    #     print(tarski_problem.goal)
    #     print(tarski_problem.init)
    #     assert False


    # def test_complex_conditional(self):
    #     problem = self.problems['complex_conditional'].problem
    #     tarski_problem = self.tc.upf_to_tarski(problem)
    #     print(problem)
    #     print(tarski_problem)
    #     print(tarski_problem.goal)
    #     print(tarski_problem.init)
    #     print(tarski_problem.actions)
    #     for n, a in tarski_problem.actions.items():
    #         print(a)
    #         print(a.precondition)
    #         print(a.effects)
    #     assert False


    # def test_basic_nested_conjunctions(self):
    #     problem = self.problems['basic_nested_conjunctions'].problem
    #     tarski_problem = self.tc.upf_to_tarski(problem)
    #     print(problem)
    #     print(tarski_problem)
    #     print(tarski_problem.goal)
    #     print(tarski_problem.init)
    #     print(tarski_problem.actions)
    #     for n, a in tarski_problem.actions.items():
    #         print(a)
    #         print(a.precondition)
    #         print(a.effects)
    #     assert False


    # def test_basic_exists(self):
    #     problem = self.problems['basic_exists'].problem
    #     tarski_problem = self.tc.upf_to_tarski(problem)
    #     print(problem)
    #     print(tarski_problem)
    #     print(tarski_problem.goal)
    #     print(tarski_problem.init)
    #     print(tarski_problem.actions)
    #     for n, a in tarski_problem.actions.items():
    #         print(a)
    #         print(a.precondition)
    #         print(a.effects)
    #     assert False


    # def test_basic_forall(self):
    #     problem = self.problems['basic_forall'].problem
    #     tarski_problem = self.tc.upf_to_tarski(problem)
    #     print(problem)
    #     print(tarski_problem)
    #     print(tarski_problem.goal)
    #     print(tarski_problem.init)
    #     print(tarski_problem.actions)
    #     for n, a in tarski_problem.actions.items():
    #         print(a)
    #         print(a.precondition)
    #         print(a.effects)
    #     assert False


    # def test_robot(self):
    #     problem = self.problems['robot'].problem
    #     tarski_problem = self.tc.upf_to_tarski(problem)
    #     print(problem)
    #     print(tarski_problem)
    #     print(tarski_problem.goal)
    #     print(tarski_problem.init)
    #     print(tarski_problem.actions)
    #     for n, a in tarski_problem.actions.items():
    #         print(a)
    #         print(a.precondition)
    #         print(a.effects)
    #     assert False
