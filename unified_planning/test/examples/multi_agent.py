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
    pos = Fluent("pos", Location)
    r.add_fluent(pos)
    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(Equals(pos, l_from))
    move.add_precondition(is_connected(l_from, l_to))
    move.add_effect(pos, l_to)
    r.add_action(move)
    problem.add_agent(r)

    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem.add_objects([l1, l2])

    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(Dot(r, pos), l1)
    problem.add_goal(Equals(Dot(r, pos), l2))

    plan = up.plans.SequentialPlan(
        [up.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2)), r)]
    )

    basic = Example(problem=problem, plan=plan)
    problems["ma-basic"] = basic

    return problems
