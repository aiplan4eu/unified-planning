from unified_planning.model.type_manager import TypeManager

from unified_planning.model.tamp.types import OccupancyMap

from unified_planning.model import Fluent, Object, Problem
from unified_planning.shortcuts import BoolType
from unified_planning.model.tamp import InstantaneousMotionAction, Waypoints

#Note that we moved all TAMP-related things into a separate package
from unified_planning.model.tamp import ConfigurationObject, MotionModels, MovableObject
from unified_planning.test import TestCase


class TestProblem(TestCase):
    def setUp(self):
        TestCase.setUp(self)

    def test_tamp_problem(self):
        tm = TypeManager()
        # assumptions:
        # 1. the world is deterministic
        # 2. the world is completely known
        # 3. the moveable object (e.g., the robot) moves in a map composed of fixed obstacles
        # 4. there is one common reference system (e.g., /world (0.0, 0.0, 0.0)) - that is the reference system of the map

        Robot = tm.MovableType("robot")

        # representation of the free and occupied working space, fixed obstacles are located on the occupied areas (e.g., Octomap)
        map = tm,OccupancyMap("./maps/test-map.yaml", (0, 0))


        # representation of the state of a movable object
        # the input is equals to the number of variables useful to define this state
        # (e.g., 3 = [x, y, yaw] - N = [N-DOFs of a robot])
        RobotConfig = tm.ConfigurationType("robot_config", map, 3)

        robot_at = Fluent("robot_at", tm.BoolType(), robot=Robot, configuration=RobotConfig)


        # configurations in the map
        # map and RobotConfig added for consistency check
        # e.g., `c1` is a configuration expressed via 5 variables and is a collision free configuration in `map`
        c1 = ConfigurationObject("c1", map, RobotConfig, (4.0, 4.0, 0.0))
        c2 = ConfigurationObject("c2", map, RobotConfig, (10.0, 2.0, 0.0))

        r1 = MovableObject("r1", Robot,
                            model="robot.urdf",
                            motion_model=MotionModels.REEDSSHEPP,
                            parameters={'turning_radius': 4.0})

        move = InstantaneousMotionAction("move", robot=Robot, c_from=RobotConfig, c_to=RobotConfig)
        robot = move.parameter("robot")
        c_from = move.parameter("c_from")
        c_to = move.parameter("c_to")
        move.add_precondition(robot_at(robot, c_from))
        move.add_effect(robot_at(robot, c_from), False)
        move.add_effect(robot_at(robot, c_to), True)

        # there exists a motion control in your motion model that lets the moveable object moves from c_from to [c_to],
        # where [c_to] is a set of waypoints in your map
        move.add_motion_constraint(Waypoints(robot, c_from, [c_to]))

        problem = Problem("robot")
        problem.add_fluent(robot_at)
        problem.add_action(move)
        problem.add_object(c1)
        problem.add_object(c2)
        problem.add_object(r1)
        problem.set_initial_value(robot_at(c1), True)
        problem.set_initial_value(robot_at(c2), False)
        problem.add_goal(robot_at(c2))
