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


import unified_planning
from unified_planning.shortcuts import *
from collections import namedtuple
#from unified_planning.io.pddl_writer import PDDLWriter
#from unified_planning.io.pddl_reader import PDDLReader

Example = namedtuple('Example', ['problem', 'plan'])

def get_example_problems():
    problems = {}

    # robot
    Location = UserType('Location')
    robot_at = Fluent('robot_at', BoolType(), [Location])
    battery_charge = Fluent('battery_charge', RealType(0, 100))
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
    problem = Problem('robot')
    problem.add_fluent(robot_at)
    problem.add_fluent(battery_charge)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    problem.set_initial_value(battery_charge, 100)
    problem.add_goal(robot_at(l2))
    plan = unified_planning.plan.SequentialPlan([unified_planning.plan.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2)))])
    robot = Example(problem=problem, plan=plan)
    problems['robot'] = robot


    #print(problem)
    '''w = PDDLWriter(problem)
    print(w.get_domain())
    print(w.get_problem())'''

    #robot fluent of user_type
    Location = UserType('Location')
    Robot = UserType('Robot')
    is_at = Fluent('is_at', Location, [Robot])
    move = InstantaneousAction('move', robot=Robot, l_from=Location, l_to=Location)
    robot = move.parameter('robot')
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    move.add_precondition(Equals(is_at(robot), l_from))
    move.add_precondition(Not(Equals(is_at(robot), l_to)))
    move.add_effect(is_at(robot), l_to)
    l1 = Object('l1', Location)
    l2 = Object('l2', Location)
    r1 = Object('r1', Robot)
    r2 = Object('r2', Robot)
    problem = Problem('robot_fluent_of_user_type')
    problem.add_fluent(is_at)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.add_object(r1)
    problem.add_object(r2)
    problem.set_initial_value(is_at(r1), l2)
    problem.set_initial_value(is_at(r2), l1)
    problem.add_goal(Equals(is_at(r1), l1))
    problem.add_goal(Equals(is_at(r2), l2))
    plan = unified_planning.plan.SequentialPlan([unified_planning.plan.ActionInstance(move, (ObjectExp(r1), ObjectExp(l2), ObjectExp(l1))),
                                    unified_planning.plan.ActionInstance(move, (ObjectExp(r2), ObjectExp(l1), ObjectExp(l2)))])
    robot_fluent_of_user_type = Example(problem=problem, plan=plan)
    problems['robot_fluent_of_user_type'] = robot_fluent_of_user_type

    # robot no negative preconditions
    Location = UserType('location')
    robot_at = Fluent('robot_at', BoolType(), [Location])
    move = InstantaneousAction('move', l_from=Location, l_to=Location)
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    move.add_precondition(robot_at(l_from))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    l1 = Object('l1', Location)
    l2 = Object('l2', Location)
    problem = Problem('robot')
    problem.add_fluent(robot_at)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    problem.add_goal(robot_at(l2))
    plan = unified_planning.plan.SequentialPlan([unified_planning.plan.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2)))])
    robot_no_negative_preconditions = Example(problem=problem, plan=plan)
    problems['robot_no_negative_preconditions'] = robot_no_negative_preconditions

    # robot decrease
    Location = UserType('Location')
    robot_at = Fluent('robot_at', BoolType(), [Location])
    battery_charge = Fluent('battery_charge', RealType(0, 100))
    move = InstantaneousAction('move', l_from=Location, l_to=Location)
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    move.add_precondition(GE(battery_charge, 10))
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(robot_at(l_from))
    move.add_precondition(Not(robot_at(l_to)))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    move.add_decrease_effect(battery_charge, 10)
    l1 = Object('l1', Location)
    l2 = Object('l2', Location)
    problem = Problem('robot_decrease')
    problem.add_fluent(robot_at)
    problem.add_fluent(battery_charge)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    problem.set_initial_value(battery_charge, 100)
    problem.add_goal(robot_at(l2))
    plan = unified_planning.plan.SequentialPlan([unified_planning.plan.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2)))])
    robot_decrease = Example(problem=problem, plan=plan)
    problems['robot_decrease'] = robot_decrease

    # robot_loader
    Location = UserType('Location')
    robot_at = Fluent('robot_at', BoolType(), [Location])
    cargo_at = Fluent('cargo_at', BoolType(), [Location])
    cargo_mounted = Fluent('cargo_mounted')
    move = InstantaneousAction('move', l_from=Location, l_to=Location)
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(robot_at(l_from))
    move.add_precondition(Not(robot_at(l_to)))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    load = InstantaneousAction('load',loc=Location)
    loc = load.parameter('loc')
    load.add_precondition(cargo_at(loc))
    load.add_precondition(robot_at(loc))
    load.add_precondition(Not(cargo_mounted))
    load.add_effect(cargo_at(loc), False)
    load.add_effect(cargo_mounted, True)
    unload = InstantaneousAction('unload', loc=Location)
    loc = unload.parameter('loc')
    unload.add_precondition(Not(cargo_at(loc)))
    unload.add_precondition(robot_at(loc))
    unload.add_precondition(cargo_mounted)
    unload.add_effect(cargo_at(loc), True)
    unload.add_effect(cargo_mounted, False)
    l1 = Object('l1', Location)
    l2 = Object('l2', Location)
    problem = Problem('robot_loader')
    problem.add_fluent(robot_at)
    problem.add_fluent(cargo_at)
    problem.add_fluent(cargo_mounted)
    problem.add_action(move)
    problem.add_action(load)
    problem.add_action(unload)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    problem.set_initial_value(cargo_at(l1), False)
    problem.set_initial_value(cargo_at(l2), True)
    problem.set_initial_value(cargo_mounted, False)
    problem.add_goal(cargo_at(l1))
    plan = unified_planning.plan.SequentialPlan([unified_planning.plan.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2))),
                               unified_planning.plan.ActionInstance(load, (ObjectExp(l2), )),
                               unified_planning.plan.ActionInstance(move, (ObjectExp(l2), ObjectExp(l1))),
                               unified_planning.plan.ActionInstance(unload, (ObjectExp(l1), ))])
    robot_loader = Example(problem=problem, plan=plan)
    problems['robot_loader'] = robot_loader

    # robot_loader_mod
    Location = UserType('Location')
    robot_at = Fluent('robot_at', BoolType(), [Location])
    cargo_at = Fluent('cargo_at', BoolType(), [Location])
    is_same_location = Fluent('is_same_location', BoolType(), [Location, Location])
    cargo_mounted = Fluent('cargo_mounted')
    move = InstantaneousAction('move', l_from=Location, l_to=Location)
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    move.add_precondition(robot_at(l_from))
    move.add_precondition(Not(robot_at(l_to)))
    move.add_precondition(Not(is_same_location(l_from, l_to)))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    load = InstantaneousAction('load',loc=Location)
    loc = load.parameter('loc')
    load.add_precondition(cargo_at(loc))
    load.add_precondition(robot_at(loc))
    load.add_precondition(Not(cargo_mounted))
    load.add_effect(cargo_at(loc), False)
    load.add_effect(cargo_mounted, True)
    unload = InstantaneousAction('unload', loc=Location)
    loc = unload.parameter('loc')
    unload.add_precondition(Not(cargo_at(loc)))
    unload.add_precondition(robot_at(loc))
    unload.add_precondition(cargo_mounted)
    unload.add_effect(cargo_at(loc), True)
    unload.add_effect(cargo_mounted, False)
    l1 = Object('l1', Location)
    l2 = Object('l2', Location)
    problem = Problem('robot_loader_mod')
    problem.add_fluent(robot_at, default_initial_value=False)
    problem.add_fluent(cargo_at, default_initial_value=False)
    problem.add_fluent(cargo_mounted, default_initial_value=False)
    problem.add_fluent(is_same_location, default_initial_value=False)
    problem.add_action(move)
    problem.add_action(load)
    problem.add_action(unload)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(cargo_at(l2), True)
    for o in problem.objects(Location):
        problem.set_initial_value(is_same_location(o, o), True)
    problem.add_goal(cargo_at(l1))
    plan = unified_planning.plan.SequentialPlan([unified_planning.plan.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2))),
                               unified_planning.plan.ActionInstance(load, (ObjectExp(l2), )),
                               unified_planning.plan.ActionInstance(move, (ObjectExp(l2), ObjectExp(l1))),
                               unified_planning.plan.ActionInstance(unload, (ObjectExp(l1), ))])
    robot_loader_mod = Example(problem=problem, plan=plan)
    problems['robot_loader_mod'] = robot_loader_mod

    # robot_loader_adv
    Robot = UserType('Robot')
    Container = UserType('Container')
    Location = UserType('Location')
    robot_at = Fluent('robot_at', BoolType(), [Robot, Location])
    cargo_at = Fluent('cargo_at', BoolType(), [Container, Location])
    cargo_mounted = Fluent('cargo_mounted', BoolType(), [Container, Robot])
    move = InstantaneousAction('move', l_from=Location, l_to=Location, r=Robot)
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    r = move.parameter('r')
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(robot_at(r, l_from))
    move.add_precondition(Not(robot_at(r, l_to)))
    move.add_effect(robot_at(r, l_from), False)
    move.add_effect(robot_at(r, l_to), True)
    load = InstantaneousAction('load', loc=Location, r=Robot, c=Container)
    loc = load.parameter('loc')
    r = load.parameter('r')
    c = load.parameter('c')
    load.add_precondition(cargo_at(c, loc))
    load.add_precondition(robot_at(r, loc))
    load.add_precondition(Not(cargo_mounted(c, r)))
    load.add_effect(cargo_at(c, loc), False)
    load.add_effect(cargo_mounted(c,r), True)
    unload = InstantaneousAction('unload', loc=Location, r=Robot, c=Container)
    loc = unload.parameter('loc')
    r = unload.parameter('r')
    c = unload.parameter('c')
    unload.add_precondition(Not(cargo_at(c, loc)))
    unload.add_precondition(robot_at(r, loc))
    unload.add_precondition(cargo_mounted(c,r))
    unload.add_effect(cargo_at(c, loc), True)
    unload.add_effect(cargo_mounted(c,r), False)
    l1 = Object('l1', Location)
    l2 = Object('l2', Location)
    l3 = Object('l3', Location)
    r1 = Object('r1', Robot)
    c1 = Object('c1', Container)
    problem = Problem('robot_loader_adv')
    problem.add_fluent(robot_at)
    problem.add_fluent(cargo_at)
    problem.add_fluent(cargo_mounted)
    problem.add_action(move)
    problem.add_action(load)
    problem.add_action(unload)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.add_object(l3)
    problem.add_object(r1)
    problem.add_object(c1)
    problem.set_initial_value(robot_at(r1,l1), True)
    problem.set_initial_value(robot_at(r1,l2), False)
    problem.set_initial_value(robot_at(r1,l3), False)
    problem.set_initial_value(cargo_at(c1,l1), False)
    problem.set_initial_value(cargo_at(c1,l2), True)
    problem.set_initial_value(cargo_at(c1,l3), False)
    problem.set_initial_value(cargo_mounted(c1,r1), False)
    problem.add_goal(cargo_at(c1,l3))
    problem.add_goal(robot_at(r1,l1))
    plan = unified_planning.plan.SequentialPlan([unified_planning.plan.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2), ObjectExp(r1))),
                               unified_planning.plan.ActionInstance(load, (ObjectExp(l2), ObjectExp(r1), ObjectExp(c1))),
                               unified_planning.plan.ActionInstance(move, (ObjectExp(l2), ObjectExp(l3), ObjectExp(r1))),
                               unified_planning.plan.ActionInstance(unload, (ObjectExp(l3), ObjectExp(r1), ObjectExp(c1))),
                               unified_planning.plan.ActionInstance(move, (ObjectExp(l3), ObjectExp(l1), ObjectExp(r1)))])
    robot_loader_adv = Example(problem=problem, plan=plan)
    problems['robot_loader_adv'] = robot_loader_adv

    #robot locations connected
    Location = UserType('Location')
    Robot = UserType('Robot')
    is_at = Fluent('is_at', BoolType(), [Location, Robot])
    battery_charge = Fluent('battery_charge', RealType(0, 100), [Robot])
    is_connected = Fluent('is_connected', BoolType(), [Location, Location])
    move = InstantaneousAction('move', robot=Robot, l_from=Location, l_to=Location)
    robot = move.parameter('robot')
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    move.add_precondition(GE(battery_charge(robot), 10))
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(is_at(l_from, robot))
    move.add_precondition(Not(is_at(l_to, robot)))
    move.add_precondition(Or(is_connected(l_from, l_to), is_connected(l_to, l_from)))
    move.add_effect(is_at(l_from, robot), False)
    move.add_effect(is_at(l_to, robot), True)
    move.add_decrease_effect(battery_charge(robot), 10)
    move_2 = InstantaneousAction('move_2', robot=Robot, l_from=Location, l_to=Location)
    robot = move_2.parameter('robot')
    l_from = move_2.parameter('l_from')
    l_to = move_2.parameter('l_to')
    move_2.add_precondition(GE(battery_charge(robot), 15))
    move_2.add_precondition(Not(Equals(l_from, l_to)))
    move_2.add_precondition(is_at(l_from, robot))
    move_2.add_precondition(Not(is_at(l_to, robot)))
    mid_location = Variable('mid_loc', Location)
    #(E (location mid_location)
    # !((mid_location == l_from) || (mid_location == l_to)) && (is_connected(l_from, mid_location) || is_connected(mid_location, l_from)) &&
    # && (is_connected(l_to, mid_location) || is_connected(mid_location, l_to)))
    move_2.add_precondition(Exists(And(Not(Or(Equals(mid_location, l_from), Equals(mid_location, l_to))),
                            Or(is_connected(l_from, mid_location), is_connected(mid_location, l_from)),
                            Or(is_connected(l_to, mid_location), is_connected(mid_location, l_to))), mid_location))
    move_2.add_effect(is_at(l_from, robot), False)
    move_2.add_effect(is_at(l_to, robot), True)
    move_2.add_decrease_effect(battery_charge(robot), 15)
    l1 = Object('l1', Location)
    l2 = Object('l2', Location)
    l3 = Object('l3', Location)
    l4 = Object('l4', Location)
    l5 = Object('l5', Location)
    r1 = Object('r1', Robot)
    problem = Problem('robot_locations_connected')
    problem.add_fluent(is_at, default_initial_value=False)
    problem.add_fluent(battery_charge)
    problem.add_fluent(is_connected, default_initial_value=False)
    problem.add_action(move)
    problem.add_action(move_2)
    problem.add_object(r1)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.add_object(l3)
    problem.add_object(l4)
    problem.add_object(l5)
    problem.set_initial_value(is_at(l1, r1), True)
    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l2, l3), True)
    problem.set_initial_value(is_connected(l3, l4), True)
    problem.set_initial_value(is_connected(l4, l5), True)
    problem.set_initial_value(battery_charge(r1), 100)
    problem.add_goal(is_at(l5, r1))
    plan = unified_planning.plan.SequentialPlan([unified_planning.plan.ActionInstance(move_2, (ObjectExp(r1), ObjectExp(l1), ObjectExp(l3))),
                                unified_planning.plan.ActionInstance(move_2, (ObjectExp(r1), ObjectExp(l3), ObjectExp(l5)))])
    robot_locations_connected = Example(problem=problem, plan=plan)
    problems['robot_locations_connected'] = robot_locations_connected

    #robot locations visited
    Location = UserType('Location')
    Robot = UserType('Robot')
    is_at = Fluent('is_at', BoolType(), [Location, Robot])
    battery_charge = Fluent('battery_charge', RealType(0, 100), [Robot])
    is_connected = Fluent('is_connected', BoolType(), [Location, Location])
    visited = Fluent('visited', BoolType(), [Location])
    move = InstantaneousAction('move', robot=Robot, l_from=Location, l_to=Location)
    robot = move.parameter('robot')
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    move.add_precondition(GE(battery_charge(robot), 10))
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(is_at(l_from, robot))
    move.add_precondition(Not(is_at(l_to, robot)))
    move.add_precondition(Or(is_connected(l_from, l_to), is_connected(l_to, l_from)))
    move.add_effect(is_at(l_from, robot), False)
    move.add_effect(is_at(l_to, robot), True)
    move.add_effect(visited(l_to), True)
    move.add_decrease_effect(battery_charge(robot), 10)
    move_2 = InstantaneousAction('move_2', robot=Robot, l_from=Location, l_to=Location)
    robot = move_2.parameter('robot')
    l_from = move_2.parameter('l_from')
    l_to = move_2.parameter('l_to')
    move_2.add_precondition(GE(battery_charge(robot), 15))
    move_2.add_precondition(Not(Equals(l_from, l_to)))
    move_2.add_precondition(is_at(l_from, robot))
    move_2.add_precondition(Not(is_at(l_to, robot)))
    mid_location = Variable('mid_loc', Location)
    #(E (location mid_location)
    # !((mid_location == l_from) || (mid_location == l_to)) && (is_connected(l_from, mid_location) || is_connected(mid_location, l_from)) &&
    # && (is_connected(l_to, mid_location) || is_connected(mid_location, l_to)))
    move_2.add_precondition(Exists(And(Not(Or(Equals(mid_location, l_from), Equals(mid_location, l_to))),
                            Or(is_connected(l_from, mid_location), is_connected(mid_location, l_from)),
                            Or(is_connected(l_to, mid_location), is_connected(mid_location, l_to))), mid_location))
    move_2.add_effect(is_at(l_from, robot), False)
    move_2.add_effect(is_at(l_to, robot), True)
    move_2.add_effect(visited(l_to), True)
    move_2.add_decrease_effect(battery_charge(robot), 15)
    l1 = Object('l1', Location)
    l2 = Object('l2', Location)
    l3 = Object('l3', Location)
    l4 = Object('l4', Location)
    l5 = Object('l5', Location)
    r1 = Object('r1', Robot)
    problem = Problem('robot_locations_visited')
    problem.add_fluent(is_at, default_initial_value=False)
    problem.add_fluent(battery_charge)
    problem.add_fluent(is_connected, default_initial_value=False)
    problem.add_fluent(visited, default_initial_value=False)
    problem.add_action(move)
    problem.add_action(move_2)
    problem.add_object(r1)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.add_object(l3)
    problem.add_object(l4)
    problem.add_object(l5)
    problem.set_initial_value(is_at(l1, r1), True)
    problem.set_initial_value(visited(l1), True)
    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l2, l3), True)
    problem.set_initial_value(is_connected(l3, l4), True)
    problem.set_initial_value(is_connected(l4, l5), True)
    problem.set_initial_value(battery_charge(r1), 50)
    problem.add_goal(is_at(l5, r1))
    visited_location = Variable('visited_loc', Location)
    problem.add_goal(Forall(visited(visited_location) , visited_location))
    plan = unified_planning.plan.SequentialPlan([unified_planning.plan.ActionInstance(move, (ObjectExp(r1), ObjectExp(l1), ObjectExp(l2))),
                                unified_planning.plan.ActionInstance(move, (ObjectExp(r1), ObjectExp(l2), ObjectExp(l3))),
                                unified_planning.plan.ActionInstance(move, (ObjectExp(r1), ObjectExp(l3), ObjectExp(l4))),
                                unified_planning.plan.ActionInstance(move, (ObjectExp(r1), ObjectExp(l4), ObjectExp(l5)))])
    robot_locations_visited = Example(problem=problem, plan=plan)
    problems['robot_locations_visited'] = robot_locations_visited

    # charger_discharger
    charger = Fluent('charger')
    b_1 = Fluent('b_1')
    b_2 = Fluent('b_2')
    b_3 = Fluent('b_3')
    charge = InstantaneousAction('charge')
    discharge = InstantaneousAction('discharge')
    charge.add_precondition(Not(charger))
    charge.add_effect(charger, True)
    # !(charger => (b_1 && b_2 && b_3)) in dnf:
    # (charger and !b_1 ) or (charger and !b_2) or (charger and !b_3)
    # which represents the charger is full and at least one battery is not
    discharge.add_precondition(Not(Implies(charger, And(b_1, b_2, b_3))))
    discharge.add_effect(charger, False)
    discharge.add_effect(b_1, True, Not(b_1))
    discharge.add_effect(b_2, True, And(b_1, Not(b_2)))
    discharge.add_effect(b_3, True, And(b_1, b_2, Not(b_3)))
    problem = Problem('charger_discharger')
    problem.add_fluent(charger)
    problem.add_fluent(b_1)
    problem.add_fluent(b_2)
    problem.add_fluent(b_3)
    problem.add_action(charge)
    problem.add_action(discharge)
    problem.set_initial_value(charger, False)
    problem.set_initial_value(b_1, False)
    problem.set_initial_value(b_2, False)
    problem.set_initial_value(b_3, False)
    problem.add_goal(b_1)
    problem.add_goal(b_2)
    problem.add_goal(b_3)
    plan = unified_planning.plan.SequentialPlan([unified_planning.plan.ActionInstance(charge), unified_planning.plan.ActionInstance(discharge),
                unified_planning.plan.ActionInstance(charge), unified_planning.plan.ActionInstance(discharge),
                unified_planning.plan.ActionInstance(charge), unified_planning.plan.ActionInstance(discharge)])
    charge_discharge = Example(problem=problem, plan=plan)
    problems['charge_discharge'] = charge_discharge

    # matchcellar
    Match = UserType('Match')
    Fuse = UserType('Fuse')
    handfree = Fluent('handfree')
    light = Fluent('light')
    match_used = Fluent('match_used', BoolType(), [Match])
    fuse_mended = Fluent('fuse_mended', BoolType(), [Fuse])
    light_match = DurativeAction('light_match', m=Match)
    m = light_match.parameter('m')
    light_match.set_fixed_duration(6)
    light_match.add_condition(StartTiming(), Not(match_used(m)))
    light_match.add_effect(StartTiming(), match_used(m), True)
    light_match.add_effect(StartTiming(), light, True)
    light_match.add_effect(EndTiming(), light, False)
    mend_fuse = DurativeAction('mend_fuse', f=Fuse)
    f = mend_fuse.parameter('f')
    mend_fuse.set_fixed_duration(5)
    mend_fuse.add_condition(StartTiming(), handfree)
    mend_fuse.add_condition(ClosedTimeInterval(StartTiming(), EndTiming()), light)
    mend_fuse.add_effect(StartTiming(), handfree, False)
    mend_fuse.add_effect(EndTiming(), fuse_mended(f), True)
    mend_fuse.add_effect(EndTiming(), handfree, True)
    f1 = Object('f1', Fuse)
    f2 = Object('f2', Fuse)
    f3 = Object('f3', Fuse)
    m1 = Object('m1', Match)
    m2 = Object('m2', Match)
    m3 = Object('m3', Match)
    problem = Problem('MatchCellar')
    problem.add_fluent(handfree)
    problem.add_fluent(light)
    problem.add_fluent(match_used, default_initial_value=False)
    problem.add_fluent(fuse_mended, default_initial_value=False)
    problem.add_action(light_match)
    problem.add_action(mend_fuse)
    problem.add_object(f1)
    problem.add_object(f2)
    problem.add_object(f3)
    problem.add_object(m1)
    problem.add_object(m2)
    problem.add_object(m3)
    problem.set_initial_value(light, False)
    problem.set_initial_value(handfree, True)
    problem.add_goal(fuse_mended(f1))
    problem.add_goal(fuse_mended(f2))
    problem.add_goal(fuse_mended(f3))
    plan = unified_planning.plan.TimeTriggeredPlan([(Fraction(0, 1), unified_planning.plan.ActionInstance(light_match, (ObjectExp(m1), )), Fraction(6, 1)),
                                  (Fraction(1, 100), unified_planning.plan.ActionInstance(mend_fuse, (ObjectExp(f1), )), Fraction(5, 1)),
                                  (Fraction(601, 100), unified_planning.plan.ActionInstance(light_match, (ObjectExp(m2), )), Fraction(6, 1)),
                                  (Fraction(602, 100), unified_planning.plan.ActionInstance(mend_fuse, (ObjectExp(f2), )), Fraction(5, 1)),
                                  (Fraction(1202, 100), unified_planning.plan.ActionInstance(light_match, (ObjectExp(m3), )), Fraction(6, 1)),
                                  (Fraction(1203, 100), unified_planning.plan.ActionInstance(mend_fuse, (ObjectExp(f3), )), Fraction(5, 1))])
    matchcellar = Example(problem=problem, plan=plan)
    problems['matchcellar'] = matchcellar

    # timed connected locations
    Location = UserType('Location')
    is_connected = Fluent('is_connected', BoolType(), [Location, Location])
    is_at = Fluent('is_at', BoolType(), [Location])
    move = DurativeAction('move', l_from=Location, l_to=Location)
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    move.set_fixed_duration(6)
    move.add_condition(StartTiming(), is_at(l_from))
    move.add_condition(StartTiming(), Not(is_at(l_to)))
    mid_location = Variable('mid_loc', Location)
    #(E (location mid_location)
    # !((mid_location == l_from) || (mid_location == l_to)) && (is_connected(l_from, mid_location) || is_connected(mid_location, l_from)) &&
    # && (is_connected(l_to, mid_location) || is_connected(mid_location, l_to)))
    move.add_condition(ClosedTimeInterval(StartTiming(), EndTiming()), Exists(And(Not(Or(Equals(mid_location, l_from), Equals(mid_location, l_to))),
                       Or(is_connected(l_from, mid_location), is_connected(mid_location, l_from)),
                       Or(is_connected(l_to, mid_location), is_connected(mid_location, l_to))), mid_location))
    move.add_condition(StartTiming(), Exists(And(Not(Or(Equals(mid_location, l_from), Equals(mid_location, l_to))),
                       Or(is_connected(l_from, mid_location), is_connected(mid_location, l_from)),
                       Or(is_connected(l_to, mid_location), is_connected(mid_location, l_to))), mid_location))
    move.add_effect(StartTiming(1), is_at(l_from), False)
    move.add_effect(EndTiming(5), is_at(l_to), True)
    l1 = Object('l1', Location)
    l2 = Object('l2', Location)
    l3 = Object('l3', Location)
    l4 = Object('l4', Location)
    l5 = Object('l5', Location)
    problem = Problem('timed_connected_locations')
    problem.add_fluent(is_at, default_initial_value=False)
    problem.add_fluent(is_connected, default_initial_value=False)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.add_object(l3)
    problem.add_object(l4)
    problem.add_object(l5)
    problem.set_initial_value(is_at(l1), True)
    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l2, l3), True)
    problem.set_initial_value(is_connected(l3, l4), True)
    problem.set_initial_value(is_connected(l4, l5), True)
    problem.add_goal(is_at(l5))
    plan = unified_planning.plan.TimeTriggeredPlan([(Fraction(0, 1), unified_planning.plan.ActionInstance(move, (ObjectExp(l1), ObjectExp(l3))), Fraction(6, 1)),
                                  (Fraction(6, 1), unified_planning.plan.ActionInstance(move, (ObjectExp(l3), ObjectExp(l5))), Fraction(6, 1))])
    timed_connected_locations = Example(problem=problem, plan=plan)
    problems['timed_connected_locations'] = timed_connected_locations

    # hierarchical blocks world
    Entity = UserType('Entity', None) # None can be avoided
    Location = UserType('Location', Entity)
    Unmovable = UserType('Unmovable', Location)
    TableSpace = UserType('TableSpace', Unmovable)
    Movable = UserType('Movable', Location)
    Block = UserType('Block', Movable)
    clear = Fluent('clear', BoolType(), [Location])
    on = Fluent('on', BoolType(), [Movable, Location])



    move = InstantaneousAction('move', item=Movable, l_from=Location, l_to=Location)
    item = move.parameter('item')
    l_from = move.parameter('l_from')
    l_to = move.parameter('l_to')
    move.add_precondition(clear(item))
    move.add_precondition(clear(l_to))
    move.add_precondition(on(item, l_from))
    move.add_effect(clear(l_from), True)
    move.add_effect(on(item, l_from), False)
    move.add_effect(clear(l_to), False)
    move.add_effect(on(item, l_to), True)

    problem = Problem('hierarchical_blocks_world')
    problem.add_fluent(clear, default_initial_value=False)
    problem.add_fluent(on, default_initial_value=False)
    problem.add_action(move)
    ts_1 = Object('ts_1', TableSpace)
    ts_2 = Object('ts_2', TableSpace)
    ts_3 = Object('ts_3', TableSpace)
    problem.add_objects([ts_1, ts_2, ts_3])
    block_1 = Object('block_1', Block)
    block_2 = Object('block_2', Block)
    block_3 = Object('block_3', Block)
    problem.add_objects([block_1, block_2, block_3])

    # The blocks are all on ts_1, in order block_3 under block_1 under block_2
    problem.set_initial_value(clear(ts_2), True)
    problem.set_initial_value(clear(ts_3), True)
    problem.set_initial_value(clear(block_2), True)
    problem.set_initial_value(on(block_3, ts_1), True)
    problem.set_initial_value(on(block_1, block_3), True)
    problem.set_initial_value(on(block_2, block_1), True)

    # We want them on ts_3 in order block_3 on block_2 on block_1
    problem.add_goal(on(block_1, ts_3))
    problem.add_goal(on(block_2, block_1))
    problem.add_goal(on(block_3, block_2))

    plan = unified_planning.plan.SequentialPlan([
            unified_planning.plan.ActionInstance(move, (ObjectExp(block_2), ObjectExp(block_1), ObjectExp(ts_2))),
            unified_planning.plan.ActionInstance(move, (ObjectExp(block_1), ObjectExp(block_3), ObjectExp(ts_3))),
            unified_planning.plan.ActionInstance(move, (ObjectExp(block_2), ObjectExp(ts_2), ObjectExp(block_1))),
            unified_planning.plan.ActionInstance(move, (ObjectExp(block_3), ObjectExp(ts_1), ObjectExp(block_2)))])
    hierarchical_blocks_world = Example(problem=problem, plan=plan)
    problems['hierarchical_blocks_world'] = hierarchical_blocks_world





























    place = UserType('place', None)
    hoist = UserType('hoist', None)
    surface = UserType('surface', None)
    #agent = UserType('agent', None)                #questo in depot è sottointeso, per ora lo specifichaimo
    depot = UserType('depot', place)                #ma anche ad agent
    distributor = UserType('distributor', place)    #ma anche ad agent
    #truck = UserType('truck', agent)
    truck = UserType('truck', None)
    crate = UserType('crate', hoist)
    pallet = UserType('pallet', surface)

    myAgent = Fluent('myAgent', None, [truck])
    clear = Fluent('clear', None, [hoist])
    clear_s = Fluent('clear', None, [surface])

    located = Fluent('located', None, [hoist, place])
    at = Fluent('at', None, [truck, place])
    placed = Fluent('placed', None, [pallet, place])
    pos = Fluent('pos', None, [crate, place])       # Non posso utilizzare (place or truck)?
    pos_u = Fluent('pos_u', None, [crate, truck])   # Si può fare in un modo migliore?
    on = Fluent('on', None, [crate, hoist])
    on_u = Fluent('on_u', None, [crate, truck])
    on_s = Fluent('on_s', None, [crate, surface])

    truck0 = Object('truck0', truck)
    truck1 = Object('truck1', truck)

    drive = InstantaneousAction('drive', truck=truck, x=place, y=place)
    truck = drive.parameter('truck')
    x = drive.parameter('x')
    y = drive.parameter('y')

    drive.add_precondition(myAgent(truck))
    # Drive.add_precondition(Equals(myAgent(truck), x)) Non supportato
    # Equality operator is not supported for Boolean terms.Use Iff instead.

    drive.add_precondition(at(truck, x))
    drive.add_effect(at(truck, y), True)

    # Load.add_precondition(pos(crate))
    # Load.add_precondition(Not(clear(crate)))
    load = InstantaneousAction('load', x=place, c=crate, h=hoist)
    c = load.parameter('c')
    # t = load.parameter('t')
    x = load.parameter('x')
    h = load.parameter('h')

    load.add_precondition(myAgent(truck))
    load.add_precondition(at(truck, x))
    # load.add_precondition(clear(truck, h))
    load.add_precondition(pos(c, x))
    load.add_precondition(Not(clear(h)))
    load.add_precondition(Not(clear(c)))
    load.add_precondition(on(c, h))
    load.add_precondition(located(h, x))

    load.add_effect(pos(c, x), True)
    load.add_effect(on(c, h), True)
    load.add_effect(clear(c), False)
    load.add_effect(clear(h), False)
    # load.add_effect(Not(clear(h)))

    unload = InstantaneousAction('unload', x=place, c=crate, h=hoist)
    c = unload.parameter('c')
    # t = load.parameter('t')
    x = unload.parameter('x')
    h = unload.parameter('h')

    unload.add_precondition(myAgent(truck))
    unload.add_precondition(located(h, x))
    load.add_precondition(at(truck, x))
    # load.add_precondition(clear(truck, h))
    unload.add_precondition(pos_u(c, truck))
    unload.add_precondition(on_u(c, truck))
    unload.add_precondition(clear(h))
    unload.add_precondition(clear(c))

    unload.add_effect(pos(c, x), True)
    unload.add_effect(on(c, h), True)
    unload.add_effect(clear(c), False)
    unload.add_effect(clear(h), False)


    problem = Problem('depot')
    depot0 = Object('depot0', depot)
    distributor0 = Object('distributor0', distributor)
    distributor1 = Object('distributor1', distributor)

    crate0 = Object('crate0', crate)
    crate1 = Object('crate1', crate)
    pallet0 = Object('pallet0', pallet)
    pallet1 = Object('pallet1', pallet)
    pallet2 = Object('pallet2', pallet)
    hoist0 = Object('hoist0', hoist)
    hoist1 = Object('hoist1', hoist)
    hoist2 = Object('hoist2', hoist)

    problem.add_object(truck0)
    problem.add_object(truck1)
    problem.add_object(depot0)
    problem.add_object(distributor0)
    problem.add_object(distributor1)
    problem.add_object(pallet0)
    problem.add_object(pallet1)
    problem.add_object(pallet2)
    problem.add_object(hoist0)
    problem.add_object(hoist1)
    problem.add_object(hoist2)

    problem.add_action(drive)
    problem.add_action(load)
    problem.add_action(unload)

    problem.add_fluent(myAgent, default_initial_value=False)
    problem.add_fluent(clear, default_initial_value=False)


    problem.add_fluent(located, default_initial_value=False)
    problem.add_fluent(at, default_initial_value=False)
    problem.add_fluent(placed, default_initial_value=False)
    problem.add_fluent(pos, default_initial_value=False)
    problem.add_fluent(pos_u, default_initial_value=False)
    problem.add_fluent(on_u, default_initial_value=False)
    problem.add_fluent(on, default_initial_value=False)

    #add_shared_data def in problem, in realistic decido gli shared data
    #Non è possibile definire dopo clear, at, ecc.. perchè non sono
    #nella lista fluents

    #possibile soluzione prenderli dai predicati e decidere quali sono
    #gli shared data in ma_realistic, in questo caso def
    #add_shared_data in ma_problem

    '''problem.add_shared_data(clear)
    problem.add_shared_data(at)
    problem.add_shared_data(pos)
    problem.add_shared_data(pos_u)
    problem.add_shared_data(on)
    problem.add_shared_data(on_u)
    problem.add_shared_data(on_s)

    print("wwwwwwwwwwwwwwwwww", problem.get_shared_data())'''



    problem.set_initial_value(myAgent(truck0), True)
    problem.set_initial_value(pos(crate0, distributor0), True)
    problem.set_initial_value(clear(crate0), True)
    problem.set_initial_value(on_s(crate0, pallet1), True)
    problem.set_initial_value(pos(crate1, depot0), True)
    problem.set_initial_value(clear(crate1), True)
    problem.set_initial_value(on_s(crate1, pallet0), True)
    problem.set_initial_value(at(truck0, distributor1), True)
    problem.set_initial_value(at(truck1, depot0), True)
    problem.set_initial_value(located(hoist0, depot0), True)
    problem.set_initial_value(clear(hoist0), True)
    problem.set_initial_value(located(hoist1, distributor0), True)
    problem.set_initial_value(clear(hoist1), True)
    problem.set_initial_value(located(hoist2, distributor1), True)
    problem.set_initial_value(clear(hoist2), True)
    problem.set_initial_value(placed(pallet0, depot0), True)
    problem.set_initial_value(Not(clear_s(pallet0)), True)
    problem.set_initial_value(placed(pallet1, distributor0), True)
    problem.set_initial_value(Not(clear_s(pallet1)), True)
    problem.set_initial_value(placed(pallet2, distributor1), True)
    problem.set_initial_value(clear_s(pallet2), True)
    # problem.set_initial_value(at(truck0, distributor1), True)

    problem.add_goal(on_s(crate0, pallet2))
    problem.add_goal(on_s(crate1, pallet1))
    plan = None
    depot = Example(problem=problem, plan=plan)
    problems['depot'] = depot


    return problems

#get_example_problems()