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
#

import unified_planning
from unified_planning.shortcuts import *
from unified_planning.model.problem_kind import (
    basic_classical_kind,
    classical_kind,
    full_numeric_kind,
    basic_temporal_kind,
    hierarchical_kind,
)
from unified_planning.test import (
    TestCase,
    skipIfNoPlanValidatorForProblemKind,
    skipIfNoOneshotPlannerForProblemKind,
    skipIfEngineNotAvailable,
)
from unified_planning.test.examples import get_example_problems
from unified_planning.engines import CompilationKind
from unified_planning.engines.compilers import Grounder


class TestGrounder(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_basic(self):
        problem = self.problems["basic"].problem

        gro = Grounder()

        res = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem = res.problem
        assert isinstance(grounded_problem, Problem)
        res_2 = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem_2 = res_2.problem

        self.assertEqual(grounded_problem, grounded_problem_2)
        grounded_problem.name = problem.name
        self.assertEqual(grounded_problem, problem)

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(full_numeric_kind))
    @skipIfNoPlanValidatorForProblemKind(classical_kind.union(full_numeric_kind))
    def test_robot(self):
        problem = self.problems["robot"].problem

        gro = Grounder()
        res = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem = res.problem
        assert isinstance(grounded_problem, Problem)
        self.assertEqual(len(grounded_problem.actions), 2)
        for a in grounded_problem.actions:
            self.assertEqual(len(a.parameters), 0)

        with OneshotPlanner(problem_kind=grounded_problem.kind) as planner:
            self.assertNotEqual(planner, None)
            grounded_plan = planner.solve(grounded_problem).plan
            plan = grounded_plan.replace_action_instances(res.map_back_action_instance)
            for ai in plan.actions:
                a = ai.action
                self.assertEqual(a, problem.action(a.name))
            with PlanValidator(problem_kind=problem.kind, plan_kind=plan.kind) as pv:
                self.assertTrue(pv.validate(problem, plan))

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(full_numeric_kind))
    @skipIfNoPlanValidatorForProblemKind(classical_kind.union(full_numeric_kind))
    def test_robot_locations_connected(self):
        problem = self.problems["robot_locations_connected"].problem

        gro = Grounder()
        res = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem = res.problem
        assert isinstance(grounded_problem, Problem)
        self.assertEqual(len(grounded_problem.actions), 28)
        for a in grounded_problem.actions:
            self.assertEqual(len(a.parameters), 0)

        with OneshotPlanner(problem_kind=grounded_problem.kind) as planner:
            self.assertNotEqual(planner, None)
            grounded_plan = planner.solve(grounded_problem).plan
            plan = grounded_plan.replace_action_instances(res.map_back_action_instance)
            for ai in plan.actions:
                a = ai.action
                self.assertEqual(a, problem.action(a.name))
            with PlanValidator(problem_kind=problem.kind, plan_kind=plan.kind) as pv:
                self.assertTrue(pv.validate(problem, plan))

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(full_numeric_kind))
    @skipIfNoPlanValidatorForProblemKind(classical_kind.union(full_numeric_kind))
    def test_robot_locations_connected_from_factory(self):
        problem = self.problems["robot_locations_connected"].problem

        with Compiler(name="up_grounder") as grounder:
            self.assertTrue(grounder.supports(problem.kind))
            res = grounder.compile(problem, CompilationKind.GROUNDING)
            grounded_problem = res.problem
            assert isinstance(grounded_problem, Problem)
            self.assertEqual(len(grounded_problem.actions), 28)
            for a in grounded_problem.actions:
                self.assertEqual(len(a.parameters), 0)

            with OneshotPlanner(problem_kind=grounded_problem.kind) as planner:
                self.assertNotEqual(planner, None)
                grounded_plan = planner.solve(grounded_problem).plan
                plan = grounded_plan.replace_action_instances(
                    res.map_back_action_instance
                )
                for ai in plan.actions:
                    a = ai.action
                    self.assertEqual(a, problem.action(a.name))
                with PlanValidator(
                    problem_kind=problem.kind, plan_kind=plan.kind
                ) as pv:
                    self.assertTrue(pv.validate(problem, plan))

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(full_numeric_kind))
    @skipIfNoPlanValidatorForProblemKind(classical_kind.union(full_numeric_kind))
    def test_robot_locations_connected_from_factory_with_problem_kind(self):
        problem = self.problems["robot_locations_connected"].problem
        kind = problem.kind

        with Compiler(
            problem_kind=kind, compilation_kind=CompilationKind.GROUNDING
        ) as embedded_grounder:
            self.assertTrue(embedded_grounder.supports(kind))
            ground_result = embedded_grounder.compile(
                problem, CompilationKind.GROUNDING
            )
            grounded_problem, rewrite_plan_funct = (
                ground_result.problem,
                ground_result.map_back_action_instance,
            )
            self.assertEqual(len(grounded_problem.actions), 28)
            for a in grounded_problem.actions:
                self.assertEqual(len(a.parameters), 0)

            with OneshotPlanner(problem_kind=grounded_problem.kind) as planner:
                self.assertNotEqual(planner, None)
                grounded_plan = planner.solve(grounded_problem).plan
                plan = grounded_plan.replace_action_instances(rewrite_plan_funct)
                for ai in plan.actions:
                    a = ai.action
                    self.assertEqual(a, problem.action(a.name))
                with PlanValidator(
                    problem_kind=problem.kind, plan_kind=plan.kind
                ) as pv:
                    self.assertTrue(pv.validate(problem, plan))

    @skipIfNoOneshotPlannerForProblemKind(hierarchical_kind)
    @skipIfNoPlanValidatorForProblemKind(hierarchical_kind)
    def test_hierarchical_blocks_world(self):
        problem = self.problems["hierarchical_blocks_world"].problem

        gro = Grounder()
        ground_result = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem = ground_result.problem
        assert isinstance(grounded_problem, Problem)
        self.assertEqual(len(grounded_problem.actions), 90)
        for a in grounded_problem.actions:
            self.assertEqual(len(a.parameters), 0)

        with OneshotPlanner(problem_kind=grounded_problem.kind) as planner:
            self.assertNotEqual(planner, None)
            grounded_plan = planner.solve(grounded_problem).plan
            plan = grounded_plan.replace_action_instances(
                ground_result.map_back_action_instance
            )
            for ai in plan.actions:
                a = ai.action
                self.assertEqual(a, problem.action(a.name))
            with PlanValidator(problem_kind=problem.kind, plan_kind=plan.kind) as pv:
                self.assertTrue(pv.validate(problem, plan))

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(basic_temporal_kind))
    @skipIfNoPlanValidatorForProblemKind(classical_kind.union(basic_temporal_kind))
    def test_matchcellar(self):
        problem = self.problems["matchcellar"].problem

        gro = Grounder()
        ground_result = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem = ground_result.problem
        assert isinstance(grounded_problem, Problem)
        self.assertEqual(len(grounded_problem.actions), 6)
        for a in grounded_problem.actions:
            self.assertEqual(len(a.parameters), 0)

        with OneshotPlanner(problem_kind=grounded_problem.kind) as planner:
            self.assertNotEqual(planner, None)
            grounded_plan = planner.solve(grounded_problem).plan
            plan = grounded_plan.replace_action_instances(
                ground_result.map_back_action_instance
            )
            for _, ai, _ in plan.timed_actions:
                a = ai.action
                self.assertEqual(a, problem.action(a.name))
            with PlanValidator(problem_kind=problem.kind, plan_kind=plan.kind) as pv:
                self.assertTrue(pv.validate(problem, plan))

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(basic_temporal_kind))
    @skipIfNoPlanValidatorForProblemKind(classical_kind.union(basic_temporal_kind))
    def test_matchcellar_grounder_from_factory(self):
        problem = self.problems["matchcellar"].problem

        gro = Grounder()
        ground_result = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem_test = ground_result.problem
        with Compiler(name="up_grounder") as grounder:
            self.assertTrue(grounder.supports(problem.kind))
            ground_result = grounder.compile(problem, CompilationKind.GROUNDING)
            grounded_problem_try, rewrite_back_plan_function = (
                ground_result.problem,
                ground_result.map_back_action_instance,
            )
            assert isinstance(grounded_problem_try, Problem)
            self.assertEqual(grounded_problem_test, grounded_problem_try)
            with OneshotPlanner(problem_kind=grounded_problem_try.kind) as planner:
                self.assertNotEqual(planner, None)
                grounded_plan = planner.solve(grounded_problem_try).plan
                plan = grounded_plan.replace_action_instances(
                    rewrite_back_plan_function
                )
                for _, ai, _ in plan.timed_actions:
                    a = ai.action
                    self.assertEqual(a, problem.action(a.name))
                with PlanValidator(
                    problem_kind=problem.kind, plan_kind=plan.kind
                ) as pv:
                    self.assertTrue(pv.validate(problem, plan))

    def test_timed_connected_locations(self):
        problem = self.problems["timed_connected_locations"].problem

        gro = Grounder()
        ground_result = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem = ground_result.problem
        assert isinstance(grounded_problem, Problem)
        self.assertEqual(len(grounded_problem.actions), 20)
        for a in grounded_problem.actions:
            self.assertEqual(len(a.parameters), 0)

    def test_ad_hoc_1(self):
        problem = Problem("ad_hoc")
        Location = UserType("Location")
        visited = Fluent("at", BoolType(), position=Location)
        l1 = Object("l1", Location)
        visit = InstantaneousAction("visit", l_to=Location)
        l_to = visit.parameter("l_to")
        visit.add_effect(visited(l_to), True)
        visit_l1 = InstantaneousAction("visit_l1")
        visit_l1.add_effect(visited(l1), True)
        problem.add_fluent(visited)
        problem.set_initial_value(visited(l1), True)
        problem.add_object(l1)
        problem.add_action(visit)
        problem.add_action(visit_l1)
        gro = Grounder()
        ground_result = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem = ground_result.problem
        assert isinstance(grounded_problem, Problem)
        self.assertEqual(len(grounded_problem.actions), 2)
        for a in grounded_problem.actions:
            self.assertEqual(len(a.parameters), 0)

    @skipIfEngineNotAvailable("pyperplan")
    def test_pyperplan_grounder(self):
        problem = self.problems["robot_no_negative_preconditions"].problem
        for action in problem.actions:
            self.assertTrue(len(action.parameters) > 0)
        with Compiler(name="pyperplan") as grounder:
            ground_result = grounder.compile(problem, CompilationKind.GROUNDING)
            grounded_problem, rewrite_back_plan_function = (
                ground_result.problem,
                ground_result.map_back_action_instance,
            )
            for grounded_action in grounded_problem.actions:
                self.assertEqual(len(grounded_action.parameters), 0)
            with OneshotPlanner(problem_kind=grounded_problem.kind) as planner:
                self.assertNotEqual(planner, None)
                grounded_plan = planner.solve(grounded_problem).plan
                plan = grounded_plan.replace_action_instances(
                    rewrite_back_plan_function
                )
                for ai in plan.actions:
                    a = ai.action
                    self.assertEqual(a, problem.action(a.name))
                with PlanValidator(
                    problem_kind=problem.kind, plan_kind=plan.kind
                ) as pv:
                    self.assertTrue(pv.validate(problem, plan))

    @skipIfEngineNotAvailable("pyperplan")
    def test_pyperplan_grounder_mockup_problem(self):
        problem = Problem("mockup")
        Location = UserType("Location")
        at = Fluent("at", BoolType(), position=Location)
        at_l2 = Fluent("at_l2")
        l1 = Object("l1", Location)
        l2 = Object("l2", Location)
        move_to = InstantaneousAction("move_to", l_to=Location)
        l_to = move_to.parameter("l_to")
        move_to.add_effect(at(l_to), True)
        move_to_l2 = InstantaneousAction("move_to_l2")
        move_to_l2.add_effect(at_l2, True)
        problem.add_fluent(at, default_initial_value=False)
        problem.add_fluent(at_l2, default_initial_value=False)
        problem.add_object(l1)
        problem.add_object(l2)
        problem.add_action(move_to)
        problem.add_action(move_to_l2)
        problem.add_goal(at(l1))
        problem.add_goal(at(l2))
        problem.add_goal(at_l2)

        with Compiler(name="pyperplan") as grounder:
            ground_result = grounder.compile(problem, CompilationKind.GROUNDING)
            grounded_problem, rewrite_back_plan_function = (
                ground_result.problem,
                ground_result.map_back_action_instance,
            )
            for grounded_action in grounded_problem.actions:
                self.assertEqual(len(grounded_action.parameters), 0)
            with OneshotPlanner(problem_kind=grounded_problem.kind) as planner:
                self.assertNotEqual(planner, None)
                grounded_plan = planner.solve(grounded_problem).plan
                plan = grounded_plan.replace_action_instances(
                    rewrite_back_plan_function
                )
                for ai in plan.actions:
                    a = ai.action
                    self.assertEqual(a, problem.action(a.name))
                with PlanValidator(
                    problem_kind=problem.kind, plan_kind=plan.kind
                ) as pv:
                    self.assertTrue(pv.validate(problem, plan))
