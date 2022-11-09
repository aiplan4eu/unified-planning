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
from unified_planning.test import skipIfNoOneshotPlannerSatisfiesOptimalityGuarantee
from unified_planning.io import PDDLWriter, PDDLReader
from unified_planning.test.examples import get_example_problems
from unified_planning.model.problem_kind import full_numeric_kind
from unified_planning.model.types import _UserType
from unified_planning.engines import PlanGenerationResultStatus


FILE_PATH = os.path.dirname(os.path.abspath(__file__))
PDDL_DOMAINS_PATH = os.path.join(FILE_PATH, "pddl")


class TestPddlIO(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_a_logistic_conf_reader(self):
        reader = PDDLReader()

        domain_filename = os.path.join(
            PDDL_DOMAINS_PATH, "logistic_conf", "domain.pddl"
        )
        problem_filename = os.path.join(
            PDDL_DOMAINS_PATH, "logistic_conf", "problem.pddl"
        )
        problem = reader.parse_problem(domain_filename, problem_filename)

        self.assertTrue(problem is not None)
        self.assertTrue(isinstance(problem, up.model.ContingentProblem))
        self.assertEqual(len(problem.fluents), 9)
        self.assertEqual(len([problem.sensing_actions]), 3)
        self.assertEqual(len(problem.actions), 11)
        natural_disaster = problem.action("natural_disaster")
        # 9 effects because the forall is expanded in 3 * 3 possible locations instantiations
        self.assertEqual(len(natural_disaster.effects), 9)
        self.assertEqual(len(list(problem.objects(problem.user_type("location")))), 3)
