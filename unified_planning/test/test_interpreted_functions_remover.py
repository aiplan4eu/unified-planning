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
import unified_planning
from unified_planning.shortcuts import *
from unified_planning.exceptions import UPProblemDefinitionError
from unified_planning.model import GlobalStartTiming
from unified_planning.model.problem_kind import (
    classical_kind,
    full_classical_kind,
    basic_temporal_kind,
)
from unified_planning.test import skipIfEngineNotAvailable, unittest_TestCase, main
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

    def test_expected_kind(self):

        problem1 = self.problems["interpreted_functions_in_conditions"].problem
        problem2 = self.problems["go_home_with_rain_and_interpreted_functions"].problem
        with Compiler(
            problem_kind=problem1.kind,
            compilation_kind=CompilationKind.INTERPRETED_FUNCTIONS_REMOVING,
        ) as if_remover:
            kind1 = if_remover.resulting_problem_kind(
                problem1.kind, CompilationKind.INTERPRETED_FUNCTIONS_REMOVING
            )
            self.assertTrue(problem1.kind.has_interpreted_functions_in_conditions())
            self.assertFalse(kind1.has_interpreted_functions_in_conditions())
        with Compiler(
            problem_kind=problem1.kind,
            compilation_kind=CompilationKind.INTERPRETED_FUNCTIONS_REMOVING,
        ) as if_remover:
            kind2 = if_remover.resulting_problem_kind(
                problem2.kind, CompilationKind.INTERPRETED_FUNCTIONS_REMOVING
            )
            self.assertTrue(problem2.kind.has_interpreted_functions_in_durations())
            self.assertFalse(kind2.has_interpreted_functions_in_durations())

    def test_interpreted_functions_in_preconditions_remover_simple(self):
        problem = self.problems["interpreted_functions_in_conditions"].problem

        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.INTERPRETED_FUNCTIONS_REMOVING,
        ) as if_remover:
            ifr = if_remover.compile(
                problem, CompilationKind.INTERPRETED_FUNCTIONS_REMOVING
            )
        compiled_problem = ifr.problem

        self.assertTrue(problem.kind.has_interpreted_functions_in_conditions())
        self.assertFalse(problem.kind.has_simple_numeric_planning())
        self.assertTrue(problem.kind.has_general_numeric_planning())
        self.assertFalse(
            compiled_problem.kind.has_interpreted_functions_in_conditions()
        )

        self.assertTrue(compiled_problem.kind.has_general_numeric_planning())

    def test_interpreted_functions_in_preconditions_remover_always_impossible(self):
        problem = self.problems[
            "interpreted_functions_in_conditions_always_impossible"
        ].problem

        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.INTERPRETED_FUNCTIONS_REMOVING,
        ) as if_remover:
            ifr = if_remover.compile(
                problem, CompilationKind.INTERPRETED_FUNCTIONS_REMOVING
            )
        compiled_problem = ifr.problem
        self.assertTrue(problem.kind.has_interpreted_functions_in_conditions())
        self.assertFalse(problem.kind.has_simple_numeric_planning())
        self.assertFalse(
            compiled_problem.kind.has_interpreted_functions_in_conditions()
        )

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
        self.assertTrue(problem.kind.has_interpreted_functions_in_conditions())
        self.assertFalse(
            compiled_problem.kind.has_interpreted_functions_in_conditions()
        )

    def test_interpreted_functions_in_durations_remover(self):

        problem = self.problems["go_home_with_rain_and_interpreted_functions"].problem
        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.INTERPRETED_FUNCTIONS_REMOVING,
        ) as if_remover:
            expectedkind = if_remover.resulting_problem_kind(
                problem.kind, CompilationKind.INTERPRETED_FUNCTIONS_REMOVING
            )
            ifr = if_remover.compile(
                problem, CompilationKind.INTERPRETED_FUNCTIONS_REMOVING
            )
        compiled_problem = ifr.problem
        self.assertTrue(problem.kind.has_interpreted_functions_in_durations())
        self.assertTrue(expectedkind.has_int_type_durations())
        self.assertFalse(expectedkind.has_interpreted_functions_in_durations())
        self.assertFalse(compiled_problem.kind.has_interpreted_functions_in_durations())
        self.assertTrue(problem.kind.has_interpreted_functions_in_boolean_assignments())
        self.assertFalse(
            compiled_problem.kind.has_interpreted_functions_in_boolean_assignments()
        )
        self.assertFalse(
            compiled_problem.kind.has_interpreted_functions_in_numeric_assignments()
        )
