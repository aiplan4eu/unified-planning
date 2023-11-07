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


import unified_planning as up
from unified_planning.shortcuts import *
from unified_planning.test import unittest_TestCase, main
from unified_planning.test.examples.multi_agent import get_example_problems


class TestProblem(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_basic(self):
        problem = self.problems["ma-basic"].problem

        self.assertEqual(len(problem.ma_environment.fluents), 1)
        self.assertEqual(len(problem.agents), 1)
        self.assertEqual(len(problem.agents[0].fluents), 1)
        self.assertEqual(len(problem.agents[0].actions), 1)
        self.assertEqual(len(problem.all_objects), 2)

    def test_loader(self):
        problem = self.problems["ma-loader"].problem

        ag1 = problem.agent("robot1")
        ag2 = problem.agent("robot2")
        self.assertEqual(ag1.name, "robot1")
        self.assertEqual(ag2.name, "robot2")

        Location = problem.user_type("Location")
        self.assertTrue(Location.is_user_type())
        self.assertEqual(Location.name, "Location")
        self.assertEqual(str(Location), "Location")

        pos = ag1.fluent("pos")
        self.assertEqual(str(pos), "bool pos[position=Location]")
        self.assertEqual(pos.arity, 1)
        self.assertTrue(pos.type.is_bool_type())

        cargo_at = problem.ma_environment.fluent("cargo_at")
        self.assertEqual(cargo_at.name, "cargo_at")
        self.assertEqual(cargo_at.arity, 1)
        self.assertEqual(
            cargo_at.signature,
            [up.model.Parameter("position", Location, problem.environment)],
        )
        self.assertTrue(cargo_at.type.is_bool_type())

        is_connected = problem.ma_environment.fluent("is_connected")
        self.assertEqual(is_connected.name, "is_connected")
        self.assertEqual(is_connected.arity, 2)
        self.assertEqual(
            is_connected.signature,
            [
                up.model.Parameter("l1", Location, problem.environment),
                up.model.Parameter("l2", Location, problem.environment),
            ],
        )
        self.assertTrue(is_connected.type.is_bool_type())

        cargo_mounted = ag1.fluent("cargo_mounted")
        self.assertEqual(cargo_mounted.name, "cargo_mounted")
        self.assertEqual(cargo_mounted.arity, 0)
        self.assertTrue(cargo_mounted.type.is_bool_type())

        move = ag1.action("move")
        l_from = move.parameter("l_from")
        l_to = move.parameter("l_to")
        self.assertEqual(move.name, "move")
        self.assertEqual(len(move.parameters), 2)
        self.assertEqual(l_from.name, "l_from")
        self.assertEqual(l_from.type, Location)
        self.assertEqual(l_to.name, "l_to")
        self.assertEqual(l_to.type, Location)
        self.assertEqual(len(move.preconditions), 2)
        self.assertEqual(len(move.effects), 2)

        load = ag1.action("load")
        loc = load.parameter("loc")
        self.assertEqual(load.name, "load")
        self.assertEqual(len(load.parameters), 1)
        self.assertEqual(loc.name, "loc")
        self.assertEqual(loc.type, Location)
        self.assertEqual(len(load.preconditions), 3)
        self.assertEqual(len(load.effects), 2)

        unload = ag1.action("unload")
        loc = unload.parameter("loc")
        self.assertEqual(unload.name, "unload")
        self.assertEqual(len(unload.parameters), 1)
        self.assertEqual(loc.name, "loc")
        self.assertEqual(loc.type, Location)
        self.assertEqual(len(unload.preconditions), 3)
        self.assertEqual(len(unload.effects), 2)

        l1 = problem.object("l1")
        l2 = problem.object("l2")
        l3 = problem.object("l3")
        self.assertEqual(l1.name, "l1")
        self.assertEqual(l1.type, Location)
        self.assertEqual(l2.name, "l2")
        self.assertEqual(l2.type, Location)
        self.assertEqual(l3.name, "l3")
        self.assertEqual(l3.type, Location)

        self.assertEqual(problem.name, "ma-loader")
        self.assertEqual(problem.ma_environment.fluent("is_connected"), is_connected)
        self.assertEqual(ag1.fluent("pos"), pos)
        self.assertEqual(ag1.fluent("cargo_mounted"), cargo_mounted)
        self.assertEqual(len(problem.user_types), 1)
        self.assertEqual(problem.user_type("Location"), Location)
        self.assertEqual(len(list(problem.objects(Location))), 3)
        self.assertEqual(list(problem.objects(Location)), [l1, l2, l3])
        self.assertEqual(len(problem.ma_environment.fluents), 2)
        self.assertEqual(len(problem.agents), 2)
        self.assertEqual(len(problem.agents[0].fluents), 2)
        self.assertEqual(len(problem.agents[0].actions), 3)
        self.assertEqual(len(problem.all_objects), 3)
        self.assertEqual(ag1.action("move"), move)
        self.assertEqual(ag1.action("load"), load)
        self.assertEqual(ag1.action("unload"), unload)
        self.assertTrue(problem.initial_value(Dot(ag1, cargo_mounted)) is not None)
        self.assertTrue(problem.initial_value(cargo_at(l1)) is not None)
        self.assertTrue(problem.initial_value(cargo_at(l2)) is not None)
        self.assertTrue(problem.initial_value(cargo_at(l3)) is not None)
        self.assertTrue(problem.initial_value(Dot(ag1, pos(l1))) is not None)
        self.assertTrue(problem.initial_value(Dot(ag1, pos(l2))) is not None)
        self.assertTrue(problem.initial_value(Dot(ag1, pos(l3))) is not None)
        self.assertEqual(len(problem.goals), 1)

    def test_normalize_plan(self):
        example = self.problems["ma-loader"]
        problem, plan = example.problem, example.valid_plans[0]

        cloned_problem = problem.clone()
        cloned_plan = cloned_problem.normalize_plan(plan)
        for a, ca in zip(plan.actions, cloned_plan.actions):
            self.assertTrue(a.is_semantically_equivalent(ca))
