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

import upf
from upf.shortcuts import *
from upf.test import TestCase, main, skipIfNoOneshotPlannerForProblemKind, basic_temporal_kind
from upf.test.examples import get_example_problems


class TestTemporalPlanner(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfNoOneshotPlannerForProblemKind(basic_temporal_kind)
    def test_matchcellar(self):
        problem = self.problems['matchcellar'].problem

        with OneshotPlanner(problem_kind=problem.kind()) as planner:
            self.assertNotEqual(planner, None)
            plan = planner.solve(problem)
            self.assertEqual(len(plan.actions()), 6)
