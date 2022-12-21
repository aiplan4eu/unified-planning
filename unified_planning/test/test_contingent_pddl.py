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
# limitations under the License

import os
import tempfile
from typing import cast
import pytest
import unified_planning
from unified_planning.shortcuts import *
from unified_planning.test import TestCase, main, skipIfNoOneshotPlannerForProblemKind
from unified_planning.io import PDDLWriter, PDDLReader
from unified_planning.test.examples import get_example_problems
from unified_planning.model.types import _UserType
from unified_planning.engines import PlanGenerationResultStatus


FILE_PATH = os.path.dirname(os.path.abspath(__file__))
CONTINGENT_PDDL_DOMAINS_PATH = os.path.join(FILE_PATH, "contingent_pddl")


class TestPddlIO(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_logistic_conf_reader(self):
        reader = PDDLReader()

        domain_filename = os.path.join(
            CONTINGENT_PDDL_DOMAINS_PATH, "logistic_conf", "domain.pddl"
        )
        problem_filename = os.path.join(
            CONTINGENT_PDDL_DOMAINS_PATH, "logistic_conf", "problem.pddl"
        )
        problem = reader.parse_problem(domain_filename, problem_filename)

        self.assertTrue(problem is not None)
        self.assertTrue(isinstance(problem, up.model.ContingentProblem))
        self.assertEqual(len(problem.fluents), 10)
        sensing_actions = [sa for sa in problem.sensing_actions]
        self.assertEqual(len(sensing_actions), 3)
        self.assertEqual(len(problem.actions), 12)

        for sa in sensing_actions:
            self.assertEqual(len(sa.parameters), 3)
            self.assertEqual(len(sa.preconditions), 1)
            self.assertEqual(len(sa.observed_fluents), 1)

    def test_colorballs_reader(self):
        reader = PDDLReader()

        domain_filename = os.path.join(
            CONTINGENT_PDDL_DOMAINS_PATH, "colorballs", "domain.pddl"
        )
        problem_filename = os.path.join(
            CONTINGENT_PDDL_DOMAINS_PATH, "colorballs", "problem.pddl"
        )
        problem = reader.parse_problem(domain_filename, problem_filename)

        self.assertTrue(problem is not None)
        self.assertTrue(isinstance(problem, up.model.ContingentProblem))
        self.assertEqual(len(problem.fluents), 8)
        sensing_actions = [sa for sa in problem.sensing_actions]
        self.assertEqual(len(sensing_actions), 2)
        self.assertEqual(len(problem.actions), 5)

        for sa in sensing_actions:
            self.assertEqual(len(sa.parameters), 2)
            self.assertEqual(len(sa.preconditions), 1)
            self.assertEqual(len(sa.observed_fluents), 1)
