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


import unified_planning as up
from unified_planning.shortcuts import *
from unified_planning.model.problem_kind import full_classical_kind, full_numeric_kind
from unified_planning.test import TestCase, main, skipIfSolverNotAvailable
from unified_planning.test.examples import get_example_problems


class TestPartialOrderPlan(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfSolverNotAvailable('sequential_plan_validator')
    def test_all(self):
        with PlanValidator(name='sequential_plan_validator') as validator:
            assert validator is not None
            for problem, plan in self.problems.values():
                if validator.supports(problem.kind):
                    assert isinstance(plan, up.plans.SequentialPlan)
                    pop_plan = plan.to_partial_order_plan(problem)
                    for sorted_plan in pop_plan.all_sequential_plans():
                        validation_result = validator.validate(problem, sorted_plan)
                        self.assertEqual(up.solvers.ValidationResultStatus.VALID, validation_result.status)
