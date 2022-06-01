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
from unified_planning.test import TestCase, skipIfNoOneshotPlannerForProblemKind, skipIfNoPlanValidatorForProblemKind, skipIfEngineNotAvailable
from unified_planning.test.examples import get_example_problems
from unified_planning.engines import CompilationKind
from unified_planning.model.problem_kind import basic_classical_kind, full_classical_kind, hierarchical_kind


class TestTarskiGrounder(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()


    @skipIfNoOneshotPlannerForProblemKind(full_classical_kind)
    @skipIfNoPlanValidatorForProblemKind(full_classical_kind)
    @skipIfEngineNotAvailable('tarski_grounder')
    def test_robot_loader(self):
        problem, plan = self.problems['robot_loader']
        with Compiler(name='tarski_grounder') as grounder:
            ground_result = grounder.compile(problem, CompilationKind.GROUNDER)
            grounded_problem, rewrite_back_plan_function = ground_result.problem, ground_result.map_back_action_instance
            for grounded_action in grounded_problem.actions:
                self.assertEqual(len(grounded_action.parameters), 0)
            with OneshotPlanner(problem_kind=grounded_problem.kind) as planner:
                self.assertNotEqual(planner, None)
                grounded_plan = planner.solve(grounded_problem).plan
                plan = grounded_plan.replace_action_instances(rewrite_back_plan_function)
                for ai in plan.actions:
                    a = ai.action
                    self.assertEqual(a, problem.action(a.name))
                with PlanValidator(problem_kind=problem.kind) as pv:
                    self.assertTrue(pv.validate(problem, plan))


    @skipIfNoOneshotPlannerForProblemKind(full_classical_kind)
    @skipIfNoPlanValidatorForProblemKind(full_classical_kind)
    @skipIfEngineNotAvailable('tarski_grounder')
    def test_robot_locations_connected_without_battery(self):
        problem, plan = self.problems['robot_locations_connected_without_battery']
        with Compiler(name='tarski_grounder') as grounder:
            ground_result = grounder.compile(problem, CompilationKind.GROUNDER)
            grounded_problem, rewrite_back_plan_function = ground_result.problem, ground_result.map_back_action_instance
            for grounded_action in grounded_problem.actions:
                self.assertEqual(len(grounded_action.parameters), 0)
            with OneshotPlanner(problem_kind=grounded_problem.kind) as planner:
                self.assertNotEqual(planner, None)
                grounded_plan = planner.solve(grounded_problem).plan
                plan = grounded_plan.replace_action_instances(rewrite_back_plan_function)
                for ai in plan.actions:
                    a = ai.action
                    self.assertEqual(a, problem.action(a.name))
                with PlanValidator(problem_kind=problem.kind) as pv:
                    self.assertTrue(pv.validate(problem, plan))


    @skipIfNoOneshotPlannerForProblemKind(basic_classical_kind.union(hierarchical_kind))
    @skipIfNoPlanValidatorForProblemKind(basic_classical_kind.union(hierarchical_kind))
    @skipIfEngineNotAvailable('tarski_grounder')
    def test_hierarchical_blocks_world(self):
        problem, plan = self.problems['hierarchical_blocks_world']
        with Compiler(name='tarski_grounder') as grounder:
            self.assertTrue(grounder.is_compiler())
            self.assertTrue(grounder.supports(problem.kind))
            self.assertTrue(grounder.supports_compilation(CompilationKind.GROUNDER))
            ground_result = grounder.compile(problem, CompilationKind.GROUNDER)
            grounded_problem, rewrite_back_plan_function = ground_result.problem, ground_result.map_back_action_instance
            for grounded_action in grounded_problem.actions:
                self.assertEqual(len(grounded_action.parameters), 0)
            with OneshotPlanner(problem_kind=grounded_problem.kind) as planner:
                self.assertNotEqual(planner, None)
                grounded_plan = planner.solve(grounded_problem).plan
                plan = grounded_plan.replace_action_instances(rewrite_back_plan_function)
                for ai in plan.actions:
                    a = ai.action
                    self.assertEqual(a, problem.action(a.name))
                with PlanValidator(problem_kind=problem.kind) as pv:
                    self.assertTrue(pv.validate(problem, plan))


    @skipIfNoOneshotPlannerForProblemKind(basic_classical_kind)
    @skipIfEngineNotAvailable('tarski_grounder')
    def test_tarski_grounder_mockup_problem(self):
        problem = Problem('mockup')
        Location = UserType('Location')
        at = Fluent('at', BoolType(), position=Location)
        at_l1 = Fluent('at_l1')
        at_l2 = Fluent('at_l2')
        l1 = Object('l1', Location)
        l2 = Object('l2', Location)
        move_to = InstantaneousAction('move_to', l_to=Location)
        l_to = move_to.parameter('l_to')
        move_to.add_effect(at(l_to), True)
        move_to.add_effect(at_l1, False, Equals(l_to, l2))
        move_to_l2 = InstantaneousAction('move_to_l2')
        move_to_l2.add_effect(at_l2, True)
        problem.add_fluent(at, default_initial_value=False)
        problem.add_fluent(at_l1, default_initial_value=True)
        problem.add_fluent(at_l2, default_initial_value=False)
        problem.add_object(l1)
        problem.add_object(l2)
        problem.add_action(move_to)
        problem.add_action(move_to_l2)
        problem.add_goal(at(l1))
        problem.add_goal(at(l2))
        problem.add_goal(at_l2)

        with Compiler(name='tarski_grounder') as grounder:
            ground_result = grounder.compile(problem, CompilationKind.GROUNDER)
            grounded_problem, rewrite_back_plan_function = ground_result.problem, ground_result.map_back_action_instance
            for grounded_action in grounded_problem.actions:
                self.assertEqual(len(grounded_action.parameters), 0)
            with OneshotPlanner(problem_kind=grounded_problem.kind) as planner:
                self.assertNotEqual(planner, None)
                grounded_plan = planner.solve(grounded_problem).plan
                plan = grounded_plan.replace_action_instances(rewrite_back_plan_function)
                for ai in plan.actions:
                    a = ai.action
                    self.assertEqual(a, problem.action(a.name))
                with PlanValidator(problem_kind=problem.kind) as pv:
                    self.assertTrue(pv.validate(problem, plan))
