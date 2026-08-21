# Copyright 2021-2023 AIPlan4EU project
# Copyright 2024-2026 Unified Planning library and its maintainers
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

from unified_planning.exceptions import UPUsageError
from unified_planning.engines.results import (
    PlanGenerationResult,
    PlanGenerationResultStatus,
    CompilerResult,
)
from unified_planning.model import Problem
from unified_planning.plans import SequentialPlan
from unified_planning.test import unittest_TestCase, main

A_PLAN = SequentialPlan([])


class TestPlanGenerationResult(unittest_TestCase):
    def test_positive_outcome_without_plan_raises(self):
        with self.assertRaises(UPUsageError):
            PlanGenerationResult(
                PlanGenerationResultStatus.SOLVED_SATISFICING, None, "some_engine"
            )

    def test_negative_outcome_with_plan_raises(self):
        with self.assertRaises(UPUsageError):
            PlanGenerationResult(
                PlanGenerationResultStatus.UNSOLVABLE_PROVEN,
                A_PLAN,
                "some_engine",
            )

    def test_consistent_positive_outcome_does_not_raise(self):
        result = PlanGenerationResult(
            PlanGenerationResultStatus.SOLVED_SATISFICING,
            A_PLAN,
            "some_engine",
        )
        self.assertEqual(result.plan, A_PLAN)

    def test_consistent_negative_outcome_does_not_raise(self):
        result = PlanGenerationResult(
            PlanGenerationResultStatus.UNSOLVABLE_PROVEN, None, "some_engine"
        )
        self.assertIsNone(result.plan)


class TestCompilerResult(unittest_TestCase):
    def test_none_problem_with_map_back_action_instance_raises(self):
        with self.assertRaises(UPUsageError):
            CompilerResult(None, lambda x: x, "some_engine")

    def test_none_problem_with_plan_back_conversion_raises(self):
        with self.assertRaises(UPUsageError):
            CompilerResult(None, None, "some_engine", plan_back_conversion=lambda x: x)

    def test_non_none_problem_without_conversions_raises(self):
        with self.assertRaises(UPUsageError):
            CompilerResult(Problem("some_problem"), None, "some_engine")

    def test_non_none_problem_with_both_conversions_raises(self):
        with self.assertRaises(UPUsageError):
            CompilerResult(
                Problem("some_problem"),
                lambda x: x,
                "some_engine",
                plan_back_conversion=lambda x: x,
            )

    def test_none_problem_without_conversions_does_not_raise(self):
        result = CompilerResult(None, None, "some_engine")
        self.assertIsNone(result.problem)

    def test_non_none_problem_with_map_back_action_instance_sets_plan_back_conversion(
        self,
    ):
        result = CompilerResult(Problem("some_problem"), lambda x: x, "some_engine")
        self.assertIsNotNone(result.plan_back_conversion)


if __name__ == "__main__":
    main()
