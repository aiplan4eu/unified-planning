# Copyright 2021-2023 AIPlan4EU project
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


import pytest
import unified_planning as up
from unified_planning.shortcuts import *
from unified_planning.model.problem_kind import basic_classical_kind, hierarchical_kind
from unified_planning.test import (
    unittest_TestCase,
    main,
    skipIfEngineNotAvailable,
    skipIfNoOneshotPlannerForProblemKind,
)
from unified_planning.test.examples import get_example_problems


class TestPartialOrderPlan(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfEngineNotAvailable("sequential_plan_validator")
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    @pytest.mark.skip(
        reason="plan translation from sequential to partial order has not been implemented for IF"
    )
    def test_all(self):
        with PlanValidator(name="sequential_plan_validator") as validator:
            assert validator is not None
            for example in self.problems.values():
                problem, plans = example.problem, example.valid_plans
                if not plans:
                    continue
                plan = plans[0]
                if validator.supports(problem.kind):
                    self.assertTrue(isinstance(plan, up.plans.SequentialPlan))
                    pop_plan = plan.convert_to(PlanKind.PARTIAL_ORDER_PLAN, problem)
                    for i, sorted_plan in enumerate(pop_plan.all_sequential_plans()):
                        validation_result = validator.validate(problem, sorted_plan)
                        self.assertEqual(
                            up.engines.ValidationResultStatus.VALID,
                            validation_result.status,
                            msg=f"\n{problem}\n{sorted_plan}",
                        )
                        if i > 100:
                            break

    @skipIfNoOneshotPlannerForProblemKind(basic_classical_kind.union(hierarchical_kind))
    def test_blocks_world(self):
        problem = self.problems["hierarchical_blocks_world"].problem
        with Compiler(
            problem_kind=problem.kind,
            compilation_kinds=[
                CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING,
                CompilationKind.NEGATIVE_CONDITIONS_REMOVING,
            ],
        ) as compiler:
            comp_res = compiler.compile(problem)
        with OneshotPlanner(problem_kind=comp_res.problem.kind) as solver:
            self.assertIsNotNone(solver)
            comp_plan = solver.solve(comp_res.problem).plan
            self.assertIsNotNone(comp_plan)
            assert isinstance(comp_plan, up.plans.SequentialPlan)
            pop_comp_plan = comp_plan.convert_to(
                PlanKind.PARTIAL_ORDER_PLAN, comp_res.problem
            )
            pop_plan = pop_comp_plan.replace_action_instances(
                comp_res.map_back_action_instance
            )
            assert isinstance(pop_plan, up.plans.PartialOrderPlan)
        with PlanValidator(problem_kind=problem.kind) as validator:
            for plan in pop_plan.all_sequential_plans():
                validation_result = validator.validate(problem, plan)
                print(plan)
                self.assertEqual(
                    up.engines.ValidationResultStatus.VALID,
                    validation_result.status,
                )
