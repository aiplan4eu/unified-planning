import unified_planning
from unified_planning.plans import SequentialPlan, ActionInstance
from unified_planning.shortcuts import *
from unified_planning.test import TestCase


def get_test_cases():
    res = {}

    problem = Problem("simple_non_linear_GT_equality_conditions")
    x = problem.add_fluent("x", IntType())
    y = problem.add_fluent("y", IntType())
    problem.set_initial_value(x, 3)
    problem.set_initial_value(y, 2)
    problem.add_goal(Equals(Times(x, y), 24))

    a1 = InstantaneousAction("a1")
    a1.add_precondition(GT(Plus(Times(x, x), y), 10))
    a1.add_effect(x, 6)
    a1.add_effect(y, 4)

    problem.add_action(a1)

    valid_plans = [SequentialPlan([a1() for _ in range(i)]) for i in range(1, 4)]
    invalid_plans = [SequentialPlan([])]
    res[problem.name] = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=valid_plans,
        invalid_plans=invalid_plans,
    )

    problem = Problem("simple_non_linear_LE_Negative_conditions")
    problem.add_fluent(x)
    problem.add_fluent(y)
    problem.set_initial_value(x, 3)
    problem.set_initial_value(y, 2)
    problem.add_goal(Not(Equals(Times(x, y), 24)))
    problem.add_goal(Not(Equals(Times(x, y), 6)))

    a1 = InstantaneousAction("a1")
    a1.add_precondition(LE(Plus(Times(x, x), y), 40))
    a1.add_effect(x, Plus(x, 3))
    a1.add_effect(y, Plus(y, 2))

    problem.add_action(a1)

    valid_plans = [SequentialPlan([a1(), a1()])]
    invalid_plans = [
        SequentialPlan([a1() for _ in range(i)]) for i in range(7) if i != 2
    ]
    res[problem.name] = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=valid_plans,
        invalid_plans=invalid_plans,
    )

    return res
