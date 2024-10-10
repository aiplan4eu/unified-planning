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


class TestProcesses(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)

    def test_state(self):
        x = Fluent("x", BoolType())
        pr = Process("Name")
        pr.add_precondition(x)

        self.assertNotEqual({x}, pr.preconditions)
