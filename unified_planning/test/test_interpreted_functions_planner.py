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


import pytest
import unified_planning
from unified_planning.engines.results import PlanGenerationResultStatus
from unified_planning.shortcuts import *
from unified_planning.exceptions import UPProblemDefinitionError
from unified_planning.model import GlobalStartTiming
from unified_planning.model.problem_kind import (
    classical_kind,
    full_classical_kind,
    basic_temporal_kind,
)
from unified_planning.test import skipIfEngineNotAvailable, unittest_TestCase, main
from unified_planning.test import (
    skipIfNoPlanValidatorForProblemKind,
    skipIfNoOneshotPlannerForProblemKind,
)
from unified_planning.test.examples import get_example_problems
from unified_planning.engines.compilers import ConditionalEffectsRemover
from unified_planning.engines import CompilationKind


class TestInterpretedFunctionsRemover(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfEngineNotAvailable("sequential_plan_validator")
    @skipIfEngineNotAvailable("tamer")
    @skipIfEngineNotAvailable("enhsp")
    def test_interpreted_functions_in_preconditions_planner(self):
        problem = self.problems["interpreted_functions_in_conditions"].problem
        # print (problem)
        # print (problem.kind)
        self.assertTrue(problem.kind.has_interpreted_functions_in_conditions())
        self.assertFalse(problem.kind.has_simple_numeric_planning())

        with OneshotPlanner(name="interpreted_functions_planning[tamer]") as planner:
            # print ("now attempting to solve")
            result = planner.solve(problem)
        # print(result)
        # print(result.plan)

        self.assertTrue(result.status in up.engines.results.POSITIVE_OUTCOMES)
        self.assertEqual(len(result.plan._actions), 1)
        self.assertTrue(
            result.plan.__eq__(
                self.problems["interpreted_functions_in_conditions"].valid_plans[0]
            )
        )

    @skipIfEngineNotAvailable("sequential_plan_validator")
    @skipIfEngineNotAvailable("tamer")
    @skipIfEngineNotAvailable("enhsp")
    def test_interpreted_functions_in_preconditions_planner_always_impossible(self):
        problem = self.problems[
            "interpreted_functions_in_conditions_always_impossible"
        ].problem
        # print (problem)
        # print (problem.kind)
        self.assertTrue(problem.kind.has_interpreted_functions_in_conditions())
        self.assertFalse(problem.kind.has_simple_numeric_planning())

        # with OneshotPlanner(name="interpreted_functions_planning[tamer]") as planner:
        with OneshotPlanner(name="interpreted_functions_planning[enhsp]") as planner:
            planner._skip_checks = True  # -----------------------------
            # print ("now attempting to solve")
            result = planner.solve(problem)
        print(result)
        print(result.plan)

        self.assertFalse(result.status in up.engines.results.POSITIVE_OUTCOMES)

    @skipIfEngineNotAvailable("sequential_plan_validator")
    @skipIfEngineNotAvailable("tamer")
    @skipIfEngineNotAvailable("enhsp")
    def test_interpreted_functions_in_preconditions_planner_refine(self):
        testproblem = self.problems["interpreted_functions_in_conditions_to_refine"]
        problem = testproblem.problem
        # print (problem)
        # print (problem.kind)
        self.assertTrue(problem.kind.has_interpreted_functions_in_conditions())
        self.assertFalse(problem.kind.has_simple_numeric_planning())

        # with OneshotPlanner(name="interpreted_functions_planning[tamer]") as planner:
        with OneshotPlanner(name="interpreted_functions_planning[enhsp]") as planner:
            planner._skip_checks = True  # -----------------------------
            # print ("now attempting to solve")
            result = planner.solve(problem)
        print(result)
        print(result.plan)
        print("increase val -> action if in condition ")
        print("is a valid solution")
        self.assertEqual(len(result.plan.actions), 2)
        self.assertEqual(result.plan.actions[0].action, problem.actions[0])
        self.assertEqual(result.plan.actions[1].action, problem.actions[1])
        self.assertTrue(result.status in up.engines.results.POSITIVE_OUTCOMES)

    @skipIfEngineNotAvailable("sequential_plan_validator")
    @skipIfEngineNotAvailable("enhsp")
    def test_interpreted_functions_in_preconditions_planner_complex(self):
        testproblem = self.problems["IF_in_conditions_complex_1"]
        problem = testproblem.problem
        self.assertTrue(problem.kind.has_interpreted_functions_in_conditions())
        self.assertFalse(problem.kind.has_simple_numeric_planning())

        with OneshotPlanner(name="interpreted_functions_planning[enhsp]") as planner:
            planner._skip_checks = True  # -----------------------------
            result = planner.solve(problem)
        print(result)
        print("known valid plan:")
        print(testproblem.valid_plans[0])
        self.assertTrue(result.status in up.engines.results.POSITIVE_OUTCOMES)
        self.assertEqual(
            len(result.plan.actions), len(testproblem.valid_plans[0].actions)
        )
        i = 0
        while i < len(testproblem.valid_plans[0].actions):
            self.assertEqual(
                result.plan.actions[i].action,
                testproblem.valid_plans[0].actions[i].action,
            )

            i = i + 1

    @skipIfEngineNotAvailable("sequential_plan_validator")
    @skipIfEngineNotAvailable("tamer")
    @pytest.mark.skip(
        reason="work in progress - timed problems are not currently supported by the compiler"
    )
    # refine currently does not work with tamer
    def test_interpreted_functions_in_durations_planner(self):
        problem = self.problems["interpreted_functions_in_durations"].problem
        # print (problem)
        # print (problem.kind)
        pa = problem.action("gohome")
        self.assertTrue(problem.kind.has_interpreted_functions_in_durations())

        with OneshotPlanner(name="interpreted_functions_planning[tamer]") as planner:
            # print("now attempting to solve")
            planner.skipChecks = True
            result = planner.solve(problem)
            print(result)

        self.assertEqual(len(result.plan._actions), 1)
        self.assertEqual((result.plan.timed_actions[0])[1].action.name, pa.name)
        # the action objects are different, one contains an IF, the other has 1-1000000 as time instead
        # this test case has to be changed once support is implemented
        # ------------------------------------------------------------
        # ------------------------------------------------------------
        # ------------------------------------------------------------
