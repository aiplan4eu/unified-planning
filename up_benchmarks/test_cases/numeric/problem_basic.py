import unified_planning
from unified_planning.plans import SequentialPlan, ActionInstance
from unified_planning.shortcuts import *
from unified_planning.test import TestCase


def get_test_cases():
    res = {}

    x = Fluent("x", IntType())
    y = Fluent("y", IntType())
    a = InstantaneousAction("a")
    a.add_precondition(GE(y, 10))
    a.add_effect(x, Plus(x, 10))
    a.add_effect(y, Minus(y, 10))
    problem = Problem("basic_numeric")
    problem.add_fluent(x)
    problem.add_fluent(y)
    problem.add_action(a)
    problem.set_initial_value(x, 0)
    problem.set_initial_value(y, 10)
    problem.add_goal(GE(x, 10))

    # TODO add plans
    res[problem.name] = TestCase(problem=problem, solvable=True)

    return res
