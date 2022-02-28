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


import unified_planning

from unified_planning.shortcuts import *
from unified_planning.interop import convert_problem_from_tarski
from unified_planning.test import TestCase, skipIfNoOneshotPlannerForProblemKind
from unified_planning.test.examples import get_example_problems
from unified_planning.interop import convert_problem_to_tarski
from unified_planning.model.problem_kind import full_classical_kind, full_numeric_kind, hierarchical_kind
from unified_planning.plan import SequentialPlan, ActionInstance
from unified_planning.solvers import SequentialPlanValidator


class TestTarskiConverter(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_some_problems(self):
        problems_to_test= ['basic', 'basic_conditional', 'complex_conditional', 'basic_without_negative_preconditions',
                            'basic_nested_conjunctions', 'basic_exists', 'basic_forall', 'robot_loader', 'robot_loader_mod',
                            'robot_loader_adv', 'hierarchical_blocks_world', 'robot_real_constants', 'robot_int_battery',
                            'robot_locations_connected_without_battery', 'hierarchical_blocks_world_exists']
        for n in problems_to_test:
            problem = self.problems[n].problem
            #modify the problem to have the same representation
            modified_problem = problem.clone()
            for action in modified_problem.actions():
                if len(action.preconditions()) > 1:
                    new_precondition_as_and_of_preconditions = modified_problem.env.expression_manager.And(\
                                action.preconditions())
                    action._set_preconditions([new_precondition_as_and_of_preconditions])
            if len(modified_problem.goals()) > 1:
                new_goal_as_and_of_goals = modified_problem.env.expression_manager.And(\
                                modified_problem.goals())
                modified_problem.clear_goals()
                modified_problem.add_goal(new_goal_as_and_of_goals)
            tarski_problem = convert_problem_to_tarski(modified_problem)
            new_problem = convert_problem_from_tarski(modified_problem.env, tarski_problem)
            self.assertEqual(modified_problem, new_problem)

    def test_plan_charger_discharger(self):
        problem, plan = self.problems['charge_discharge']
        tarski_problem = convert_problem_to_tarski(problem)
        new_problem = convert_problem_from_tarski(problem.env, tarski_problem)
        new_plan = _switch_plan(plan, new_problem)
        pv = SequentialPlanValidator()
        self.assertTrue(pv.validate(new_problem, new_plan))

    def test_plan_robot(self):
        problem, plan = self.problems['robot']
        tarski_problem = convert_problem_to_tarski(problem)
        new_problem = convert_problem_from_tarski(problem.env, tarski_problem)
        new_plan = _switch_plan(plan, new_problem)
        pv = SequentialPlanValidator()
        self.assertTrue(pv.validate(new_problem, new_plan))

    def test_plan_robot_decrease(self):
        problem, plan = self.problems['robot_decrease']
        tarski_problem = convert_problem_to_tarski(problem)
        new_problem = convert_problem_from_tarski(problem.env, tarski_problem)
        new_plan = _switch_plan(plan, new_problem)
        pv = SequentialPlanValidator()
        self.assertTrue(pv.validate(new_problem, new_plan))

    def test_plan_robot_locations_connected(self):
        problem, plan = self.problems['robot_locations_connected']
        tarski_problem = convert_problem_to_tarski(problem)
        new_problem = convert_problem_from_tarski(problem.env, tarski_problem)
        new_plan = _switch_plan(plan, new_problem)
        pv = SequentialPlanValidator()
        self.assertTrue(pv.validate(new_problem, new_plan))

    def test_plan_robot_locations_visited(self):
        problem, plan = self.problems['robot_locations_visited']
        tarski_problem = convert_problem_to_tarski(problem)
        new_problem = convert_problem_from_tarski(problem.env, tarski_problem)
        new_plan = _switch_plan(plan, new_problem)
        pv = SequentialPlanValidator()
        self.assertTrue(pv.validate(new_problem, new_plan))
    
    @skipIfNoOneshotPlannerForProblemKind(hierarchical_kind)
    def test_plan_hierarchical_blocks_world_object_as_root(self):
        problem, plan = self.problems['hierarchical_blocks_world_object_as_root']
        tarski_problem = convert_problem_to_tarski(problem)
        new_problem = convert_problem_from_tarski(problem.env, tarski_problem)
        with OneshotPlanner(problem_kind=new_problem.kind()) as planner:
            new_plan = planner.solve(new_problem)
            self.assertEqual(str(plan), str(new_plan))

    @skipIfNoOneshotPlannerForProblemKind(hierarchical_kind)
    def test_plan_hierarchical_blocks_world_with_object(self):
        problem, plan = self.problems['hierarchical_blocks_world_with_object']
        tarski_problem = convert_problem_to_tarski(problem)
        new_problem = convert_problem_from_tarski(problem.env, tarski_problem)
        with OneshotPlanner(problem_kind=new_problem.kind()) as planner:
            new_plan = planner.solve(new_problem)
            self.assertEqual(str(plan), str(new_plan))

def _switch_plan(original_plan, new_problem):
    #This function switches a plan to be a plan of the given problem
    new_plan_action_instances = []
    for ai in original_plan.actions():
        new_plan_action_instances.append(ActionInstance(new_problem.action(ai.action().name), ai.actual_parameters()))
    new_plan = SequentialPlan(new_plan_action_instances)
    return new_plan
