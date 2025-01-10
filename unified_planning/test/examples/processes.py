from unified_planning.shortcuts import *
from unified_planning.test import TestCase

# TODO we need more tests for better coverage


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
    b.add_increase_continuous_effect(d, 1)

    problem = Problem("1d_Movement")
    problem.add_fluent(on)
    problem.add_fluent(d)
    problem.add_action(a)
    problem.add_process(b)
    problem.add_event(evt)
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

    problem = Problem("boiling_water")
    boiler_on = Fluent("boiler_on")
    temperature = Fluent("temperature", RealType())
    water_level = Fluent("water_level", RealType())
    chimney_vent_open = Fluent("chimney_vent_open")

    turn_on_boiler = InstantaneousAction("turn_on_boiler")
    turn_on_boiler.add_precondition(Not(boiler_on))
    turn_on_boiler.add_effect(boiler_on, True)

    water_heating = Process("water_heating")
    water_heating.add_precondition(And(boiler_on, LE(temperature, 100)))
    water_heating.add_increase_continuous_effect(temperature, 1)

    water_boiling = Process("water_boiling")
    water_boiling.add_precondition(And(boiler_on, GE(temperature, 100)))
    water_boiling.add_decrease_continuous_effect(water_level, 1)

    open_chimney_vent_auto = Event("open_chimney_vent_auto")
    open_chimney_vent_auto.add_precondition(
        And(Not(chimney_vent_open), GE(temperature, 100))
    )
    open_chimney_vent_auto.add_effect(chimney_vent_open, True)

    turn_off_boiler_auto = Event("turn_off_boiler_auto")
    turn_off_boiler_auto.add_precondition(And(LE(water_level, 0), boiler_on))
    turn_off_boiler_auto.add_effect(boiler_on, False)

    problem.add_fluent(boiler_on)
    problem.set_initial_value(boiler_on, False)
    problem.add_fluent(chimney_vent_open)
    problem.set_initial_value(chimney_vent_open, False)
    problem.add_fluent(temperature)
    problem.set_initial_value(temperature, 20)
    problem.add_fluent(water_level)
    problem.set_initial_value(water_level, 10)
    problem.add_action(turn_on_boiler)
    problem.add_process(water_heating)
    problem.add_process(water_boiling)
    problem.add_event(open_chimney_vent_auto)
    problem.add_event(turn_off_boiler_auto)
    problem.add_goal(And(Not(boiler_on), And(chimney_vent_open, LE(water_level, 2))))

    test_problem = TestCase(
        problem=problem,
        solvable=True,
        valid_plans=[],
        invalid_plans=[],
    )
    problems["boiling_water"] = test_problem

    return problems
