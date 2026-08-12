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
from unified_planning.engines import CompilationKind
from unified_planning.engines.compilers import (
    ConditionalEffectsRemover,
    StateInvariantsRemover,
)
from unified_planning.exceptions import UPProblemDefinitionError
from unified_planning.model import GlobalStartTiming
from unified_planning.model.problem_kind import (
    basic_temporal_kind,
    classical_kind,
    full_classical_kind,
)
from unified_planning.shortcuts import *
from unified_planning.test import (
    main,
    skipIfNoOneshotPlannerForProblemKind,
    skipIfNoPlanValidatorForProblemKind,
    unittest_TestCase,
)
from unified_planning.test.examples import get_example_problems


class TestStateInvariantsRemover(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_basic_problem(self):
        problem = self.problems["basic"].problem.clone()
        x = problem.fluent("x")
        problem.add_state_invariant(Not(x))

        problem_kind = problem.kind
        self.assertEqual(len(problem.state_invariants), 1)
        self.assertTrue(problem.state_invariants[0] == Not(x))
        self.assertTrue(problem_kind.has_state_invariants())

        with Compiler(
            problem_kind=problem_kind,
            compilation_kind=CompilationKind.STATE_INVARIANTS_REMOVING,
        ) as compiler:
            compiled_problem = compiler.compile(problem).problem
            # The goal of the original problem is x and we add not(x), so the goal becomes False
            self.assertEqual(len(compiled_problem.goals), 1)
            self.assertEqual(
                compiled_problem.goals[0],
                compiled_problem.environment.expression_manager.FALSE(),
            )

    def test_resulting_problem_kind_with_state_invariants(self):
        problem = self.problems["robot_loader_weak_bridge"].problem
        self.assertTrue(problem.kind.has_state_invariants())

        new_kind = StateInvariantsRemover.resulting_problem_kind(
            problem.kind, CompilationKind.STATE_INVARIANTS_REMOVING
        )
        self.assertFalse(new_kind.has_state_invariants())

        compiled = (
            StateInvariantsRemover()
            .compile(problem, CompilationKind.STATE_INVARIANTS_REMOVING)
            .problem
        )
        assert isinstance(compiled, Problem)
        self.assertTrue(compiled.kind <= new_kind)

    def test_compilers_pipeline_with_state_invariants(self):
        problem = self.problems["robot_loader_weak_bridge"].problem
        with Compiler(
            problem_kind=problem.kind,
            compilation_kinds=[CompilationKind.STATE_INVARIANTS_REMOVING],
        ) as compiler:
            compiled = compiler.compile(problem).problem
        self.assertFalse(compiled.kind.has_state_invariants())
