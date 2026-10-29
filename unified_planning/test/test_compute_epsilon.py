# Copyright 2026 Unified Planning library and its maintainers
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

from fractions import Fraction
from unified_planning.shortcuts import *
from unified_planning.test import unittest_TestCase
from unified_planning.engines.compilers.utils import compute_epsilon


class TestComputeEpsilon(unittest_TestCase):
    def test_constant_durations(self):
        problem = Problem("constant_durations")
        x = problem.add_fluent("x", default_initial_value=False)
        a = DurativeAction("a")
        a.set_fixed_duration(6)
        a.add_effect(EndTiming(), x, True)
        problem.add_action(a)
        b = DurativeAction("b")
        b.set_closed_duration_interval(5, 8)
        b.add_effect(EndTiming(), x, False)
        problem.add_action(b)
        self.assertEqual(compute_epsilon(problem), Fraction(1, 2))

    def test_timing_delays(self):
        problem = Problem("timing_delays")
        x = problem.add_fluent("x", default_initial_value=False)
        y = problem.add_fluent("y", default_initial_value=False)
        a = DurativeAction("a")
        a.set_fixed_duration(6)
        a.add_condition(ClosedTimeInterval(StartTiming(), EndTiming() - 2), y)
        a.add_effect(StartTiming(3), x, True)
        a.add_effect(EndTiming() - 1, y, True)
        problem.add_action(a)
        self.assertEqual(compute_epsilon(problem), Fraction(1, 10))

    def test_timed_effects_and_goals(self):
        problem = Problem("timed_effects_and_goals")
        x = problem.add_fluent("x", default_initial_value=False)
        a = DurativeAction("a")
        a.set_fixed_duration(6)
        a.add_effect(EndTiming(), x, True)
        problem.add_action(a)
        problem.add_timed_effect(GlobalStartTiming(4), x, True)
        self.assertEqual(compute_epsilon(problem), Fraction(4, 10))
        problem.add_timed_goal(
            ClosedTimeInterval(GlobalStartTiming(2), GlobalStartTiming(50)), x
        )
        self.assertEqual(compute_epsilon(problem), Fraction(2, 10))

    def test_close_timed_effects(self):
        problem = Problem("close_timed_effects")
        x = problem.add_fluent("x", default_initial_value=False)
        problem.add_timed_effect(GlobalStartTiming(10), x, True)
        problem.add_timed_effect(GlobalStartTiming(Fraction(21, 2)), x, False)
        self.assertEqual(compute_epsilon(problem), Fraction(1, 20))

    def test_narrow_timed_goal_window(self):
        problem = Problem("narrow_timed_goal_window")
        x = problem.add_fluent("x", default_initial_value=False)
        problem.add_timed_goal(
            ClosedTimeInterval(
                GlobalStartTiming(10), GlobalStartTiming(Fraction(51, 5))
            ),
            x,
        )
        self.assertEqual(compute_epsilon(problem), Fraction(1, 50))

    def test_close_action_timings(self):
        problem = Problem("close_action_timings")
        x = problem.add_fluent("x", default_initial_value=False)
        y = problem.add_fluent("y", default_initial_value=False)
        a = DurativeAction("a")
        a.set_fixed_duration(6)
        a.add_effect(StartTiming(3), x, True)
        a.add_effect(StartTiming(Fraction(31, 10)), y, True)
        problem.add_action(a)
        self.assertEqual(compute_epsilon(problem), Fraction(1, 100))

    def test_end_timing_close_to_start_with_fixed_duration(self):
        # with a fixed duration of 5, end - 49/10 is 1/10 after the start
        problem = Problem("end_timing_close_to_start")
        x = problem.add_fluent("x", default_initial_value=False)
        a = DurativeAction("a")
        a.set_fixed_duration(5)
        a.add_condition(EndTiming() - Fraction(49, 10), x)
        problem.add_action(a)
        self.assertEqual(compute_epsilon(problem), Fraction(1, 100))

    def test_variable_duration_timings_grouped_by_anchor(self):
        problem = Problem("variable_duration_timings")
        x = problem.add_fluent("x", default_initial_value=False)
        y = problem.add_fluent("y", default_initial_value=False)
        a = DurativeAction("a")
        a.set_closed_duration_interval(5, 8)
        # start-relative timings are 1 apart, end-relative timings are 1/2 apart
        a.add_effect(StartTiming(2), x, True)
        a.add_effect(StartTiming(3), y, True)
        a.add_effect(EndTiming() - 1, x, False)
        a.add_effect(EndTiming() - Fraction(3, 2), y, False)
        problem.add_action(a)
        self.assertEqual(compute_epsilon(problem), Fraction(1, 20))
        # the gap between start + 3 and end - 1 depends on the chosen duration, so
        # it is not considered (it would be 1/10 if the duration was 4 + 1/10)
        b = DurativeAction("b")
        b.set_closed_duration_interval(Fraction(41, 10), 8)
        b.add_effect(StartTiming(3), x, True)
        b.add_effect(EndTiming() - 1, y, True)
        problem.add_action(b)
        self.assertEqual(compute_epsilon(problem), Fraction(1, 20))

    def test_non_constant_durations_ignored(self):
        problem = Problem("non_constant_durations")
        Location = UserType("Location")
        distance = problem.add_fluent(
            "distance", RealType(), default_initial_value=10, l1=Location, l2=Location
        )
        x = problem.add_fluent("x", default_initial_value=False)
        move = DurativeAction("move", l_from=Location, l_to=Location)
        move.set_fixed_duration(distance(move.l_from, move.l_to))
        move.add_effect(EndTiming(), x, True)
        problem.add_action(move)
        self.assertIsNone(compute_epsilon(problem))
        l1 = Object("l1", Location)
        problem.add_object(l1)
        quick = DurativeAction("quick")
        quick.set_closed_duration_interval(0, distance(l1, l1))
        quick.add_effect(EndTiming(), x, False)
        problem.add_action(quick)
        self.assertIsNone(compute_epsilon(problem))

    def test_no_temporal_constants(self):
        problem = Problem("no_temporal_constants")
        x = problem.add_fluent("x", default_initial_value=False)
        a = InstantaneousAction("a")
        a.add_effect(x, True)
        problem.add_action(a)
        problem.add_goal(x)
        self.assertIsNone(compute_epsilon(problem))
