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

import unified_planning
from unified_planning.shortcuts import *
from unified_planning.model.problem_kind import (
    basic_temporal_kind,
    temporal_kind,
    classical_kind,
)
from unified_planning.plans import TimeTriggeredPlan
from unified_planning.test import TestCase, main, skipIfNoOneshotPlannerForProblemKind
from unified_planning.test.examples import get_example_problems


class TestTemporalPlanner(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfNoOneshotPlannerForProblemKind(basic_temporal_kind.union(classical_kind))
    def test_matchcellar(self):
        problem = self.problems["matchcellar"].problem

        with OneshotPlanner(problem_kind=problem.kind) as planner:
            self.assertNotEqual(planner, None)
            plan = planner.solve(problem).plan
            self.assertEqual(len(plan.timed_actions), 6)

    @skipIfNoOneshotPlannerForProblemKind(temporal_kind)
    def test_static_fluents_duration(self):
        problem = self.problems["robot_with_static_fluents_duration"].problem

        with OneshotPlanner(problem_kind=problem.kind) as planner:
            self.assertNotEqual(planner, None)
            plan = planner.solve(problem).plan
            self.assertEqual(len(plan.timed_actions), 4)

    @skipIfNoOneshotPlannerForProblemKind(basic_temporal_kind.union(classical_kind))
    def test_epsilon(self):
        # Test the matchcellar problem with different increasing required epsilons,
        # assuming that the planner will never return a plan after the epsilon becomes
        # too big to handle

        # List that can be modified with the Epsilons to test.
        epsilons_str = ["10", "1", "0.1", "0.01", "0.001", "0.0001"]

        problem = self.problems["matchcellar"].problem
        problem = problem.clone()

        epsilons = tuple(map(Fraction, epsilons_str))
        epsilon_too_high = False
        with OneshotPlanner(problem_kind=problem.kind) as planner:
            self.assertNotEqual(planner, None)
            for eps in sorted(epsilons):
                problem.epsilon = eps
                plan = planner.solve(problem).plan
                if plan is not None:
                    self.assertFalse(epsilon_too_high)
                    assert isinstance(plan, TimeTriggeredPlan)
                    problem_epsilon = problem.epsilon
                    plan_epsilon = plan.extract_epsilon(problem)
                    assert plan_epsilon is not None
                    self.assertGreaterEqual(plan_epsilon, problem_epsilon)
                else:
                    epsilon_too_high = True
