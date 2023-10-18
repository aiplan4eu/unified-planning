import unified_planning
from unified_planning.shortcuts import *
from unified_planning.model.multi_agent import *
from unified_planning.test import TestCase


def get_test_cases():
    res = {}
    problem = MultiAgentProblem("simple_MA")
    robot_a = Agent("robot_a", problem)
    scale_a = Agent("scale_a", problem)
    Location = UserType("Location")
    door = UserType("door")
    home = UserType("home", Location)
    office = UserType("office", Location)
    open20 = UserType("open20", door)
    close20 = UserType("close20", door)

    open = Fluent("open", door=door)
    pos = Fluent("pos", loc=Location)

    robot_a.add_fluent(pos, default_initial_value=False)
    scale_a.add_fluent(open, default_initial_value=False)

    movegripper = InstantaneousAction("movegripper", x=office, y=home)
    x = movegripper.parameter("x")
    y = movegripper.parameter("y")
    movegripper.add_precondition(pos(x))
    movegripper.add_effect(pos(y), True)

    open_door = InstantaneousAction("open_door", z=close20, w=open20)
    z = open_door.parameter("z")
    w = open_door.parameter("w")
    open_door.add_precondition(open(z))
    open_door.add_effect(open(w), True)

    robot_a.add_action(movegripper)
    scale_a.add_action(open_door)

    home1 = Object("home1", home)
    office1 = Object("office1", office)
    open20_ = Object("open20_", open20)
    close20_ = Object("close20_", close20)

    problem.add_object(home1)
    problem.add_object(office1)
    problem.add_object(open20_)
    problem.add_object(close20_)

    problem.add_agent(robot_a)
    problem.add_agent(scale_a)

    problem.set_initial_value(Dot(robot_a, pos(office1)), True)
    problem.set_initial_value(Dot(scale_a, open(close20_)), True)

    problem.add_goal(Dot(robot_a, pos(home1)))
    problem.add_goal(Dot(scale_a, open(open20_)))

    res[problem.name] = TestCase(problem, solvable=True)
    return res
