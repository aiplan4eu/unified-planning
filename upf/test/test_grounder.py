import os
import upf
from upf.shortcuts import *
from upf.model.problem_kind import basic_classical_kind, classical_kind, full_numeric_kind, basic_temporal_kind
from upf.test import TestCase, skipIfNoPlanValidatorForProblemKind, skipIfNoOneshotPlannerForProblemKind
from upf.test.examples import get_example_problems
from upf.transformers import Grounder


class TestDisjunctiveConditionsRemover(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfNoOneshotPlannerForProblemKind(basic_classical_kind)
    @skipIfNoPlanValidatorForProblemKind(basic_classical_kind)
    def test_basic(self):
        problem = self.problems['basic'].problem

        gro = Grounder(problem)
        grounded_problem = gro.get_rewritten_problem()
        grounded_problem_2 = gro.get_rewritten_problem()
        self.assertEqual(grounded_problem, grounded_problem_2)
        grounded_problem.name = problem.name
        self.assertEqual(grounded_problem, problem)

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(full_numeric_kind))
    @skipIfNoPlanValidatorForProblemKind(classical_kind.union(full_numeric_kind))
    def test_robot(self):
        problem = self.problems['robot'].problem

        gro = Grounder(problem)
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

        gro = Grounder(problem)
        grounded_problem = gro.get_rewritten_problem()
        self.assertEqual(len(grounded_problem.actions()), 40)
        for a in grounded_problem.actions():
            self.assertEqual(len(a.parameters()), 0)
        for a in problem.actions():
            self.assertEqual(len(gro.get_transformed_actions(a)), 20)

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

        gro = Grounder(problem)
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
            print(plan)
            for _, ai, _ in plan.actions():
                a = ai.action()
                self.assertEqual(a, problem.action(a.name))
            with PlanValidator(problem_kind=problem.kind()) as pv:
                self.assertTrue(pv.validate(problem, plan))
