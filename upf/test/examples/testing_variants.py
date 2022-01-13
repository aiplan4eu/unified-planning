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

Example = namedtuple('Example', ['problem', 'plan'])

def get_example_problems():
    problems = {}

    # robot_real_constants
    #this version of the problem robot has reals instead of integers as constants
    Location = UserType('Location')
    robot_at = Fluent('robot_at', BoolType(), [Location])
    battery_charge = Fluent('battery_charge', RealType(0, 100))
    move = InstantaneousAction('move', l_from=Location, l_to=Location)
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    move.add_precondition(GE(battery_charge, 10.0))
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(robot_at(l_from))
    move.add_precondition(Not(robot_at(l_to)))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    move.add_effect(battery_charge, Minus(battery_charge, 10.0))
    l1 = Object('l1', Location)
    l2 = Object('l2', Location)
    problem = Problem('robot_real_constants')
    problem.add_fluent(robot_at)
    problem.add_fluent(battery_charge)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    problem.set_initial_value(battery_charge, 100.0)
    problem.add_goal(robot_at(l2))
    plan = upf.plan.SequentialPlan([upf.plan.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2)))])
    robot = Example(problem=problem, plan=plan)
    problems['robot_real_constants'] = robot

    # robot_int_battery
    #this version of the problem robot has the battery charge fluent represented as an int instead of a real
    Location = UserType('Location')
    robot_at = Fluent('robot_at', BoolType(), [Location])
    battery_charge = Fluent('battery_charge', IntType(0, 100))
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
    problem = Problem('robot_int_battery')
    problem.add_fluent(robot_at)
    problem.add_fluent(battery_charge)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    problem.set_initial_value(battery_charge, 100)
    problem.add_goal(robot_at(l2))
    plan = upf.plan.SequentialPlan([upf.plan.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2)))])
    robot = Example(problem=problem, plan=plan)
    problems['robot_int_battery'] = robot

    #robot fluent of user_type with int ID
    Int_t = IntType(0,1)
    Location = UserType('Location')
    is_at = Fluent('is_at', Location, [Int_t])
    move = InstantaneousAction('move', robot=Int_t, l_from=Location, l_to=Location)
    robot = move.parameter('robot')
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    move.add_precondition(Equals(is_at(robot), l_from))
    move.add_precondition(Not(Equals(is_at(robot), l_to)))
    move.add_effect(is_at(robot), l_to)
    l1 = Object('l1', Location)
    l2 = Object('l2', Location)
    problem = Problem('robot_fluent_of_user_type_with_int_id')
    problem.add_fluent(is_at)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(is_at(Int(0)), l1)
    problem.set_initial_value(is_at(1), l1)
    plan = upf.plan.SequentialPlan([upf.plan.ActionInstance(move, (Int(0), ObjectExp(l1), ObjectExp(l2))),
                                    upf.plan.ActionInstance(move, (Int(1), ObjectExp(l1), ObjectExp(l2)))])
    robot_fluent_of_user_type_with_int_id = Example(problem=problem, plan=plan)
    problems['robot_fluent_of_user_type_with_int_id'] = robot_fluent_of_user_type_with_int_id

    return problems
