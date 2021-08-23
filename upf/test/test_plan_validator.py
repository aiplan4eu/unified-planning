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
from upf.test import TestCase, main
from upf.test.examples import get_example_problems
from upf.plan_validator import PlanValidator
from upf.environment import get_env

class TestProblem(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_basic(self):
        problem, plan = self.problems['basic'].problem, self.problems['basic'].plan
        pv = PlanValidator(get_env())
        self.assertTrue(pv.is_valid_plan(problem, plan))

    def test_robot(self):
        problem, plan = self.problems['robot'].problem, self.problems['robot'].plan
        pv = PlanValidator(get_env())
        self.assertTrue(pv.is_valid_plan(problem, plan))

    def test_complex_conditional(self):
        problem, plan = self.problems['complex_conditional'].problem, self.problems['complex_conditional'].plan
        pv = PlanValidator(get_env())
        self.assertTrue(pv.is_valid_plan(problem, plan))

    def test_all(self):
        pv = PlanValidator(get_env())
        for p in self.problems.values():
            problem, plan = p.problem, p.plan
            self.assertTrue(pv.is_valid_plan(problem, plan))
