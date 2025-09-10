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

from random import shuffle
import unified_planning
from unified_planning.shortcuts import *
from unified_planning.test import unittest_TestCase
from unified_planning.exceptions import UPValueError


class TestUPState(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)

    def assert_same_state(self, state_1, state_2):
        self.assertEqual(state_1, state_2)
        self.assertEqual(state_2, state_1)
        self.assertEqual(hash(state_1), hash(state_2))
        self.assertEqual(hash(state_2), hash(state_1))

    def assert_different_state(self, state_1, state_2):
        self.assertNotEqual(state_1, state_2)
        self.assertNotEqual(state_2, state_1)

    def test_state(self):
        dummy_problem = Problem()

        fluents = [FluentExp(Fluent(f"{n}", IntType())) for n in "abc"]
        a, b, c = fluents
        numbers = [Int(n) for n in range(6)]
        n0, n1, n2, n3, n4, n5 = numbers

        state_1 = UPState({a: n0, b: n1, c: n2}, dummy_problem)
        state_1_copy = UPState({a: n0, b: n1, c: n2}, dummy_problem)

        self.assert_same_state(state_1, state_1_copy)

        state_1 = state_1.make_child({a: n3})
        state_1_copy = state_1_copy.make_child({a: n3})

        self.assert_same_state(state_1, state_1_copy)

        state_2 = UPState({a: n0, b: n1, c: n2}, dummy_problem)

        self.assert_different_state(state_1, state_2)

        state_3 = state_2.make_child({a: n3})
        self.assert_different_state(state_2, state_3)
        self.assert_same_state(state_1, state_3)
        state_4 = state_3.make_child({a: n0})

        self.assert_same_state(state_2, state_4)

        state_2 = state_2.make_child({c: n4})
        state_4 = state_4.make_child({c: n5})

        self.assert_different_state(state_2, state_4)

        state_2 = state_2.make_child({b: n3})
        state_4 = state_4.make_child({b: n3})

        self.assert_different_state(state_2, state_4)

        state_2 = state_2.make_child({c: n5})

        self.assert_same_state(state_2, state_4)

    def test_non_constant_values(self):
        dummy_problem = Problem()

        fluents = [FluentExp(Fluent(f"{n}", IntType())) for n in "ab"]
        a, b = fluents
        n0 = Int(0)

        with self.assertRaises(UPValueError):
            UPState({a: b}, dummy_problem)

        with self.assertRaises(UPValueError):
            UPState({a: n0 + b}, dummy_problem)
