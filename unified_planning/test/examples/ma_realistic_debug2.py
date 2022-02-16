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
# limitations under the License.


import unified_planning
from unified_planning.shortcuts import *
from collections import namedtuple
from unified_planning.model.agent import Agent
from unified_planning.model.ma_problem import MultiAgentProblem
from realistic import get_example_problems
from unified_planning.model.environment import Environment_

from unified_planning.io.pddl_writer import PDDLWriter
#from unified_planning.io.pddl_reader import PDDLReader

Example = namedtuple('Example', ['problem', 'plan'])
problems = {}
examples = get_example_problems()

def prova():
    Location = UserType('location')
    robot_at = Fluent('robot_at', BoolType(), [Location])
    robot_at_2 = Fluent('robot_at_2', BoolType(), [Location])
    move = InstantaneousAction('move', l_from=Location, l_to=Location)
    move_2 = InstantaneousAction('move_2', l_from=Location, l_to=Location)
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    move.add_precondition(robot_at(l_from))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)

    move_2.add_precondition(robot_at_2(l_from))
    move_2.add_effect(robot_at_2(l_from), False)
    move_2.add_effect(robot_at_2(l_to), True)

    l1 = Object('l1', Location)
    l2 = Object('l2', Location)
    '''l3 = Object('l3', Location)
    l4 = Object('l4', Location)'''


    problem = Problem('robotto')
    problem.add_fluent(robot_at)
    problem.add_fluent(robot_at_2)
    problem.add_action(move)
    problem.add_action(move_2)

    problem.add_object(l1)
    problem.add_object(l2)

    '''problem.add_object(l3)
    problem.add_object(l4)'''

    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    '''problem.set_initial_value(robot_at(l3), False)
    problem.set_initial_value(robot_at(l4), False)'''

    problem.set_initial_value(robot_at_2(l1), True)
    problem.set_initial_value(robot_at_2(l2), False)
    '''problem.set_initial_value(robot_at_2(l1), False)
    problem.set_initial_value(robot_at_2(l2), False)'''

    problem.add_goal(robot_at(l2))
    problem.add_goal(robot_at_2(l2))


    print(problem)
    '''w = PDDLWriter(problem)
    print(w.get_domain())
    print(w.get_problem())'''
    print(problem.env)
    with OneshotPlanner(name='pyperplan') as planner:
        solve_plan = planner.solve(problem)
        print("Pyperplan returned: %s" % solve_plan)

#ciao()

def prova2():
    Location = UserType('Location')
    robot_at = Fluent('robot_at', BoolType(), [Location])
    robot_at_2 = Fluent('robot_at_2', BoolType(), [Location])
    battery_charge = Fluent('battery_charge', RealType(0, 100))
    battery_charge_2 = Fluent('battery_charge_2', RealType(0, 100))
    move = InstantaneousAction('move', l_from=Location, l_to=Location)
    move_2 = InstantaneousAction('move_2', l_from=Location, l_to=Location)
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')

    move.add_precondition(GE(battery_charge, 10))
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(robot_at(l_from))
    move.add_precondition(Not(robot_at(l_to)))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    move.add_effect(battery_charge, Minus(battery_charge, 10))

    move_2.add_precondition(GE(battery_charge_2, 10))
    move_2.add_precondition(Not(Equals(l_from, l_to)))
    move_2.add_precondition(robot_at(l_from))
    move_2.add_precondition(Not(robot_at(l_to)))
    move_2.add_effect(robot_at(l_from), False)
    move_2.add_effect(robot_at(l_to), True)
    move_2.add_effect(battery_charge_2, Minus(battery_charge_2, 10))


    l1 = Object('l1', Location)
    l2 = Object('l2', Location)
    problem = Problem('robot')
    problem.add_fluent(robot_at)
    problem.add_fluent(robot_at_2)
    problem.add_fluent(battery_charge)
    problem.add_fluent(battery_charge_2)
    problem.add_action(move)
    problem.add_action(move_2)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    problem.set_initial_value(robot_at_2(l1), True)
    problem.set_initial_value(robot_at_2(l2), False)
    problem.set_initial_value(battery_charge, 100)
    problem.set_initial_value(battery_charge_2, 100)
    problem.add_goal(robot_at(l2))
    problem.add_goal(robot_at_2(l2))
    print(problem)

    w = PDDLWriter(problem)
    print(w.get_domain())
    print(w.get_problem())