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


import upf

from upf.shortcuts import *
from upf.solvers.upf_tarski_converter import TarskiConverter
from upf.test import TestCase
from upf.test.examples import get_example_problems
from upf.interop.tarski import convert_tarski_problem
from upf.model.problem_kind import full_classical_kind, full_numeric_kind
from upf.plan import SequentialPlan, ActionInstance
from upf.solvers import SequentialPlanValidator


class TestGrounder(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()
        self.tc = TarskiConverter()

    def test_all_equals(self):
        problems_to_avoid = ['charger_discharger', 'robot', 'robot_decrease', 'robot_locations_connected',
                                'robot_locations_visited']
        #the charger_discharger problem has Implies, which tarski represents with Or and Not
        #the robot problem has Integers, which are casted to reals by tarski
        #the robot_decrease, connected and visited problems have decrese, which is represented as an assignment
        for p in self.problems.values():
            problem = p.problem
            problem_kind = problem.kind()
            if problem_kind <= full_classical_kind.union(full_numeric_kind):
                if problem.name in problems_to_avoid:
                    continue
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
                tarski_problem = self.tc.upf_to_tarski(modified_problem)
                new_problem = convert_tarski_problem(modified_problem.env, tarski_problem)
                self.assertEqual(modified_problem, new_problem)

    def test_plan_charger_discharger(self):
        problem, plan = self.problems['charge_discharge']
        tarski_problem = self.tc.upf_to_tarski(problem)
        new_problem = convert_tarski_problem(problem.env, tarski_problem)
        new_plan = _switch_plan(plan, new_problem)
        pv = SequentialPlanValidator()
        self.assertTrue(pv.validate(new_problem, new_plan))

    def test_plan_robot(self):
        problem, plan = self.problems['robot']
        tarski_problem = self.tc.upf_to_tarski(problem)
        new_problem = convert_tarski_problem(problem.env, tarski_problem)
        new_plan = _switch_plan(plan, new_problem)
        pv = SequentialPlanValidator()
        self.assertTrue(pv.validate(new_problem, new_plan))

    def test_plan_robot_decrease(self):
        problem, plan = self.problems['robot_decrease']
        tarski_problem = self.tc.upf_to_tarski(problem)
        new_problem = convert_tarski_problem(problem.env, tarski_problem)
        new_plan = _switch_plan(plan, new_problem)
        pv = SequentialPlanValidator()
        self.assertTrue(pv.validate(new_problem, new_plan))

    def test_plan_robot_locations_connected(self):
        problem, plan = self.problems['robot_locations_connected']
        tarski_problem = self.tc.upf_to_tarski(problem)
        new_problem = convert_tarski_problem(problem.env, tarski_problem)
        new_plan = _switch_plan(plan, new_problem)
        pv = SequentialPlanValidator()
        self.assertTrue(pv.validate(new_problem, new_plan))

    def test_plan_robot_locations_visited(self):
        problem, plan = self.problems['robot_locations_visited']
        tarski_problem = self.tc.upf_to_tarski(problem)
        new_problem = convert_tarski_problem(problem.env, tarski_problem)
        new_plan = _switch_plan(plan, new_problem)
        pv = SequentialPlanValidator()
        self.assertTrue(pv.validate(new_problem, new_plan))

def _switch_plan(original_plan, new_problem):
    #This function switches a plan to be a plan of the given problem
    new_plan_action_instances = []
    for ai in original_plan.actions():
        new_plan_action_instances.append(ActionInstance(new_problem.action(ai.action().name), ai.actual_parameters()))
    new_plan = SequentialPlan(new_plan_action_instances)
    return new_plan
