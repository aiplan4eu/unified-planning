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
from unified_planning.exceptions import UPTypeError
from unified_planning.shortcuts import *
from unified_planning.test import TestCase


class UndefinedCheck(TestCase):
    def test_undefined(self):
        u = UNDEFINED()
        f = Fluent("f")
        self.assertTrue(u.type.is_undefined_type())

        exp_1 = And(u, f)
        self.assertTrue(exp_1.type.is_undefined_type())

        exp_2 = Plus(exp_1, 5)
        self.assertTrue(exp_2.type.is_undefined_type())

        with self.assertRaises(UPTypeError):
            Plus(f, 5)

        exp_3 = And(u, Plus(f, 5))
        exp_4 = And(Plus(f, 5), u)
