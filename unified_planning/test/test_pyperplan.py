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

import warnings
import unified_planning as up
from unified_planning.shortcuts import *
from unified_planning.engines.results import POSITIVE_OUTCOMES
from unified_planning.test import TestCase, main, skipIfEngineNotAvailable
from unified_planning.environment import get_environment
from unified_planning.test.examples import get_example_problems


class TestPyperplan(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.environment = get_environment()
        self.problems = get_example_problems()

    @skipIfEngineNotAvailable("pyperplan")
    def test_pyperplan(self):
        problem, plan = self.problems["robot_no_negative_preconditions"]
        with OneshotPlanner(name="pyperplan") as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)
            self.assertIn(final_report.status, POSITIVE_OUTCOMES)
            self.assertEqual(str(plan), str(final_report.plan))

    @skipIfEngineNotAvailable("pyperplan")
    def test_basic_without_negative_preconditions(self):
        problem, plan = self.problems["basic_without_negative_preconditions"]
        with OneshotPlanner(name="pyperplan") as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)
            self.assertIn(final_report.status, POSITIVE_OUTCOMES)
            self.assertEqual(str(plan), str(final_report.plan))

    @skipIfEngineNotAvailable("pyperplan")
    def test_basic_nested_conjunctions(self):
        problem, plan = self.problems["basic_nested_conjunctions"]
        with OneshotPlanner(name="pyperplan") as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)
            self.assertIn(final_report.status, POSITIVE_OUTCOMES)
            self.assertEqual(str(plan), str(final_report.plan))

    @skipIfEngineNotAvailable("pyperplan")
    def test_hierarchical_blocks_world(self):
        problem, plan = self.problems["hierarchical_blocks_world"]
        with OneshotPlanner(name="pyperplan") as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)
            self.assertIn(final_report.status, POSITIVE_OUTCOMES)
            self.assertEqual(str(plan), str(final_report.plan))

    @skipIfEngineNotAvailable("pyperplan")
    def test_hierarchical_blocks_world_object_as_root(self):
        problem, plan = self.problems["hierarchical_blocks_world_object_as_root"]
        with OneshotPlanner(name="pyperplan") as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)
            self.assertIn(final_report.status, POSITIVE_OUTCOMES)
            self.assertEqual(str(plan), str(final_report.plan))

    @skipIfEngineNotAvailable("pyperplan")
    def test_hierarchical_blocks_world_with_object(self):
        problem, plan = self.problems["hierarchical_blocks_world_with_object"]
        with OneshotPlanner(name="pyperplan") as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)
            self.assertIn(final_report.status, POSITIVE_OUTCOMES)
            self.assertEqual(str(plan), str(final_report.plan))

    @skipIfEngineNotAvailable("pyperplan")
    def test_hierarchical_blocks_world_with_object_with_timeout(self):
        problem, plan = self.problems["hierarchical_blocks_world_with_object"]
        with OneshotPlanner(name="pyperplan") as planner:
            self.assertNotEqual(planner, None)
            with warnings.catch_warnings(record=True) as w:
                final_report = planner.solve(problem, timeout=0.001)
                self.assertIn(final_report.status, POSITIVE_OUTCOMES)
                self.assertEqual(str(plan), str(final_report.plan))
                self.assertEqual(len(w), 1)
                self.assertEqual(
                    "Pyperplan does not support timeout.", str(w[-1].message)
                )
