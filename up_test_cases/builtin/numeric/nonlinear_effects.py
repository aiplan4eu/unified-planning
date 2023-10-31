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

    valid_plans = [SequentialPlan([a()])]
    invalid_plans = [
        SequentialPlan([a() for _ in range(i)]) for i in range(5) if i != 1
    ]
    res[problem.name] = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=valid_plans,
        invalid_plans=invalid_plans,
    )

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
    problem.add_goal(Equals(x, Fraction(625, 10000)))

    valid_plans = [SequentialPlan([a(), a()])]
    invalid_plans = [
        SequentialPlan([a() for _ in range(i)]) for i in range(5) if i != 2
    ]
    res[problem.name] = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=valid_plans,
        invalid_plans=invalid_plans,
    )

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

    valid_plans = [SequentialPlan([a(), a(), a(), a()])]
    invalid_plans = [
        SequentialPlan([a() for _ in range(i)]) for i in range(7) if i != 4
    ]
    res[problem.name] = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=valid_plans,
        invalid_plans=invalid_plans,
    )

    return res
