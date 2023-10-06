import unified_planning
from unified_planning.plans import SequentialPlan, ActionInstance
from unified_planning.shortcuts import *
from unified_planning.test import TestCase


def get_test_cases():
    res = {}

    x = Fluent("x", IntType())
    a = InstantaneousAction("action1")
    a.add_effect(condition=Equals(x, 0), fluent=x, value=Plus(x, 11))
    problem = Problem("linear_conditional_effects")
    problem.add_fluent(x)
    problem.add_action(a)
    problem.set_initial_value(x, 0)
    problem.add_goal(GT(x, 10))

    res[problem.name] = TestCase(problem=problem, solvable=True)

    return res
