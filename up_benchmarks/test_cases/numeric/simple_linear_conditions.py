import unified_planning
from unified_planning.plans import SequentialPlan, ActionInstance
from unified_planning.shortcuts import *
from unified_planning.test import TestCase


def get_test_cases():
    res = {}

    x = Fluent("x", RealType())
    problem = Problem("GT_linear_conditions")
    problem.set_initial_value(x, 5.1)
    problem.add_goal(GT(x, 10))

    a1 = InstantaneousAction("a1")
    a1.add_precondition(GT(x, 5.05))
    a1.add_effect(x, Plus(x, 5.09))

    problem.add_fluent(x)
    problem.add_action(a1)

    # TODO add plans
    res[problem.name] = TestCase(problem=problem, solvable=True)

    problem = Problem("LT_linear_conditions")
    problem.set_initial_value(x, 5.1)
    problem.add_goal(LT(x, 0.1))

    a1 = InstantaneousAction("a1")
    a1.add_precondition(LT(x, 5.15))
    a1.add_effect(x, Minus(x, 5.01))

    problem.add_fluent(x)
    problem.add_action(a1)

    # TODO add plans
    res[problem.name] = TestCase(problem=problem, solvable=True)

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

    # TODO add plans
    res[problem.name] = TestCase(problem=problem, solvable=True)

    a = InstantaneousAction("action1")
    a.add_precondition(Not(Equals(x, 10)))
    a.add_effect(x, Minus(x, 10))
    problem = Problem("negative_linear_conditions")
    problem.add_fluent(x)
    problem.add_action(a)
    problem.set_initial_value(x, 0)
    problem.add_goal(Not(Equals(x, 0)))

    # TODO add plans
    res[problem.name] = TestCase(problem=problem, solvable=True)

    a = InstantaneousAction("action1")
    a.add_effect(x, Minus(x, 10))
    problem = Problem("equality_linear_conditions")
    problem.add_fluent(x)
    problem.add_action(a)
    problem.set_initial_value(x, 10)
    problem.add_goal(Equals(x, 0))

    # TODO add plans
    res[problem.name] = TestCase(problem=problem, solvable=True)

    return res
