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

from typing import Tuple
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
from unified_planning.engines.results import (
    ValidationResultStatus,
    PlanGenerationResultStatus,
)
from unified_planning.exceptions import UPNoSuitableEngineAvailableException
from unified_planning.plans import TimeTriggeredPlan


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

        for a, na in zip(problem.actions, new_problem.actions):
            self.assertTrue(isinstance(a, DurativeAction))
            self.assertFalse(isinstance(na, DurativeAction))
        self.assertEqual(
            len(new_problem.fluents),
            (len(problem.fluents) + (len(problem.actions) * 2) + 1),
        )
        self.assertEqual(len(problem.actions), len(new_problem.actions))
        self.assertEqual(len(problem.actions), len(new_problem.processes))
        self.assertEqual(len(problem.processes), 0)
        self.assertEqual(len(new_problem.events), len(problem.actions) * 2)
        self.assertEqual(len(problem.events), 0)
        self.assertEqual(
            len(new_problem.goals), len(problem.goals) + len(problem.actions) + 1
        )

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
        self.assertEqual(len(new_problem.events), len(problem.actions) * 2)
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
        problem = self.problems["robot_holding"].problem

        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION,
        ) as cer:
            res = cer.compile(
                problem, CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
            )
        new_problem = res.problem
        for a, na in zip(problem.actions, new_problem.actions):
            self.assertIsInstance(a, DurativeAction)
            self.assertIsInstance(na, InstantaneousAction)
        goal_counter = len(problem.goals) + 1  # old goals + alive
        for a in problem.actions:
            if isinstance(a, DurativeAction):
                running_fluents = 1
                for p in a.parameters:
                    running_fluents *= len(tuple(problem.objects(p.type)))
                goal_counter += running_fluents
        self.assertEqual(goal_counter, len(new_problem.goals))
        # every action has an end event, a duration exceeded event and
        # the 2 overall conditions of pick_up and put_down actions
        events = len(problem.actions) * 2 + 2
        self.assertEqual(len(new_problem.events), events)

    # TODO this test uses the use_counter flag
    # def test_ad_hoc_2(self):
    #     problem = self.problems["robot_holding"].problem
    #     with Compiler(
    #         problem_kind=problem.kind,
    #         compilation_kind=CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION,
    #     ) as cer:
    #         cer._use_counter = False
    #         res = cer.compile(
    #             problem, CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
    #         )
    #     new_problem = res.problem
    #     self.assertFalse(cer._use_counter)
    #     for a, na in zip(problem.actions, new_problem.actions):
    #         self.assertTrue(isinstance(a, DurativeAction))
    #         self.assertFalse(isinstance(na, DurativeAction))
    #     events = len(problem.actions) * 2 + 2
    #     self.assertEqual(len(new_problem.events), events)
    #     self.assertGreater(len(new_problem.goals), len(problem.goals))

    def test_ad_hoc3(self):
        # problem = Problem("robot_with_variable_duration")
        # Location = UserType("Location")
        # Robot = UserType("Robot")

        # is_at = Fluent("is_at", BoolType(), position=Location, robot=Robot)
        # is_connected = Fluent(
        #     "is_connected", BoolType(), l_from=Location, l_to=Location
        # )
        # distance = Fluent("distance", RealType(), l_from=Location, l_to=Location)
        # problem.add_fluent(is_at, default_initial_value=False)
        # problem.add_fluent(is_connected, default_initial_value=False)
        # problem.add_fluent(distance, default_initial_value=1)

        # dur_move = DurativeAction("move", r=Robot, l_from=Location, l_to=Location)
        # r = dur_move.parameter("r")
        # l_from = dur_move.parameter("l_from")
        # l_to = dur_move.parameter("l_to")
        # dur_move.set_closed_duration_interval(5, 7)
        # dur_move.add_condition(StartTiming(), is_connected(l_from, l_to))
        # dur_move.add_condition(StartTiming(), is_at(l_from, r))
        # dur_move.add_condition(StartTiming(), Not(is_at(l_to, r)))
        # dur_move.add_effect(StartTiming(), is_at(l_from, r), False)
        # dur_move.add_effect(EndTiming(), is_at(l_to, r), True)
        # problem.add_action(dur_move)

        # r1 = Object("r1", Robot)
        # l1 = Object("l1", Location)
        # l2 = Object("l2", Location)
        # l3 = Object("l3", Location)
        # l4 = Object("l4", Location)
        # l5 = Object("l5", Location)
        # problem.add_objects([r1, l1, l2, l3, l4, l5])

        # problem.set_initial_value(is_at(l1, r1), True)
        # problem.set_initial_value(is_connected(l1, l2), True)
        # problem.set_initial_value(is_connected(l2, l3), True)
        # problem.set_initial_value(is_connected(l3, l4), True)
        # problem.set_initial_value(is_connected(l4, l5), True)
        # problem.set_initial_value(distance(l1, l2), 10)
        # problem.set_initial_value(distance(l2, l3), 10)
        # problem.set_initial_value(distance(l3, l4), 10)
        # problem.set_initial_value(distance(l4, l5), 10)

        # problem.add_goal(is_at(l5, r1))

        problem = self.problems["robot_with_variable_duration [5, 7]"].problem

        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION,
        ) as cer:
            res = cer.compile(
                problem, CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
            )
        new_problem = res.problem
        self.assertEqual(2 * len(problem.actions), len(new_problem.actions))
        self.assertEqual(len(problem.actions), len(new_problem.processes))

    def test_ad_hoc_4(self):
        # problem = Problem("robot_with_variable_duration")
        # Location = UserType("Location")
        # Robot = UserType("Robot")

        # is_at = Fluent("is_at", BoolType(), position=Location, robot=Robot)
        # is_connected = Fluent(
        #     "is_connected", BoolType(), l_from=Location, l_to=Location
        # )
        # distance = Fluent("distance", RealType(), l_from=Location, l_to=Location)
        # problem.add_fluent(is_at, default_initial_value=False)
        # problem.add_fluent(is_connected, default_initial_value=False)
        # problem.add_fluent(distance, default_initial_value=1)

        # dur_move = DurativeAction("move", r=Robot, l_from=Location, l_to=Location)
        # r = dur_move.parameter("r")
        # l_from = dur_move.parameter("l_from")
        # l_to = dur_move.parameter("l_to")
        # dur_move.set_open_duration_interval(5, 7)
        # dur_move.add_condition(StartTiming(), is_connected(l_from, l_to))
        # dur_move.add_condition(StartTiming(), is_at(l_from, r))
        # dur_move.add_condition(StartTiming(), Not(is_at(l_to, r)))
        # dur_move.add_effect(StartTiming(), is_at(l_from, r), False)
        # dur_move.add_effect(EndTiming(), is_at(l_to, r), True)
        # problem.add_action(dur_move)

        # r1 = Object("r1", Robot)
        # l1 = Object("l1", Location)
        # l2 = Object("l2", Location)
        # l3 = Object("l3", Location)
        # l4 = Object("l4", Location)
        # l5 = Object("l5", Location)
        # problem.add_objects([r1, l1, l2, l3, l4, l5])

        # problem.set_initial_value(is_at(l1, r1), True)
        # problem.set_initial_value(is_connected(l1, l2), True)
        # problem.set_initial_value(is_connected(l2, l3), True)
        # problem.set_initial_value(is_connected(l3, l4), True)
        # problem.set_initial_value(is_connected(l4, l5), True)
        # problem.set_initial_value(distance(l1, l2), 10)
        # problem.set_initial_value(distance(l2, l3), 10)
        # problem.set_initial_value(distance(l3, l4), 10)
        # problem.set_initial_value(distance(l4, l5), 10)

        # problem.add_goal(is_at(l5, r1))

        problem = self.problems["robot_with_variable_duration (5, 7)"].problem

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

    def test_ad_hoc_5(self):
        # problem = Problem("robot_with_variable_duration")
        # Location = UserType("Location")
        # Robot = UserType("Robot")

        # is_at = Fluent("is_at", BoolType(), position=Location, robot=Robot)
        # is_connected = Fluent(
        #     "is_connected", BoolType(), l_from=Location, l_to=Location
        # )
        # distance = Fluent("distance", RealType(), l_from=Location, l_to=Location)
        # problem.add_fluent(is_at, default_initial_value=False)
        # problem.add_fluent(is_connected, default_initial_value=False)
        # problem.add_fluent(distance, default_initial_value=1)

        # dur_move = DurativeAction("move", r=Robot, l_from=Location, l_to=Location)
        # r = dur_move.parameter("r")
        # l_from = dur_move.parameter("l_from")
        # l_to = dur_move.parameter("l_to")
        # dur_move.set_fixed_duration(5)
        # dur_move.add_condition(StartTiming(), is_connected(l_from, l_to))
        # dur_move.add_condition(StartTiming(), is_at(l_from, r))
        # dur_move.add_condition(StartTiming(), Not(is_at(l_to, r)))
        # dur_move.add_effect(StartTiming() + 1, is_at(l_from, r), False)
        # dur_move.add_effect(EndTiming(), is_at(l_to, r), True)
        # problem.add_action(dur_move)

        # r1 = Object("r1", Robot)
        # l1 = Object("l1", Location)
        # l2 = Object("l2", Location)
        # l3 = Object("l3", Location)
        # l4 = Object("l4", Location)
        # l5 = Object("l5", Location)
        # problem.add_objects([r1, l1, l2, l3, l4, l5])

        # problem.set_initial_value(is_at(l1, r1), True)
        # problem.set_initial_value(is_connected(l1, l2), True)
        # problem.set_initial_value(is_connected(l2, l3), True)
        # problem.set_initial_value(is_connected(l3, l4), True)
        # problem.set_initial_value(is_connected(l4, l5), True)
        # problem.set_initial_value(distance(l1, l2), 10)
        # problem.set_initial_value(distance(l2, l3), 10)
        # problem.set_initial_value(distance(l3, l4), 10)
        # problem.set_initial_value(distance(l4, l5), 10)

        # problem.add_goal(is_at(l5, r1))

        problem = self.problems[
            "robot_with_variable_duration [5, 5] start delay eff 1"
        ].problem

        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION,
        ) as cer:
            res = cer.compile(
                problem, CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
            )
        new_problem = res.problem
        events = len(problem.actions) * 2 + 1
        self.assertEqual(len(new_problem.events), events)

    def test_ad_hoc_6(self):
        # problem = Problem("robot_with_variable_duration")
        # Location = UserType("Location")
        # Robot = UserType("Robot")

        # is_at = Fluent("is_at", BoolType(), position=Location, robot=Robot)
        # is_connected = Fluent(
        #     "is_connected", BoolType(), l_from=Location, l_to=Location
        # )
        # distance = Fluent("distance", RealType(), l_from=Location, l_to=Location)
        # problem.add_fluent(is_at, default_initial_value=False)
        # problem.add_fluent(is_connected, default_initial_value=False)
        # problem.add_fluent(distance, default_initial_value=1)

        # dur_move = DurativeAction("move", r=Robot, l_from=Location, l_to=Location)
        # r = dur_move.parameter("r")
        # l_from = dur_move.parameter("l_from")
        # l_to = dur_move.parameter("l_to")
        # dur_move.set_fixed_duration(5)
        # dur_move.add_condition(StartTiming(), is_connected(l_from, l_to))
        # dur_move.add_condition(StartTiming(), is_at(l_from, r))
        # dur_move.add_condition(StartTiming(), Not(is_at(l_to, r)))
        # dur_move.add_effect(StartTiming(), is_at(l_from, r), False)
        # dur_move.add_effect(EndTiming() - 1, is_at(l_to, r), True)
        # problem.add_action(dur_move)

        # r1 = Object("r1", Robot)
        # l1 = Object("l1", Location)
        # l2 = Object("l2", Location)
        # l3 = Object("l3", Location)
        # l4 = Object("l4", Location)
        # l5 = Object("l5", Location)
        # problem.add_objects([r1, l1, l2, l3, l4, l5])

        # problem.set_initial_value(is_at(l1, r1), True)
        # problem.set_initial_value(is_connected(l1, l2), True)
        # problem.set_initial_value(is_connected(l2, l3), True)
        # problem.set_initial_value(is_connected(l3, l4), True)
        # problem.set_initial_value(is_connected(l4, l5), True)
        # problem.set_initial_value(distance(l1, l2), 10)
        # problem.set_initial_value(distance(l2, l3), 10)
        # problem.set_initial_value(distance(l3, l4), 10)
        # problem.set_initial_value(distance(l4, l5), 10)

        # problem.add_goal(is_at(l5, r1))

        problem = self.problems[
            "robot_with_variable_duration [5, 5] end delay eff 1"
        ].problem

        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION,
        ) as cer:
            res = cer.compile(
                problem, CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
            )
        new_problem = res.problem
        events = len(problem.actions) * 2 + 1
        self.assertEqual(len(new_problem.events), events)

    def test_ad_hoc_7(self):
        # problem = Problem("robot_with_variable_duration")
        # Location = UserType("Location")
        # Robot = UserType("Robot")

        # is_at = Fluent("is_at", BoolType(), position=Location, robot=Robot)
        # is_connected = Fluent(
        #     "is_connected", BoolType(), l_from=Location, l_to=Location
        # )
        # distance = Fluent("distance", RealType(), l_from=Location, l_to=Location)
        # problem.add_fluent(is_at, default_initial_value=False)
        # problem.add_fluent(is_connected, default_initial_value=False)
        # problem.add_fluent(distance, default_initial_value=1)

        # dur_move = DurativeAction("move", r=Robot, l_from=Location, l_to=Location)
        # r = dur_move.parameter("r")
        # l_from = dur_move.parameter("l_from")
        # l_to = dur_move.parameter("l_to")
        # dur_move.set_closed_duration_interval(3, 5)
        # dur_move.add_condition(StartTiming(), is_connected(l_from, l_to))
        # dur_move.add_condition(StartTiming(), is_at(l_from, r))
        # dur_move.add_condition(StartTiming(), Not(is_at(l_to, r)))
        # dur_move.add_effect(StartTiming(), is_at(l_from, r), False)
        # dur_move.add_effect(EndTiming() - 1, is_at(l_to, r), True)
        # problem.add_action(dur_move)

        # r1 = Object("r1", Robot)
        # l1 = Object("l1", Location)
        # l2 = Object("l2", Location)
        # l3 = Object("l3", Location)
        # l4 = Object("l4", Location)
        # l5 = Object("l5", Location)
        # problem.add_objects([r1, l1, l2, l3, l4, l5])

        # problem.set_initial_value(is_at(l1, r1), True)
        # problem.set_initial_value(is_connected(l1, l2), True)
        # problem.set_initial_value(is_connected(l2, l3), True)
        # problem.set_initial_value(is_connected(l3, l4), True)
        # problem.set_initial_value(is_connected(l4, l5), True)
        # problem.set_initial_value(distance(l1, l2), 10)
        # problem.set_initial_value(distance(l2, l3), 10)
        # problem.set_initial_value(distance(l3, l4), 10)
        # problem.set_initial_value(distance(l4, l5), 10)

        # problem.add_goal(is_at(l5, r1))

        problem = self.problems[
            "robot_with_variable_duration [3, 5] end delay eff 1"
        ].problem

        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION,
        ) as cer:
            res = cer.compile(
                problem, CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
            )
        new_problem = res.problem
        events = len(problem.actions) * 3
        self.assertEqual(len(new_problem.events), events)
        self.assertEqual(len(new_problem.actions), len(problem.actions) + 1)

    def test_ad_hoc_8(self):
        # problem = Problem("robot_with_variable_duration")
        # Location = UserType("Location")
        # Robot = UserType("Robot")

        # is_at = Fluent("is_at", BoolType(), position=Location, robot=Robot)
        # is_connected = Fluent(
        #     "is_connected", BoolType(), l_from=Location, l_to=Location
        # )
        # distance = Fluent("distance", RealType(), l_from=Location, l_to=Location)
        # problem.add_fluent(is_at, default_initial_value=False)
        # problem.add_fluent(is_connected, default_initial_value=False)
        # problem.add_fluent(distance, default_initial_value=1)

        # dur_move = DurativeAction("move", r=Robot, l_from=Location, l_to=Location)
        # r = dur_move.parameter("r")
        # l_from = dur_move.parameter("l_from")
        # l_to = dur_move.parameter("l_to")
        # dur_move.set_fixed_duration(7)
        # dur_move.add_condition(StartTiming() + 1, is_connected(l_from, l_to))
        # dur_move.add_condition(StartTiming(), is_at(l_from, r))
        # dur_move.add_condition(StartTiming() + 1, Not(is_at(l_to, r)))
        # dur_move.add_effect(StartTiming(), is_at(l_from, r), False)
        # dur_move.add_effect(EndTiming(), is_at(l_to, r), True)
        # problem.add_action(dur_move)

        # r1 = Object("r1", Robot)
        # l1 = Object("l1", Location)
        # l2 = Object("l2", Location)
        # l3 = Object("l3", Location)
        # l4 = Object("l4", Location)
        # l5 = Object("l5", Location)
        # problem.add_objects([r1, l1, l2, l3, l4, l5])

        # problem.set_initial_value(is_at(l1, r1), True)
        # problem.set_initial_value(is_connected(l1, l2), True)
        # problem.set_initial_value(is_connected(l2, l3), True)
        # problem.set_initial_value(is_connected(l3, l4), True)
        # problem.set_initial_value(is_connected(l4, l5), True)
        # problem.set_initial_value(distance(l1, l2), 10)
        # problem.set_initial_value(distance(l2, l3), 10)
        # problem.set_initial_value(distance(l3, l4), 10)
        # problem.set_initial_value(distance(l4, l5), 10)

        # problem.add_goal(is_at(l5, r1))

        problem = self.problems[
            "robot_with_variable_duration [7, 7] start delay cond 1"
        ].problem

        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION,
        ) as cer:
            cer._use_counter = True
            res = cer.compile(
                problem, CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
            )
        new_problem = res.problem
        self.assertTrue(cer._use_counter)
        self.assertEqual(len(new_problem.events), len(problem.actions) + 2)
        self.assertEqual(len(new_problem.actions), len(problem.actions))

    def test_ad_hoc_9(self):
        # problem = Problem("robot_with_variable_duration")
        # Location = UserType("Location")
        # Robot = UserType("Robot")

        # is_at = Fluent("is_at", BoolType(), position=Location, robot=Robot)
        # is_connected = Fluent(
        #     "is_connected", BoolType(), l_from=Location, l_to=Location
        # )
        # distance = Fluent("distance", RealType(), l_from=Location, l_to=Location)
        # problem.add_fluent(is_at, default_initial_value=False)
        # problem.add_fluent(is_connected, default_initial_value=False)
        # problem.add_fluent(distance, default_initial_value=1)

        # dur_move = DurativeAction("move", r=Robot, l_from=Location, l_to=Location)
        # r = dur_move.parameter("r")
        # l_from = dur_move.parameter("l_from")
        # l_to = dur_move.parameter("l_to")
        # dur_move.set_fixed_duration(7)
        # dur_move.add_condition(StartTiming(), is_connected(l_from, l_to))
        # dur_move.add_condition(StartTiming(), is_at(l_from, r))
        # dur_move.add_condition(EndTiming() - 1, Not(is_at(l_to, r)))
        # dur_move.add_effect(StartTiming(), is_at(l_from, r), False)
        # dur_move.add_effect(EndTiming(), is_at(l_to, r), True)
        # problem.add_action(dur_move)

        # r1 = Object("r1", Robot)
        # l1 = Object("l1", Location)
        # l2 = Object("l2", Location)
        # l3 = Object("l3", Location)
        # l4 = Object("l4", Location)
        # l5 = Object("l5", Location)
        # problem.add_objects([r1, l1, l2, l3, l4, l5])

        # problem.set_initial_value(is_at(l1, r1), True)
        # problem.set_initial_value(is_connected(l1, l2), True)
        # problem.set_initial_value(is_connected(l2, l3), True)
        # problem.set_initial_value(is_connected(l3, l4), True)
        # problem.set_initial_value(is_connected(l4, l5), True)
        # problem.set_initial_value(distance(l1, l2), 10)
        # problem.set_initial_value(distance(l2, l3), 10)
        # problem.set_initial_value(distance(l3, l4), 10)
        # problem.set_initial_value(distance(l4, l5), 10)

        # problem.add_goal(is_at(l5, r1))

        problem = self.problems[
            "robot_with_variable_duration [7, 7] end delay cond 1"
        ].problem

        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION,
        ) as cer:
            res = cer.compile(
                problem, CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
            )
        new_problem = res.problem
        events = len(problem.actions) * 2 + 1
        self.assertEqual(len(new_problem.events), events)
        self.assertEqual(len(new_problem.actions), len(problem.actions))

    def test_ad_hoc_10(self):
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
        pick_up.set_fixed_duration(3)
        robot = pick_up.parameter("robot")
        obj = pick_up.parameter("obj")
        table = pick_up.parameter("table")
        room = pick_up.parameter("room")
        pick_up.add_condition(StartTiming(), handvoid(robot))
        pick_up.add_condition(StartTiming(), inside(table, room))
        pick_up.add_condition(StartTiming(), obj_on(obj, table))
        pick_up.add_condition(StartTiming(), Not(holding(robot, obj)))
        pick_up.add_condition(
            ClosedTimeInterval(StartTiming() + 1, StartTiming() + 3),
            robot_in(robot, room),
        )
        pick_up.add_effect(StartTiming(), handvoid(robot), False)
        pick_up.add_effect(StartTiming(), obj_on(obj, table), False)
        pick_up.add_effect(EndTiming(), holding(robot, obj), True)
        put_down = DurativeAction(
            "put_down", robot=Robot, obj=Obj, table=Table, room=Room
        )
        put_down.set_fixed_duration(3)
        robot = put_down.parameter("robot")
        obj = put_down.parameter("obj")
        table = put_down.parameter("table")
        room = put_down.parameter("room")
        put_down.add_condition(StartTiming(), Not(handvoid(robot)))
        put_down.add_condition(StartTiming(), inside(table, room))
        put_down.add_condition(StartTiming(), Not(obj_on(obj, table)))
        put_down.add_condition(StartTiming(), holding(robot, obj))
        put_down.add_condition(
            OpenTimeInterval(StartTiming() + 1, StartTiming() + 3),
            robot_in(robot, room),
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
            cer._use_counter = True
            res = cer.compile(
                problem, CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
            )
        new_problem = res.problem
        events = len(problem.actions) * 2 + 2
        self.assertEqual(len(new_problem.events), events)

    def test_ad_hoc_11(self):
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
        pick_up.set_fixed_duration(3)
        robot = pick_up.parameter("robot")
        obj = pick_up.parameter("obj")
        table = pick_up.parameter("table")
        room = pick_up.parameter("room")
        pick_up.add_condition(StartTiming(), handvoid(robot))
        pick_up.add_condition(StartTiming(), inside(table, room))
        pick_up.add_condition(StartTiming(), obj_on(obj, table))
        pick_up.add_condition(StartTiming(), Not(holding(robot, obj)))
        pick_up.add_condition(
            ClosedTimeInterval(EndTiming() - 3, EndTiming() - 1),
            robot_in(robot, room),
        )
        pick_up.add_effect(StartTiming(), handvoid(robot), False)
        pick_up.add_effect(StartTiming(), obj_on(obj, table), False)
        pick_up.add_effect(EndTiming(), holding(robot, obj), True)
        put_down = DurativeAction(
            "put_down", robot=Robot, obj=Obj, table=Table, room=Room
        )
        put_down.set_fixed_duration(3)
        robot = put_down.parameter("robot")
        obj = put_down.parameter("obj")
        table = put_down.parameter("table")
        room = put_down.parameter("room")
        put_down.add_condition(StartTiming(), Not(handvoid(robot)))
        put_down.add_condition(StartTiming(), inside(table, room))
        put_down.add_condition(StartTiming(), Not(obj_on(obj, table)))
        put_down.add_condition(StartTiming(), holding(robot, obj))
        put_down.add_condition(
            OpenTimeInterval(EndTiming() - 3, EndTiming() - 1),
            robot_in(robot, room),
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
        events = len(problem.actions) * 2 + 2
        self.assertEqual(len(new_problem.events), events)

    def test_ad_hoc_12(self):
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
        pick_up.set_fixed_duration(5)
        robot = pick_up.parameter("robot")
        obj = pick_up.parameter("obj")
        table = pick_up.parameter("table")
        room = pick_up.parameter("room")
        pick_up.add_condition(StartTiming(), handvoid(robot))
        pick_up.add_condition(StartTiming(), inside(table, room))
        pick_up.add_condition(StartTiming(), obj_on(obj, table))
        pick_up.add_condition(StartTiming(), Not(holding(robot, obj)))
        pick_up.add_condition(
            ClosedTimeInterval(StartTiming() + 2, EndTiming() - 1),
            robot_in(robot, room),
        )
        pick_up.add_effect(StartTiming(), handvoid(robot), False)
        pick_up.add_effect(StartTiming(), obj_on(obj, table), False)
        pick_up.add_effect(EndTiming(), holding(robot, obj), True)
        put_down = DurativeAction(
            "put_down", robot=Robot, obj=Obj, table=Table, room=Room
        )
        put_down.set_fixed_duration(3)
        robot = put_down.parameter("robot")
        obj = put_down.parameter("obj")
        table = put_down.parameter("table")
        room = put_down.parameter("room")
        put_down.add_condition(StartTiming(), Not(handvoid(robot)))
        put_down.add_condition(StartTiming(), inside(table, room))
        put_down.add_condition(StartTiming(), Not(obj_on(obj, table)))
        put_down.add_condition(StartTiming(), holding(robot, obj))
        put_down.add_condition(
            OpenTimeInterval(StartTiming(), EndTiming()),
            robot_in(robot, room),
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
        events = len(problem.actions) * 2 + 2
        self.assertEqual(len(new_problem.events), events)

    def test_all(self):

        with OneshotPlanner(
            name="opt-pddl-planner",
            params={"params": "-d 0.001"},  # set epsilon as 0.001
        ) as solver:

            with Compiler(
                name="up_durative_actions_to_processes",
                compilation_kind=CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION,
            ) as cer:
                for problem_name, tc in self.problems.items():
                    problem = tc.problem
                    if not isinstance(problem, Problem):
                        continue
                    kind = problem.kind
                    if any(
                        not isinstance(a, (DurativeAction, InstantaneousAction))
                        for a in problem.actions
                    ):
                        continue
                    if all(isinstance(a, InstantaneousAction) for a in problem.actions):
                        continue
                    if not cer.supports(kind):
                        continue
                    res = cer.compile(
                        problem,
                        CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION,
                    )
                    new_problem = res.problem
                    if not solver.supports(new_problem.kind):
                        continue
                    solver_res = solver.solve(new_problem, timeout=5)
                    plan = solver_res.plan
                    if solver_res.status == PlanGenerationResultStatus.TIMEOUT:
                        continue
                    self.assertIsInstance(plan, TimeTriggeredPlan, problem_name)
                    original_plan = res.plan_back_conversion(plan)

                    with PlanValidator(problem_kind=problem.kind) as validator:
                        val_res = validator.validate(problem, original_plan)
                        self.assertEqual(
                            val_res.status, ValidationResultStatus.VALID, problem_name
                        )

    # TODO this test is local to have proof and does not work in CI
    # def test_all_val(self):
    #     env = get_environment()
    #     try:
    #         env.factory.add_engine("val", "up_val.VAL","VAL")
    #     except Exception as e:
    #         return

    #     validator = PlanValidator(name="val")
    #     solved, skipped = [], []

    #     with Compiler(
    #         name="up_durative_actions_to_processes",
    #         compilation_kind=CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION,
    #         params={"default_epsilon": "1/10000"}
    #     ) as cer:
    #         for problem_name, tc in self.problems.items():
    #             known_skips = {
    #                 "timed_connected_locations", # TODO understand why no output
    #             }
    #             if problem_name in known_skips:
    #                 continue
    #             problem = tc.problem
    #             if not isinstance(problem, Problem):
    #                 continue
    #             kind = problem.kind
    #             if any(
    #                 not isinstance(a, (DurativeAction, InstantaneousAction))
    #                 for a in problem.actions
    #             ):
    #                 continue
    #             if all(isinstance(a, InstantaneousAction) for a in problem.actions):
    #                 continue
    #             if not cer.supports(kind):
    #                 continue
    #             res = cer.compile(
    #                 problem,
    #                 CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION,
    #             )
    #             compiled_problem = res.problem
    #             print("-"*50, end="")
    #             print("PROBLEM NAME: ", problem_name)
    #             print(validator.supports(compiled_problem.kind))
    #             # print(problem)
    #             for original_plan in tc.valid_plans:
    #                 compiled_plan = res.plan_forward_conversion(original_plan)
    #                 self.assertIsInstance(compiled_plan, TimeTriggeredPlan, problem_name)
    #                 new_problem, compiled_plan = _add_end_action(original_plan, compiled_plan, compiled_problem)
    #                 if not validator.supports(new_problem.kind):
    #                     skipped.append(problem_name)
    #                     continue

    #                 # with PlanValidator(problem_kind=new_problem.kind) as validator:
    #                 # with PlanValidator(name="val") as validator:
    #                 val_res = validator.validate(new_problem, compiled_plan)

    #                 if val_res.status != ValidationResultStatus.VALID:
    #                     from pprint import pprint
    #                     print(new_problem.goals)
    #                     print(compiled_plan)
    #                     print(val_res)
    #                     for k, v in val_res.trace.items():
    #                         print(f"Time: {k}")
    #                         print(f"State: {v}")

    #                     # pprint(val_res.trace)
    #                 self.assertEqual(
    #                     val_res.status, ValidationResultStatus.VALID, problem_name
    #                 )
    #                 solved.append(problem_name)

    #     print(skipped)
    #     print(solved)
    #     assert False


def _add_end_action(
    original_plan: TimeTriggeredPlan,
    compiled_plan: TimeTriggeredPlan,
    compiled_problem: Problem,
) -> Tuple[Problem, TimeTriggeredPlan]:
    original_plan_duration = Fraction(1)
    for trigger_time, _, duration in original_plan.timed_actions:
        end_action = trigger_time
        if duration is not None:
            end_action = trigger_time + duration
        original_plan_duration = max(original_plan_duration, end_action)

    original_plan_duration = original_plan_duration + 5 * 3
    compiled_plan_actions = list(compiled_plan.timed_actions)

    new_problem = compiled_problem.clone()
    alive = new_problem.fluent("alive")
    useless_action = InstantaneousAction("useless")
    useless_action.add_precondition(alive)
    useless_action.add_effect(alive, True)
    new_problem.add_action(useless_action)

    compiled_plan_actions.append((original_plan_duration, useless_action(), None))

    return new_problem, TimeTriggeredPlan(compiled_plan_actions)
