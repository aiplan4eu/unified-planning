import unified_planning
from unified_planning.plans import SequentialPlan, ActionInstance
from unified_planning.shortcuts import *
from unified_planning.test import TestCase


def get_test_cases():
    res = {}

    problem = Problem("constant_increase_effect")

    x = problem.add_fluent("x", IntType(), default_initial_value=0)
    a = InstantaneousAction("act")
    a.add_increase_effect(x, 10)
    problem.add_action(a)
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

    problem = problem.clone()
    problem.name = "constant_increase_effect_2"

    problem.clear_goals()
    problem.add_goal(Equals(x, 30))

    valid_plans = [SequentialPlan([a(), a(), a()])]
    invalid_plans = [
        SequentialPlan([a() for _ in range(i)]) for i in range(6) if i != 3
    ]
    res[problem.name] = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=valid_plans,
        invalid_plans=invalid_plans,
    )

    problem = Problem("constant_decrease_effect")

    x = problem.add_fluent("x", IntType(), default_initial_value=10)
    a = InstantaneousAction("act")
    a.add_decrease_effect(x, 10)
    problem.add_action(a)
    problem.add_goal(Equals(x, 0))

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

    problem = problem.clone()
    problem.name = "constant_decrease_effect_2"

    problem.set_initial_value(x, 30)

    valid_plans = [SequentialPlan([a(), a(), a()])]
    invalid_plans = [
        SequentialPlan([a() for _ in range(i)]) for i in range(6) if i != 3
    ]
    res[problem.name] = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=valid_plans,
        invalid_plans=invalid_plans,
    )

    return res
