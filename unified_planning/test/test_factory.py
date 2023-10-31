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

import os
import inspect
import tempfile
import unified_planning
from unified_planning.test.examples import get_example_problems
from unified_planning.shortcuts import *
from unified_planning.test import unittest_TestCase, skipIfEngineNotAvailable


class TestFactory(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfEngineNotAvailable("pyperplan")
    @skipIfEngineNotAvailable("tamer")
    def test_config_file(self):
        self.assertTrue("pyperplan" in get_environment().factory.preference_list)
        with tempfile.TemporaryDirectory() as tempdir:
            config_filename = os.path.join(tempdir, "up.ini")
            with open(config_filename, "w") as config:
                config.write("[global]\n")
                config.write("engine_preference_list: tamer\n")
            environment = unified_planning.environment.Environment()
            environment.factory.configure_from_file(config_filename)
            self.assertTrue("pyperplan" not in environment.factory.preference_list)
            self.assertEqual(environment.factory.preference_list, ["tamer"])

    @skipIfEngineNotAvailable("pyperplan")
    @skipIfEngineNotAvailable("tamer")
    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_get_all_applicable_engines(self):
        problem = self.problems["basic"].problem
        factory = problem.environment.factory
        names = factory.get_all_applicable_engines(problem.kind)
        expected_names = ["tamer", "opt-pddl-planner"]
        for name in expected_names:
            self.assertIn(name, names)

        problem = self.problems["basic_without_negative_preconditions"].problem
        names = factory.get_all_applicable_engines(problem.kind)
        expected_names = ["tamer", "opt-pddl-planner", "pyperplan"]
        for name in expected_names:
            self.assertIn(name, names)

        global_env_names = get_all_applicable_engines(problem.kind)
        self.assertEqual(global_env_names, names)
