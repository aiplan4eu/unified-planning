import unified_planning
from unified_planning.plans import SequentialPlan, ActionInstance
from unified_planning.shortcuts import *
from unified_planning.test import TestCase


def get_test_cases():
    res = {}

    base_problem = Problem()
    Obj = UserType("Obj")
    x = Object("x", Obj)
    y = Object("y", Obj)

    base_problem.add_objects([x, y])

    fun = Fluent("fun", RealType(), o=Obj)
    base_problem.add_fluent(fun)

    base_problem.set_initial_value(fun(x), 2)
    base_problem.set_initial_value(fun(y), 3)

    problem = base_problem.clone()
    problem.name = "disjunctive_nonlinear_conditions"

    action = InstantaneousAction("action1")
    action.add_precondition(
        Or(Equals(Div(fun(y), fun(x)), Fraction(15, 10)), LT(fun(y), 2))
    )
    action.add_effect(fun(y), 10)
    problem.add_action(action)

    problem.add_goal(Or(Equals(Times(fun(x), fun(y)), 20), GT(fun(y), 100)))

    valid_plans = [SequentialPlan([action()])]
    invalid_plans = [SequentialPlan([action(), action()]), SequentialPlan([])]
    res[problem.name] = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=valid_plans,
        invalid_plans=invalid_plans,
    )

    problem = base_problem.clone()
    problem.name = "existential_nonlinear_conditions"

    action = InstantaneousAction("action1")
    a = Variable("a", Obj)
    action.add_precondition(Exists(Equals(Times(fun(a), fun(x)), 6), a))
    action.add_effect(fun(y), 4)
    problem.add_action(action)

    problem.add_goal(Exists(Equals(Times(fun(a), fun(x)), 8), a))

    valid_plans = [SequentialPlan([action()])]
    invalid_plans = [SequentialPlan([action(), action()]), SequentialPlan([])]
    res[problem.name] = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=valid_plans,
        invalid_plans=invalid_plans,
    )

    problem = base_problem.clone()
    problem.name = "universal_nonlinear_conditions"

    action = InstantaneousAction("action1")
    action.add_precondition(Forall(GT(Times(fun(a), fun(a)), 3), a))
    action.add_effect(fun(x), 3)
    problem.add_action(action)

    problem.add_goal(Forall(Equals(Times(fun(a), fun(a)), 9), a))

    valid_plans = [SequentialPlan([action()]), SequentialPlan([action(), action()])]
    invalid_plans = [SequentialPlan([])]
    res[problem.name] = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=valid_plans,
        invalid_plans=invalid_plans,
    )

    return res
