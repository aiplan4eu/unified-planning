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
from unified_planning.model.problem_kind import classical_kind
from unified_planning.engines.results import POSITIVE_OUTCOMES, NEGATIVE_OUTCOMES
from unified_planning.test import TestCase, main
from unified_planning.test import skipIfNoOneshotPlannerForProblemKind
from unified_planning.test.examples import get_example_problems


class TestReplanner(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    def test_basic(self):
        problem = self.problems["basic"].problem
        a = problem.action("a")
        x = problem.fluent("x")

        with Replanner(problem) as replanner:
            res = replanner.resolve()
            self.assertIn(res.status, POSITIVE_OUTCOMES)

            replanner.remove_action(a.name)
            res = replanner.resolve()
            self.assertIn(res.status, NEGATIVE_OUTCOMES)

            replanner.add_action(a)
            res = replanner.resolve()
            self.assertIn(res.status, POSITIVE_OUTCOMES)

            replanner.update_initial_value(x, True)
            res = replanner.resolve()
            self.assertIn(res.status, POSITIVE_OUTCOMES)
            self.assertEqual(len(res.plan.actions), 0)

            replanner.remove_goal(x)
            replanner.add_goal(Not(x))
            res = replanner.resolve()
            self.assertIn(res.status, NEGATIVE_OUTCOMES)

            replanner.remove_action(a.name)
            a = InstantaneousAction("a")
            a.add_precondition(x)
            a.add_effect(x, False)
            replanner.add_action(a)
            res = replanner.resolve()
            self.assertIn(res.status, POSITIVE_OUTCOMES)
