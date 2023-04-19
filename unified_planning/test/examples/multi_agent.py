# Copyright 2021 AIPlan4EU project
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
            up.plans.ActionInstance(move, (ObjectExp(l2), ObjectExp(l1)), robot1),
            up.plans.ActionInstance(load, (ObjectExp(l1),), robot1),
            up.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2)), robot1),
            up.plans.ActionInstance(unload, (ObjectExp(l2),), robot1),
            up.plans.ActionInstance(load, (ObjectExp(l2),), robot2),
            up.plans.ActionInstance(move, (ObjectExp(l2), ObjectExp(l3)), robot2),
            up.plans.ActionInstance(unload, (ObjectExp(l3),), robot2),
        ]
    )
    ma_loader = Example(problem=problem, plan=plan)
    problems["ma-loader"] = ma_loader

    return problems
