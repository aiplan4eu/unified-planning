# Copyright 2023 AIPlan4EU project
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

import os

import unified_planning as up
from unified_planning.io import PDDLReader
from unified_planning.model.htn import TaskNetwork, Task
from unified_planning.model.htn.ordering import PartialOrder, TotalOrder
from unified_planning.shortcuts import *
from unified_planning.test import TestCase, main, examples
from unified_planning.test.examples import get_example_problems


FILE_PATH = os.path.dirname(os.path.abspath(__file__))


class TestScheduling(TestCase):
    def test_load_all(self):
        problems = up.test.scheduling.problems()
        for name, test_case in problems.items():
            problem = test_case.problem
            print(f"======== {name} =============")
            print(problem)

            cloned = problem.clone()
            self.assertEqual(problem, cloned)
            self.assertEqual(hash(problem), hash(cloned))
