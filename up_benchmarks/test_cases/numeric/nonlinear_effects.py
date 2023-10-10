import unified_planning
from unified_planning.plans import SequentialPlan, ActionInstance
from unified_planning.shortcuts import *
from unified_planning.test import TestCase


def get_test_cases():
    res = {}

    x = Fluent("x", IntType())
    a = InstantaneousAction("action1")
    a.add_increase_effect(x, Times(x, Times(x, x)))
    problem = Problem("nonlinear_increase_effects")
    problem.add_fluent(x)
    problem.add_action(a)
    problem.set_initial_value(x, 2)
    problem.add_goal(Equals(x, 10))

    # TODO add plans
    res[problem.name] = TestCase(problem=problem, solvable=True)

    x = Fluent("x", RealType())
    y = Fluent("y", RealType())
    a = InstantaneousAction("action1")
    a.add_effect(x, Div(x, Times(y, y)))
    problem = Problem("nonlinear_assign_effects")
    problem.add_fluent(x)
    problem.add_fluent(y)
    problem.add_action(a)
    problem.set_initial_value(x, 1)
    problem.set_initial_value(y, 2)
    problem.add_goal(Equals(x, 0.0625))

    # TODO add plans
    res[problem.name] = TestCase(problem=problem, solvable=True)

    a = InstantaneousAction("action1")
    a.add_effect(x, Plus(x, 1), Equals(Times(x, y), Times(x, x)))
    a.add_effect(y, Plus(y, 1), Equals(Times(x, y), Times(x, x)))
    problem = Problem("nonlinear_conditional_effects")
    problem.add_fluent(x)
    problem.add_fluent(y)
    problem.add_action(a)
    problem.set_initial_value(x, 1)
    problem.set_initial_value(y, 1)
    problem.add_goal(Equals(Times(x, y), 25))

    # TODO add plans (5 times a)
    res[problem.name] = TestCase(problem=problem, solvable=True)

    return res
