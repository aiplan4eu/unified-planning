import unified_planning
from unified_planning.plans import SequentialPlan, ActionInstance
from unified_planning.shortcuts import *
from unified_planning.test import TestCase


def get_test_cases():
    res = {}

    problem = Problem("constant_increase_effect")

    x = problem.add_fluent("x", IntType(), default_initial_value=0)
    a = InstantaneousAction(f"act")
    a.add_increase_effect(x, 10)
    problem.add_goal(Equals(x, 10))

    # TODO add plans
    res[problem.name] = TestCase(problem=problem, solvable=True)

    problem = problem.clone()
    problem.name = "constant_increase_effect_2"

    problem.clear_goals()
    problem.add_goal(Equals(x, 30))

    # TODO add plans
    res[problem.name] = TestCase(problem=problem, solvable=True)

    problem = Problem("constant_decrease_effect")

    x = problem.add_fluent("x", IntType(), default_initial_value=10)
    a = InstantaneousAction(f"act")
    a.add_decrease_effect(x, 10)
    problem.add_goal(Equals(x, 0))

    # TODO add plans
    res[problem.name] = TestCase(problem=problem, solvable=True)

    problem = problem.clone()
    problem.name = "constant_decrease_effect_2"

    problem.set_initial_value(x, 30)

    # TODO add plans
    res[problem.name] = TestCase(problem=problem, solvable=True)

    return res
