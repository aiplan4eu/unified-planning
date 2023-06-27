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
#

from unified_planning.shortcuts import *
from unified_planning.model.multi_agent import *
from collections import namedtuple
import unified_planning
from unified_planning.model.problem_kind import (
    basic_classical_kind,
    classical_kind,
    simple_numeric_kind,
    bounded_types_kind,
    full_classical_kind,
    basic_temporal_kind,
)
from unified_planning.test import (
    TestCase,
    skipIfNoPlanValidatorForProblemKind,
    skipIfNoOneshotPlannerForProblemKind,
)
from unified_planning.test.examples.multi_agent import get_example_problems
from unified_planning.engines import CompilationKind
from unified_planning.engines.compilers.ma_conditional_effects_remover import (
    MAConditionalEffectsRemover,
)


class TestMAConditionalEffectsRemover(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    @skipIfNoPlanValidatorForProblemKind(full_classical_kind)
    def test_ma_buttons(self):
        problem = self.problems["ma_buttons"].problem

        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.CONDITIONAL_EFFECTS_REMOVING,
        ) as cer:
            res = cer.compile(problem, CompilationKind.CONDITIONAL_EFFECTS_REMOVING)
        unconditional_problem = res.problem

        self.assertTrue(problem.kind.has_conditional_effects())
        self.assertFalse(unconditional_problem.kind.has_conditional_effects())
        for ag in unconditional_problem.agents:
            for a in ag.actions:
                self.assertFalse(a.is_conditional())

        self.assertEqual(len(problem.agent("a1").actions), 2)
        self.assertEqual(len(problem.agent("a2").actions), 4)
        self.assertEqual(len(problem.agent("a3").actions), 4)
        self.assertEqual(len(unconditional_problem.agent("a1").actions), 2)
        self.assertEqual(len(unconditional_problem.agent("a2").actions), 4)
        self.assertEqual(len(unconditional_problem.agent("a3").actions), 4)
