# Copyright 2026 Unified Planning library and its maintainers
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

from typing import Dict

from unified_planning.shortcuts import *
from unified_planning.exceptions import (
    UPProblemDefinitionError,
    UPStateMissingFluentError,
)
from unified_planning.model import UPState
from unified_planning.model.walkers import QuantifierSimplifier, StateEvaluator
from unified_planning.test import unittest_TestCase


class TestStateEvaluator(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problem = Problem("state_evaluator")
        self.f1 = FluentExp(self.problem.add_fluent("f1", BoolType()))
        self.f2 = FluentExp(self.problem.add_fluent("f2", BoolType()))
        self.f3 = FluentExp(self.problem.add_fluent("f3", BoolType()))
        # f2 has no value in this state.
        self.state_without_f2 = UPState(
            {self.f1: FALSE(), self.f3: TRUE()}, self.problem
        )
        self.full_state = UPState(
            {self.f1: TRUE(), self.f2: TRUE(), self.f3: TRUE()}, self.problem
        )
        self.se = StateEvaluator(self.problem)

    def test_evaluate_after_missing_fluent_error(self):
        with self.assertRaises(UPStateMissingFluentError):
            self.se.evaluate(Not(self.f2), self.state_without_f2)
        self.assertEqual(self.se.evaluate(self.f1, self.state_without_f2), FALSE())

    def test_no_stale_memoization_after_error(self):
        # Children are walked last-first: Not(f1) is computed (TRUE in this
        # state) before f2 raises.
        with self.assertRaises(UPStateMissingFluentError):
            self.se.evaluate(Or(Not(self.f2), Not(self.f1)), self.state_without_f2)
        self.assertEqual(self.se.evaluate(Not(self.f1), self.full_state), FALSE())

    def test_no_leftover_stack_after_error(self):
        with self.assertRaises(UPStateMissingFluentError):
            self.se.evaluate(Or(Not(self.f2), Not(self.f1)), self.state_without_f2)
        self.assertEqual(self.se.stack, [])
        self.assertEqual(self.se.evaluate(self.f3, self.state_without_f2), TRUE())

    def test_qsimplify_after_missing_fluent_error(self):
        qs = QuantifierSimplifier(self.problem.environment, self.problem)
        assignments: Dict[Expression, Expression] = {self.f1: FALSE()}
        with self.assertRaises(UPProblemDefinitionError):
            qs.qsimplify(Not(self.f2), assignments, {})
        self.assertEqual(qs.qsimplify(self.f1, assignments, {}), FALSE())
