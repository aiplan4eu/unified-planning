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


import unified_planning
from unified_planning.shortcuts import *
from unified_planning.test import TestCase, main
from unified_planning.test.examples import get_example_problems
from unified_planning.engines import SequentialPlanValidator, ValidationResultStatus
from unified_planning.environment import get_environment


class TestProblem(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_all(self):
        pv = SequentialPlanValidator(environment=get_environment())
        for p in self.problems.values():
            if not pv.supports(p.problem.kind):
                continue
            problem, plan = p.problem, p.plan
            if SequentialPlanValidator.supports(problem.kind):
                validation_result = pv.validate(problem, plan)
                self.assertEqual(validation_result.status, ValidationResultStatus.VALID)

    def test_all_from_factory(self):
        with PlanValidator(name="sequential_plan_validator") as pv:
            self.assertEqual(pv.name, "sequential_plan_validator")
            for p in self.problems.values():
                if not pv.supports(p.problem.kind):
                    continue
                problem, plan = p.problem, p.plan
                validation_result = pv.validate(problem, plan)
                self.assertEqual(validation_result.status, ValidationResultStatus.VALID)

    def test_all_from_factory_with_problem_kind(self):
        for p in self.problems.values():
            problem, plan = p.problem, p.plan
            pk = problem.kind
            if SequentialPlanValidator.supports(pk):
                environment = unified_planning.environment.Environment()
                environment.factory.preference_list = [
                    e for e in environment.factory.preference_list if e != "tamer"
                ]
                with environment.factory.PlanValidator(
                    problem_kind=pk, plan_kind=plan.kind
                ) as pv:
                    self.assertEqual(pv.name, "sequential_plan_validator")
                    validation_result = pv.validate(problem, plan)
                    self.assertEqual(
                        validation_result.status, ValidationResultStatus.VALID
                    )
