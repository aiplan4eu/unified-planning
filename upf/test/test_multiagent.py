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


import upf
from upf.shortcuts import *
from collections import namedtuple
from agent import agent
from ma_problem import MultiAgentProblem

Example = namedtuple('Example', ['problem', 'plan'])

def ma_example_problem():
    problems = {}

    Location = UserType('Location')
    robot_at = Fluent('robot_at', BoolType(), [Location])
    battery_charge = Fluent('battery_charge', RealType(0, 100))
    cargo_at = Fluent('cargo_at', BoolType(), [Location])

    # Creation of the robot1 object and addition of fluents
    robot1 = agent(robot_at, [], [], [])
    robot1.add_fluents(battery_charge)
    #robot1.add_fluents(cargo_at)

    # Action move with its preconditions and effects
    move = InstantaneousAction('move', l_from=Location, l_to=Location)
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    move.add_precondition(GE(battery_charge, 10))
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(robot_at(l_from))
    move.add_precondition(Not(robot_at(l_to)))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    move.add_effect(battery_charge, Minus(battery_charge, 10))
    l1 = Object('l1', Location)
    l2 = Object('l2', Location)

    # Adding goals
    robot1.add_goals(l1)
    robot1.add_goals(l2)

    # Add action with associated preconditions and effects
    robot1.add_actions(move)

    ######################################ROBOT2######################################
    Location2 = UserType('Location2')
    robot_at2 = Fluent('robot_at2', BoolType(), [Location2])
    battery_charge2 = Fluent('battery_charge2', RealType(0, 100))
    cargo_at2 = Fluent('cargo_at2', BoolType(), [Location2])

    # Creation of the robot2 object and addition of fluents
    robot2 = agent(robot_at2, [], [], [])
    robot2.add_fluents(battery_charge2)
    #robot2.add_fluents(cargo_at2)

    # Action move2 with its preconditions and effects
    move2 = InstantaneousAction('move_2', l_from=Location2, l_to=Location2)
    l_from = move2.parameter('l_from')
    l_to = move2.parameter('l_to')
    move2.add_precondition(GE(battery_charge2, 10))
    move2.add_precondition(Not(Equals(l_from, l_to)))
    move2.add_precondition(robot_at2(l_from))
    move2.add_precondition(Not(robot_at2(l_to)))
    move2.add_effect(robot_at2(l_from), False)
    move2.add_effect(robot_at2(l_to), True)
    move2.add_effect(battery_charge2, Minus(battery_charge2, 10))
    l1_2 = Object('l1_1', Location2)
    l2_2 = Object('l2_2', Location2)

    # Adding goals
    robot2.add_goals(l1_2)
    robot2.add_goals(l2_2)

    # Add action with associated preconditions and effects
    robot2.add_actions(move2)

    ######################################Problem######################################
    problem = MultiAgentProblem('robots')

    problem.add_agent(robot1)
    problem.add_agent(robot2)

    #Robot1
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    problem.set_initial_value(battery_charge, 100)
    problem.add_goal(robot_at(l2))

    #Robot2
    problem.add_object(l1_2)
    problem.add_object(l2_2)
    problem.set_initial_value(robot_at2(l1_2), True)
    problem.set_initial_value(robot_at2(l2_2), False)
    problem.set_initial_value(battery_charge2, 80)
    problem.add_goal(robot_at2(l2_2))


    problem.compile(problem)
    plan = problem.solve_compile(problem)
    robots = Example(problem=problem, plan=plan)
    problems['robots'] = robots

    print("-------------------------problems-------------------------\n", problems['robots'])

    return problems




