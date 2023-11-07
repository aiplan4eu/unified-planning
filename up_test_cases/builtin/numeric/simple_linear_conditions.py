import unified_planning
from unified_planning.plans import SequentialPlan, ActionInstance
from unified_planning.shortcuts import *
from unified_planning.test import TestCase


def get_test_cases():
    res = {}

    problem = Problem("GT_linear_conditions")
    x = problem.add_fluent("x", RealType())
    problem.set_initial_value(x, Fraction(51, 10))
    problem.add_goal(GT(x, 10))

    a1 = InstantaneousAction("a1")
    a1.add_precondition(GT(x, Fraction(505, 100)))
    a1.add_effect(x, Plus(x, Fraction(509, 100)))

    problem.add_action(a1)

    valid_plans = [SequentialPlan([a1() for _ in range(i)]) for i in range(7) if i > 0]
    invalid_plans = [SequentialPlan([])]
    res[problem.name] = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=valid_plans,
        invalid_plans=invalid_plans,
    )

    problem = Problem("LT_linear_conditions")
    problem.set_initial_value(x, Fraction(51, 10))
    problem.add_goal(LT(x, Fraction(1, 10)))

    a1 = InstantaneousAction("a1")
    a1.add_precondition(LT(x, Fraction(515, 100)))
    a1.add_effect(x, Minus(x, Fraction(501, 100)))

    problem.add_fluent(x)
    problem.add_action(a1)

    valid_plans = [SequentialPlan([a1() for _ in range(i)]) for i in range(7) if i > 0]
    invalid_plans = [SequentialPlan([])]
    res[problem.name] = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=valid_plans,
        invalid_plans=invalid_plans,
    )

    problem = Problem("GTE_LTE_linear_conditions")
    problem.set_initial_value(x, 0)
    problem.add_goal(GE(x, 10))

    a1 = InstantaneousAction("increase-to-5")
    a1.add_precondition(LT(x, 5))
    a1.add_effect(x, Plus(x, 5))

    a2 = InstantaneousAction("increase-to-10")
    a2.add_precondition(GT(x, 4))
    a2.add_precondition(LE(x, 9))
    a2.add_effect(x, Plus(x, 5))

    problem.add_fluent(x)
    problem.add_action(a1)
    problem.add_action(a2)

    valid_plans = [SequentialPlan([a1(), a2()])]
    invalid_plans = [
        SequentialPlan([]),
        SequentialPlan([a1(), a2(), a2()]),
        SequentialPlan([a1(), a1(), a2()]),
    ]
    res[problem.name] = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=valid_plans,
        invalid_plans=invalid_plans,
    )

    a = InstantaneousAction("action1")
    a.add_precondition(Not(Equals(x, 10)))
    a.add_effect(x, Minus(x, 10))
    problem = Problem("negative_linear_conditions")
    problem.add_fluent(x)
    problem.add_action(a)
    problem.set_initial_value(x, 0)
    problem.add_goal(Not(Equals(x, 0)))

    valid_plans = [SequentialPlan([a() for _ in range(i)]) for i in range(7) if i > 0]
    invalid_plans = [SequentialPlan([])]
    res[problem.name] = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=valid_plans,
        invalid_plans=invalid_plans,
    )

    a = InstantaneousAction("action1")
    a.add_effect(x, Minus(x, 10))
    problem = Problem("equality_linear_conditions")
    problem.add_fluent(x)
    problem.add_action(a)
    problem.set_initial_value(x, 10)
    problem.add_goal(Equals(x, 0))

    valid_plans = [SequentialPlan([a()])]
    invalid_plans = [
        SequentialPlan([a() for _ in range(i)]) for i in range(7) if i != 1
    ]
    res[problem.name] = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=valid_plans,
        invalid_plans=invalid_plans,
    )

    return res
