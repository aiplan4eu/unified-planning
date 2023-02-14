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


import os
from unified_planning.shortcuts import *
from collections import namedtuple

Example = namedtuple("Example", ["problem", "plan"])

FILE_PATH = os.path.dirname(os.path.abspath(__file__))


def get_example_problems():
    problems = {}

    # assumptions:
    # 1. the world is deterministic
    # 2. the world is completely known
    # 3. the moveable object (e.g., the robot) moves in a map composed of fixed obstacles
    # 4. there is one common reference system (e.g., /world (0.0, 0.0, 0.0)) - that is the reference system of the map

    Robot = MovableType("robot")

    # representation of the free and occupied working space, fixed obstacles are located on the occupied areas (e.g., Octomap)
    map = OccupancyMap(os.path.join(FILE_PATH, "..", "tamp", "test-map.yaml"), (0, 0))

    # representation of the state of a movable object
    # the input is equals to the number of variables useful to define this state
    # (e.g., 3 = [x, y, yaw] - N = [N-DOFs of a robot])
    RobotConfig = ConfigurationType("robot_config", map, 3)

    robot_at = Fluent("robot_at", BoolType(), robot=Robot, configuration=RobotConfig)

    # configurations in the map
    # map and RobotConfig added for consistency check
    # e.g., `c1` is a configuration expressed via 5 variables and is a collision free configuration in `map`
    c1 = ConfigurationObject("c1", RobotConfig, (4.0, 4.0, 0.0))
    c2 = ConfigurationObject("c2", RobotConfig, (26.0, 4.0, 0.0))

    r1 = MovableObject(
        "r1",
        Robot,
        footprint=[(-1.0, 0.5), (1.0, 0.5), (1.0, -0.5), (-1.0, -0.5)],
        motion_model=MotionModels.REEDSSHEPP,
        parameters={"turning_radius": 4.0},
    )

    move = InstantaneousMotionAction(
        "move", robot=Robot, c_from=RobotConfig, c_to=RobotConfig
    )
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
    problem.set_initial_value(robot_at(r1, c1), True)
    problem.set_initial_value(robot_at(r1, c2), False)
    problem.add_goal(robot_at(r1, c2))

    plan = up.plans.SequentialPlan(
        [up.plans.ActionInstance(move, (ObjectExp(r1), ObjectExp(c1), ObjectExp(c2)))]
    )

    tamp_feasible = Example(problem=problem, plan=plan)
    problems["tamp_feasible"] = tamp_feasible

    return problems
