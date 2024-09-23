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

import pytest
import unified_planning as up
from unified_planning.shortcuts import *
from unified_planning.model.problem_kind import (
    simple_numeric_kind,
    quality_metrics_kind,
)
from unified_planning.engines.results import PlanGenerationResultStatus
from unified_planning.io import PDDLReader
from unified_planning.model.metrics import MinimizeSequentialPlanLength
from unified_planning.test import (
    unittest_TestCase,
    skipIfNoAnytimePlannerForProblemKind,
)


FILE_PATH = os.path.dirname(os.path.abspath(__file__))
PDDL_DOMAINS_PATH = os.path.join(FILE_PATH, "pddl")


class TestAnytimePlanning(unittest_TestCase):
    @skipIfNoAnytimePlannerForProblemKind(
        simple_numeric_kind.union(quality_metrics_kind),
        up.engines.AnytimeGuarantee.INCREASING_QUALITY,
    )
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    # the following skip MUST BE REMOVED
    @pytest.mark.skip(
        reason="There is currently a bug with this one - planner returns engine error"
    )  # this fails now even without adding if problems to minimals
    def test_counters(self):
        reader = PDDLReader()
        domain_filename = os.path.join(PDDL_DOMAINS_PATH, "counters", "domain.pddl")
        problem_filename = os.path.join(PDDL_DOMAINS_PATH, "counters", "problem2.pddl")
        problem = reader.parse_problem(domain_filename, problem_filename)
        problem.add_quality_metric(MinimizeSequentialPlanLength())

        with AnytimePlanner(
            problem_kind=problem.kind, anytime_guarantee="INCREASING_QUALITY"
        ) as planner:
            self.assertTrue(planner.is_anytime_planner())
            solutions = []
            for p in planner.get_solutions(problem):
                self.assertTrue(p.plan is not None)
                solutions.append(p)
                if len(solutions) == 2:
                    break
        # print(solutions[0].actions)
        # print(solutions[1].actions)

        self.assertEqual(len(solutions), 2)
        self.assertEqual(solutions[0].status, PlanGenerationResultStatus.INTERMEDIATE)
        if solutions[1].status == PlanGenerationResultStatus.INTERMEDIATE:
            self.assertGreater(
                len(solutions[0].plan.actions), len(solutions[1].plan.actions)
            )
        else:
            self.assertGreaterEqual(
                len(solutions[0].plan.actions), len(solutions[1].plan.actions)
            )
