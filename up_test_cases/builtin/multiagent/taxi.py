import unified_planning
from unified_planning.shortcuts import *
from unified_planning.model.multi_agent import *
from unified_planning.test import TestCase


def get_test_cases():
    res = {}

    problem = MultiAgentProblem("ma-taxi")
    location = UserType("location")
    taxi = UserType("taxi")
    driver1 = Agent("driver1", problem)
    driver2 = Agent("driver2", problem)
    person1 = Agent("person1", problem)
    person2 = Agent("person2", problem)

    pos = Fluent("pos", location=location)
    at = Fluent("at", BoolType(), taxi=taxi, location=location)
    In = Fluent("in", BoolType(), taxi=taxi)
    empty = Fluent("empty", BoolType(), taxi=taxi)
    free = Fluent("free", BoolType(), location=location)
    directly_connected = Fluent(
        "directly_connected", BoolType(), l1=location, l2=location
    )
    goal_of = Fluent("goal_of", BoolType(), location=location)
    driving = Fluent("driving", taxi=taxi)

    person1.add_private_fluent(goal_of, default_initial_value=False)
    person1.add_public_fluent(pos, default_initial_value=False)
    person1.add_public_fluent(In, default_initial_value=False)

    person2.add_private_fluent(goal_of, default_initial_value=False)
    person2.add_public_fluent(pos, default_initial_value=False)
    person2.add_public_fluent(In, default_initial_value=False)

    driver1.add_public_fluent(pos, default_initial_value=False)
    driver1.add_public_fluent(In, default_initial_value=False)
    driver1.add_private_fluent(driving, default_initial_value=False)

    driver2.add_public_fluent(pos, default_initial_value=False)
    driver2.add_public_fluent(In, default_initial_value=False)
    driver2.add_private_fluent(driving, default_initial_value=False)

    problem.ma_environment.add_fluent(free, default_initial_value=False)
    problem.ma_environment.add_fluent(directly_connected, default_initial_value=False)
    problem.ma_environment.add_fluent(at, default_initial_value=False)
    problem.ma_environment.add_fluent(empty, default_initial_value=False)

    enter_p = InstantaneousAction("enter_p", t=taxi, l=location)
    l = enter_p.parameter("l")
    t = enter_p.parameter("t")
    enter_p.add_precondition(pos(l))
    enter_p.add_precondition(at(t, l))
    enter_p.add_precondition(empty(t))
    enter_p.add_effect(empty(t), False)
    enter_p.add_effect(pos(l), False)
    enter_p.add_effect(In(t), True)

    exit_p = InstantaneousAction("exit_p", t=taxi, l=location)
    l = exit_p.parameter("l")
    t = exit_p.parameter("t")
    exit_p.add_precondition(In(t))
    exit_p.add_precondition(at(t, l))
    exit_p.add_precondition(goal_of(l))

    exit_p.add_effect(In(t), False)
    exit_p.add_effect(empty(t), True)
    exit_p.add_effect(pos(l), True)

    drive_t = InstantaneousAction("drive_t", t=taxi, from_=location, to=location)
    from_ = drive_t.parameter("from_")
    to = drive_t.parameter("to")
    drive_t.add_precondition(driving(t))
    drive_t.add_precondition(at(t, from_))
    drive_t.add_precondition(directly_connected(from_, to))
    drive_t.add_precondition(free(to))
    drive_t.add_effect(at(t, from_), False)
    drive_t.add_effect(free(to), False)
    drive_t.add_effect(at(t, to), True)
    drive_t.add_effect(free(from_), True)

    person1.add_action(enter_p)
    person1.add_action(exit_p)

    person2.add_action(enter_p)
    person2.add_action(exit_p)

    driver1.add_action(drive_t)
    driver2.add_action(drive_t)

    problem.add_agent(person1)
    problem.add_agent(person2)
    problem.add_agent(driver1)
    problem.add_agent(driver2)

    g1 = Object("g1", location)
    g2 = Object("g2", location)
    c = Object("c", location)
    h1 = Object("h1", location)
    h2 = Object("h2", location)
    t1 = Object("t1", taxi)
    t2 = Object("t2", taxi)

    problem.add_object(g1)
    problem.add_object(g2)
    problem.add_object(c)
    problem.add_object(h1)
    problem.add_object(h2)
    problem.add_object(t1)
    problem.add_object(t2)

    problem.set_initial_value(directly_connected(g1, c), True)
    problem.set_initial_value(directly_connected(g2, c), True)
    problem.set_initial_value(directly_connected(c, g1), True)
    problem.set_initial_value(directly_connected(c, g2), True)
    problem.set_initial_value(directly_connected(c, h1), True)
    problem.set_initial_value(directly_connected(c, h2), True)
    problem.set_initial_value(directly_connected(h1, c), True)
    problem.set_initial_value(directly_connected(h2, c), True)
    problem.set_initial_value(Dot(person1, pos(h1)), True)
    problem.set_initial_value(Dot(person2, pos(h2)), True)
    problem.set_initial_value(at(t1, g1), True)
    problem.set_initial_value(at(t2, g2), True)
    problem.set_initial_value(empty(t1), True)
    problem.set_initial_value(empty(t2), True)
    problem.set_initial_value(free(h1), True)
    problem.set_initial_value(free(h2), True)
    problem.set_initial_value(free(c), True)
    problem.set_initial_value(Dot(person1, goal_of(c)), True)
    problem.set_initial_value(Dot(person2, goal_of(c)), True)
    problem.set_initial_value(Dot(driver1, driving(t1)), True)
    problem.set_initial_value(Dot(driver2, driving(t2)), True)

    problem.add_goal(Dot(person1, pos(c)))
    problem.add_goal(Dot(person2, pos(c)))
    problem.add_goal(at(t1, g1))
    problem.add_goal(at(t2, g2))

    res[problem.name] = TestCase(problem, solvable=True)

    return res
