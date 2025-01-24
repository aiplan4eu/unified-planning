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


from itertools import product
import unified_planning
from unified_planning.shortcuts import *
from unified_planning.test import TestCase


def get_example_problems():
    problems = {}

    # basic_bool_fluent_param
    x = Fluent("x", int_param=BoolType())
    a = InstantaneousAction("a")
    a.add_precondition(Not(x(True)))
    a.add_effect(x(True), True)
    problem = Problem("basic_bool_fluent_param")
    problem.add_fluent(x, default_initial_value=False)
    problem.add_action(a)
    problem.set_initial_value(x(False), True)
    problem.add_goal(And(x(True), x(False)))
    plan = up.plans.SequentialPlan([up.plans.ActionInstance(a)])
    basic_bool_fluent_param = TestCase(
        problem=problem, solvable=True, valid_plans=[plan]
    )
    problems["basic_bool_fluent_param"] = basic_bool_fluent_param

    # basic_int_fluent_param
    int_3_6 = IntType(3, 6)
    x = Fluent("x", int_param=int_3_6)
    a = InstantaneousAction("a")
    a.add_precondition(Not(x(3)))
    a.add_effect(x(3), True)
    problem = Problem("basic_int_fluent_param")
    problem.add_fluent(x, default_initial_value=False)
    problem.add_action(a)
    problem.set_initial_value(x(4), True)
    problem.add_goal(And(x(3), x(4), Not(x(5))))
    plan = up.plans.SequentialPlan([up.plans.ActionInstance(a)])
    basic_int_fluent_param = TestCase(
        problem=problem, solvable=True, valid_plans=[plan]
    )
    problems["basic_int_fluent_param"] = basic_int_fluent_param

    # basic_bounded_int_action_param
    int_3_6 = IntType(3, 6)
    x = Fluent("x", int_param=int_3_6)
    a = InstantaneousAction("a", int_param=int_3_6)
    a.add_precondition(Not(x(a.int_param)))
    a.add_effect(x(a.int_param), True)
    problem = Problem("basic_bounded_int_action_param")
    problem.add_fluent(x, default_initial_value=False)
    problem.add_action(a)
    problem.add_goal(And(x(3), x(4), Not(x(5))))
    plan = up.plans.SequentialPlan(
        [up.plans.ActionInstance(a, (Int(3),)), up.plans.ActionInstance(a, (Int(4),))]
    )
    basic_bounded_int_action_param = TestCase(
        problem=problem, solvable=True, valid_plans=[plan]
    )
    problems["basic_bounded_int_action_param"] = basic_bounded_int_action_param

    # basic_unbounded_int_action_param
    int_3_6 = IntType(3, 6)
    int_3 = IntType(3)
    x = Fluent("x", int_param=int_3_6)
    a = InstantaneousAction("a", int_param=int_3)
    a.add_precondition(Not(x(a.int_param)))
    a.add_effect(x(a.int_param), True)
    problem = Problem("basic_unbounded_int_action_param")
    problem.add_fluent(x, default_initial_value=False)
    problem.add_action(a)
    problem.add_goal(And(x(3), x(4), Not(x(5))))
    plan = up.plans.SequentialPlan(
        [up.plans.ActionInstance(a, (Int(3),)), up.plans.ActionInstance(a, (Int(4),))]
    )
    basic_unbounded_int_action_param = TestCase(
        problem=problem, solvable=True, valid_plans=[plan]
    )
    problems["basic_unbounded_int_action_param"] = basic_unbounded_int_action_param

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
    robot_example = TestCase(problem=problem, solvable=True, valid_plans=[plan])
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
    robot_example = TestCase(problem=problem, solvable=True, valid_plans=[plan])
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
    problem.add_goal(is_at(0).Equals(l2))
    problem.add_goal(is_at(1).Equals(l2))
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
    robot_fluent_of_user_type_with_int_id = TestCase(
        problem=problem, solvable=True, valid_plans=[plan]
    )
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
    robot_locations_connected_without_battery = TestCase(
        problem=problem, solvable=True, valid_plans=[plan]
    )
    problems[
        "robot_locations_connected_without_battery"
    ] = robot_locations_connected_without_battery

    # robot_loader_weak_bridge
    # version of robot loader with weak bridges that can't be crossed with
    # the cargo loaded. Uses global_constraints.
    Location = UserType("Location")
    locations = [Object(f"l{i}", Location) for i in range(1, 4)]
    l1, l2, l3 = locations
    robot_is_at = Fluent("robot_is_at", BoolType(), position=Location)
    robot_was_at = Fluent("robot_was_at", BoolType(), past_position=Location)
    cargo_at = Fluent("cargo_at", BoolType(), position=Location)
    cargo_mounted = Fluent("cargo_mounted")
    weak_bridge = Fluent("weak_bridge", BoolType(), l_from=Location, l_to=Location)

    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(robot_is_at(l_from))
    move.add_precondition(Not(robot_is_at(l_to)))
    move.add_effect(robot_is_at(l_from), False)
    move.add_effect(robot_is_at(l_to), True)
    move.add_effect(robot_was_at(l_from), True)
    for l_obj in locations:  # note that this works for the add-after-delete semantic
        move.add_effect(robot_was_at(l_obj), False)

    load = InstantaneousAction("load", loc=Location)
    loc = load.parameter("loc")
    load.add_precondition(cargo_at(loc))
    load.add_precondition(robot_is_at(loc))
    load.add_precondition(Not(cargo_mounted))
    load.add_effect(cargo_at(loc), False)
    load.add_effect(cargo_mounted, True)
    load.add_effect(robot_was_at(loc), True)
    for l_obj in locations:
        load.add_effect(robot_was_at(l_obj), False)

    unload = InstantaneousAction("unload", loc=Location)
    loc = unload.parameter("loc")
    unload.add_precondition(Not(cargo_at(loc)))
    unload.add_precondition(robot_is_at(loc))
    unload.add_precondition(cargo_mounted)
    unload.add_effect(cargo_at(loc), True)
    unload.add_effect(cargo_mounted, False)
    unload.add_effect(robot_was_at(loc), True)
    for l_obj in locations:
        unload.add_effect(robot_was_at(l_obj), False)

    problem = Problem("robot_loader_weak_bridge")
    problem.add_fluent(robot_is_at, default_initial_value=False)
    problem.add_fluent(robot_was_at, default_initial_value=False)
    problem.add_fluent(cargo_at, default_initial_value=False)
    problem.add_fluent(cargo_mounted, default_initial_value=False)
    problem.add_fluent(weak_bridge, default_initial_value=False)
    problem.add_action(move)
    problem.add_action(load)
    problem.add_action(unload)
    problem.add_objects(locations)
    problem.set_initial_value(robot_is_at(l1), True)
    problem.set_initial_value(robot_was_at(l1), True)
    problem.set_initial_value(cargo_at(l3), True)
    problem.set_initial_value(weak_bridge(l3, l1), True)
    problem.set_initial_value(weak_bridge(l1, l3), True)
    problem.add_goal(cargo_at(l1))
    # for all the possible couples of locations, it must never be True that:
    # The robot is loaded when crossing a weak bridge.
    for l_from_v, l_to_v in product(locations, repeat=2):
        problem.add_state_invariant(
            Not(
                And(
                    weak_bridge(l_from_v, l_to_v),
                    robot_was_at(l_from_v),
                    robot_is_at(l_to_v),
                    cargo_mounted,
                )
            )
        )
    plan = up.plans.SequentialPlan(
        [
            up.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l3))),
            up.plans.ActionInstance(load, (ObjectExp(l3),)),
            up.plans.ActionInstance(move, (ObjectExp(l3), ObjectExp(l2))),
            up.plans.ActionInstance(move, (ObjectExp(l2), ObjectExp(l1))),
            up.plans.ActionInstance(unload, (ObjectExp(l1),)),
        ]
    )
    robot_loader_weak_bridge = TestCase(
        problem=problem, solvable=True, valid_plans=[plan]
    )
    problems["robot_loader_weak_bridge"] = robot_loader_weak_bridge

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
    hierarchical_blocks_world_exists = TestCase(
        problem=problem, solvable=True, valid_plans=[plan]
    )
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
    hierarchical_blocks_world_object_as_root = TestCase(
        problem=problem, solvable=True, valid_plans=[plan]
    )
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
    hierarchical_blocks_world_with_object = TestCase(
        problem=problem, solvable=True, valid_plans=[plan]
    )
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
    travel_with_consumptions = TestCase(
        problem=problem, solvable=True, valid_plans=[plan]
    )
    problems["travel_with_consumptions"] = travel_with_consumptions

    # matchcellar with static duration
    Match = UserType("Match")
    Fuse = UserType("Fuse")
    handfree = Fluent("handfree")
    light = Fluent("light")
    match_durability = Fluent("match_durability", RealType(), match=Match)
    fuse_difficulty = Fluent("fuse_difficulty", RealType(), fuse=Fuse)
    match_used = Fluent("match_used", BoolType(), match=Match)
    fuse_mended = Fluent("fuse_mended", BoolType(), fuse=Fuse)
    light_match = DurativeAction("light_match", m=Match)
    m = light_match.parameter("m")
    light_match.set_fixed_duration(match_durability(m))
    light_match.add_condition(StartTiming(), Not(match_used(m)))
    light_match.add_effect(StartTiming(), match_used(m), True)
    light_match.add_effect(StartTiming(), light, True)
    light_match.add_effect(EndTiming(), light, False)
    mend_fuse = DurativeAction("mend_fuse", f=Fuse)
    f = mend_fuse.parameter("f")
    mend_fuse.set_fixed_duration(fuse_difficulty(f))
    mend_fuse.add_condition(StartTiming(), handfree)
    mend_fuse.add_condition(ClosedTimeInterval(StartTiming(), EndTiming()), light)
    mend_fuse.add_effect(StartTiming(), handfree, False)
    mend_fuse.add_effect(EndTiming(), fuse_mended(f), True)
    mend_fuse.add_effect(EndTiming(), handfree, True)
    f1 = Object("f1", Fuse)
    f2 = Object("f2", Fuse)
    f3 = Object("f3", Fuse)
    m1 = Object("m1", Match)
    m2 = Object("m2", Match)
    m3 = Object("m3", Match)
    problem = Problem("matchcellar_static_duration")
    problem.add_fluent(handfree)
    problem.add_fluent(light)
    problem.add_fluent(match_durability)
    problem.add_fluent(fuse_difficulty)
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
    problem.set_initial_value(match_durability(m1), 2)
    problem.set_initial_value(match_durability(m2), 3)
    problem.set_initial_value(match_durability(m3), 4)
    problem.set_initial_value(fuse_difficulty(f1), 1)
    problem.set_initial_value(fuse_difficulty(f2), 2)
    problem.set_initial_value(fuse_difficulty(f3), 3)
    problem.add_goal(fuse_mended(f1))
    problem.add_goal(fuse_mended(f2))
    problem.add_goal(fuse_mended(f3))
    t_plan = up.plans.TimeTriggeredPlan(
        [
            (
                Fraction(0, 1),
                up.plans.ActionInstance(light_match, (ObjectExp(m1),)),
                Fraction(2, 1),
            ),
            (
                Fraction(1, 100),
                up.plans.ActionInstance(mend_fuse, (ObjectExp(f1),)),
                Fraction(1, 1),
            ),
            (
                Fraction(201, 100),
                up.plans.ActionInstance(light_match, (ObjectExp(m2),)),
                Fraction(3, 1),
            ),
            (
                Fraction(202, 100),
                up.plans.ActionInstance(mend_fuse, (ObjectExp(f2),)),
                Fraction(2, 1),
            ),
            (
                Fraction(502, 100),
                up.plans.ActionInstance(light_match, (ObjectExp(m3),)),
                Fraction(4, 1),
            ),
            (
                Fraction(503, 100),
                up.plans.ActionInstance(mend_fuse, (ObjectExp(f3),)),
                Fraction(3, 1),
            ),
        ]
    )
    matchcellar_static_duration = TestCase(
        problem=problem, solvable=True, valid_plans=[t_plan]
    )
    problems["matchcellar_static_duration"] = matchcellar_static_duration

    # locations connected visited oversubscription
    Location = UserType("Location")
    is_at = Fluent("is_at", BoolType(), position=Location)
    is_connected = Fluent(
        "is_connected", BoolType(), location_1=Location, location_2=Location
    )
    visited = Fluent("visited", BoolType(), location=Location)
    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(is_at(l_from))
    move.add_precondition(Not(is_at(l_to)))
    move.add_precondition(is_connected(l_from, l_to))
    move.add_effect(is_at(l_from), False)
    move.add_effect(is_at(l_to), True)
    move.add_effect(visited(l_to), True)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    l3 = Object("l3", Location)
    l4 = Object("l4", Location)
    l5 = Object("l5", Location)
    problem = Problem("locations_connected_visited_oversubscription")
    problem.add_fluent(is_at, default_initial_value=False)
    problem.add_fluent(visited, default_initial_value=False)
    problem.add_fluent(is_connected, default_initial_value=False)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.add_object(l3)
    problem.add_object(l4)
    problem.add_object(l5)
    problem.set_initial_value(is_at(l1), True)
    problem.set_initial_value(visited(l1), True)
    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l1, l3), True)
    problem.set_initial_value(is_connected(l1, l5), True)
    problem.set_initial_value(is_connected(l2, l3), True)
    problem.set_initial_value(is_connected(l2, l5), True)
    problem.set_initial_value(is_connected(l3, l4), True)
    problem.set_initial_value(is_connected(l4, l5), True)
    problem.add_goal(is_at(l5))
    loc_var = Variable("loc_var", Location)
    problem.add_quality_metric(
        Oversubscription(
            {
                visited(l2): 9,
                visited(l2) | visited(l3): 5,
                Forall(visited(loc_var) | loc_var.Equals(l2), loc_var)
                & visited(l2).Not(): 10,
            }
        )
    )

    plan = unified_planning.plans.SequentialPlan(
        [
            unified_planning.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l3))),
            unified_planning.plans.ActionInstance(move, (ObjectExp(l3), ObjectExp(l4))),
            unified_planning.plans.ActionInstance(move, (ObjectExp(l4), ObjectExp(l5))),
        ]
    )
    locations_connected_visited_oversubscription = TestCase(
        problem=problem, solvable=True, valid_plans=[plan], optimum=15
    )
    problems[
        "locations_connected_visited_oversubscription"
    ] = locations_connected_visited_oversubscription

    # locations connected cost minimize
    Location = UserType("Location")
    is_at = Fluent("is_at", BoolType(), position=Location)
    is_connected = Fluent(
        "is_connected", BoolType(), location_1=Location, location_2=Location
    )
    distance = Fluent("distance", RealType(), location_1=Location, location_2=Location)
    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(Not(Equals(l_from, l_to)))
    move.add_precondition(is_at(l_from))
    move.add_precondition(Not(is_at(l_to)))
    move.add_precondition(Or(is_connected(l_from, l_to), is_connected(l_to, l_from)))
    move.add_effect(is_at(l_from), False)
    move.add_effect(is_at(l_to), True)
    move_cost = distance(l_from, l_to)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    l3 = Object("l3", Location)
    l4 = Object("l4", Location)
    l5 = Object("l5", Location)
    problem = Problem("locations_connected_cost_minimize")
    problem.add_fluent(is_at, default_initial_value=False)
    problem.add_fluent(is_connected, default_initial_value=False)
    problem.add_fluent(distance, default_initial_value=100)
    problem.add_action(move)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.add_object(l3)
    problem.add_object(l4)
    problem.add_object(l5)
    problem.set_initial_value(is_at(l1), True)
    problem.set_initial_value(is_connected(l1, l2), True)
    problem.set_initial_value(is_connected(l1, l3), True)
    problem.set_initial_value(is_connected(l1, l5), True)
    problem.set_initial_value(is_connected(l2, l3), True)
    problem.set_initial_value(is_connected(l2, l5), True)
    problem.set_initial_value(is_connected(l3, l4), True)
    problem.set_initial_value(is_connected(l4, l5), True)
    problem.set_initial_value(distance(l1, l2), 4)
    problem.set_initial_value(distance(l1, l3), 8)
    problem.set_initial_value(distance(l1, l5), 11)
    problem.set_initial_value(distance(l2, l3), 5)
    problem.set_initial_value(distance(l2, l5), 8)
    problem.set_initial_value(distance(l3, l4), 1)
    problem.set_initial_value(distance(l4, l5), 1)

    problem.set_initial_value(distance(l2, l1), 4)
    problem.set_initial_value(distance(l3, l1), 8)
    problem.set_initial_value(distance(l5, l1), 11)
    problem.set_initial_value(distance(l3, l2), 5)
    problem.set_initial_value(distance(l5, l2), 8)
    problem.set_initial_value(distance(l4, l3), 1)
    problem.set_initial_value(distance(l5, l4), 1)
    problem.add_goal(is_at(l5))
    problem.add_quality_metric(MinimizeActionCosts({move: move_cost}))

    plan = unified_planning.plans.SequentialPlan(
        [
            unified_planning.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l3))),
            unified_planning.plans.ActionInstance(move, (ObjectExp(l3), ObjectExp(l4))),
            unified_planning.plans.ActionInstance(move, (ObjectExp(l4), ObjectExp(l5))),
        ]
    )
    locations_connected_cost_minimize = TestCase(
        problem=problem, solvable=True, valid_plans=[plan], optimum=10
    )
    problems["locations_connected_cost_minimize"] = locations_connected_cost_minimize

    # robot_conditional_effects
    Location = UserType("Location")
    connected = Fluent("connected", BoolType(), l_from=Location, l_to=Location)
    robot_at = Fluent("robot_at", BoolType(), position=Location)
    battery_charge = Fluent("battery_charge", RealType(0, 100))
    move_cond = DurativeAction("move", l_from=Location, l_to=Location)
    l_from = move_cond.parameter("l_from")
    l_to = move_cond.parameter("l_to")
    move_cond.set_fixed_duration(10)
    move_cond.add_condition(StartTiming(), connected(l_from, l_to))
    move_cond.add_condition(StartTiming(), robot_at(l_from))
    move_cond.add_condition(StartTiming(), GE(battery_charge, 10))
    move_cond.add_effect(StartTiming(), robot_at(l_from), False)
    move_cond.add_effect(EndTiming(), robot_at(l_to), True, GE(battery_charge, 10))
    move_cond.add_decrease_continuous_effect(
        ClosedTimeInterval(StartTiming(), EndTiming()),
        battery_charge,
        1,
    )
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem = Problem("robot_conditional_effects")
    problem.add_fluent(robot_at, default_initial_value=False)
    problem.add_fluent(connected, default_initial_value=False)
    problem.add_fluent(battery_charge, default_initial_value=100)
    problem.add_action(move_cond)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(connected(l1, l2), True)
    problem.set_initial_value(robot_at(l1), True)
    problem.add_goal(robot_at(l2))
    problem.add_goal(Equals(battery_charge, 90))
    t_plan = up.plans.TimeTriggeredPlan(
        [
            (
                Fraction(0, 1),
                up.plans.ActionInstance(move_cond, (ObjectExp(l1), ObjectExp(l2))),
                Fraction(10, 1),
            )
        ]
    )
    robot_conditional_effects = TestCase(
        problem=problem, solvable=True, valid_plans=[t_plan]
    )
    problems["robot_conditional_effects"] = robot_conditional_effects

    # robot_non_linear_continuous_1
    Location = UserType("Location")
    connected = Fluent("connected", BoolType(), l_from=Location, l_to=Location)
    robot_at = Fluent("robot_at", BoolType(), position=Location)
    battery_charge = Fluent("battery_charge", RealType(0, 100))
    derivative = Fluent("derivative", RealType())
    move_non_lin = DurativeAction("move", l_from=Location, l_to=Location)
    l_from = move_non_lin.parameter("l_from")
    l_to = move_non_lin.parameter("l_to")
    move_non_lin.set_fixed_duration(10)
    move_non_lin.add_condition(StartTiming(), connected(l_from, l_to))
    move_non_lin.add_condition(StartTiming(), robot_at(l_from))
    move_non_lin.add_effect(StartTiming(), robot_at(l_from), False)
    move_non_lin.add_effect(EndTiming(), robot_at(l_to), True)
    move_non_lin.add_decrease_continuous_effect(
        ClosedTimeInterval(StartTiming(), EndTiming()), battery_charge, derivative
    )
    move_non_lin.add_increase_continuous_effect(
        ClosedTimeInterval(StartTiming(), EndTiming()), derivative, Fraction(1, 10)
    )
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem = Problem("robot_non_linear_continuous_1")
    problem.add_fluent(robot_at, default_initial_value=False)
    problem.add_fluent(connected, default_initial_value=False)
    problem.add_fluent(battery_charge, default_initial_value=100)
    problem.add_fluent(derivative, default_initial_value=0)
    problem.add_action(move_non_lin)
    problem.add_object(l1)
    problem.add_object(l2)
    problem.set_initial_value(connected(l1, l2), True)
    problem.set_initial_value(robot_at(l1), True)
    problem.add_goal(robot_at(l2))
    problem.add_goal(Equals(battery_charge, 95))
    t_plan = up.plans.TimeTriggeredPlan(
        [
            (
                Fraction(0, 1),
                up.plans.ActionInstance(move_non_lin, (ObjectExp(l1), ObjectExp(l2))),
                Fraction(10, 1),
            )
        ]
    )
    robot_non_linear_continuous_1 = TestCase(
        problem=problem, solvable=True, valid_plans=[t_plan]
    )
    problems["robot_non_linear_continuous_1"] = robot_non_linear_continuous_1

    return problems
