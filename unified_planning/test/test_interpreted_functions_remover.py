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


import unified_planning
from unified_planning.shortcuts import *
from unified_planning.exceptions import UPProblemDefinitionError
from unified_planning.model import GlobalStartTiming
from unified_planning.model.problem_kind import (
    classical_kind,
    full_classical_kind,
    basic_temporal_kind,
)
from unified_planning.test import unittest_TestCase, main
from unified_planning.test import (
    skipIfNoPlanValidatorForProblemKind,
    skipIfNoOneshotPlannerForProblemKind,
)
from unified_planning.test.examples import get_example_problems
from unified_planning.engines.compilers import ConditionalEffectsRemover
from unified_planning.engines import CompilationKind


class TestInterpretedFunctionsRemover(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_interpreted_functions_in_preconditions_remover(self):
        problem = self.problems["interpreted_functions_in_conditions"].problem

        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.INTERPRETED_FUNCTIONS_REMOVING,
        ) as if_remover:
            ifr = if_remover.compile(
                problem, CompilationKind.INTERPRETED_FUNCTIONS_REMOVING
            )
        compiled_problem = ifr.problem
        print(problem)
        print(problem.kind)
        print(compiled_problem)
        print(compiled_problem.kind)
        self.assertTrue(problem.kind.has_interpreted_functions_in_conditions())
        self.assertFalse(problem.kind.has_simple_numeric_planning())
        self.assertFalse(
            compiled_problem.kind.has_interpreted_functions_in_conditions()
        )
        self.assertTrue(compiled_problem.kind.has_simple_numeric_planning())

    def test_interpreted_functions_in_durative_conditions_remover(self):
        problem = self.problems["interpreted_functions_in_durative_conditions"].problem

        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.INTERPRETED_FUNCTIONS_REMOVING,
        ) as if_remover:
            ifr = if_remover.compile(
                problem, CompilationKind.INTERPRETED_FUNCTIONS_REMOVING
            )
        compiled_problem = ifr.problem
        print(problem)
        print(problem.kind)
        print(compiled_problem)
        print(compiled_problem.kind)
        self.assertTrue(problem.kind.has_interpreted_functions_in_conditions())
        self.assertFalse(problem.kind.has_simple_numeric_planning())
        self.assertFalse(
            compiled_problem.kind.has_interpreted_functions_in_conditions()
        )
        self.assertTrue(compiled_problem.kind.has_simple_numeric_planning())