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


import unified_planning as up
from unified_planning.shortcuts import *
from unified_planning.test import unittest_TestCase
from unified_planning.test.examples import get_example_problems
from unified_planning.exceptions import UPTypeError


class TestProblemKindVersioning(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_version_2_1(self):
        equals_expected_result = {
            (
                ProblemKind(
                    ("CONTINUOUS_NUMBERS", "DISCRETE_NUMBERS", "NUMERIC_FLUENTS")
                ),
                ProblemKind(("REAL_FLUENTS", "INT_FLUENTS")),
            ): False,
            (
                ProblemKind(("CONTINUOUS_NUMBERS", "NUMERIC_FLUENTS"), 1),
                ProblemKind(("REAL_FLUENTS",)),
            ): False,
            (
                ProblemKind(("CONTINUOUS_NUMBERS", "NUMERIC_FLUENTS"), 1),
                ProblemKind(("CONTINUOUS_NUMBERS", "NUMERIC_FLUENTS")),
            ): True,
            (
                ProblemKind(("CONTINUOUS_NUMBERS",), 1),
                ProblemKind(("REAL_FLUENTS",)),
            ): False,
            (
                ProblemKind(("CONTINUOUS_NUMBERS", "DISCRETE_NUMBERS"), 2),
                ProblemKind(("REAL_FLUENTS", "INT_FLUENTS")),
            ): False,
            (
                ProblemKind(
                    (
                        "CONTINUOUS_NUMBERS",
                        "DISCRETE_NUMBERS",
                        "REAL_FLUENTS",
                        "INT_FLUENTS",
                    ),
                    2,
                ),
                ProblemKind(("REAL_FLUENTS", "INT_FLUENTS")),
            ): True,
            (
                ProblemKind(("REAL_FLUENTS", "INT_FLUENTS")),
                ProblemKind(("CONTINUOUS_NUMBERS", "DISCRETE_NUMBERS"), 2),
            ): False,
        }

        le_expected_results = {
            (
                ProblemKind(("CONTINUOUS_NUMBERS", "DISCRETE_NUMBERS")),
                ProblemKind(("REAL_FLUENTS", "INT_FLUENTS")),
            ): True,
            (
                ProblemKind(("CONTINUOUS_NUMBERS", "DISCRETE_NUMBERS"), 1),
                ProblemKind(("REAL_FLUENTS", "INT_FLUENTS")),
            ): True,
            (
                ProblemKind(("CONTINUOUS_NUMBERS", "DISCRETE_NUMBERS"), 2),
                ProblemKind(("REAL_FLUENTS", "INT_FLUENTS")),
            ): True,
            (
                ProblemKind(("REAL_FLUENTS", "INT_FLUENTS")),
                ProblemKind(("CONTINUOUS_NUMBERS", "DISCRETE_NUMBERS"), 2),
            ): False,
            (
                ProblemKind(("NUMERIC_FLUENTS", "DISCRETE_NUMBERS")),
                ProblemKind(("UNBOUNDED_INT_ACTION_PARAMETERS", "INT_FLUENTS")),
            ): True,
        }

        for i, ((left_pk, right_pk), res) in enumerate(equals_expected_result.items()):
            self.assertEqual(
                left_pk == right_pk,
                res,
                f"{i}) {left_pk} == {right_pk} expected {res} but returned {left_pk == right_pk}",
            )
            assert (right_pk == left_pk) == (
                right_pk == left_pk
            ), f"{i}) Error, equality does not work both ways"

        for i, ((left_pk, right_pk), res) in enumerate(le_expected_results.items()):
            self.assertEqual(
                left_pk <= right_pk,
                res,
                f"{i}) {left_pk} <= {right_pk} expected {res} but returned {left_pk <= right_pk}",
            )
