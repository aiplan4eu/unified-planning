import os
import upf
from upf.shortcuts import *
from upf.exceptions import UPFUsageError
from upf.model.problem_kind import basic_classical_kind, classical_kind, full_numeric_kind, basic_temporal_kind
from upf.test import TestCase, skipIfNoPlanValidatorForProblemKind, skipIfNoOneshotPlannerForProblemKind
from upf.test.examples import get_example_problems
from upf.transformers import Grounder as TransformersGrounder


class TestGrounder(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_basic(self):
        problem = self.problems['basic'].problem

        gro = TransformersGrounder(problem)
        with self.assertRaises(UPFUsageError) as e:
            gro.get_rewrite_back_map()
        self.assertIn('The get_rewrite_back_map method must be called after the function get_rewritten_problem!', str(e.exception))

        grounded_problem = gro.get_rewritten_problem()
        grounded_problem_2 = gro.get_rewritten_problem()
        self.assertEqual(grounded_problem, grounded_problem_2)
        grounded_problem.name = problem.name
        self.assertEqual(grounded_problem, problem)

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(full_numeric_kind))
    @skipIfNoPlanValidatorForProblemKind(classical_kind.union(full_numeric_kind))
    def test_robot(self):
        problem = self.problems['robot'].problem

        gro = TransformersGrounder(problem)
        grounded_problem = gro.get_rewritten_problem()
        self.assertEqual(len(grounded_problem.actions()), 2)
        for a in grounded_problem.actions():
            self.assertEqual(len(a.parameters()), 0)

        with OneshotPlanner(problem_kind=grounded_problem.kind()) as planner:
            self.assertNotEqual(planner, None)
            grounded_plan = planner.solve(grounded_problem)
            plan = gro.rewrite_back_plan(grounded_plan)
            for ai in plan.actions():
                a = ai.action()
                self.assertEqual(a, problem.action(a.name))
            with PlanValidator(problem_kind=problem.kind()) as pv:
                self.assertTrue(pv.validate(problem, plan))

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(full_numeric_kind))
    @skipIfNoPlanValidatorForProblemKind(classical_kind.union(full_numeric_kind))
    def test_robot_locations_connected(self):
        problem = self.problems['robot_locations_connected'].problem

        gro = TransformersGrounder(problem)
        grounded_problem = gro.get_rewritten_problem()
        self.assertEqual(len(grounded_problem.actions()), 28)
        for a in grounded_problem.actions():
            self.assertEqual(len(a.parameters()), 0)
        for i, a in enumerate(problem.actions()):
            if i == 0:
                self.assertEqual(len(gro.get_transformed_actions(a)), 8)
            elif i == 1:
                self.assertEqual(len(gro.get_transformed_actions(a)), 20)
            else:
                self.assertTrue(False)

        with OneshotPlanner(problem_kind=grounded_problem.kind()) as planner:
            self.assertNotEqual(planner, None)
            grounded_plan = planner.solve(grounded_problem)
            plan = gro.rewrite_back_plan(grounded_plan)
            for ai in plan.actions():
                a = ai.action()
                self.assertEqual(a, problem.action(a.name))
            with PlanValidator(problem_kind=problem.kind()) as pv:
                self.assertTrue(pv.validate(problem, plan))


    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(basic_temporal_kind))
    @skipIfNoPlanValidatorForProblemKind(classical_kind.union(basic_temporal_kind))
    def test_matchcellar(self):
        problem = self.problems['matchcellar'].problem

        gro = TransformersGrounder(problem)
        grounded_problem = gro.get_rewritten_problem()
        self.assertEqual(len(grounded_problem.actions()), 6)
        for a in grounded_problem.actions():
            self.assertEqual(len(a.parameters()), 0)
        for a in problem.actions():
            self.assertEqual(len(gro.get_transformed_actions(a)), 3)

        with OneshotPlanner(problem_kind=grounded_problem.kind()) as planner:
            self.assertNotEqual(planner, None)
            grounded_plan = planner.solve(grounded_problem)
            plan = gro.rewrite_back_plan(grounded_plan)
            for _, ai, _ in plan.actions():
                a = ai.action()
                self.assertEqual(a, problem.action(a.name))
            with PlanValidator(problem_kind=problem.kind()) as pv:
                self.assertTrue(pv.validate(problem, plan))


    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(basic_temporal_kind))
    @skipIfNoPlanValidatorForProblemKind(classical_kind.union(basic_temporal_kind))
    def test_matchcellar_grounder_from_factory(self):
        problem = self.problems['matchcellar'].problem

        gro = TransformersGrounder(problem)
        grounded_problem_test = gro.get_rewritten_problem()
        with Grounder(name='grounder') as grounder:
            grounded_problem_try, rewrite_back_plan_function = grounder.ground(problem)
            self.assertEqual(grounded_problem_test, grounded_problem_try)
            with OneshotPlanner(problem_kind=grounded_problem_try.kind()) as planner:
                self.assertNotEqual(planner, None)
                grounded_plan = planner.solve(grounded_problem_try)
                plan = rewrite_back_plan_function(grounded_plan)
                for _, ai, _ in plan.actions():
                    a = ai.action()
                    self.assertEqual(a, problem.action(a.name))
                with PlanValidator(problem_kind=problem.kind()) as pv:
                    self.assertTrue(pv.validate(problem, plan))

    def test_timed_connected_locations(self):
        problem = self.problems['timed_connected_locations'].problem

        gro = TransformersGrounder(problem)
        grounded_problem = gro.get_rewritten_problem()
        self.assertEqual(len(grounded_problem.actions()), 20)
        for a in grounded_problem.actions():
            self.assertEqual(len(a.parameters()), 0)
        for a in problem.actions():
            self.assertEqual(len(gro.get_transformed_actions(a)), 20)

    def test_ad_hoc_1(self):
        problem = Problem('ad_hoc')
        Location = UserType('Location')
        visited = Fluent('at', BoolType(), [Location])
        l1 = Object('l1', Location)
        visit = InstantaneousAction('visit', l_to=Location)
        l_to = visit.parameter('l_to')
        visit.add_effect(visited(l_to), True)
        visit_l1 = InstantaneousAction('visit_l1')
        visit_l1.add_effect(visited(l1), True)
        problem.add_fluent(visited)
        problem.set_initial_value(visited(l1), True)
        problem.add_object(l1)
        problem.add_action(visit)
        problem.add_action(visit_l1)
        gro = TransformersGrounder(problem)
        grounded_problem = gro.get_rewritten_problem()
        self.assertEqual(len(grounded_problem.actions()), 2)
        for a in grounded_problem.actions():
            self.assertEqual(len(a.parameters()), 0)
        for a in problem.actions():
            self.assertEqual(len(gro.get_transformed_actions(a)), 1)

    def test_ad_hoc_2(self):
        problem = Problem('ad_hoc')
        gro = TransformersGrounder(problem)
        gro.get_rewritten_problem()
        with self.assertRaises(NotImplementedError):
            gro.rewrite_back_plan(problem)
