import math
import os
from unified_planning.shortcuts import *

t_robot = MovableType("robot")

occ_map = OccupancyMap(
    os.path.join("../notebooks", "maps", "office-map-1.yaml"), (0, 0)
)

t_robot_config = ConfigurationType("robot_config", occ_map, 3)
t_parcel = UserType("parcel")

robot_at = Fluent("robot_at", BoolType(), robot=t_robot, configuration=t_robot_config)
parcel_at = Fluent(
    "parcel_at", BoolType(), parcel=t_parcel, configuration=t_robot_config
)
carries = Fluent("carries", BoolType(), robot=t_robot, parcel=t_parcel)

park1 = ConfigurationObject("parking-1", t_robot_config, (46.0, 26.0, 3 * math.pi / 2))
park2 = ConfigurationObject("parking-2", t_robot_config, (40.0, 26.0, 3 * math.pi / 2))

office1 = ConfigurationObject("office-1", t_robot_config, (4.0, 4.0, 3 * math.pi / 2))
office2 = ConfigurationObject("office-2", t_robot_config, (14.0, 4.0, math.pi / 2))
office3 = ConfigurationObject("office-3", t_robot_config, (24.0, 4.0, 3 * math.pi / 2))
office4 = ConfigurationObject("office-4", t_robot_config, (32.0, 4.0, 3 * math.pi / 2))
office5 = ConfigurationObject("office-5", t_robot_config, (4.0, 24.0, 3 * math.pi / 2))
office6 = ConfigurationObject("office-6", t_robot_config, (14.0, 24.0, math.pi / 2))
office7 = ConfigurationObject("office-7", t_robot_config, (24.0, 24.0, math.pi / 2))
office8 = ConfigurationObject("office-8", t_robot_config, (32.0, 24.0, math.pi / 2))

r1 = MovableObject(
    "robot-1",
    t_robot,
    footprint=[(-1.0, 0.5), (1.0, 0.5), (1.0, -0.5), (-1.0, -0.5)],
    motion_model=MotionModels.REEDSSHEPP,
    parameters={"turning_radius": 2.0},
)

r2 = MovableObject(
    "robot-2",
    t_robot,
    footprint=[(-1.0, 0.5), (1.0, 0.5), (1.0, -0.5), (-1.0, -0.5)],
    motion_model=MotionModels.REEDSSHEPP,
    parameters={"turning_radius": 2.0},
)

nothing = Object("nothing", t_parcel)
p1 = Object("parcel-1", t_parcel)
p2 = Object("parcel-2", t_parcel)

move = InstantaneousMotionAction(
    "move", robot=t_robot, c_from=t_robot_config, c_to=t_robot_config
)
robot = move.parameter("robot")
c_from = move.parameter("c_from")
c_to = move.parameter("c_to")
move.add_precondition(robot_at(robot, c_from))
move.add_effect(robot_at(robot, c_from), False)
move.add_effect(robot_at(robot, c_to), True)
move.add_motion_constraint(Waypoints(robot, c_from, [c_to]))

pick = InstantaneousMotionAction(
    "pick", robot=t_robot, loc=t_robot_config, parcel=t_parcel
)
pick_robot = pick.parameter("robot")
pick_loc = pick.parameter("loc")
pick_parcel = pick.parameter("parcel")
pick.add_precondition(robot_at(pick_robot, pick_loc))
pick.add_precondition(parcel_at(pick_parcel, pick_loc))
pick.add_precondition(carries(pick_robot, nothing))
pick.add_precondition(Not(carries(pick_robot, pick_parcel)))
pick.add_effect(carries(pick_robot, pick_parcel), True)
pick.add_effect(parcel_at(pick_parcel, pick_loc), False)
pick.add_effect(carries(pick_robot, nothing), False)


place = InstantaneousMotionAction(
    "place", robot=t_robot, loc=t_robot_config, parcel=t_parcel
)
place_robot = place.parameter("robot")
place_loc = place.parameter("loc")
place_parcel = place.parameter("parcel")
place.add_precondition(robot_at(place_robot, place_loc))
place.add_precondition(carries(place_robot, place_parcel))
place.add_precondition(Not(parcel_at(place_parcel, place_loc)))
place.add_precondition(Not(carries(place_robot, nothing)))
place.add_effect(carries(place_robot, place_parcel), False)
place.add_effect(carries(place_robot, nothing), True)
place.add_effect(parcel_at(place_parcel, place_loc), True)


problem = Problem("tamp")
problem.add_fluent(robot_at, default_initial_value=False)
problem.add_fluent(parcel_at, default_initial_value=False)
problem.add_fluent(carries, default_initial_value=False)
problem.add_action(move)
problem.add_action(pick)
problem.add_action(place)

problem.add_object(park1)
problem.add_object(park2)
problem.add_object(office1)
problem.add_object(office2)
problem.add_object(office3)
problem.add_object(office4)
problem.add_object(office5)
problem.add_object(office6)
problem.add_object(office7)
problem.add_object(office8)

problem.add_object(r1)
problem.add_object(r2)

problem.add_object(nothing)
problem.add_object(p1)
problem.add_object(p2)

problem.set_initial_value(carries(r1, nothing), True)
problem.set_initial_value(carries(r2, nothing), True)

problem.set_initial_value(parcel_at(p1, office1), True)
problem.set_initial_value(parcel_at(p2, office6), True)

problem.set_initial_value(robot_at(r1, park1), True)

problem.add_goal(robot_at(r1, park1))
problem.add_goal(parcel_at(p1, office2))
problem.add_goal(parcel_at(p2, office3))
