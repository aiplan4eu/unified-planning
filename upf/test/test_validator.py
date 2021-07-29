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


class TestPlanValidator(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_basic(self):
        problem, plan = self.problems['basic']

        with PlanValidator(problem_kind=problem.kind()) as validator:
            self.assertNotEqual(validator, None)

            res = validator.validate(problem, plan)
            self.assertTrue(res)

            plan = upf.SequentialPlan([])
            res = validator.validate(problem, plan)
            self.assertFalse(res)

    def test_robot(self):
        problem, plan = self.problems['robot']

        with PlanValidator(problem_kind=problem.kind()) as validator:
            self.assertNotEqual(validator, None)

            res = validator.validate(problem, plan)
            self.assertTrue(res)

            plan = upf.SequentialPlan([])
            res = validator.validate(problem, plan)
            self.assertFalse(res)

    def test_robot_loader(self):
        problem, plan = self.problems['robot_loader']

        with PlanValidator(problem_kind=problem.kind()) as validator:
            self.assertNotEqual(validator, None)

            res = validator.validate(problem, plan)
            self.assertTrue(res)

            plan = upf.SequentialPlan([])
            res = validator.validate(problem, plan)
            self.assertFalse(res)

    def test_robot_loader_adv(self):
        problem, plan = self.problems['robot_loader_adv']

        with PlanValidator(problem_kind=problem.kind()) as validator:
            self.assertNotEqual(validator, None)

            res = validator.validate(problem, plan)
            self.assertTrue(res)

            plan = upf.SequentialPlan([])
            res = validator.validate(problem, plan)
            self.assertFalse(res)


if __name__ == "__main__":
    main()
