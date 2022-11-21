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

Example = namedtuple("Example", ["problem", "plan"])


def get_example_problems():
    problems = {}

    # robot_real_constants
    # this version of the problem robot has reals instead of integers as constants
    Location = UserType("Location")
    robot_at = Fluent("robot_at", BoolType(), position=Location)
    battery_charge = Fluent("battery_charge", RealType(0, 100))
    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(GE(battery_charge, 10.0))
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(robot_at(l_from))
    move.add_precondition(Not(robot_at(l_to)))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    move.add_effect(battery_charge, Minus(battery_charge, 10.0))
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem = Problem("robot_real_constants")
    problem.add_fluent(robot_at)
    problem.add_fluent(battery_charge)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    problem.set_initial_value(battery_charge, 100.0)
    problem.add_goal(robot_at(l2))
    plan = unified_planning.plans.SequentialPlan(
        [unified_planning.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2)))]
    )
    robot_example = Example(problem=problem, plan=plan)
    problems["robot_real_constants"] = robot_example

    # robot_int_battery
    # this version of the problem robot has the battery charge fluent represented as an int instead of a real
    Location = UserType("Location")
    robot_at = Fluent("robot_at", BoolType(), position=Location)
    battery_charge = Fluent("battery_charge", IntType(0, 100))
    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(GE(battery_charge, 10))
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(robot_at(l_from))
    move.add_precondition(Not(robot_at(l_to)))
    move.add_effect(robot_at(l_from), False)
    move.add_effect(robot_at(l_to), True)
    move.add_effect(battery_charge, Minus(battery_charge, 10))
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem = Problem("robot_int_battery")
    problem.add_fluent(robot_at)
    problem.add_fluent(battery_charge)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(robot_at(l1), True)
    problem.set_initial_value(robot_at(l2), False)
    problem.set_initial_value(battery_charge, 100)
    problem.add_goal(robot_at(l2))
    plan = unified_planning.plans.SequentialPlan(
        [unified_planning.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l2)))]
    )
    robot_example = Example(problem=problem, plan=plan)
    problems["robot_int_battery"] = robot_example

    # robot fluent of user_type with int ID
    Int_t = IntType(0, 1)
    Location = UserType("Location")
    is_at = Fluent("is_at", Location, id=Int_t)
    move = InstantaneousAction("move", robot=Int_t, l_from=Location, l_to=Location)
    robot = move.parameter("robot")
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(Equals(is_at(robot), l_from))
    move.add_precondition(Not(Equals(is_at(robot), l_to)))
    move.add_effect(is_at(robot), l_to)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem = Problem("robot_fluent_of_user_type_with_int_id")
    problem.add_fluent(is_at)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(is_at(Int(0)), l1)
    problem.set_initial_value(is_at(1), l1)
    plan = unified_planning.plans.SequentialPlan(
        [
            unified_planning.plans.ActionInstance(
                move, (Int(0), ObjectExp(l1), ObjectExp(l2))
            ),
            unified_planning.plans.ActionInstance(
                move, (Int(1), ObjectExp(l1), ObjectExp(l2))
            ),
        ]
    )
    robot_fluent_of_user_type_with_int_id = Example(problem=problem, plan=plan)
    problems[
        "robot_fluent_of_user_type_with_int_id"
    ] = robot_fluent_of_user_type_with_int_id

    # robot locations connected without battery
    Location = UserType("Location")
    Robot = UserType("Robot")
    is_at = Fluent("is_at", BoolType(), position=Location, robot=Robot)
    is_connected = Fluent(
        "is_connected", BoolType(), location_1=Location, location_2=Location
    )
    move = InstantaneousAction("move", robot=Robot, l_from=Location, l_to=Location)
    robot = move.parameter("robot")
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(is_at(l_from, robot))
    move.add_precondition(Not(is_at(l_to, robot)))
    move.add_precondition(Or(is_connected(l_from, l_to), is_connected(l_to, l_from)))
    move.add_effect(is_at(l_from, robot), False)
    move.add_effect(is_at(l_to, robot), True)
    move_2 = InstantaneousAction("move_2", robot=Robot, l_from=Location, l_to=Location)
    robot = move_2.parameter("robot")
    l_from = move_2.parameter("l_from")
    l_to = move_2.parameter("l_to")
    move_2.add_precondition(Not(Equals(l_from, l_to)))
    move_2.add_precondition(is_at(l_from, robot))
    move_2.add_precondition(Not(is_at(l_to, robot)))
    mid_location = Variable("mid_loc", Location)
    # (E (location mid_location)
    # !((mid_location == l_from) || (mid_location == l_to)) && (is_connected(l_from, mid_location) || is_connected(mid_location, l_from)) &&
    # && (is_connected(l_to, mid_location) || is_connected(mid_location, l_to)))
    move_2.add_precondition(
        Exists(
            And(
                Not(Or(Equals(mid_location, l_from), Equals(mid_location, l_to))),
                Or(
                    is_connected(l_from, mid_location),
                    is_connected(mid_location, l_from),
                ),
                Or(is_connected(l_to, mid_location), is_connected(mid_location, l_to)),
            ),
            mid_location,
        )
    )
    move_2.add_effect(is_at(l_from, robot), False)
    move_2.add_effect(is_at(l_to, robot), True)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    l3 = Object("l3", Location)
    l4 = Object("l4", Location)
    l5 = Object("l5", Location)
    r1 = Object("r1", Robot)
    problem = Problem("robot_locations_connected_without_battery")
    problem.add_fluent(is_at, default_initial_value=False)
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
    problem.add_goal(is_at(l5, r1))
    plan = unified_planning.plans.SequentialPlan(
        [
            unified_planning.plans.ActionInstance(
                move_2, (ObjectExp(r1), ObjectExp(l1), ObjectExp(l3))
            ),
            unified_planning.plans.ActionInstance(
                move_2, (ObjectExp(r1), ObjectExp(l3), ObjectExp(l5))
            ),
        ]
    )
    robot_locations_connected_without_battery = Example(problem=problem, plan=plan)
    problems[
        "robot_locations_connected_without_battery"
    ] = robot_locations_connected_without_battery

    # hierarchical blocks world exists
    Entity = UserType("Entity", None)  # None can be avoided
    Location = UserType("Location", Entity)
    Unmovable = UserType("Unmovable", Location)
    TableSpace = UserType("TableSpace", Unmovable)
    Movable = UserType("Movable", Location)
    Block = UserType("Block", Movable)
    clear = Fluent("clear", BoolType(), space=Location)
    on = Fluent("on", BoolType(), object=Movable, space=Location)

    move = InstantaneousAction("move", item=Movable, l_from=Location, l_to=Location)
    item = move.parameter("item")
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(clear(item))
    move.add_precondition(clear(l_to))
    move.add_precondition(on(item, l_from))
    move.add_effect(clear(l_from), True)
    move.add_effect(on(item, l_from), False)
    move.add_effect(clear(l_to), False)
    move.add_effect(on(item, l_to), True)

    problem = Problem("hierarchical_blocks_world_exists")
    problem.add_fluent(clear, default_initial_value=False)
    problem.add_fluent(on, default_initial_value=False)
    problem.add_action(move)
    ts_1 = Object("ts_1", TableSpace)
    ts_2 = Object("ts_2", TableSpace)
    ts_3 = Object("ts_3", TableSpace)
    problem.add_objects([ts_1, ts_2, ts_3])
    block_1 = Object("block_1", Block)
    block_2 = Object("block_2", Block)
    block_3 = Object("block_3", Block)
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
    m_var = Variable("m_var", Movable)
    problem.add_goal(Exists(on(m_var, block_1), m_var))
    problem.add_goal(on(block_3, block_2))

    plan = unified_planning.plans.SequentialPlan(
        [
            unified_planning.plans.ActionInstance(
                move, (ObjectExp(block_2), ObjectExp(block_1), ObjectExp(ts_2))
            ),
            unified_planning.plans.ActionInstance(
                move, (ObjectExp(block_1), ObjectExp(block_3), ObjectExp(ts_3))
            ),
            unified_planning.plans.ActionInstance(
                move, (ObjectExp(block_2), ObjectExp(ts_2), ObjectExp(block_1))
            ),
            unified_planning.plans.ActionInstance(
                move, (ObjectExp(block_3), ObjectExp(ts_1), ObjectExp(block_2))
            ),
        ]
    )
    hierarchical_blocks_world_exists = Example(problem=problem, plan=plan)
    problems["hierarchical_blocks_world_exists"] = hierarchical_blocks_world_exists

    # hierarchical blocks world object as root
    object = UserType("object")
    Entity = UserType("Entity", object)
    Location = UserType("Location", Entity)
    Unmovable = UserType("Unmovable", Location)
    TableSpace = UserType("TableSpace", Unmovable)
    Movable = UserType("Movable", Location)
    Block = UserType("Block", Movable)
    clear = Fluent("clear", BoolType(), space=Location)
    on = Fluent("on", BoolType(), object=Movable, space=Location)

    move = InstantaneousAction("move", item=Movable, l_from=Location, l_to=Location)
    item = move.parameter("item")
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(clear(item))
    move.add_precondition(clear(l_to))
    move.add_precondition(on(item, l_from))
    move.add_effect(clear(l_from), True)
    move.add_effect(on(item, l_from), False)
    move.add_effect(clear(l_to), False)
    move.add_effect(on(item, l_to), True)

    problem = Problem("hierarchical_blocks_world_object_as_root")
    problem.add_fluent(clear, default_initial_value=False)
    problem.add_fluent(on, default_initial_value=False)
    problem.add_action(move)
    ts_1 = Object("ts_1", TableSpace)
    ts_2 = Object("ts_2", TableSpace)
    ts_3 = Object("ts_3", TableSpace)
    problem.add_objects([ts_1, ts_2, ts_3])
    block_1 = Object("block_1", Block)
    block_2 = Object("block_2", Block)
    block_3 = Object("block_3", Block)
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

    plan = unified_planning.plans.SequentialPlan(
        [
            unified_planning.plans.ActionInstance(
                move, (ObjectExp(block_2), ObjectExp(block_1), ObjectExp(ts_2))
            ),
            unified_planning.plans.ActionInstance(
                move, (ObjectExp(block_1), ObjectExp(block_3), ObjectExp(ts_3))
            ),
            unified_planning.plans.ActionInstance(
                move, (ObjectExp(block_2), ObjectExp(ts_2), ObjectExp(block_1))
            ),
            unified_planning.plans.ActionInstance(
                move, (ObjectExp(block_3), ObjectExp(ts_1), ObjectExp(block_2))
            ),
        ]
    )
    hierarchical_blocks_world_object_as_root = Example(problem=problem, plan=plan)
    problems[
        "hierarchical_blocks_world_object_as_root"
    ] = hierarchical_blocks_world_object_as_root

    # hierarchical blocks world with object
    Entity = UserType("Entity", None)  # None can be avoided
    object = UserType("object", Entity)
    Unmovable = UserType("Unmovable", object)
    TableSpace = UserType("TableSpace", Unmovable)
    Movable = UserType("Movable", object)
    Block = UserType("Block", Movable)
    clear = Fluent("clear", BoolType(), space=object)
    on = Fluent("on", BoolType(), object=Movable, space=object)

    move = InstantaneousAction("move", item=Movable, l_from=object, l_to=object)
    item = move.parameter("item")
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(clear(item))
    move.add_precondition(clear(l_to))
    move.add_precondition(on(item, l_from))
    move.add_effect(clear(l_from), True)
    move.add_effect(on(item, l_from), False)
    move.add_effect(clear(l_to), False)
    move.add_effect(on(item, l_to), True)

    problem = Problem("hierarchical_blocks_world_with_object")
    problem.add_fluent(clear, default_initial_value=False)
    problem.add_fluent(on, default_initial_value=False)
    problem.add_action(move)
    ts_1 = Object("ts_1", TableSpace)
    ts_2 = Object("ts_2", TableSpace)
    ts_3 = Object("ts_3", TableSpace)
    problem.add_objects([ts_1, ts_2, ts_3])
    block_1 = Object("block_1", Block)
    block_2 = Object("block_2", Block)
    block_3 = Object("block_3", Block)
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

    plan = unified_planning.plans.SequentialPlan(
        [
            unified_planning.plans.ActionInstance(
                move, (ObjectExp(block_2), ObjectExp(block_1), ObjectExp(ts_2))
            ),
            unified_planning.plans.ActionInstance(
                move, (ObjectExp(block_1), ObjectExp(block_3), ObjectExp(ts_3))
            ),
            unified_planning.plans.ActionInstance(
                move, (ObjectExp(block_2), ObjectExp(ts_2), ObjectExp(block_1))
            ),
            unified_planning.plans.ActionInstance(
                move, (ObjectExp(block_3), ObjectExp(ts_1), ObjectExp(block_2))
            ),
        ]
    )
    hierarchical_blocks_world_with_object = Example(problem=problem, plan=plan)
    problems[
        "hierarchical_blocks_world_with_object"
    ] = hierarchical_blocks_world_with_object

    # travel with consumptions
    problem = Problem("travel_with_consumptions")

    Location = UserType("Location")

    is_at = Fluent("is_at", BoolType(), position=Location)
    is_connected = Fluent("is_connected", BoolType(), l_from=Location, l_to=Location)
    travel_time = Fluent("travel_time", IntType(0, 500), l_from=Location, l_to=Location)
    road_consumption_factor = Fluent(
        "road_consumption_factor", IntType(5, 100), l_from=Location, l_to=Location
    )
    total_travel_time = Fluent("total_travel_time", IntType())
    total_fuel_consumption = Fluent("total_fuel_consumption", IntType())

    problem.add_fluent(is_at, default_initial_value=False)
    problem.add_fluent(is_connected, default_initial_value=False)
    problem.add_fluent(travel_time, default_initial_value=500)
    problem.add_fluent(road_consumption_factor, default_initial_value=100)
    problem.add_fluent(total_travel_time, default_initial_value=0)
    problem.add_fluent(total_fuel_consumption, default_initial_value=0)

    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(is_at(l_from))
    move.add_precondition(is_connected(l_from, l_to))
    move.add_effect(is_at(l_from), False)
    move.add_effect(is_at(l_to), True)
    move.add_increase_effect(total_travel_time, travel_time(l_from, l_to))
    move.add_increase_effect(
        total_fuel_consumption,
        travel_time(l_from, l_to) * road_consumption_factor(l_from, l_to),
    )
    problem.add_action(move)

    problem.add_quality_metric(
        up.model.metrics.MinimizeExpressionOnFinalState(
            2 * total_fuel_consumption + 50 * total_travel_time
        )
    )

    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    l3 = Object("l3", Location)
    l4 = Object("l4", Location)
    l5 = Object("l5", Location)
    problem.add_objects([l1, l2, l3, l4, l5])

    problem.set_initial_value(is_at(l1), True)
    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l2, l3), True)
    problem.set_initial_value(is_connected(l1, l3), True)
    problem.set_initial_value(is_connected(l3, l4), True)
    problem.set_initial_value(is_connected(l4, l5), True)
    problem.set_initial_value(is_connected(l3, l5), True)
    problem.set_initial_value(travel_time(l1, l2), 60)
    problem.set_initial_value(travel_time(l2, l3), 70)
    problem.set_initial_value(travel_time(l1, l3), 100)
    problem.set_initial_value(travel_time(l3, l4), 100)
    problem.set_initial_value(travel_time(l4, l5), 120)
    problem.set_initial_value(travel_time(l3, l5), 200)
    problem.set_initial_value(road_consumption_factor(l1, l2), 30)
    problem.set_initial_value(road_consumption_factor(l2, l3), 27)
    problem.set_initial_value(road_consumption_factor(l1, l3), 50)
    problem.set_initial_value(road_consumption_factor(l3, l4), 15)
    problem.set_initial_value(road_consumption_factor(l4, l5), 13)
    problem.set_initial_value(road_consumption_factor(l3, l5), 40)

    problem.add_goal(is_at(l5))

    plan = up.plans.SequentialPlan(
        [
            up.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l3))),
            up.plans.ActionInstance(move, (ObjectExp(l3), ObjectExp(l4))),
            up.plans.ActionInstance(move, (ObjectExp(l4), ObjectExp(l5))),
        ]
    )
    travel_with_consumptions = Example(problem=problem, plan=plan)
    problems["travel_with_consumptions"] = travel_with_consumptions

    return problems
