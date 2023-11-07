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

from unified_planning.shortcuts import *
from unified_planning.model.problem_kind import (
    classical_kind,
    full_classical_kind,
)
from unified_planning.test import unittest_TestCase, main
from unified_planning.test import (
    skipIfNoPlanValidatorForProblemKind,
    skipIfNoOneshotPlannerForProblemKind,
)
from unified_planning.test.examples import get_example_problems
from unified_planning.engines import CompilationKind


class TestCompilersPipeline(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    @skipIfNoPlanValidatorForProblemKind(full_classical_kind)
    def test_basic_conditional(self):
        problem = self.problems["basic_conditional"].problem
        with Compiler(
            problem_kind=problem.kind,
            compilation_kinds=[
                CompilationKind.CONDITIONAL_EFFECTS_REMOVING,
                CompilationKind.NEGATIVE_CONDITIONS_REMOVING,
            ],
        ) as compiler:
            res = compiler.compile(problem)
        new_problem = res.problem

        self.assertTrue(problem.kind.has_conditional_effects())
        self.assertFalse(new_problem.kind.has_conditional_effects())
        self.assertFalse(new_problem.kind.has_negative_conditions())

        with OneshotPlanner(problem_kind=new_problem.kind) as planner:
            self.assertNotEqual(planner, None)
            uncond_plan = planner.solve(new_problem).plan
            new_plan = uncond_plan.replace_action_instances(
                res.map_back_action_instance
            )
            with PlanValidator(
                problem_kind=problem.kind, plan_kind=new_plan.kind
            ) as pv:
                self.assertTrue(pv.validate(problem, new_plan))
