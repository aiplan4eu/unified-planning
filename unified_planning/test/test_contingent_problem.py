from unified_planning.test import unittest_TestCase

from unified_planning.model.contingent import ContingentProblem
from unified_planning.shortcuts import *


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
