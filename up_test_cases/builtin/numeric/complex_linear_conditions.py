import unified_planning
from unified_planning.plans import SequentialPlan, ActionInstance
from unified_planning.shortcuts import *
from unified_planning.test import TestCase


def get_test_cases():
    res = {}

    Obj = UserType("Obj")
    x = Object("x", Obj)
    y = Object("y", Obj)

    base_problem = Problem()
    base_problem.add_objects([x, y])

    fun = Fluent("fun", IntType(), o=Obj)
    base_problem.add_fluent(fun, default_initial_value=0)

    # disjunctive_linear_conditions
    problem = base_problem.clone()
    problem.name = "disjunctive_linear_conditions"

    action = InstantaneousAction("action1")
    action.add_precondition(Or(GT(fun(x), 10), GT(fun(y), 10)))
    action.add_effect(fun(y), Plus(fun(y), 10))
    problem.add_action(action)

    problem.set_initial_value(fun(x), 11)
    problem.add_goal(Or(Equals(fun(y), 10), LT(fun(x), 1)))

    # TODO add plans
    res[problem.name] = TestCase(problem=problem, solvable=True)

    # existential_linear_conditions
    problem = base_problem.clone()
    problem.name = "existential_linear_conditions"

    action = InstantaneousAction("action1", param=Obj)
    param = action.parameter("param")
    var = Variable("a", Obj)
    action.add_precondition(Exists(GT(fun(var), 10), var))
    action.add_effect(fun(param), Plus(fun(param), 10))
    problem.add_action(action)

    problem.set_initial_value(fun(y), 11)

    problem.add_goal(Exists(Equals(fun(var), 10), var))

    # TODO add plans
    res[problem.name] = TestCase(problem=problem, solvable=True)

    # universal_linear_conditions
    problem = base_problem.clone()
    problem.name = "universal_linear_conditions"

    action1 = InstantaneousAction("action1", param1=Obj, param2=Obj)
    param1 = action1.parameter("param1")
    param2 = action1.parameter("param2")

    action1.add_precondition(Forall(Equals(fun(var), 0), var))
    action1.add_effect(fun(param1), Plus(fun(param1), 5))
    action1.add_effect(fun(param2), Plus(fun(param2), 5))
    problem.add_action(action1)

    problem.add_goal(Forall(Equals(fun(var), 5), var))

    # TODO add plans
    res[problem.name] = TestCase(problem=problem, solvable=True)

    # universal_existential_linear_conditions

    type1 = UserType("Type1")
    type2 = UserType("Type2")

    x = Object("x", type1)
    y = Object("y", type1)
    z = Object("z", type2)
    k = Object("k", type2)

    problem = Problem("universal_existential_linear_conditions")
    problem.add_objects([x, y, z, k])

    fun = Fluent("fun", RealType(), t1=type1, t2=type2)
    problem.add_fluent(fun, default_initial_value=0)

    action = InstantaneousAction("action1", param1=type1, param2=type2)
    param1 = action.parameter("param1")
    param2 = action.parameter("param2")
    var1 = Variable("a", type1)
    var2 = Variable("b", type2)
    action.add_precondition(Forall(Exists(GT(fun(var1, var2), 0), var2), var1))
    action.add_effect(fun(param1, param2), Plus(fun(param1, param2), Fraction(15, 10)))
    problem.add_action(action)

    problem.set_initial_value(fun(x, z), Fraction(1, 10))
    problem.set_initial_value(fun(y, k), Fraction(1, 10))

    problem.add_goal(Forall(Exists(GT(fun(var1, var2), Fraction(15, 10)), var2), var1))

    # TODO add plans
    res[problem.name] = TestCase(problem=problem, solvable=True)

    return res
