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


import unified_planning
from unified_planning.shortcuts import *
from unified_planning.test.examples import get_example_problems
from unified_planning.test import TestCase, main


class TestModel(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_clone_problem_and_action(self):
        for _, (problem, _) in self.problems.items():
            problem_clone_1 = problem.clone()
            problem_clone_2 = problem.clone()
            for action_1, action_2 in zip(problem_clone_1.actions, problem_clone_2.actions):
                if isinstance(action_2, InstantaneousAction):
                    action_2._effects = []
                    action_1_clone = action_1.clone()
                    action_1_clone._effects = []
                elif isinstance(action_2, DurativeAction):
                    action_2._effects = {}
                    action_1_clone = action_1.clone()
                    action_1_clone._effects = {}
                else:
                    raise NotImplementedError
                self.assertEqual(action_2, action_1_clone)
                self.assertEqual(action_1_clone, action_2)
                self.assertNotEqual(action_1, action_1_clone)
                self.assertNotEqual(action_1_clone, action_1)
                self.assertNotEqual(action_1, action_1_clone.name)
                self.assertNotEqual(action_1_clone.name, action_1)
            self.assertEqual(problem_clone_1, problem)
            self.assertEqual(problem, problem_clone_1)
            self.assertNotEqual(problem_clone_2, problem)
            self.assertNotEqual(problem, problem_clone_2)

    def test_clone_action(self):
        Location = UserType('Location')
        a = Action('move', l_from=Location, l_to=Location)
        with self.assertRaises(NotImplementedError):
            a.clone()
        with self.assertRaises(NotImplementedError):
            hash(a)
        with self.assertRaises(NotImplementedError):
            a == a.name
        with self.assertRaises(NotImplementedError):
            a.is_conditional()

    def test_clone_effect(self):
        x = FluentExp(Fluent('x'))
        y = FluentExp(Fluent('y'))
        z = FluentExp(Fluent('z'))
        e = Effect(x, z, y, unified_planning.model.EffectKind.ASSIGN)
        e_clone_1 = e.clone()
        e_clone_2 = e.clone()
        e_clone_2._condition = TRUE()
        self.assertEqual(e_clone_1, e)
        self.assertEqual(e, e_clone_1)
        self.assertNotEqual(e_clone_2, e)
        self.assertNotEqual(e, e_clone_2)
        self.assertNotEqual(e, e.value)
        self.assertNotEqual(e.value, e)

    def test_istantaneous_action(self):
        Location = UserType('Location')
        move = InstantaneousAction('move', l_from=Location, l_to=Location)
        km = Fluent('km', IntType())
        move.add_increase_effect(km, 10)
        e = Effect(FluentExp(km), Int(10), TRUE(), unified_planning.model.EffectKind.INCREASE)
        self.assertEqual(move.effects[0], e)

    def test_durative_action(self):
        Location = UserType('Location')
        x = Fluent('x')
        move = DurativeAction('move', l_from=Location, l_to=Location)
        km = Fluent('km', IntType())
        move.add_decrease_effect(StartTiming(), km, 5)
        move.add_increase_effect(EndTiming(), km, 20)
        e_end = Effect(FluentExp(km), Int(20), TRUE(), unified_planning.model.EffectKind.INCREASE)
        e_start = Effect(FluentExp(km), Int(5), TRUE(), unified_planning.model.EffectKind.DECREASE)
        effects_test = {StartTiming(): [e_start], EndTiming(): [e_end]}
        self.assertEqual(effects_test, move.effects)
        move.set_closed_duration_interval(1, 2)
        self.assertEqual(move.duration, ClosedDurationInterval(Int(1), Int(2)))
        move.set_open_duration_interval(2, Fraction(7, 2))
        self.assertEqual(move.duration, OpenDurationInterval(Int(2), Real(Fraction(7, 2))))
        move.set_left_open_duration_interval(1, 2)
        self.assertEqual(move.duration, LeftOpenDurationInterval(Int(1), Int(2)))
        move.set_right_open_duration_interval(1, 2)
        self.assertEqual(move.duration, RightOpenDurationInterval(Int(1), Int(2)))
        move.add_condition(StartTiming(), x)
        move.add_condition(ClosedTimeInterval(StartTiming(), EndTiming()), x)
        self.assertIn('duration = [1, 2)', str(move))

    def test_problem(self):
        x = Fluent('x')
        y = Fluent('y')
        km = Fluent('km', IntType())
        problem = Problem('problem_test')
        problem.add_fluent(x, default_initial_value=True)
        problem.add_fluent(y, default_initial_value=False)
        problem.add_fluent(km, default_initial_value=Int(0))
        problem.add_timed_effect(GlobalStartTiming(5), x, y)
        problem.add_timed_goal(GlobalStartTiming(11), x)
        problem.add_timed_goal(TimeInterval(GlobalStartTiming(5), GlobalStartTiming(9)), x)
        problem.add_action(DurativeAction('move'))
        problem.add_action(InstantaneousAction('stop_moving'))
        stop_moving_list = [a for a in problem.instantaneous_actions]
        self.assertEqual(len(stop_moving_list), 1)
        stop_moving = stop_moving_list[0]
        self.assertEqual(stop_moving.name, 'stop_moving')
        move_list = [a for a in problem.durative_actions]
        self.assertEqual(len(move_list), 1)
        move = move_list[0]
        self.assertEqual(move.name, 'move')
        problem.add_increase_effect(GlobalStartTiming(5), km, 10)
        problem.add_decrease_effect(GlobalStartTiming(10), km, 5)
        self.assertIn(str(Effect(FluentExp(km), Int(10), TRUE(), unified_planning.model.EffectKind.INCREASE)), str(problem))
