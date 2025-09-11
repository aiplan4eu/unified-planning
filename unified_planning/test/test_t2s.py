# Copyright 2025 Unified Planning library and its maintainers
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


from unified_planning.environment import get_environment
from unified_planning.shortcuts import *
from unified_planning.test import (
    unittest_TestCase,
)
from unified_planning.test.examples import get_example_problems

from unified_planning.engines.compilers.timed_to_sequential import TimedToSequential
from unified_planning.plans import SequentialPlan, TimeTriggeredPlan
from typing import Callable


class TestT2S(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_base_example(self):
        problem = Problem("wompwomp")

        x = Fluent("x", IntType())
        problem.add_fluent(x)
        problem.set_initial_value(x, 10)

        y = Fluent("y", IntType())
        problem.add_fluent(y)
        problem.set_initial_value(y, 10)

        z = Fluent("z", IntType())
        problem.add_fluent(z)
        problem.set_initial_value(z, 10)

        w = Fluent("w", IntType())
        problem.add_fluent(w)
        problem.set_initial_value(w, 10)

        tda = DurativeAction("tda")
        tda.set_closed_duration_interval(5, 10)

        tda.add_increase_effect(StartTiming(), x, 1)
        tda.add_increase_effect(StartTiming(), x, 1)
        tda.add_decrease_effect(EndTiming(), x, 2)
        tda.add_increase_effect(StartTiming(), y, 3)
        tda.add_effect(EndTiming(), z, y + 4)
        tda.add_decrease_effect(EndTiming(), w, x)

        tda.add_condition(StartTiming(), Equals(x, 1))
        # tda.add_condition(StartTiming() + 2, Equals(x, 5))
        tda.add_condition(EndTiming(), Not(Equals(y, 1)))
        tda.add_condition(EndTiming(), Equals(x, 1))

        problem.add_action(tda)

        t2s = TimedToSequential()
        comp_res = t2s.compile(problem)
        assert isinstance(comp_res.problem, Problem)
        self.assertTrue(problem.kind.has_continuous_time())
        self.assertFalse(comp_res.problem.kind.has_continuous_time())
        comp_tda = comp_res.problem.action("tda")
        expected_tda = InstantaneousAction("tda")
        expected_tda.add_precondition(Equals(x, 1))
        # expected_tda.add_precondition(Equals(Plus(x, 1), 5))
        expected_tda.add_precondition(Not(Equals(Plus(y, 3), 1)))
        expected_tda.add_precondition(Equals(Plus(Plus(x, 1), 1), 1))
        expected_tda.add_effect(x, Minus(Plus(Plus(x, 1), 1), 2))
        expected_tda.add_increase_effect(y, 3)
        expected_tda.add_effect(z, Plus(Plus(y, 3), 4))
        expected_tda.add_effect(w, Minus(w, Plus(Plus(x, 1), 1)))

        self.assertEqual(expected_tda, comp_tda)

        sp = SequentialPlan([comp_tda(), comp_tda()])
        assert comp_res.plan_back_conversion is not None
        self.assertTrue(comp_res.plan_back_conversion is not None)
        mapped_back_ttp = comp_res.plan_back_conversion(sp)
        self.assertTrue(isinstance(mapped_back_ttp, TimeTriggeredPlan))
        expected_ttp = TimeTriggeredPlan(
            [
                (Fraction(0), tda(), Fraction(5)),
                (Fraction(501, 100), tda(), Fraction(5)),
            ]
        )
        self.assertEqual(expected_ttp, mapped_back_ttp)

    def test_logistic(self):
        problem = self.problems["logistic"].problem
        assert isinstance(problem, Problem)
        t2s = TimedToSequential()
        comp_res = t2s.compile(problem)
        assert isinstance(comp_res.problem, Problem)
        self.assertTrue(problem.kind.has_continuous_time())
        self.assertFalse(comp_res.problem.kind.has_continuous_time())

        compiled_move = comp_res.problem.action("move")
        Robot = problem.user_type("Robot")
        Location = problem.user_type("Location")
        robot_at = problem.fluent("robot_at")
        is_connected = problem.fluent("is_connected")
        r1 = problem.object("r1")
        r2 = problem.object("r2")
        expected_move = InstantaneousAction(
            "move", robot=Robot, l_from=Location, l_to=Location
        )
        robot = expected_move.parameter("robot")
        l_from = expected_move.parameter("l_from")
        l_to = expected_move.parameter("l_to")
        expected_move.add_precondition(robot_at(robot, l_from))
        expected_move.add_precondition(is_connected(l_from, l_to))
        expected_move.add_precondition(Not(robot_at(r1, l_to)))
        expected_move.add_precondition(Not(robot_at(r2, l_to)))
        expected_move.add_effect(robot_at(robot, l_from), False)
        expected_move.add_effect(robot_at(robot, l_to), True)
        self.assertEqual(compiled_move, expected_move)

    def test_temporal_counter(self):
        problem = self.problems["temporal_counter"].problem
        assert isinstance(problem, Problem)
        t2s = TimedToSequential()
        comp_res = t2s.compile(problem)
        assert isinstance(comp_res.problem, Problem)
        self.assertTrue(problem.kind.has_continuous_time())
        self.assertFalse(comp_res.problem.kind.has_continuous_time())
        compiled_d = comp_res.problem.action("decrease")
        compiled_i = comp_res.problem.action("increase")
        counter_f = problem.fluent("counter")
        expected_i = InstantaneousAction("increase")
        expected_i.add_precondition(LT(counter_f, 99))
        # NOTE currently effects at end are always compiled into assignments
        expected_i.add_effect(counter_f, Plus(counter_f, 2))
        expected_d = InstantaneousAction("decrease")
        expected_d.add_precondition(GT(counter_f, 0))
        expected_d.add_effect(counter_f, Minus(counter_f, 1))
        self.assertEqual(compiled_d, expected_d)
        self.assertEqual(compiled_i, expected_i)
