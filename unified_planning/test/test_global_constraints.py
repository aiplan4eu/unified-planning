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
from unified_planning.exceptions import UPProblemDefinitionError
from unified_planning.model import GlobalStartTiming
from unified_planning.model.problem_kind import (
    classical_kind,
    full_classical_kind,
    basic_temporal_kind,
)
from unified_planning.test import TestCase, main
from unified_planning.test import (
    skipIfNoPlanValidatorForProblemKind,
    skipIfNoOneshotPlannerForProblemKind,
)
from unified_planning.test.examples import get_example_problems
from unified_planning.engines.compilers import ConditionalEffectsRemover
from unified_planning.engines import CompilationKind


class TestGlobalConstraintsRemover(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_basic_problem(self):
        problem = self.problems["basic"].problem.clone()
        x = problem.fluent("x")
        problem.add_global_constraint(Not(x))

        problem_kind = problem.kind
        self.assertEqual(len(problem.global_constraints), 1)
        self.assertTrue(problem.global_constraints[0] == Not(x))
        self.assertTrue(problem_kind.has_global_constraints())

        with Compiler(
            problem_kind=problem_kind,
            compilation_kind=CompilationKind.GLOBAL_CONSTRAINTS_REMOVING,
        ) as compiler:
            compiled_problem = compiler.compile(problem).problem
            # The goal of the original problem is x and we add not(x), so the goal becomes False
            self.assertEqual(len(compiled_problem.goals), 1)
            self.assertEqual(
                compiled_problem.goals[0],
                compiled_problem.environment.expression_manager.FALSE(),
            )
