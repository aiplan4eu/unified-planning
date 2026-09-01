# Copyright 2021-2023 AIPlan4EU project
# Copyright 2024-2026 Unified Planning library and its maintainers
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


import warnings
from typing import cast
import unified_planning as up
from unified_planning.shortcuts import *
from unified_planning.environment import Environment
from unified_planning.test import unittest_TestCase, main, examples
from unified_planning.test.examples import get_example_problems
from unified_planning.exceptions import UPTypeError, UPValueError
from unified_planning.engines.compilers.utils import remove_fluents
from unified_planning.model.htn import HierarchicalProblem
from unified_planning.model.contingent import ContingentProblem
from unified_planning.model.multi_agent import MultiAgentProblem, Agent
from unified_planning.model.scheduling import SchedulingProblem
from unified_planning.model.mixins import name_index


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
        self.assertEqual(str(battery_charge), "real battery_charge")
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
            "temporal_counter",
            "counter_to_50",
            "robot_decrease",
            "robot_locations_connected",
            "robot_locations_visited",
            "basic_numeric",
            "basic_numeric_with_timed_effect",
            "basic_undef_numeric",
            "sched:basic",
            "sched:resource_set",
            "sched:jobshop-ft06-operators",
            "sched:optional_activities_effects",
            "1d_Movement",
            "boiling_water",
            "robot_with_variable_duration",
        ]
        for example in self.problems.values():
            problem = example.problem
            if problem.name in names_of_SNP_problems:
                self.assertTrue(
                    problem.kind.has_simple_numeric_planning(),
                    str(problem.name) + str(problem.kind),
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

    def test_undefined_initial_state(self):
        undefs_num = [
            "basic_undef_numeric",
            "undef_numeric_with_timed_effects",
            "interpreted_functions_undef_numeric",
            "interpreted_functions_undef_numeric_durative",
        ]
        undefs_sym = ["basic_undef_bool"]
        for pb_name in self.problems:
            problem = self.problems[pb_name].problem
            kind = problem.kind
            self.assertEqual(
                "UNDEFINED_INITIAL_NUMERIC" in kind.features,
                pb_name in undefs_num,
                pb_name,
            )
            self.assertEqual(
                "UNDEFINED_INITIAL_SYMBOLIC" in kind.features,
                pb_name in undefs_sym,
                pb_name,
            )

    def test_natural_transitions(self):
        p = self.problems["1d_movement"].problem
        print(p)
        self.assertTrue(p.has_process("moving"))
        self.assertTrue(p.has_event("turn_off_automatically"))
        print(p.process("moving"))
        print(p.event("turn_off_automatically"))
        p.clear_events()
        p.clear_processes()
        self.assertEqual(len(p.natural_transitions), 0)
        p_boiling_water = self.problems["boiling_water"].problem
        self.assertFalse(p_boiling_water.kind.has_non_linear_continuous_effects())
        self.assertTrue(p_boiling_water.kind.has_increase_continuous_effects())
        self.assertTrue(p_boiling_water.kind.has_decrease_continuous_effects())

    def test_durative_continuous(self):
        p = self.problems["durative_continuous_example"].problem
        self.assertTrue(p.kind.has_increase_continuous_effects())
        self.assertFalse(p.kind.has_events())
        self.assertFalse(p.kind.has_processes())

    def test_interpreted_functions_simple(self):
        problem = self.problems[
            "interpreted_functions_in_conditions_always_impossible"
        ].problem
        self.assertTrue(problem.kind.has_interpreted_functions_in_conditions())
        self.assertFalse(problem.kind.has_simple_numeric_planning())
        problem = self.problems["interpreted_functions_in_conditions"].problem
        self.assertTrue(problem.kind.has_interpreted_functions_in_conditions())
        self.assertFalse(problem.kind.has_simple_numeric_planning())
        problem = self.problems["interpreted_functions_in_durative_conditions"].problem
        self.assertTrue(problem.kind.has_interpreted_functions_in_conditions())
        problem = self.problems["interpreted_functions_in_boolean_assignment"].problem
        self.assertTrue(problem.kind.has_interpreted_functions_in_boolean_assignments())
        self.assertFalse(problem.kind.has_simple_numeric_planning())
        problem = self.problems["interpreted_functions_in_numeric_assignment"].problem
        self.assertTrue(problem.kind.has_interpreted_functions_in_numeric_assignments())
        self.assertFalse(problem.kind.has_simple_numeric_planning())

    def test_name_index_consistency(self):
        # ActionsSetMixin/FluentsSetMixin/ObjectsSetMixin/UserTypesSetMixin each keep a
        # lazily-rebuilt name index (unified_planning/model/mixins/name_index.py) instead of
        # a linear scan; this exercises every way the underlying list can change and asserts
        # has_action/has_fluent/has_object/has_type (and the singular accessors) always agree
        # with a brute-force scan, catching any desync the index's self-healing token might miss.
        loc = UserType("Loc")

        def check(problem):
            for a in problem.actions:
                self.assertTrue(problem.has_action(a.name))
                self.assertIs(problem.action(a.name), a)
            for f in problem.fluents:
                self.assertTrue(problem.has_fluent(f.name))
                self.assertIs(problem.fluent(f.name), f)
            for o in problem.all_objects:
                self.assertTrue(problem.has_object(o.name))
                self.assertIs(problem.object(o.name), o)
            for t in problem.user_types:
                name = cast(up.model.types._UserType, t).name
                self.assertTrue(problem.has_type(name))
                self.assertIs(problem.user_type(name), t)
            self.assertFalse(problem.has_action("__nonexistent__"))
            self.assertFalse(problem.has_fluent("__nonexistent__"))
            self.assertFalse(problem.has_object("__nonexistent__"))
            self.assertFalse(problem.has_type("__nonexistent__"))

        problem = Problem("name_index")
        f1 = Fluent("f1", BoolType(), l=loc)
        f2 = Fluent("f2", BoolType())
        problem.add_fluent(f1, default_initial_value=False)
        problem.add_fluent(f2, default_initial_value=False)
        o1 = Object("o1", loc)
        o2 = Object("o2", loc)
        problem.add_objects([o1, o2])
        a1 = InstantaneousAction("a1", x=loc)
        a1.add_effect(f1(a1.parameter("x")), True)
        a2 = InstantaneousAction("a2")
        a2.add_effect(f2, True)
        problem.add_action(a1)
        problem.add_action(a2)
        check(problem)

        # clear_actions/clear_fluents reassign the underlying list wholesale.
        problem.clear_actions()
        check(problem)
        problem.add_action(a1)
        problem.clear_fluents()
        check(problem)
        problem.add_fluent(f1, default_initial_value=False)
        check(problem)

        # remove_fluents mutates the list in place (list.remove), not via clear_fluents.
        problem.add_fluent(f2, default_initial_value=False)
        remove_fluents(problem, {f2})
        check(problem)

        # clone() reassigns every list wholesale, bypassing add_*/clear_*.
        cloned = problem.clone()
        check(cloned)

        # Renaming an action in place (list identity and length both unchanged) does not by
        # itself trigger the index's usual identity/length staleness check -- it's tracked
        # separately, via a global rename counter that `Transition.name`'s setter bumps and
        # `NameIndex(track_renames=True)` compares itself against on every lookup (see
        # unified_planning/model/mixins/name_index.py). Force the index to build *before* the
        # rename, so this actually exercises the invalidation path rather than just a rebuild
        # that would have picked up the new name anyway.
        renamed = problem.clone()
        target = renamed.actions[0]
        old_name = target.name
        self.assertTrue(renamed.has_action(old_name))  # force the index to build now
        target.name = "renamed_action"
        self.assertFalse(renamed.has_action(old_name))
        self.assertTrue(renamed.has_action("renamed_action"))
        self.assertIs(renamed.action("renamed_action"), target)

        # The in-library rename pattern (several compilers clone an action, rename it via
        # `get_fresh_name`, *then* add it) must stay cheap: renaming an action that has never
        # been indexed yet must not bump the shared rename counter, so it can't force a
        # rebuild of some unrelated, already-built index.
        epoch_before = name_index.current_rename_epoch()
        fresh_action = a1.clone()
        fresh_action.name = "not_indexed_yet"  # never indexed: must not bump the epoch
        self.assertEqual(name_index.current_rename_epoch(), epoch_before)
        other = problem.clone()
        other.add_action(fresh_action)
        self.assertTrue(other.has_action("not_indexed_yet"))
        self.assertIs(other.action("not_indexed_yet"), fresh_action)

        # A name shared ACROSS categories (here, an action and a fluent) is legal when
        # error_used_name is disabled -- add_action's own duplicate guard always raises for
        # two entries of the *same* category regardless of this flag, so that case can't
        # arise through the public API. Each category keeps its own independent index, so
        # this must not create any cross-category confusion.
        env = Environment()
        env.error_used_name = False
        dup_problem = Problem("dup_names", env)
        dup_fluent = Fluent("dup", BoolType(), environment=env)
        dup_problem.add_fluent(dup_fluent, default_initial_value=False)
        dup_action = InstantaneousAction("dup", _env=env)
        dup_action.add_effect(dup_fluent, True)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            dup_problem.add_action(dup_action)
        self.assertTrue(dup_problem.has_action("dup"))
        self.assertTrue(dup_problem.has_fluent("dup"))
        self.assertIs(dup_problem.action("dup"), dup_action)
        self.assertIs(dup_problem.fluent("dup"), dup_fluent)

    def test_name_index_removing_then_adding_a_fluent_keeps_lookups_consistent(self):
        # The name index's staleness token is identity+length, which a remove followed by an
        # append restores exactly: same list object, same length, so nothing looks stale even
        # though both the removed and the added fluent are now wrong. FluentsSetMixin's
        # _remove_fluent must invalidate the index explicitly.
        problem = Problem("remove_then_add")
        f1 = Fluent("f1")
        f2 = Fluent("f2")
        f3 = Fluent("f3")
        problem.add_fluent(f1, default_initial_value=False)
        problem.add_fluent(f2, default_initial_value=False)

        self.assertTrue(problem.has_fluent("f1"))  # builds the index at length 2
        problem._remove_fluent(f2)
        problem._fluents.append(
            f3
        )  # bare append: no has_name call to refresh the index
        problem._fluents_index.note_appended(problem._fluents)

        self.assertEqual([f.name for f in problem.fluents], ["f1", "f3"])
        self.assertFalse(problem.has_fluent("f2"))
        self.assertTrue(problem.has_fluent("f3"))
        self.assertIs(problem.fluent("f3"), f3)
        with self.assertRaises(UPValueError):
            problem.fluent("f2")

    def test_name_index_consistency_on_problem_subclasses(self):
        # Lighter smoke checks that the same index machinery is wired correctly through every
        # AbstractProblem subclass with its own has_name composition (see
        # unified_planning/model/mixins/name_index.py's docstring for why a shared global
        # index would be wrong here: each subclass's has_name covers a different set of
        # name-bearing collections).
        loc = UserType("Loc")

        htn = HierarchicalProblem("htn_name_index")
        f = Fluent("f", BoolType())
        htn.add_fluent(f, default_initial_value=False)
        a = InstantaneousAction("a")
        a.add_effect(f, True)
        htn.add_action(a)
        self.assertTrue(htn.has_action("a") and htn.has_fluent("f"))
        self.assertIs(htn.action("a"), a)
        cloned_htn = htn.clone()
        self.assertTrue(cloned_htn.has_action("a"))
        self.assertIsNot(cloned_htn.action("a"), a)  # actions are cloned, not shared

        cp = ContingentProblem("contingent_name_index")
        cp.add_fluent(f, default_initial_value=False)
        cp.add_action(a)
        self.assertTrue(cp.has_action("a") and cp.has_fluent("f"))
        cloned_cp = cp.clone()
        self.assertTrue(cloned_cp.has_action("a"))

        ma = MultiAgentProblem("ma_name_index")
        agent = Agent("ag1", ma)
        agent.add_fluent(f, default_initial_value=False)
        agent.add_action(a)
        ma.add_agent(agent)
        o = Object("o1", loc)
        ma.add_object(o)
        self.assertTrue(ma.has_object("o1"))
        self.assertTrue(agent.has_action("a") and agent.has_fluent("f"))
        self.assertIs(agent.action("a"), a)

        sp = SchedulingProblem("scheduling_name_index")
        sp.add_fluent(f, default_initial_value=False)
        sp.add_object(o)
        self.assertTrue(sp.has_fluent("f") and sp.has_object("o1"))
        self.assertIs(sp.fluent("f"), f)
        self.assertIs(sp.object("o1"), o)

    def test_interpreted_functions_complex(self):
        problem = self.problems["go_home_with_rain_and_interpreted_functions"].problem
        self.assertTrue(problem.kind.has_interpreted_functions_in_durations())
        self.assertTrue(problem.kind.has_interpreted_functions_in_boolean_assignments())
        IF_string = repr(problem.action("gohome").duration.lower.interpreted_function())
        self.assertTrue(isinstance(IF_string, str))
        problem = self.problems["IF_in_conditions_complex_1"].problem
        self.assertTrue(problem.kind.has_interpreted_functions_in_conditions())
        problem = self.problems["if_reals_condition_effect_pizza"].problem
        self.assertTrue(problem.kind.has_interpreted_functions_in_numeric_assignments())
        self.assertTrue(problem.kind.has_interpreted_functions_in_conditions())


if __name__ == "__main__":
    main()
