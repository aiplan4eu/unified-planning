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

from io import StringIO
import unified_planning
from unified_planning.shortcuts import *
from unified_planning.model.problem_kind import classical_kind, full_numeric_kind, full_classical_kind
from unified_planning.test import TestCase, skipIfSolverNotAvailable


class TestCredits(TestCase):
    def setUp(self):
        TestCase.setUp(self)

    @skipIfSolverNotAvailable('tamer')
    def test_robot_locations_visited(self):
        credits = StringIO()
        test_credits = '''You are using Tamer, developed by Fondazione Bruno Kessler.
Tamer solver and validator, more information can be found at the following link: https://www.ai4europe.eu/research/ai-catalog/tamer-unified-planning-interface

'''
        with OneshotPlanner(name='tamer', credits_stream=credits):
            self.assertEqual(credits.getvalue(), test_credits)
