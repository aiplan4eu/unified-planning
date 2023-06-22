# Copyright 2021-2023 AIPlan4EU project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from unified_planning.shortcuts import *
from unified_planning.model.multi_agent import *
from collections import namedtuple

Example = namedtuple("Example", ["problem", "plan"])


def get_example_problems():
    problems = {}

    # basic multi agent
    problem = MultiAgentProblem("ma-basic")

    Location = UserType("Location")

    is_connected = Fluent("is_connected", BoolType(), l1=Location, l2=Location)
    problem.ma_environment.add_fluent(is_connected, default_initial_value=False)

    r = Agent("robot", problem)
    pos = Fluent("pos", position=Location)
    r.add_fluent(pos, default_initial_value=False)
    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(pos(l_from))
    move.add_precondition(is_connected(l_from, l_to))
    move.add_effect(pos(l_to), True)
    move.add_effect(pos(l_from), False)
    r.add_action(move)
    problem.add_agent(r)

    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem.add_objects([l1, l2])

    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(Dot(r, pos(l1)), True)
    problem.add_goal(Dot(r, pos(l2)))

    plan = up.plans.SequentialPlan(
        [up.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2)), r)]
    )

    basic = Example(problem=problem, plan=plan)
    problems["ma-basic"] = basic

    # Loader multi agent
    problem = MultiAgentProblem("ma-loader")

    Location = UserType("Location")

    is_connected = Fluent("is_connected", BoolType(), l1=Location, l2=Location)
    cargo_at = Fluent("cargo_at", BoolType(), position=Location)
    problem.ma_environment.add_fluent(is_connected, default_initial_value=False)
    problem.ma_environment.add_fluent(cargo_at, default_initial_value=False)

    robot1 = Agent("robot1", problem)
    robot2 = Agent("robot2", problem)
    pos = Fluent("pos", position=Location)

    cargo_mounted = Fluent("cargo_mounted")
    robot1.add_fluent(pos, default_initial_value=False)
    robot1.add_fluent(cargo_mounted)
    robot2.add_fluent(pos, default_initial_value=False)
    robot2.add_fluent(cargo_mounted)

    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(pos(l_from))
    move.add_precondition(is_connected(l_from, l_to))
    move.add_effect(pos(l_to), True)
    move.add_effect(pos(l_from), False)

    load = InstantaneousAction("load", loc=Location)
    loc = load.parameter("loc")
    load.add_precondition(cargo_at(loc))
    load.add_precondition(pos(loc))
    load.add_precondition(Not(cargo_mounted))
    load.add_effect(cargo_at(loc), False)
    load.add_effect(cargo_mounted, True)

    unload = InstantaneousAction("unload", loc=Location)
    loc = unload.parameter("loc")
    unload.add_precondition(Not(cargo_at(loc)))
    unload.add_precondition(pos(loc))
    unload.add_precondition(cargo_mounted)
    unload.add_effect(cargo_at(loc), True)
    unload.add_effect(cargo_mounted, False)

    robot1.add_action(move)
    robot2.add_action(move)
    robot1.add_action(load)
    robot2.add_action(load)
    robot1.add_action(unload)
    robot2.add_action(unload)
    problem.add_agent(robot1)
    problem.add_agent(robot2)

    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    l3 = Object("l3", Location)
    problem.add_objects([l1, l2, l3])

    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l2, l1), True)
    problem.set_initial_value(is_connected(l2, l3), True)
    problem.set_initial_value(Dot(robot1, pos(l2)), True)
    problem.set_initial_value(Dot(robot2, pos(l2)), True)
    problem.set_initial_value(cargo_at(l1), True)
    problem.set_initial_value(cargo_at(l2), False)
    problem.set_initial_value(cargo_at(l3), False)
    problem.set_initial_value(Dot(robot1, cargo_mounted), False)
    problem.set_initial_value(Dot(robot2, cargo_mounted), False)

    problem.add_goal(cargo_at(l3))

    plan = up.plans.SequentialPlan(
        [
            move(l2, l1, agent=robot1),
            load(l1, agent=robot1),
            move(l1, l2, agent=robot1),
            unload(l2, agent=robot1),
            load(l2, agent=robot2),
            move(l2, l3, agent=robot2),
            unload(l3, agent=robot2),
        ]
    )
    ma_loader = Example(problem=problem, plan=plan)
    problems["ma-loader"] = ma_loader

    # TYPEs
    Location = UserType("Location")
    button = UserType("button")
    problem = MultiAgentProblem("ma_bottons")

    reedButton = Object("reedButton", button)
    reedButton1 = Object("reedButton1", button)
    reedButton2 = Object("reedButton2", button)
    greenButton = Object("greenButton", button)
    yellowButton = Object("yellowButton", button)

    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    l3 = Object("l3", Location)
    l4 = Object("l4", Location)
    l5 = Object("l5", Location)
    l6 = Object("l6", Location)
    l7 = Object("l7", Location)
    l8 = Object("l8", Location)
    problem.add_objects([l1, l2, l3, l4, l5, l6, l7, l8])
    problem.add_object(reedButton)
    problem.add_object(reedButton1)
    problem.add_object(reedButton2)
    problem.add_object(greenButton)
    problem.add_object(yellowButton)

    # FLUENTS
    activeButton = Fluent("activeButton", button=button)
    pressButton = Fluent(
        "pressButton",
        BoolType(),
        button=button,
        position=Location,
        connect_from=Location,
        connect_to=Location,
    )
    pressButton_contemp = Fluent(
        "pressButton_contemp",
        BoolType(),
        button=button,
        position=Location,
        connect_from=Location,
        connect_to=Location,
    )
    at_gB = Fluent(
        "at_gB",
        BoolType(),
        postion=Location,
        connect_from=Location,
        connect_to=Location,
    )
    at_rB = Fluent(
        "at_rB",
        BoolType(),
        postion=Location,
        connect_from=Location,
        connect_to=Location,
    )

    # AGENTs
    a1 = Agent("a1", problem)
    a2 = Agent("a2", problem)
    a3 = Agent("a3", problem)

    is_connected = Fluent("is_connected", BoolType(), l1=Location, l2=Location)
    problem.ma_environment.add_fluent(is_connected, default_initial_value=False)
    pos = Fluent("pos", position=Location)
    a1.add_public_fluent(pos, default_initial_value=False)
    a2.add_public_fluent(pos, default_initial_value=False)
    a3.add_public_fluent(pos, default_initial_value=False)

    problem.ma_environment.add_fluent(activeButton, default_initial_value=False)
    problem.ma_environment.add_fluent(pressButton, default_initial_value=False)
    problem.ma_environment.add_fluent(pressButton_contemp, default_initial_value=False)
    problem.ma_environment.add_fluent(at_gB, default_initial_value=False)
    problem.ma_environment.add_fluent(at_rB, default_initial_value=False)

    # ACTIONS
    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(pos(l_from))
    move.add_precondition(is_connected(l_from, l_to))
    move.add_effect(pos(l_to), True)
    move.add_effect(pos(l_from), False)

    push_button = InstantaneousAction(
        "push_button",
        butt=button,
        loc=Location,
        connect_from=Location,
        connect_to=Location,
    )  # , l_from=Location, l_to=Location)
    butt = push_button.parameter("butt")
    loc = push_button.parameter("loc")
    connect_from = push_button.parameter("connect_from")
    connect_to = push_button.parameter("connect_to")
    push_button.add_precondition(pos(loc))
    push_button.add_precondition(pressButton(butt, loc, connect_from, connect_to))
    push_button.add_precondition(Not(activeButton(butt)))
    push_button.add_effect(activeButton(butt), True)
    push_button.add_effect(is_connected(connect_from, connect_to), True)

    push_red_button1 = InstantaneousAction(
        "push_red_button1",
        butt=button,
        loc=Location,
        connect_from=Location,
        connect_to=Location,
    )
    loc = push_red_button1.parameter("loc")
    connect_from = push_red_button1.parameter("connect_from")
    connect_to = push_red_button1.parameter("connect_to")
    butt = push_red_button1.parameter("butt")
    push_red_button1.add_precondition(Dot(a3, pos(loc)))
    push_red_button1.add_precondition(Dot(a2, pos(loc)))
    push_red_button1.add_precondition(
        pressButton_contemp(butt, loc, connect_from, connect_to)
    )
    push_red_button1.add_effect(
        activeButton(reedButton2), True, Not(activeButton(reedButton2))
    )

    push_red_button2 = InstantaneousAction(
        "push_red_button2",
        butt=button,
        loc=Location,
        connect_from=Location,
        connect_to=Location,
    )
    loc = push_red_button2.parameter("loc")
    connect_from = push_red_button2.parameter("connect_from")
    connect_to = push_red_button2.parameter("connect_to")
    butt = push_red_button2.parameter("butt")
    push_red_button2.add_precondition(Dot(a3, pos(loc)))
    push_red_button2.add_precondition(Dot(a2, pos(loc)))
    push_red_button2.add_precondition(
        pressButton_contemp(butt, loc, connect_from, connect_to)
    )
    push_red_button2.add_effect(
        activeButton(reedButton1), True, Not(activeButton(reedButton1))
    )

    unpush_push_button = InstantaneousAction(
        "unpush_push_button",
        butt=button,
        loc=Location,
        connect_from=Location,
        connect_to=Location,
    )  # , l_from=Location, l_to=Location)
    loc = unpush_push_button.parameter("loc")
    connect_from = unpush_push_button.parameter("connect_from")
    connect_to = unpush_push_button.parameter("connect_to")
    butt = unpush_push_button.parameter("butt")
    unpush_push_button.add_precondition(Dot(a3, pos(loc)))
    unpush_push_button.add_precondition(Dot(a2, pos(loc)))
    unpush_push_button.add_precondition(activeButton(reedButton1))
    unpush_push_button.add_precondition(activeButton(reedButton2))
    unpush_push_button.add_precondition(
        pressButton_contemp(butt, loc, connect_from, connect_to)
    )
    unpush_push_button.add_effect(
        is_connected(connect_from, connect_to),
        True,
        And(activeButton(reedButton1), activeButton(reedButton2)),
    )

    a1.add_action(move)
    a1.add_action(push_button)

    a2.add_action(move)
    a2.add_action(push_button)
    a2.add_action(unpush_push_button)
    a2.add_action(push_red_button1)

    a3.add_action(move)
    a3.add_action(push_button)
    a3.add_action(unpush_push_button)
    a3.add_action(push_red_button2)

    problem.add_agent(a1)
    problem.add_agent(a2)
    problem.add_agent(a3)

    # INITIAL VALUEs
    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l5, l6), True)
    problem.set_initial_value(activeButton(reedButton), False)
    problem.set_initial_value(activeButton(reedButton1), False)
    problem.set_initial_value(activeButton(reedButton2), False)

    problem.set_initial_value(Dot(a1, pos(l1)), True)
    problem.set_initial_value(Dot(a2, pos(l4)), True)
    problem.set_initial_value(Dot(a3, pos(l7)), True)

    problem.set_initial_value(pressButton(yellowButton, l2, l4, l5), True)
    problem.set_initial_value(pressButton(greenButton, l5, l7, l6), True)
    problem.set_initial_value(pressButton_contemp(reedButton, l6, l2, l3), True)

    # GOALs
    problem.add_goal(Dot(a1, pos(l3)))
    problem.add_goal(Dot(a2, pos(l6)))
    problem.add_goal(Dot(a3, pos(l6)))

    plan = up.plans.SequentialPlan(
        [
            up.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2)), a1),
            up.plans.ActionInstance(
                push_button,
                (ObjectExp(yellowButton), ObjectExp(l2), ObjectExp(l4), ObjectExp(l5)),
                a1,
            ),
            up.plans.ActionInstance(move, (ObjectExp(l4), ObjectExp(l5)), a2),
            up.plans.ActionInstance(
                push_button,
                (ObjectExp(greenButton), ObjectExp(l5), ObjectExp(l7), ObjectExp(l6)),
                a2,
            ),
            up.plans.ActionInstance(move, (ObjectExp(l7), ObjectExp(l6)), a3),
            up.plans.ActionInstance(move, (ObjectExp(l5), ObjectExp(l6)), a2),
            up.plans.ActionInstance(
                push_red_button2,
                (ObjectExp(reedButton), ObjectExp(l6), ObjectExp(l2), ObjectExp(l3)),
                a3,
            ),
            up.plans.ActionInstance(
                push_red_button1,
                (ObjectExp(reedButton), ObjectExp(l6), ObjectExp(l2), ObjectExp(l3)),
                a2,
            ),
            up.plans.ActionInstance(move, (ObjectExp(l2), ObjectExp(l3)), a1),
        ]
    )
    ma_RM = Example(problem=problem, plan=plan)
    problems["ma_buttons"] = ma_RM

    return problems
