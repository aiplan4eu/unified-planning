from unified_planning.shortcuts import *
from unified_planning.model.natural_transition import Process
from unified_planning.test import TestCase


def get_test_cases():
    res = {}

    x = Fluent("on")
    d = Fluent("d", RealType())

    a = InstantaneousAction("turn_on")
    a.add_precondition(Not(x))
    a.add_effect(x, True)

    evt = Event("turn_off_automatically")
    evt.add_precondition(GE(d, 200))
    evt.add_effect(x, False)

    b = Process("moving")
    b.add_precondition(x)
    b.add_derivative(d, 1)

    problem = Problem("basic")
    problem.add_fluent(x)
    problem.add_fluent(d)
    problem.add_action(a)
    problem.add_action(b)
    problem.add_action(evt)
    problem.set_initial_value(x, False)
    problem.set_initial_value(d, 0)
    problem.add_goal(GE(d, 10))

    res[problem.name] = TestCase(problem=problem, solvable=True)

    return res
