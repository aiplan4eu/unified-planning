import unified_planning
from unified_planning.plans import SequentialPlan, ActionInstance, Plan
from unified_planning.shortcuts import *
from unified_planning.test import TestCase


def get_test_cases():
    test_cases = {}

    # basic
    x = Fluent("x")
    y = Fluent("y")
    a = InstantaneousAction("a")
    a.add_precondition(y)
    a.add_effect(x, True)
    a.add_effect(y, False)
    problem = Problem("basic")
    problem.add_fluent(x)
    problem.add_fluent(y)
    problem.add_action(a)
    problem.set_initial_value(x, False)
    problem.set_initial_value(y, True)
    problem.add_goal(x)

    plan = SequentialPlan([ActionInstance(a)])
    test_cases[problem.name] = TestCase(
        problem=problem, solvable=True, valid_plans=[plan]
    )

    # basic unsolvable
    uns_problem = problem.clone()
    uns_problem.name = "basic unsolvable"
    uns_problem.add_goal(y)
    plan = SequentialPlan([ActionInstance(a)])
    test_cases[uns_problem.name] = TestCase(
        problem=uns_problem, solvable=False, invalid_plans=[plan]
    )

    # conditional effect
    a = InstantaneousAction("a")
    a.add_effect(x, True)
    b = InstantaneousAction("b")
    b.add_effect(y, True, x)
    problem = Problem("conditional_effect")
    problem.add_fluent(x)
    problem.add_fluent(y)
    problem.add_action(a)
    problem.add_action(b)
    problem.set_initial_value(x, False)
    problem.set_initial_value(y, False)
    problem.add_goal(y)

    valid_plans: List[Plan] = [
        SequentialPlan([ActionInstance(a), ActionInstance(b)]),
        SequentialPlan([ActionInstance(a), ActionInstance(b), ActionInstance(a)]),
    ]
    invalid_plans: List[Plan] = [
        SequentialPlan([ActionInstance(b), ActionInstance(a)]),
        SequentialPlan([ActionInstance(b), ActionInstance(a), ActionInstance(b)]),
    ]

    test_cases[problem.name] = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=valid_plans,
        invalid_plans=invalid_plans,
    )

    return test_cases
