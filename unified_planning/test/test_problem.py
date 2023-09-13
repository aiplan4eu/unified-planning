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
from unified_planning.test import unittest_TestCase, main, examples
from unified_planning.test.examples import get_example_problems
from unified_planning.exceptions import UPTypeError


class TestProblem(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_problem_kind(self):
        problem_kind = ProblemKind()
        self.assertFalse(problem_kind.has_discrete_time())
        self.assertFalse(problem_kind.has_continuous_time())
        problem_kind.set_time("DISCRETE_TIME")
        self.assertTrue(problem_kind.has_discrete_time())
        problem_kind.set_time("CONTINUOUS_TIME")
        self.assertTrue(problem_kind.has_continuous_time())

    def test_basic(self):
        problem = self.problems["basic"].problem

        x = problem.fluent("x")
        self.assertEqual(x.name, "x")
        self.assertEqual(str(x), "bool x")
        self.assertEqual(x.arity, 0)
        self.assertTrue(x.type.is_bool_type())

        a = problem.action("a")
        self.assertEqual(a.name, "a")
        self.assertEqual(len(a.preconditions), 1)
        self.assertEqual(len(a.effects), 1)
        a_str = str(a)
        self.assertIn("action a", a_str)
        self.assertIn("preconditions", a_str)
        self.assertIn("not x", a_str)
        self.assertIn("effects", a_str)
        self.assertIn("x := true", a_str)

        self.assertEqual(problem.name, "basic")
        self.assertEqual(len(problem.fluents), 1)
        self.assertEqual(len(problem.actions), 1)
        self.assertTrue(problem.initial_value(x) is not None)
        self.assertEqual(len(problem.goals), 1)
        problem_str = str(problem)
        self.assertIn("fluents", problem_str)
        self.assertIn("actions", problem_str)
        self.assertIn("initial values", problem_str)
        self.assertIn("goals", problem_str)

    def test_basic_conditional(self):
        problem = self.problems["basic_conditional"].problem

        x = problem.fluent("x")
        self.assertEqual(x.name, "x")
        self.assertEqual(str(x), "bool x")
        self.assertEqual(x.arity, 0)
        self.assertTrue(x.type.is_bool_type())

        y = problem.fluent("y")
        self.assertEqual(y.name, "y")
        self.assertEqual(str(y), "bool y")
        self.assertEqual(y.arity, 0)
        self.assertTrue(y.type.is_bool_type())

        a_x = problem.action("a_x")
        self.assertEqual(a_x.name, "a_x")
        self.assertEqual(len(a_x.preconditions), 1)
        self.assertEqual(len(a_x.effects), 1)
        ax_str = str(a_x)
        self.assertIn("action a_x", ax_str)
        self.assertIn("preconditions", ax_str)
        self.assertIn("not x", ax_str)
        self.assertIn("effects", ax_str)
        self.assertIn("if y then x := true", ax_str)

        a_y = problem.action("a_y")
        self.assertEqual(a_y.name, "a_y")
        self.assertEqual(len(a_y.preconditions), 1)
        self.assertEqual(len(a_y.effects), 1)
        ay_str = str(a_y)
        self.assertIn("action a_y", ay_str)
        self.assertIn("preconditions", ay_str)
        self.assertIn("not y", ay_str)
        self.assertIn("effects", ay_str)
        self.assertIn("y := true", ay_str)

        self.assertEqual(problem.name, "basic_conditional")
        self.assertEqual(len(problem.fluents), 2)
        self.assertEqual(len(problem.actions), 2)
        self.assertTrue(problem.initial_value(x) is not None)
        self.assertTrue(problem.initial_value(y) is not None)
        self.assertEqual(len(problem.goals), 1)
        problem_str = str(problem)
        self.assertIn("fluents", problem_str)
        self.assertIn("actions", problem_str)
        self.assertIn("initial values", problem_str)
        self.assertIn("goals", problem_str)

    def test_robot(self):
        problem = self.problems["robot"].problem

        Location = problem.user_type("Location")
        self.assertTrue(Location.is_user_type())
        self.assertEqual(Location.name, "Location")
        self.assertEqual(str(Location), "Location")

        robot_at = problem.fluent("robot_at")
        self.assertEqual(robot_at.name, "robot_at")
        self.assertEqual(str(robot_at), "bool robot_at[position=Location]")
        self.assertEqual(robot_at.arity, 1)
        self.assertEqual(
            robot_at.signature,
            [up.model.Parameter("position", Location, problem.environment)],
        )
        self.assertTrue(robot_at.type.is_bool_type())

        battery_charge = problem.fluent("battery_charge")
        self.assertEqual(battery_charge.name, "battery_charge")
        self.assertEqual(str(battery_charge), "real[0, 100] battery_charge")
        self.assertEqual(battery_charge.arity, 0)
        self.assertTrue(battery_charge.type.is_real_type())

        move = problem.action("move")
        l_from = move.parameter("l_from")
        l_to = move.parameter("l_to")
        self.assertEqual(move.name, "move")
        self.assertEqual(len(move.parameters), 2)
        self.assertEqual(l_from.name, "l_from")
        self.assertEqual(l_from.type, Location)
        self.assertEqual(l_to.name, "l_to")
        self.assertEqual(l_to.type, Location)
        self.assertEqual(len(move.preconditions), 4)
        self.assertEqual(len(move.effects), 3)
        move_str = str(move)
        self.assertTrue("action move(Location l_from, Location l_to)" in move_str)
        self.assertTrue("preconditions" in move_str)
        self.assertTrue("10 <= battery_charge" in move_str)
        self.assertTrue("not (l_from == l_to)" in move_str)
        self.assertTrue("robot_at(l_from)" in move_str)
        self.assertTrue("not robot_at(l_to)" in move_str)
        self.assertTrue("effects" in move_str)
        self.assertTrue("robot_at(l_from) := false" in move_str)
        self.assertTrue("robot_at(l_to) := true" in move_str)
        self.assertTrue("battery_charge := (battery_charge - 10)" in move_str)

        l1 = problem.object("l1")
        l2 = problem.object("l2")
        self.assertEqual(l1.name, "l1")
        self.assertEqual(str(l1), "l1")
        self.assertEqual(l1.type, Location)
        self.assertEqual(l2.name, "l2")
        self.assertEqual(str(l2), "l2")
        self.assertEqual(l2.type, Location)

        self.assertEqual(problem.name, "robot")
        self.assertEqual(len(problem.fluents), 2)
        self.assertEqual(problem.fluent("robot_at"), robot_at)
        self.assertEqual(problem.fluent("battery_charge"), battery_charge)
        self.assertEqual(len(problem.user_types), 1)
        self.assertEqual(problem.user_type("Location"), Location)
        self.assertEqual(len(list(problem.objects(Location))), 2)
        self.assertEqual(list(problem.objects(Location)), [l1, l2])
        self.assertEqual(len(problem.actions), 1)
        self.assertEqual(problem.action("move"), move)
        self.assertTrue(problem.initial_value(robot_at(l1)) is not None)
        self.assertTrue(problem.initial_value(robot_at(l2)) is not None)
        self.assertTrue(problem.initial_value(battery_charge) is not None)
        self.assertEqual(len(problem.goals), 1)
        problem_str = str(problem)
        self.assertTrue("types" in problem_str)
        self.assertTrue("fluents" in problem_str)
        self.assertTrue("actions" in problem_str)
        self.assertTrue("objects" in problem_str)
        self.assertTrue("initial values" in problem_str)
        self.assertTrue("goals" in problem_str)

    def test_robot_loader(self):
        problem = self.problems["robot_loader"].problem

        Location = problem.user_type("Location")
        self.assertTrue(Location.is_user_type())
        self.assertEqual(Location.name, "Location")

        robot_at = problem.fluent("robot_at")
        self.assertEqual(robot_at.name, "robot_at")
        self.assertEqual(robot_at.arity, 1)
        self.assertEqual(
            robot_at.signature,
            [up.model.Parameter("position", Location, problem.environment)],
        )
        self.assertTrue(robot_at.type.is_bool_type())

        cargo_at = problem.fluent("cargo_at")
        self.assertEqual(cargo_at.name, "cargo_at")
        self.assertEqual(cargo_at.arity, 1)
        self.assertEqual(
            cargo_at.signature,
            [up.model.Parameter("position", Location, problem.environment)],
        )
        self.assertTrue(cargo_at.type.is_bool_type())

        cargo_mounted = problem.fluent("cargo_mounted")
        self.assertEqual(cargo_mounted.name, "cargo_mounted")
        self.assertEqual(cargo_mounted.arity, 0)
        self.assertTrue(cargo_mounted.type.is_bool_type())

        move = problem.action("move")
        l_from = move.parameter("l_from")
        l_to = move.parameter("l_to")
        self.assertEqual(move.name, "move")
        self.assertEqual(len(move.parameters), 2)
        self.assertEqual(l_from.name, "l_from")
        self.assertEqual(l_from.type, Location)
        self.assertEqual(l_to.name, "l_to")
        self.assertEqual(l_to.type, Location)
        self.assertEqual(len(move.preconditions), 3)
        self.assertEqual(len(move.effects), 2)

        load = problem.action("load")
        loc = load.parameter("loc")
        self.assertEqual(load.name, "load")
        self.assertEqual(len(load.parameters), 1)
        self.assertEqual(loc.name, "loc")
        self.assertEqual(loc.type, Location)
        self.assertEqual(len(load.preconditions), 3)
        self.assertEqual(len(load.effects), 2)

        unload = problem.action("unload")
        loc = unload.parameter("loc")
        self.assertEqual(unload.name, "unload")
        self.assertEqual(len(unload.parameters), 1)
        self.assertEqual(loc.name, "loc")
        self.assertEqual(loc.type, Location)
        self.assertEqual(len(unload.preconditions), 3)
        self.assertEqual(len(unload.effects), 2)

        l1 = problem.object("l1")
        l2 = problem.object("l2")
        self.assertEqual(l1.name, "l1")
        self.assertEqual(l1.type, Location)
        self.assertEqual(l2.name, "l2")
        self.assertEqual(l2.type, Location)

        self.assertEqual(problem.name, "robot_loader")
        self.assertEqual(len(problem.fluents), 3)
        self.assertEqual(problem.fluent("robot_at"), robot_at)
        self.assertEqual(problem.fluent("cargo_at"), cargo_at)
        self.assertEqual(problem.fluent("cargo_mounted"), cargo_mounted)
        self.assertEqual(len(problem.user_types), 1)
        self.assertEqual(problem.user_type("Location"), Location)
        self.assertEqual(len(list(problem.objects(Location))), 2)
        self.assertEqual(list(problem.objects(Location)), [l1, l2])
        self.assertEqual(len(problem.actions), 3)
        self.assertEqual(problem.action("move"), move)
        self.assertEqual(problem.action("load"), load)
        self.assertEqual(problem.action("unload"), unload)
        self.assertTrue(problem.initial_value(robot_at(l1)) is not None)
        self.assertTrue(problem.initial_value(robot_at(l2)) is not None)
        self.assertTrue(problem.initial_value(cargo_at(l1)) is not None)
        self.assertTrue(problem.initial_value(cargo_at(l2)) is not None)
        self.assertTrue(problem.initial_value(cargo_mounted) is not None)
        self.assertEqual(len(problem.goals), 1)

    def test_robot_loader_adv(self):
        problem = self.problems["robot_loader_adv"].problem

        Location = problem.user_type("Location")
        self.assertTrue(Location.is_user_type())
        self.assertEqual(Location.name, "Location")

        Robot = problem.user_type("Robot")
        self.assertTrue(Robot.is_user_type())
        self.assertEqual(Robot.name, "Robot")

        Container = problem.user_type("Container")
        self.assertTrue(Container.is_user_type())
        self.assertEqual(Container.name, "Container")

        robot_at = problem.fluent("robot_at")
        self.assertEqual(robot_at.name, "robot_at")
        self.assertEqual(robot_at.arity, 2)
        self.assertEqual(
            robot_at.signature,
            [
                up.model.Parameter("robot", Robot, problem.environment),
                up.model.Parameter("position", Location, problem.environment),
            ],
        )
        self.assertTrue(robot_at.type.is_bool_type())

        cargo_at = problem.fluent("cargo_at")
        self.assertEqual(cargo_at.name, "cargo_at")
        self.assertEqual(cargo_at.arity, 2)
        self.assertEqual(
            cargo_at.signature,
            [
                up.model.Parameter("cargo", Container, problem.environment),
                up.model.Parameter("position", Location, problem.environment),
            ],
        )
        self.assertTrue(cargo_at.type.is_bool_type())

        cargo_mounted = problem.fluent("cargo_mounted")
        self.assertEqual(cargo_mounted.name, "cargo_mounted")
        self.assertEqual(cargo_mounted.arity, 2)
        self.assertEqual(
            cargo_mounted.signature,
            [
                up.model.Parameter("cargo", Container, problem.environment),
                up.model.Parameter("robot", Robot, problem.environment),
            ],
        )
        self.assertTrue(cargo_mounted.type.is_bool_type())

        move = problem.action("move")
        l_from = move.parameter("l_from")
        l_to = move.parameter("l_to")
        r = move.parameter("r")
        self.assertEqual(move.name, "move")
        self.assertEqual(len(move.parameters), 3)
        self.assertEqual(l_from.name, "l_from")
        self.assertEqual(l_from.type, Location)
        self.assertEqual(l_to.name, "l_to")
        self.assertEqual(l_to.type, Location)
        self.assertEqual(r.name, "r")
        self.assertEqual(r.type, Robot)
        self.assertEqual(len(move.preconditions), 3)
        self.assertEqual(len(move.effects), 2)

        load = problem.action("load")
        loc = load.parameter("loc")
        r = load.parameter("r")
        c = load.parameter("c")
        self.assertEqual(load.name, "load")
        self.assertEqual(len(load.parameters), 3)
        self.assertEqual(loc.name, "loc")
        self.assertEqual(loc.type, Location)
        self.assertEqual(r.name, "r")
        self.assertEqual(r.type, Robot)
        self.assertEqual(c.name, "c")
        self.assertEqual(c.type, Container)
        self.assertEqual(len(load.preconditions), 3)
        self.assertEqual(len(load.effects), 2)

        unload = problem.action("unload")
        loc = unload.parameter("loc")
        r = unload.parameter("r")
        c = unload.parameter("c")
        self.assertEqual(unload.name, "unload")
        self.assertEqual(len(unload.parameters), 3)
        self.assertEqual(loc.name, "loc")
        self.assertEqual(loc.type, Location)
        self.assertEqual(r.name, "r")
        self.assertEqual(r.type, Robot)
        self.assertEqual(c.name, "c")
        self.assertEqual(c.type, Container)
        self.assertEqual(len(unload.preconditions), 3)
        self.assertEqual(len(unload.effects), 2)

        l1 = problem.object("l1")
        l2 = problem.object("l2")
        l3 = problem.object("l3")
        r1 = problem.object("r1")
        c1 = problem.object("c1")
        self.assertEqual(l1.name, "l1")
        self.assertEqual(l1.type, Location)
        self.assertEqual(l2.name, "l2")
        self.assertEqual(l2.type, Location)
        self.assertEqual(l3.name, "l3")
        self.assertEqual(l3.type, Location)
        self.assertEqual(r1.name, "r1")
        self.assertEqual(r1.type, Robot)
        self.assertEqual(c1.name, "c1")
        self.assertEqual(c1.type, Container)

        self.assertEqual(problem.name, "robot_loader_adv")
        self.assertEqual(len(problem.fluents), 3)
        self.assertEqual(problem.fluent("robot_at"), robot_at)
        self.assertEqual(problem.fluent("cargo_at"), cargo_at)
        self.assertEqual(problem.fluent("cargo_mounted"), cargo_mounted)
        self.assertEqual(len(problem.user_types), 3)
        self.assertEqual(problem.user_type("Location"), Location)
        self.assertEqual(len(list(problem.objects(Location))), 3)
        self.assertEqual(list(problem.objects(Location)), [l1, l2, l3])
        self.assertEqual(problem.user_type("Robot"), Robot)
        self.assertEqual(len(list(problem.objects(Robot))), 1)
        self.assertEqual(list(problem.objects(Robot)), [r1])
        self.assertEqual(problem.user_type("Container"), Container)
        self.assertEqual(len(list(problem.objects(Container))), 1)
        self.assertEqual(list(problem.objects(Container)), [c1])
        self.assertEqual(len(problem.actions), 3)
        self.assertEqual(problem.action("move"), move)
        self.assertEqual(problem.action("load"), load)
        self.assertEqual(problem.action("unload"), unload)
        self.assertTrue(problem.initial_value(robot_at(r1, l1)) is not None)
        self.assertTrue(problem.initial_value(robot_at(r1, l2)) is not None)
        self.assertTrue(problem.initial_value(robot_at(r1, l3)) is not None)
        self.assertTrue(problem.initial_value(cargo_at(c1, l1)) is not None)
        self.assertTrue(problem.initial_value(cargo_at(c1, l2)) is not None)
        self.assertTrue(problem.initial_value(cargo_at(c1, l3)) is not None)
        self.assertTrue(problem.initial_value(cargo_mounted(c1, r1)) is not None)
        self.assertEqual(len(problem.goals), 2)

    def test_fluents_defaults(self):
        Location = UserType("Location")
        robot_at = Fluent("robot_at", BoolType(), position=Location)
        distance = Fluent(
            "distance", RealType(), location_1=Location, location_2=Location
        )

        N = 10
        locations = [Object(f"l{i}", Location) for i in range(N)]

        problem = Problem("robot")
        problem.add_fluent(robot_at, default_initial_value=False)
        problem.add_fluent(distance, default_initial_value=Fraction(-1))
        problem.add_objects(locations)
        problem.set_initial_value(robot_at(locations[0]), True)
        for i in range(N - 1):
            problem.set_initial_value(
                distance(locations[i], locations[i + 1]), Fraction(10)
            )

        self.assertEqual(problem.initial_value(robot_at(locations[0])), TRUE())
        for i in range(1, N):
            self.assertEqual(problem.initial_value(robot_at(locations[i])), FALSE())

        for i in range(N):
            for j in range(N):
                if j == i + 1:
                    self.assertEqual(
                        problem.initial_value(distance(locations[i], locations[j])),
                        Int(10),
                    )
                else:
                    self.assertEqual(
                        problem.initial_value(distance(locations[i], locations[j])),
                        Int(-1),
                    )

    def test_problem_defaults(self):
        Location = UserType("Location")
        robot_at = Fluent("robot_at", BoolType(), position=Location)
        distance = Fluent(
            "distance", IntType(), location_1=Location, location_2=Location
        )
        cost = Fluent("cost", IntType(), location_1=Location, location_2=Location)

        N = 10
        locations = [Object(f"l{i}", Location) for i in range(N)]

        problem = Problem("robot", initial_defaults={IntType(): 0})
        problem.add_fluent(robot_at, default_initial_value=False)
        problem.add_fluent(distance, default_initial_value=-1)
        problem.add_fluent(cost)
        problem.add_objects(locations)
        problem.set_initial_value(robot_at(locations[0]), True)
        for i in range(N - 1):
            problem.set_initial_value(distance(locations[i], locations[i + 1]), 10)
            problem.set_initial_value(cost(locations[i], locations[i + 1]), 100)

        self.assertEqual(problem.initial_value(robot_at(locations[0])), TRUE())
        for i in range(1, N):
            self.assertEqual(problem.initial_value(robot_at(locations[i])), FALSE())

        for i in range(N):
            for j in range(N):
                if j == i + 1:
                    self.assertEqual(
                        problem.initial_value(distance(locations[i], locations[j])),
                        Int(10),
                    )
                    self.assertEqual(
                        problem.initial_value(cost(locations[i], locations[j])),
                        Int(100),
                    )
                else:
                    self.assertEqual(
                        problem.initial_value(distance(locations[i], locations[j])),
                        Int(-1),
                    )
                    self.assertEqual(
                        problem.initial_value(cost(locations[i], locations[j])), Int(0)
                    )

    def test_simple_numeric_planning_kind(self):

        problem = self.problems["robot"].problem
        # False because the problem has an assignment instead of a decrease
        self.assertFalse(problem.kind.has_simple_numeric_planning())

        problem = self.problems["robot_decrease"].problem
        # Fixes problem above
        self.assertTrue(problem.kind.has_simple_numeric_planning())

        problem = self.problems["travel"].problem
        # False because the problem has a non-constant increase
        self.assertFalse(problem.kind.has_simple_numeric_planning())

        problem = self.problems["travel_with_consumptions"].problem
        # False because the problem has a multiplication of 2 static fluents
        self.assertFalse(problem.kind.has_simple_numeric_planning())

        names_of_SNP_problems = [
            "counter_to_50",
            "robot_decrease",
            "robot_locations_connected",
            "robot_locations_visited",
            "robot_fluent_of_user_type_with_int_id",
            "basic_int_fluent_param",
            "basic_bounded_int_action_param",
            "basic_unbounded_int_action_param",
            "basic_numeric",
            "sched:basic",
            "sched:resource_set",
            "sched:jobshop-ft06-operators",
        ]
        for example in self.problems.values():
            problem = example.problem
            if problem.name in names_of_SNP_problems:
                self.assertTrue(
                    problem.kind.has_simple_numeric_planning(), problem.name
                )
            else:
                self.assertFalse(
                    problem.kind.has_simple_numeric_planning(), problem.name
                )

    def test_simple_numeric_planning_ad_hoc_1(self):
        problem = Problem("ad_hoc_1")
        Location = UserType("Location")
        is_at = Fluent("is_at", position=Location)
        distance = Fluent("distance", IntType(), loc_1=Location, loc_2=Location)
        total_distance = Fluent("total_distance", IntType())
        move = InstantaneousAction("move", l_from=Location, l_to=Location)
        l_from = move.parameter("l_from")
        l_to = move.parameter("l_to")
        move.add_precondition(is_at(l_from))
        move.add_effect(is_at(l_from), False)
        move.add_effect(is_at(l_to), True)
        move.add_increase_effect(
            total_distance, 2 * distance(l_from, l_to)
        )  # Makes no sense, just for testing
        l1 = Object("l1", Location)
        l2 = Object("l2", Location)
        problem.add_fluent(is_at, default_initial_value=False)
        problem.add_fluent(distance, default_initial_value=100)
        problem.add_fluent(total_distance, default_initial_value=0)
        problem.set_initial_value(distance(l1, l2), 5)
        problem.add_action(move)
        problem.add_goal(distance(l1, l2) < 6)

        # This problem is not SNP because of the increase of 2*distance(l_from, l_to)
        # by grounding, this distance(l_from, l_to) becomes distance(l1, l2), so it can be seen as a constant.
        self.assertFalse(problem.kind.has_simple_numeric_planning())
        with Compiler(
            problem_kind=problem.kind, compilation_kind=CompilationKind.GROUNDING
        ) as grounder:
            grounded_problem = grounder.compile(
                problem, CompilationKind.GROUNDING
            ).problem
            self.assertTrue(grounded_problem.kind.has_simple_numeric_planning())

        with self.assertRaises(UPTypeError):
            problem.set_initial_value(distance(l2, l1), 2.1)
        with self.assertRaises(UPTypeError):
            problem.set_initial_value(distance(l2, l1), "2.1")
        with self.assertRaises(UPTypeError):
            problem.set_initial_value(distance(l2, l1), "3/2")
        with self.assertRaises(UPTypeError):
            problem.set_initial_value(distance(l2, l1), Div(4, 2))
        problem.set_initial_value(distance(l2, l1), "20")


if __name__ == "__main__":
    main()
