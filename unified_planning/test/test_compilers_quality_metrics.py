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

from unified_planning.shortcuts import *
from unified_planning.model.problem_kind import (
    basic_classical_kind,
    oversubscription_kind,
)
from unified_planning.test import TestCase, main
from unified_planning.test import skipIfNoOneshotPlannerForProblemKind
from unified_planning.test.examples import get_example_problems
from unified_planning.engines import CompilationKind


class TestCompilersPipeline(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfNoOneshotPlannerForProblemKind(
        basic_classical_kind.union(oversubscription_kind)
    )
    def test_locations_connected_visited_oversubscription(self):
        problem, test_plan = self.problems[
            "locations_connected_visited_oversubscription"
        ]
        with Compiler(
            problem_kind=problem.kind,
            compilation_kinds=[
                CompilationKind.GROUNDING,
                CompilationKind.QUANTIFIERS_REMOVING,
                CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING,
                CompilationKind.NEGATIVE_CONDITIONS_REMOVING,
            ],
        ) as compiler:
            res = compiler.compile(problem)
        new_problem = res.problem

        with OneshotPlanner(problem_kind=problem.kind) as planner:
            self.assertNotEqual(planner, None)
            plan = planner.solve(new_problem).plan
            new_plan = plan.replace_action_instances(res.map_back_action_instance)
            self.assertEqual(new_plan, test_plan)
