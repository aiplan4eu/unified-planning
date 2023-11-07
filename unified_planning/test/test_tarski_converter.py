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
from unified_planning.test import (
    unittest_TestCase,
    skipIfNoOneshotPlannerForProblemKind,
    skipIfEngineNotAvailable,
)
from unified_planning.test.examples import get_example_problems
from unified_planning.model.problem_kind import (
    full_classical_kind,
    hierarchical_kind,
)
from unified_planning.plans import SequentialPlan, ActionInstance
from unified_planning.engines import SequentialPlanValidator


class TestTarskiConverter(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfEngineNotAvailable("tarski_grounder")
    def test_some_problems(self):
        problems_to_test = [
            "basic",
            "basic_conditional",
            "complex_conditional",
            "basic_without_negative_preconditions",
            "basic_nested_conjunctions",
            "basic_exists",
            "basic_forall",
            "robot_loader",
            "robot_loader_mod",
            "robot_loader_adv",
            "hierarchical_blocks_world",
            "robot_real_constants",
            "robot_int_battery",
            "robot_locations_connected_without_battery",
            "hierarchical_blocks_world_exists",
            "charge_discharge",
            "robot",
            "robot_decrease",
            "robot_locations_connected",
            "robot_locations_visited",
        ]
        for n in problems_to_test:
            example = self.problems[n]
            problem, plan = example.problem, example.valid_plans[0]
            tarski_problem = up.interop.convert_problem_to_tarski(problem)
            new_problem = up.interop.convert_problem_from_tarski(
                problem.environment, tarski_problem
            )
            new_plan = _switch_plan(plan, new_problem)
            pv = SequentialPlanValidator()
            self.assertTrue(pv.validate(new_problem, new_plan))

    @skipIfEngineNotAvailable("tarski_grounder")
    @skipIfNoOneshotPlannerForProblemKind(hierarchical_kind)
    def test_plan_hierarchical_blocks_world_object_as_root(self):
        example = self.problems["hierarchical_blocks_world_object_as_root"]
        problem, plan = example.problem, example.valid_plans[0]
        tarski_problem = up.interop.convert_problem_to_tarski(problem)
        new_problem = up.interop.convert_problem_from_tarski(
            problem.environment, tarski_problem
        )
        with OneshotPlanner(problem_kind=new_problem.kind) as planner:
            new_plan = planner.solve(new_problem).plan
            self.assertIsNotNone(new_plan)
            self.assertEqual(str(plan), str(new_plan))

    @skipIfEngineNotAvailable("tarski_grounder")
    @skipIfNoOneshotPlannerForProblemKind(hierarchical_kind)
    def test_plan_hierarchical_blocks_world_with_object(self):
        example = self.problems["hierarchical_blocks_world_with_object"]
        problem, plan = example.problem, example.valid_plans[0]
        tarski_problem = up.interop.convert_problem_to_tarski(problem)
        new_problem = up.interop.convert_problem_from_tarski(
            problem.environment, tarski_problem
        )
        with OneshotPlanner(problem_kind=new_problem.kind) as planner:
            new_plan = planner.solve(new_problem).plan
            self.assertIsNotNone(new_plan)
            self.assertEqual(str(plan), str(new_plan))


def _switch_plan(original_plan, new_problem):
    # This function switches a plan to be a plan of the given problem
    new_plan_action_instances = []
    for ai in original_plan.actions:
        new_plan_action_instances.append(
            ActionInstance(new_problem.action(ai.action.name), ai.actual_parameters)
        )
    new_plan = SequentialPlan(new_plan_action_instances)
    return new_plan
