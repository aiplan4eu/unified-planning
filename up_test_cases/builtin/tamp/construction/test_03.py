import math
import os
from unified_planning.shortcuts import *
from unified_planning.test import TestCase

FILE_PATH = os.path.dirname(os.path.abspath(__file__))


def get_test_cases():

    res = {}

    t_robot = MovableType("robot")

    occ_map = OccupancyMap(
        os.path.join(FILE_PATH, "maps", "simple-construction-map.yaml"), (0, 0)
    )

    t_robot_config = ConfigurationType("robot_config", occ_map, 3)
    t_material = UserType("material")

    robot_at = Fluent(
        "robot_at", BoolType(), robot=t_robot, configuration=t_robot_config
    )
    material_at = Fluent(
        "material_at", BoolType(), material=t_material, configuration=t_robot_config
    )
    provider = Fluent(
        "provider", BoolType(), locaction=t_robot_config, material=t_material
    )
    consumer = Fluent(
        "consumer", BoolType(), locaction=t_robot_config, material=t_material
    )
    loaded = Fluent("loaded", BoolType(), robot=t_robot, material=t_material)
    connected = Fluent(
        "connected", BoolType(), loc_a=t_robot_config, loc_b=t_robot_config
    )
    occupied = Fluent("occupied", BoolType(), loc=t_robot_config)

    queue1 = ConfigurationObject("queue-1", t_robot_config, (10.306, 46.206, -3.111))
    queue2 = ConfigurationObject("queue-2", t_robot_config, (14.120, 46.213, -3.136))
    queue3 = ConfigurationObject("queue-3", t_robot_config, (17.606, 42.904, 2.245))

    dump1 = ConfigurationObject("dump-1", t_robot_config, (39.724, 37.334, 2.344))

    park1 = ConfigurationObject("parking-1", t_robot_config, (34.935, 4.191, 1.542))
    park2 = ConfigurationObject("parking-2", t_robot_config, (40.102, 4.374, 1.539))
    park3 = ConfigurationObject("parking-3", t_robot_config, (44.537, 4.068, 1.540))

    truck1 = MovableObject(
        "truck1",
        t_robot,
        footprint=[(-1.0, 0.5), (1.0, 0.5), (1.0, -0.5), (-1.0, -0.5)],
        motion_model=MotionModels.REEDSSHEPP,
        parameters={"turning_radius": 2.0},
    )

    truck2 = MovableObject(
        "truck2",
        t_robot,
        footprint=[(-1.0, 0.5), (1.0, 0.5), (1.0, -0.5), (-1.0, -0.5)],
        motion_model=MotionModels.REEDSSHEPP,
        parameters={"turning_radius": 2.0},
    )

    truck3 = MovableObject(
        "truck3",
        t_robot,
        footprint=[(-1.0, 0.5), (1.0, 0.5), (1.0, -0.5), (-1.0, -0.5)],
        motion_model=MotionModels.REEDSSHEPP,
        parameters={"turning_radius": 2.0},
    )

    nothing = Object("nothing", t_material)
    m1 = Object("sand", t_material)
    m2 = Object("cement", t_material)
    m3 = Object("planks", t_material)

    move = InstantaneousMotionAction(
        "move", robot=t_robot, c_from=t_robot_config, c_to=t_robot_config
    )
    robot = move.parameter("robot")
    c_from = move.parameter("c_from")
    c_to = move.parameter("c_to")
    move.add_precondition(robot_at(robot, c_from))
    move.add_precondition(connected(c_from, c_to))
    move.add_precondition(occupied(c_from))
    move.add_precondition(Not(occupied(c_to)))
    move.add_effect(robot_at(robot, c_from), False)
    move.add_effect(robot_at(robot, c_to), True)
    move.add_effect(occupied(c_from), False)
    move.add_effect(occupied(c_to), True)

    move.add_motion_constraint(Waypoints(robot, c_from, [c_to]))

    load = InstantaneousMotionAction(
        "load", robot=t_robot, loc=t_robot_config, material=t_material
    )
    load_robot = load.parameter("robot")
    load_loc = load.parameter("loc")
    load_material = load.parameter("material")
    load.add_precondition(robot_at(load_robot, load_loc))
    load.add_precondition(provider(load_loc, load_material))
    load.add_precondition(loaded(load_robot, nothing))
    load.add_precondition(Not(loaded(load_robot, load_material)))
    load.add_effect(loaded(load_robot, load_material), True)
    load.add_effect(loaded(load_robot, nothing), False)

    dump = InstantaneousMotionAction(
        "dump", robot=t_robot, loc=t_robot_config, material=t_material
    )
    dump_robot = dump.parameter("robot")
    dump_loc = dump.parameter("loc")
    dump_material = dump.parameter("material")
    dump.add_precondition(robot_at(dump_robot, dump_loc))
    dump.add_precondition(consumer(dump_loc, dump_material))
    dump.add_precondition(loaded(dump_robot, dump_material))
    dump.add_precondition(Not(loaded(dump_robot, nothing)))
    dump.add_precondition(Not(material_at(dump_material, dump_loc)))
    dump.add_effect(loaded(dump_robot, dump_material), False)
    dump.add_effect(loaded(dump_robot, nothing), True)
    dump.add_effect(material_at(dump_material, dump_loc), True)

    problem = Problem("construction-test-3")
    problem.add_fluent(robot_at, default_initial_value=False)
    problem.add_fluent(material_at, default_initial_value=False)
    problem.add_fluent(loaded, default_initial_value=False)
    problem.add_fluent(connected, default_initial_value=False)
    problem.add_fluent(provider, default_initial_value=False)
    problem.add_fluent(occupied, default_initial_value=False)
    problem.add_fluent(consumer, default_initial_value=False)

    problem.add_action(move)
    problem.add_action(load)
    problem.add_action(dump)

    problem.add_object(park1)
    problem.add_object(park2)
    problem.add_object(park3)

    problem.add_object(dump1)

    problem.add_object(queue1)
    problem.add_object(queue2)
    problem.add_object(queue3)

    problem.add_object(truck1)
    problem.add_object(truck2)
    problem.add_object(truck3)

    problem.add_object(nothing)
    problem.add_object(m1)
    problem.add_object(m2)
    problem.add_object(m3)

    problem.set_initial_value(connected(queue1, park1), True)
    problem.set_initial_value(connected(queue1, park2), True)
    problem.set_initial_value(connected(queue1, park3), True)
    problem.set_initial_value(connected(queue1, queue3), True)
    problem.set_initial_value(connected(queue1, dump1), True)

    problem.set_initial_value(connected(dump1, park1), True)
    problem.set_initial_value(connected(dump1, park2), True)
    problem.set_initial_value(connected(dump1, park3), True)
    problem.set_initial_value(connected(dump1, queue3), True)

    problem.set_initial_value(connected(park1, dump1), True)
    problem.set_initial_value(connected(park1, queue3), True)
    problem.set_initial_value(connected(park2, dump1), True)
    problem.set_initial_value(connected(park2, queue3), True)
    problem.set_initial_value(connected(park3, dump1), True)
    problem.set_initial_value(connected(park3, queue3), True)

    problem.set_initial_value(consumer(dump1, m1), True)
    problem.set_initial_value(consumer(dump1, m2), True)
    problem.set_initial_value(consumer(dump1, m3), True)

    problem.set_initial_value(connected(queue2, queue1), True)
    problem.set_initial_value(connected(queue3, queue2), True)

    problem.set_initial_value(loaded(truck1, nothing), True)
    problem.set_initial_value(loaded(truck2, nothing), True)
    problem.set_initial_value(loaded(truck3, nothing), True)

    problem.set_initial_value(provider(queue1, m1), True)
    problem.set_initial_value(provider(queue1, m2), True)
    problem.set_initial_value(provider(queue1, m3), True)

    problem.set_initial_value(robot_at(truck1, park1), True)
    problem.set_initial_value(robot_at(truck2, park2), True)
    problem.set_initial_value(robot_at(truck3, park3), True)

    problem.set_initial_value(occupied(park1), True)
    problem.set_initial_value(occupied(park2), True)
    problem.set_initial_value(occupied(park3), True)

    problem.add_goal(robot_at(truck1, park1))
    problem.add_goal(robot_at(truck2, park2))
    problem.add_goal(robot_at(truck3, park3))

    problem.add_goal(material_at(m1, dump1))
    problem.add_goal(material_at(m2, dump1))
    problem.add_goal(material_at(m3, dump1))

    res[problem.name] = TestCase(problem, solvable=True)

    return res
