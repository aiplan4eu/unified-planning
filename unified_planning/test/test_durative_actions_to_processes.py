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

import unified_planning
from unified_planning.shortcuts import *
from unified_planning.model.problem_kind import (
    classical_kind,
    full_classical_kind,
    basic_temporal_kind,
)
from unified_planning.test import unittest_TestCase, main
from unified_planning.test import (
    skipIfNoPlanValidatorForProblemKind,
)
from unified_planning.test.examples import get_example_problems
from unified_planning.engines import CompilationKind


class TestDurativeActionsToProcesses(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfNoPlanValidatorForProblemKind(basic_temporal_kind)
    def test_base_temporal_counter(self):
        problem = self.problems["temporal_counter"].problem
        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION,
        ) as cer:
            res = cer.compile(
                problem, CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
            )
        new_problem = res.problem
        self.assertTrue(cer._use_counter)

        for a, na in zip(problem.actions, new_problem.actions):
            self.assertTrue(isinstance(a, DurativeAction))
            self.assertFalse(isinstance(na, DurativeAction))
        self.assertEqual(
            len(new_problem.fluents),
            (len(problem.fluents) + (len(problem.actions) * 2) + 2),
        )
        self.assertEqual(len(problem.actions), len(new_problem.actions))
        self.assertEqual(len(problem.actions), len(new_problem.processes))
        self.assertEqual(len(problem.processes), 0)
        self.assertEqual(len(problem.actions), len(new_problem.events))
        self.assertEqual(len(problem.events), 0)
        self.assertEqual(len(new_problem.goals), len(problem.goals) + 2)

    @skipIfNoPlanValidatorForProblemKind(basic_temporal_kind)
    def test_base_temporal_counter_2(self):
        problem = self.problems["temporal_counter"].problem
        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION,
        ) as cer:
            cer._use_counter = False
            res = cer.compile(
                problem, CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
            )
        new_problem = res.problem
        self.assertFalse(cer._use_counter)
        for a, na in zip(problem.actions, new_problem.actions):
            self.assertTrue(isinstance(a, DurativeAction))
            self.assertFalse(isinstance(na, DurativeAction))
        self.assertEqual(
            len(new_problem.fluents),
            (len(problem.fluents) + ((len(problem.actions) * 2) + 1)),
        )
        self.assertEqual(len(problem.actions), len(new_problem.actions))
        self.assertEqual(len(problem.actions), len(new_problem.processes))
        self.assertEqual(len(problem.processes), 0)
        self.assertEqual(len(problem.actions), len(new_problem.events))
        self.assertEqual(len(problem.events), 0)
        self.assertGreater(len(new_problem.goals), len(problem.goals))

    @skipIfNoPlanValidatorForProblemKind(full_classical_kind)
    def test_base_basic_numeric(self):
        problem = self.problems["robot_decrease"].problem
        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION,
        ) as cer:
            res = cer.compile(
                problem, CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
            )
        new_problem = res.problem
        self.assertTrue(cer._use_counter)
        for a, na in zip(problem.actions, new_problem.actions):
            self.assertTrue(isinstance(a, InstantaneousAction))
            self.assertTrue(isinstance(na, InstantaneousAction))
        self.assertEqual(len(problem.actions), len(new_problem.actions))
        self.assertTrue(Effect.is_decrease(problem.actions[0].effects[2]))
        self.assertTrue(Effect.is_decrease(new_problem.actions[0].effects[2]))

    @skipIfNoPlanValidatorForProblemKind(full_classical_kind)
    def test_base_basic_numeric_2(self):
        problem = self.problems["robot_decrease"].problem
        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION,
        ) as cer:
            cer._use_counter = False
            res = cer.compile(
                problem, CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
            )
        new_problem = res.problem
        self.assertFalse(cer._use_counter)
        for a, na in zip(problem.actions, new_problem.actions):
            self.assertTrue(isinstance(a, InstantaneousAction))
            self.assertTrue(isinstance(na, InstantaneousAction))
        self.assertEqual(len(problem.actions), len(new_problem.actions))
        self.assertTrue(Effect.is_decrease(problem.actions[0].effects[2]))
        self.assertTrue(Effect.is_decrease(new_problem.actions[0].effects[2]))

    def test_ad_hoc_1(self):
        Robot = UserType("robot")
        Room = UserType("room")
        Obj = UserType("obj")
        Table = UserType("table")
        robot_in = Fluent("robot_in", robot=Robot, room=Room)
        connect = Fluent("connect", l_from=Room, l_to=Room)
        handvoid = Fluent("handvoid", robot=Robot)
        holding = Fluent("holding", robot=Robot, obj=Obj)
        obj_on = Fluent("obj_on", obj=Obj, table=Table)
        inside = Fluent("inside", table=Table, room=Room)
        pick_up = DurativeAction(
            "pick_up", robot=Robot, obj=Obj, table=Table, room=Room
        )
        pick_up.set_fixed_duration(2)
        robot = pick_up.parameter("robot")
        obj = pick_up.parameter("obj")
        table = pick_up.parameter("table")
        room = pick_up.parameter("room")
        pick_up.add_condition(StartTiming(), handvoid(robot))
        pick_up.add_condition(StartTiming(), inside(table, room))
        pick_up.add_condition(StartTiming(), obj_on(obj, table))
        pick_up.add_condition(StartTiming(), Not(holding(robot, obj)))
        pick_up.add_condition(
            ClosedTimeInterval(StartTiming(), EndTiming()), robot_in(robot, room)
        )
        pick_up.add_effect(StartTiming(), handvoid(robot), False)
        pick_up.add_effect(StartTiming(), obj_on(obj, table), False)
        pick_up.add_effect(EndTiming(), holding(robot, obj), True)
        put_down = DurativeAction(
            "put_down", robot=Robot, obj=Obj, table=Table, room=Room
        )
        put_down.set_fixed_duration(2)
        robot = put_down.parameter("robot")
        obj = put_down.parameter("obj")
        table = put_down.parameter("table")
        room = put_down.parameter("room")
        put_down.add_condition(StartTiming(), Not(handvoid(robot)))
        put_down.add_condition(StartTiming(), inside(table, room))
        put_down.add_condition(StartTiming(), Not(obj_on(obj, table)))
        put_down.add_condition(StartTiming(), holding(robot, obj))
        put_down.add_condition(
            ClosedTimeInterval(StartTiming(), EndTiming()), robot_in(robot, room)
        )
        put_down.add_effect(EndTiming(), obj_on(obj, table), True)
        put_down.add_effect(StartTiming(), holding(robot, obj), False)
        put_down.add_effect(EndTiming(), handvoid(robot), True)
        move = DurativeAction("move", robot=Robot, l_from=Room, l_to=Room)
        move.set_fixed_duration(5)
        robot = move.parameter("robot")
        l_from = move.parameter("l_from")
        l_to = move.parameter("l_to")
        move.add_condition(StartTiming(), robot_in(robot, l_from))
        move.add_condition(
            StartTiming(), Or(connect(l_from, l_to), connect(l_to, l_from))
        )
        move.add_effect(StartTiming(), robot_in(robot, l_from), False)
        move.add_effect(EndTiming(), robot_in(robot, l_to), True)
        problem = Problem("movimento")
        problem.add_fluent(robot_in, default_initial_value=False)
        problem.add_fluent(connect, default_initial_value=False)
        problem.add_fluent(handvoid, default_initial_value=True)
        problem.add_fluent(holding, default_initial_value=False)
        problem.add_fluent(obj_on, default_initial_value=False)
        problem.add_fluent(inside, default_initial_value=False)
        problem.add_action(pick_up)
        problem.add_action(put_down)
        problem.add_action(move)
        NLOC = 6
        locations = [Object("l%s" % i, Room) for i in range(NLOC)]
        problem.add_objects(locations)
        NTAB = 6
        tables = [Object("t%s" % i, Table) for i in range(NTAB)]
        problem.add_objects(tables)
        rob = Object("r", Robot)
        problem.add_object(rob)
        objects = [Object("o%s" % i, Obj) for i in range(2)]
        problem.add_objects(objects)
        for i in range(NLOC - 1):
            problem.set_initial_value(connect(locations[i], locations[i + 1]), True)
        for i in range(NLOC):
            problem.set_initial_value(inside(tables[i], locations[i]), True)
        problem.set_initial_value(robot_in(rob, locations[0]), True)
        problem.set_initial_value(obj_on(objects[0], tables[0]), True)
        problem.set_initial_value(obj_on(objects[1], tables[1]), True)
        problem.add_goal(obj_on(objects[0], tables[-1]))
        problem.add_goal(obj_on(objects[1], tables[2]))
        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION,
        ) as cer:
            res = cer.compile(
                problem, CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
            )
        new_problem = res.problem
        self.assertTrue(cer._use_counter)
        for a, na in zip(problem.actions, new_problem.actions):
            self.assertTrue(isinstance(a, DurativeAction))
            self.assertFalse(isinstance(na, DurativeAction))
        self.assertEqual(len(problem.goals) + 2, len(new_problem.goals))
        self.assertEqual(len(new_problem.events), len(problem.actions) + 2)

    def test_ad_hoc_2(self):
        Robot = UserType("robot")
        Room = UserType("room")
        Obj = UserType("obj")
        Table = UserType("table")
        robot_in = Fluent("robot_in", robot=Robot, room=Room)
        connect = Fluent("connect", l_from=Room, l_to=Room)
        handvoid = Fluent("handvoid", robot=Robot)
        holding = Fluent("holding", robot=Robot, obj=Obj)
        obj_on = Fluent("obj_on", obj=Obj, table=Table)
        inside = Fluent("inside", table=Table, room=Room)
        pick_up = DurativeAction(
            "pick_up", robot=Robot, obj=Obj, table=Table, room=Room
        )
        pick_up.set_fixed_duration(2)
        robot = pick_up.parameter("robot")
        obj = pick_up.parameter("obj")
        table = pick_up.parameter("table")
        room = pick_up.parameter("room")
        pick_up.add_condition(StartTiming(), handvoid(robot))
        pick_up.add_condition(StartTiming(), inside(table, room))
        pick_up.add_condition(StartTiming(), obj_on(obj, table))
        pick_up.add_condition(StartTiming(), Not(holding(robot, obj)))
        pick_up.add_condition(
            ClosedTimeInterval(StartTiming(), EndTiming()), robot_in(robot, room)
        )
        pick_up.add_effect(StartTiming(), handvoid(robot), False)
        pick_up.add_effect(StartTiming(), obj_on(obj, table), False)
        pick_up.add_effect(EndTiming(), holding(robot, obj), True)
        put_down = DurativeAction(
            "put_down", robot=Robot, obj=Obj, table=Table, room=Room
        )
        put_down.set_fixed_duration(2)
        robot = put_down.parameter("robot")
        obj = put_down.parameter("obj")
        table = put_down.parameter("table")
        room = put_down.parameter("room")
        put_down.add_condition(StartTiming(), Not(handvoid(robot)))
        put_down.add_condition(StartTiming(), inside(table, room))
        put_down.add_condition(StartTiming(), Not(obj_on(obj, table)))
        put_down.add_condition(StartTiming(), holding(robot, obj))
        put_down.add_condition(
            ClosedTimeInterval(StartTiming(), EndTiming()), robot_in(robot, room)
        )
        put_down.add_effect(EndTiming(), obj_on(obj, table), True)
        put_down.add_effect(StartTiming(), holding(robot, obj), False)
        put_down.add_effect(EndTiming(), handvoid(robot), True)
        move = DurativeAction("move", robot=Robot, l_from=Room, l_to=Room)
        move.set_fixed_duration(5)
        robot = move.parameter("robot")
        l_from = move.parameter("l_from")
        l_to = move.parameter("l_to")
        move.add_condition(StartTiming(), robot_in(robot, l_from))
        move.add_condition(
            StartTiming(), Or(connect(l_from, l_to), connect(l_to, l_from))
        )
        move.add_effect(StartTiming(), robot_in(robot, l_from), False)
        move.add_effect(EndTiming(), robot_in(robot, l_to), True)
        problem = Problem("movimento")
        problem.add_fluent(robot_in, default_initial_value=False)
        problem.add_fluent(connect, default_initial_value=False)
        problem.add_fluent(handvoid, default_initial_value=True)
        problem.add_fluent(holding, default_initial_value=False)
        problem.add_fluent(obj_on, default_initial_value=False)
        problem.add_fluent(inside, default_initial_value=False)
        problem.add_action(pick_up)
        problem.add_action(put_down)
        problem.add_action(move)
        NLOC = 6
        locations = [Object("l%s" % i, Room) for i in range(NLOC)]
        problem.add_objects(locations)
        NTAB = 6
        tables = [Object("t%s" % i, Table) for i in range(NTAB)]
        problem.add_objects(tables)
        rob = Object("r", Robot)
        problem.add_object(rob)
        objects = [Object("o%s" % i, Obj) for i in range(2)]
        problem.add_objects(objects)
        for i in range(NLOC - 1):
            problem.set_initial_value(connect(locations[i], locations[i + 1]), True)
        for i in range(NLOC):
            problem.set_initial_value(inside(tables[i], locations[i]), True)
        problem.set_initial_value(robot_in(rob, locations[0]), True)
        problem.set_initial_value(obj_on(objects[0], tables[0]), True)
        problem.set_initial_value(obj_on(objects[1], tables[1]), True)
        problem.add_goal(obj_on(objects[0], tables[-1]))
        problem.add_goal(obj_on(objects[1], tables[2]))
        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION,
        ) as cer:
            cer._use_counter = False
            res = cer.compile(
                problem, CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
            )
        new_problem = res.problem
        self.assertFalse(cer._use_counter)
        for a, na in zip(problem.actions, new_problem.actions):
            self.assertTrue(isinstance(a, DurativeAction))
            self.assertFalse(isinstance(na, DurativeAction))
        self.assertEqual(len(new_problem.events), len(problem.actions) + 2)
        self.assertGreater(len(new_problem.goals), len(problem.goals))

    def test_ad_hoc3(self):
        problem = Problem("robot_with_variable_duration")
        Location = UserType("Location")
        Robot = UserType("Robot")

        is_at = Fluent("is_at", BoolType(), position=Location, robot=Robot)
        is_connected = Fluent(
            "is_connected", BoolType(), l_from=Location, l_to=Location
        )
        distance = Fluent("distance", RealType(), l_from=Location, l_to=Location)
        problem.add_fluent(is_at, default_initial_value=False)
        problem.add_fluent(is_connected, default_initial_value=False)
        problem.add_fluent(distance, default_initial_value=1)

        dur_move = DurativeAction("move", r=Robot, l_from=Location, l_to=Location)
        r = dur_move.parameter("r")
        l_from = dur_move.parameter("l_from")
        l_to = dur_move.parameter("l_to")
        dur_move.set_closed_duration_interval(5, 7)
        dur_move.add_condition(StartTiming(), is_connected(l_from, l_to))
        dur_move.add_condition(StartTiming(), is_at(l_from, r))
        dur_move.add_condition(StartTiming(), Not(is_at(l_to, r)))
        dur_move.add_effect(StartTiming(), is_at(l_from, r), False)
        dur_move.add_effect(EndTiming(), is_at(l_to, r), True)
        problem.add_action(dur_move)

        r1 = Object("r1", Robot)
        l1 = Object("l1", Location)
        l2 = Object("l2", Location)
        l3 = Object("l3", Location)
        l4 = Object("l4", Location)
        l5 = Object("l5", Location)
        problem.add_objects([r1, l1, l2, l3, l4, l5])

        problem.set_initial_value(is_at(l1, r1), True)
        problem.set_initial_value(is_connected(l1, l2), True)
        problem.set_initial_value(is_connected(l2, l3), True)
        problem.set_initial_value(is_connected(l3, l4), True)
        problem.set_initial_value(is_connected(l4, l5), True)
        problem.set_initial_value(distance(l1, l2), 10)
        problem.set_initial_value(distance(l2, l3), 10)
        problem.set_initial_value(distance(l3, l4), 10)
        problem.set_initial_value(distance(l4, l5), 10)

        problem.add_goal(is_at(l5, r1))

        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION,
        ) as cer:
            res = cer.compile(
                problem, CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
            )
        new_problem = res.problem
        self.assertTrue(cer._use_counter)
        self.assertEqual(2 * len(problem.actions), len(new_problem.actions))
        self.assertEqual(len(problem.actions), len(new_problem.processes))

    def test_ad_hoc_4(self):
        problem = Problem("robot_with_variable_duration")
        Location = UserType("Location")
        Robot = UserType("Robot")

        is_at = Fluent("is_at", BoolType(), position=Location, robot=Robot)
        is_connected = Fluent(
            "is_connected", BoolType(), l_from=Location, l_to=Location
        )
        distance = Fluent("distance", RealType(), l_from=Location, l_to=Location)
        problem.add_fluent(is_at, default_initial_value=False)
        problem.add_fluent(is_connected, default_initial_value=False)
        problem.add_fluent(distance, default_initial_value=1)

        dur_move = DurativeAction("move", r=Robot, l_from=Location, l_to=Location)
        r = dur_move.parameter("r")
        l_from = dur_move.parameter("l_from")
        l_to = dur_move.parameter("l_to")
        dur_move.set_open_duration_interval(5, 7)
        dur_move.add_condition(StartTiming(), is_connected(l_from, l_to))
        dur_move.add_condition(StartTiming(), is_at(l_from, r))
        dur_move.add_condition(StartTiming(), Not(is_at(l_to, r)))
        dur_move.add_effect(StartTiming(), is_at(l_from, r), False)
        dur_move.add_effect(EndTiming(), is_at(l_to, r), True)
        problem.add_action(dur_move)

        r1 = Object("r1", Robot)
        l1 = Object("l1", Location)
        l2 = Object("l2", Location)
        l3 = Object("l3", Location)
        l4 = Object("l4", Location)
        l5 = Object("l5", Location)
        problem.add_objects([r1, l1, l2, l3, l4, l5])

        problem.set_initial_value(is_at(l1, r1), True)
        problem.set_initial_value(is_connected(l1, l2), True)
        problem.set_initial_value(is_connected(l2, l3), True)
        problem.set_initial_value(is_connected(l3, l4), True)
        problem.set_initial_value(is_connected(l4, l5), True)
        problem.set_initial_value(distance(l1, l2), 10)
        problem.set_initial_value(distance(l2, l3), 10)
        problem.set_initial_value(distance(l3, l4), 10)
        problem.set_initial_value(distance(l4, l5), 10)

        problem.add_goal(is_at(l5, r1))

        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION,
        ) as cer:
            cer._use_counter = False
            res = cer.compile(
                problem, CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
            )
        new_problem = res.problem
        self.assertFalse(cer._use_counter)
        self.assertEqual(2 * len(problem.actions), len(new_problem.actions))
        self.assertEqual(len(problem.actions), len(new_problem.processes))
