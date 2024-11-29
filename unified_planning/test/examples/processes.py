from unified_planning.shortcuts import *
from unified_planning.model.transition import Process
from unified_planning.test import TestCase


def get_example_problems():
    problems = {}
    on = Fluent("on")
    d = Fluent("d", RealType())

    a = InstantaneousAction("turn_on")
    a.add_precondition(Not(on))
    a.add_effect(on, True)

    evt = Event("turn_off_automatically")
    evt.add_precondition(GE(d, 200))
    evt.add_effect(on, False)

    b = Process("moving")
    b.add_precondition(on)
    b.add_derivative(d, 1)

    problem = Problem("1d_Movement")
    problem.add_fluent(on)
    problem.add_fluent(d)
    problem.add_action(a)
    problem.add_action(b)
    problem.add_action(evt)
    problem.set_initial_value(on, False)
    problem.set_initial_value(d, 0)
    problem.add_goal(GE(d, 10))

    z = Fluent("z", BoolType())
    pr = Process("Name")
    pr.add_precondition(z)
    test_problem = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=[],
        invalid_plans=[],
    )
    problems["1d_movement"] = test_problem
    return problems
