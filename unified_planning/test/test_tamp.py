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
#

from unified_planning.shortcuts import *
from unified_planning.test import unittest_TestCase
from unified_planning.test.examples.tamp import get_example_problems


class TestTAMPProblem(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_tamp_problem_creation(self):
        problem = self.problems["tamp_feasible"].problem
        self.assertTrue(isinstance(problem, Problem))

        self.assertTrue(problem.kind.has_tamp())
        self.assertEqual(1, len(problem.fluents))
        self.assertEqual(1, len(problem.actions))
        self.assertEqual(3, len(problem.all_objects))
        self.assertTrue(problem.object("r1").type.is_movable_type())
        self.assertTrue(problem.object("c1").type.is_configuration_type())
        self.assertTrue(problem.object("c2").type.is_configuration_type())

        move = problem.action("move")
        self.assertEqual(1, len(move.motion_constraints))
        self.assertTrue(isinstance(move.motion_constraints[0], Waypoints))


class TestMotionActivity(unittest_TestCase):
    def test_repr_bare(self):
        act = MotionActivity("act1", duration=2)
        self.assertEqual(
            repr(act),
            "\n".join(
                [
                    "motion-activity {",
                    "  act1 {",
                    "      duration = [2, 2]",
                    "    }",
                    "  motion-constraints",
                    "  motion-effects",
                    "}",
                ]
            ),
        )

    def test_repr_with_constraints_and_effects(self):
        Robot = MovableType("robot")
        occupancy_map = OccupancyMap("map.yaml", SE2(0, 0, 0))
        RobotConfig = ConfigurationType(
            "robot_config", occupancy_map, ConfigurationKind.SE2
        )
        c1 = ConfigurationObject("c1", RobotConfig, SE2(0.0, 0.0, 0.0))
        c2 = ConfigurationObject("c2", RobotConfig, SE2(1.0, 1.0, 0.0))
        r1 = MovableObject(
            "r1",
            Robot,
            footprint=[(-1.0, 0.5), (1.0, 0.5), (1.0, -0.5), (-1.0, -0.5)],
            motion_model=MotionModels.REEDSSHEPP,
            control_parameters={"turning_radius": 1.0},
        )

        act = MotionActivity("act1", duration=2)
        constraint = Waypoints(r1, c1, [c2])
        act.add_motion_constraint(constraint)
        act.add_motion_effect(r1, c2)

        r = repr(act)

        self.assertEqual(
            r,
            "\n".join(
                [
                    "motion-activity {",
                    "  act1 {",
                    "      duration = [2, 2]",
                    "    }",
                    "  motion-constraints",
                    f"      {str(constraint)}",
                    "  motion-effects",
                    f"      {str(r1)} := {str(c2)}",
                    "}",
                ]
            ),
        )
        self.assertNotIn("\n\n", r)
