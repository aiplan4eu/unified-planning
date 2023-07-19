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
from unified_planning.test import TestCase
from unified_planning.test.examples.tamp import get_example_problems


class TestTAMPProblem(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_tamp_problem_creation(self):
        problem = self.problems["tamp_feasible"].problem
        self.assertTrue(isinstance(problem, Problem))

        self.assertTrue(problem.kind.has_tamp())
        self.assertEqual(1, len(problem.fluents))
        self.assertEqual(1, len(problem.actions))
        self.assertEqual(3, len(problem.all_objects))
        self.assertTrue(problem.object("r1").type.is_movable_type())
        self.assertTrue(problem.object("c1").type.is_configuration_type())
        self.assertTrue(problem.object("c2").type.is_configuration_type())

        move = problem.action("move")
        self.assertEqual(1, len(move.motion_constraints))
        self.assertTrue(isinstance(move.motion_constraints[0], Waypoints))
