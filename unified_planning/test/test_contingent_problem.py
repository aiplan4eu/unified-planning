from fractions import Fraction

from unified_planning.model.contingent import ContingentProblem
from unified_planning.shortcuts import *
from unified_planning.test import unittest_TestCase


class TestContingentProblem(unittest_TestCase):
    def test_contingent_problem_equality_with_oneof(self):
        BlockType = UserType("block")
        clear = Fluent("clear", BoolType(), b=BlockType)
        b1 = Object("b1", BlockType)
        b2 = Object("b2", BlockType)

        def make():
            p = ContingentProblem("eq_test")
            p.add_fluent(clear, default_initial_value=False)
            p.add_object(b1)
            p.add_object(b2)
            p.add_oneof_initial_constraint([clear(b1), clear(b2)])
            p.add_goal(clear(b1))
            return p

        self.assertEqual(make(), make())

    def test_contingent_problem_equality_different_oneof(self):
        BlockType = UserType("block")
        clear = Fluent("clear", BoolType(), b=BlockType)
        on_table = Fluent("on_table", BoolType(), b=BlockType)
        b1 = Object("b1", BlockType)
        b2 = Object("b2", BlockType)

        p1 = ContingentProblem("eq_test")
        p1.add_fluent(clear, default_initial_value=False)
        p1.add_fluent(on_table, default_initial_value=False)
        p1.add_object(b1)
        p1.add_object(b2)
        p1.add_oneof_initial_constraint([clear(b1), clear(b2)])
        p1.add_goal(clear(b1))

        p2 = ContingentProblem("eq_test")
        p2.add_fluent(clear, default_initial_value=False)
        p2.add_fluent(on_table, default_initial_value=False)
        p2.add_object(b1)
        p2.add_object(b2)
        p2.add_oneof_initial_constraint([on_table(b1), on_table(b2)])
        p2.add_goal(clear(b1))

        self.assertNotEqual(p1, p2)

    def test_contingent_problem_equality_with_or(self):
        BlockType = UserType("block")
        clear = Fluent("clear", BoolType(), b=BlockType)
        b1 = Object("b1", BlockType)
        b2 = Object("b2", BlockType)

        def make():
            p = ContingentProblem("or_eq_test")
            p.add_fluent(clear, default_initial_value=False)
            p.add_object(b1)
            p.add_object(b2)
            p.add_or_initial_constraint([clear(b1), clear(b2)])
            p.add_goal(clear(b1))
            return p

        self.assertEqual(make(), make())

    def test_contingent_problem_equality_not_contingent(self):
        BlockType = UserType("block")
        clear = Fluent("clear", BoolType(), b=BlockType)
        b1 = Object("b1", BlockType)

        contingent = ContingentProblem("p")
        contingent.add_fluent(clear, default_initial_value=False)
        contingent.add_object(b1)
        contingent.add_goal(clear(b1))

        regular = Problem("p")
        regular.add_fluent(clear, default_initial_value=False)
        regular.add_object(b1)
        regular.add_goal(clear(b1))

        self.assertNotEqual(contingent, regular)

    def test_contingent_problem_hash_equals_for_equal_problems(self):
        BlockType = UserType("block")
        clear = Fluent("clear", BoolType(), b=BlockType)
        b1 = Object("b1", BlockType)
        b2 = Object("b2", BlockType)

        def make():
            p = ContingentProblem("hash_test")
            p.add_fluent(clear, default_initial_value=False)
            p.add_object(b1)
            p.add_object(b2)
            p.add_oneof_initial_constraint([clear(b1), clear(b2)])
            p.add_or_initial_constraint([clear(b1), clear(b2)])
            p.add_goal(clear(b1))
            return p

        p1, p2 = make(), make()
        self.assertEqual(p1, p2)
        self.assertEqual(hash(p1), hash(p2))

    def test_contingent_problem_clone_preserves_fields(self):
        BlockType = UserType("block")
        clear = Fluent("clear", BoolType(), b=BlockType)
        b1 = Object("b1", BlockType)
        b2 = Object("b2", BlockType)
        a = InstantaneousAction("a")
        a.add_effect(clear(b1), True)

        problem = ContingentProblem("p")
        problem.add_fluent(clear, default_initial_value=False)
        problem.add_object(b1)
        problem.add_object(b2)
        problem.add_action(a)

        # TimeModelMixin state
        problem.epsilon = Fraction(1, 100)
        problem.discrete_time = True
        problem.self_overlapping = True

        # natural transitions
        event = Event("ev")
        event.add_effect(clear(b1), True)
        problem.add_event(event)
        process = Process("proc")
        y = Fluent("y", RealType())
        problem.add_fluent(y, default_initial_value=0)
        process.add_increase_continuous_effect(y, 1)
        problem.add_process(process)

        # quality metric default
        problem.add_quality_metric(MinimizeActionCosts({a: 5}, default=99))

        # trajectory constraint
        problem.add_trajectory_constraint(Always(clear(b1)))

        # contingent-specific state
        problem.add_oneof_initial_constraint([clear(b1), clear(b2)])
        problem.add_or_initial_constraint([clear(b1), clear(b2)])
        problem.add_goal(clear(b1))

        clone = problem.clone()

        self.assertEqual(problem.epsilon, clone.epsilon)
        self.assertEqual(problem.discrete_time, clone.discrete_time)
        self.assertEqual(problem.self_overlapping, clone.self_overlapping)
        self.assertEqual(len(problem.events), len(clone.events))
        self.assertEqual(len(problem.processes), len(clone.processes))
        metric, clone_metric = problem.quality_metrics[0], clone.quality_metrics[0]
        assert isinstance(metric, MinimizeActionCosts) and isinstance(
            clone_metric, MinimizeActionCosts
        )
        self.assertEqual(metric.default, clone_metric.default)
        self.assertEqual(problem.trajectory_constraints, clone.trajectory_constraints)
        self.assertEqual(problem.hidden_fluents, clone.hidden_fluents)
        self.assertEqual(problem, clone)
        self.assertEqual(clone, problem)

    def test_contingent_problem_hash_equals_with_duplicate_constraints(self):
        BlockType = UserType("block")
        clear = Fluent("clear", BoolType(), b=BlockType)
        b1 = Object("b1", BlockType)
        b2 = Object("b2", BlockType)

        p1 = ContingentProblem("hash_dup_test")
        p1.add_fluent(clear, default_initial_value=False)
        p1.add_object(b1)
        p1.add_object(b2)
        p1.add_oneof_initial_constraint([clear(b1), clear(b2)])
        p1.add_goal(clear(b1))

        # p2 has a duplicate constraint that __eq__ collapses
        p2 = ContingentProblem("hash_dup_test")
        p2.add_fluent(clear, default_initial_value=False)
        p2.add_object(b1)
        p2.add_object(b2)
        p2.add_oneof_initial_constraint([clear(b1), clear(b2)])
        p2.add_oneof_initial_constraint([clear(b1), clear(b2)])  # duplicate
        p2.add_goal(clear(b1))

        self.assertEqual(p1, p2)
        self.assertEqual(hash(p1), hash(p2))
