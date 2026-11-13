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

from unified_planning.shortcuts import *
from unified_planning.test import (
    unittest_TestCase,
    skipIfNoOneshotPlannerForProblemKind,
)
from unified_planning.test.examples import get_example_problems
from unified_planning.model.problem_kind import classical_kind, general_numeric_kind
from unified_planning.engines.compilers.timed_to_sequential import TimedToSequential
from unified_planning.plans import SequentialPlan, TimeTriggeredPlan
from unified_planning.engines.results import (
    ValidationResultStatus,
    POSITIVE_OUTCOMES,
)
from unified_planning.engines.plan_validator import (
    SequentialPlanValidator,
    TimeTriggeredPlanValidator,
)
from unified_planning.model.walkers import InterpretedFunctionsExtractor
from unified_planning.io import PDDLWriter
from unified_planning.exceptions import (
    UPProblemDefinitionError,
    UPUnsupportedProblemTypeError,
)
from fractions import Fraction
from typing import Dict


def _get_interpreted_function(*expressions):
    """Extracts the single `InterpretedFunction` used across the given expressions."""
    ife = InterpretedFunctionsExtractor()
    if_functions = set()
    for e in expressions:
        if_functions |= {if_exp.interpreted_function() for if_exp in ife.get(e)}
    (if_function,) = if_functions
    return if_function


class TestT2S(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_base_example(self):
        problem = Problem("wompwomp")

        x = Fluent("x", IntType())
        problem.add_fluent(x)
        problem.set_initial_value(x, 20)

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
        tda.set_closed_duration_interval(z(), 100)

        tda.add_increase_effect(StartTiming(), x, 1)
        tda.add_increase_effect(StartTiming(), x, 1)
        tda.add_decrease_effect(EndTiming(), x, 2)
        tda.add_increase_effect(StartTiming(), y, 3)
        tda.add_effect(EndTiming(), z, y + 4, GE(x, y))
        tda.add_decrease_effect(EndTiming(), w, x)

        # subs after start:
        # x = x + 1 +1
        # y = y + 3

        tda.add_condition(StartTiming(), Not(Equals(x, 1)))
        # tda.add_condition(StartTiming() + 2, Equals(x, 5))
        tda.add_condition(EndTiming(), Not(Equals(y, 1)))
        tda.add_condition(EndTiming(), Not(Equals(x, 1)))

        problem.add_action(tda)

        t2s = TimedToSequential()
        t2s.skip_checks = True
        comp_res = t2s.compile(problem)
        assert isinstance(comp_res.problem, Problem)
        self.assertTrue(problem.kind.has_continuous_time())
        self.assertFalse(comp_res.problem.kind.has_continuous_time())
        comp_tda = comp_res.problem.action("tda")
        expected_tda = InstantaneousAction("tda")
        expected_tda.add_precondition(Not(Equals(x, 1)))
        # expected_tda.add_precondition(Equals(Plus(x, 1), 5))
        expected_tda.add_precondition(Not(Equals(Plus(y, 3), 1)))
        expected_tda.add_precondition(Not(Equals(Plus(x, 2), 1)))
        # the duration interval [z, 100] must not be empty
        expected_tda.add_precondition(LE(z, 100))
        expected_tda.add_effect(x, Minus(Plus(x, 2), 2))
        expected_tda.add_increase_effect(y, 3)
        expected_tda.add_effect(z, Plus(y, 7), GE(Plus(x, 2), Plus(y, 3)))
        expected_tda.add_effect(w, Minus(w, Plus(x, 2)))

        self.assertEqual(expected_tda, comp_tda)

        sp = SequentialPlan([comp_tda(), comp_tda()])
        assert comp_res.plan_back_conversion is not None
        self.assertTrue(comp_res.plan_back_conversion is not None)
        mapped_back_ttp = comp_res.plan_back_conversion(sp)
        self.assertTrue(isinstance(mapped_back_ttp, TimeTriggeredPlan))
        expected_ttp = TimeTriggeredPlan(
            [
                (Fraction(0), tda(), Fraction(10)),
                (Fraction(1001, 100), tda(), Fraction(17)),
            ]
        )
        self.assertEqual(expected_ttp, mapped_back_ttp)

    def test_start_only_decrease_effect(self):
        # regression test: a start-time decrease effect on a fluent with no matching
        # end-time effect must be compiled into a decrease effect, not an increase one
        problem = Problem("start_only_decrease")
        x = Fluent("x", IntType())
        problem.add_fluent(x)
        problem.set_initial_value(x, 10)

        tda = DurativeAction("tda")
        tda.set_fixed_duration(1)
        tda.add_decrease_effect(StartTiming(), x, 3)
        problem.add_action(tda)

        t2s = TimedToSequential()
        comp_res = t2s.compile(problem)
        assert isinstance(comp_res.problem, Problem)
        compiled_tda = comp_res.problem.action("tda")

        expected_tda = InstantaneousAction("tda")
        expected_tda.add_decrease_effect(x, 3)
        self.assertEqual(expected_tda, compiled_tda)

    def test_multiple_end_increase_decrease_effects_same_fluent(self):
        # several end-time increase/decrease effects on the same fluent happen at the
        # same instant and sum up: they must be merged into a single assignment
        problem = Problem("multiple_end_inc_dec")
        f = Fluent("f", IntType())
        g = Fluent("g", IntType())
        h = Fluent("h", IntType())
        problem.add_fluent(f, default_initial_value=0)
        problem.add_fluent(g, default_initial_value=0)
        problem.add_fluent(h, default_initial_value=0)

        tda = DurativeAction("tda")
        tda.set_fixed_duration(1)
        tda.add_increase_effect(EndTiming(), f, 2)
        tda.add_increase_effect(EndTiming(), f, 3)
        tda.add_increase_effect(EndTiming(), g, 2)
        tda.add_decrease_effect(EndTiming(), g, 1)
        tda.add_increase_effect(StartTiming(), h, 1)
        tda.add_increase_effect(EndTiming(), h, 2)
        tda.add_decrease_effect(EndTiming(), h, 1)
        problem.add_action(tda)
        problem.add_goal(Equals(f, 10))
        problem.add_goal(Equals(g, 2))
        problem.add_goal(Equals(h, 4))

        t2s = TimedToSequential()
        comp_res = t2s.compile(problem)
        assert isinstance(comp_res.problem, Problem)
        compiled_tda = comp_res.problem.action("tda")

        expected_tda = InstantaneousAction("tda")
        expected_tda.add_effect(f, Plus(f, 5))
        expected_tda.add_effect(g, Minus(Plus(g, 2), 1))
        expected_tda.add_effect(h, Minus(Plus(h, 3), 1))
        self.assertEqual(expected_tda, compiled_tda)

        sp = SequentialPlan([compiled_tda(), compiled_tda()])
        assert comp_res.plan_back_conversion is not None
        mapped_back_ttp = comp_res.plan_back_conversion(sp)
        with TimeTriggeredPlanValidator() as validator:
            val_result = validator.validate(problem, mapped_back_ttp)
        self.assertEqual(val_result.status, ValidationResultStatus.VALID)

    def test_conditional_effect_in_multiple_end_increase_group_raises(self):
        # conditional increase/decrease effects can not be merged with other end-time
        # effects on the same fluent into a single assignment
        problem = Problem("conditional_multiple_end_inc")
        f = Fluent("f", IntType())
        c = Fluent("c", BoolType())
        problem.add_fluent(f, default_initial_value=0)
        problem.add_fluent(c, default_initial_value=True)

        tda = DurativeAction("tda")
        tda.set_fixed_duration(1)
        tda.add_increase_effect(EndTiming(), f, 2, c)
        tda.add_increase_effect(EndTiming(), f, 3)
        problem.add_action(tda)

        t2s = TimedToSequential()
        t2s.skip_checks = True
        with self.assertRaises(UPUnsupportedProblemTypeError):
            t2s.compile(problem)

    def test_left_open_duration_map_back(self):
        # a left-open duration interval excludes its lower bound: the mapped back
        # duration must be strictly greater than it, and still inside the interval
        def check(
            name,
            set_duration,
            expected_duration,
            epsilon=None,
            start_effect_to_end_condition=False,
        ):
            with self.subTest(name):
                problem = Problem(name)
                x = Fluent("x", IntType())
                y = Fluent("y", IntType())
                g = Fluent("g", BoolType())
                problem.add_fluent(x, default_initial_value=5)
                problem.add_fluent(y, default_initial_value=10)
                problem.add_fluent(g, default_initial_value=False)
                # x and y are written, so they are not pruned from the compiled problem
                touch = InstantaneousAction("touch")
                touch.add_effect(x, 5)
                touch.add_effect(y, 10)
                problem.add_action(touch)
                tda = DurativeAction("tda")
                set_duration(tda, x, y)
                tda.add_effect(EndTiming(), g, True)
                if start_effect_to_end_condition:
                    # the end condition only holds after the start effect, so the end
                    # of the action must come strictly after its start
                    s = Fluent("s", BoolType())
                    problem.add_fluent(s, default_initial_value=False)
                    tda.add_effect(StartTiming(), s, True)
                    tda.add_condition(EndTiming(), s)
                problem.add_action(tda)
                problem.add_goal(g)
                if epsilon is not None:
                    problem.epsilon = epsilon

                comp_res = TimedToSequential().compile(problem)
                assert isinstance(comp_res.problem, Problem)
                assert comp_res.plan_back_conversion is not None
                sp = SequentialPlan([comp_res.problem.action("tda")()])
                ttp = comp_res.plan_back_conversion(sp)
                assert isinstance(ttp, TimeTriggeredPlan)
                ((_, _, duration),) = ttp.timed_actions
                self.assertEqual(duration, expected_duration)
                with TimeTriggeredPlanValidator() as validator:
                    val_result = validator.validate(problem, ttp)
                self.assertEqual(val_result.status, ValidationResultStatus.VALID)

        check(
            "constant",
            lambda a, x, y: a.set_left_open_duration_interval(5, 10),
            Fraction(501, 100),
        )
        check(
            "fluents",
            lambda a, x, y: a.set_left_open_duration_interval(x, y),
            Fraction(501, 100),
        )
        check(
            "narrower_than_step_right_closed",
            lambda a, x, y: a.set_left_open_duration_interval(5, Fraction(1001, 200)),
            Fraction(1001, 200),
        )
        check(
            "narrower_than_step_open",
            lambda a, x, y: a.set_open_duration_interval(5, Fraction(1001, 200)),
            Fraction(2001, 400),
        )
        check(
            "epsilon",
            lambda a, x, y: a.set_left_open_duration_interval(5, 10),
            Fraction(6),
            epsilon=1,
        )
        # the duration must be strictly positive, since the compiled action puts the
        # end of the durative action strictly after its start: a lower bound <= 0 is
        # stepped past like an excluded one
        check(
            "negative_lower_left_open",
            lambda a, x, y: a.set_left_open_duration_interval(-5, 10),
            Fraction(1, 100),
        )
        check(
            "negative_lower_closed",
            lambda a, x, y: a.set_closed_duration_interval(-5, 10),
            Fraction(1, 100),
        )
        check(
            "zero_lower_closed",
            lambda a, x, y: a.set_closed_duration_interval(0, 10),
            Fraction(1, 100),
        )
        check(
            "zero_lower_closed_start_effect_to_end_condition",
            lambda a, x, y: a.set_closed_duration_interval(0, 10),
            Fraction(1, 100),
            start_effect_to_end_condition=True,
        )
        check(
            "zero_lower_closed_narrower_than_step",
            lambda a, x, y: a.set_closed_duration_interval(0, Fraction(1, 200)),
            Fraction(1, 200),
            start_effect_to_end_condition=True,
        )
        # (an empty interval admits no duration at all: the compiled action is not
        # applicable then, see test_duration_interval_preconditions)

    def test_discrete_time_map_back(self):
        # with discrete time every time point is an integer: the mapped back plan must
        # use integer start times and durations. The plan validator does not support
        # discrete time, so the mapped back values are checked directly.
        def check(
            name,
            set_duration,
            expected_a_duration,
            expected_b_start,
            epsilon=None,
            discrete_time=True,
        ):
            with self.subTest(name):
                problem = Problem(name)
                problem.discrete_time = discrete_time
                x = Fluent("x", IntType())
                y = Fluent("y", IntType())
                p = Fluent("p", BoolType())
                g = Fluent("g", BoolType())
                problem.add_fluent(x, default_initial_value=5)
                problem.add_fluent(y, default_initial_value=10)
                problem.add_fluent(p, default_initial_value=False)
                problem.add_fluent(g, default_initial_value=False)
                # x and y are written, so they are not pruned from the compiled problem
                touch = InstantaneousAction("touch")
                touch.add_effect(x, 5)
                touch.add_effect(y, 10)
                problem.add_action(touch)
                a = DurativeAction("a")
                set_duration(a, x, y)
                a.add_effect(EndTiming(), p, True)
                problem.add_action(a)
                b = DurativeAction("b")
                b.set_fixed_duration(2)
                b.add_condition(StartTiming(), p)
                b.add_effect(EndTiming(), g, True)
                problem.add_action(b)
                problem.add_goal(g)
                if epsilon is not None:
                    problem.epsilon = epsilon

                comp_res = TimedToSequential().compile(problem)
                assert isinstance(comp_res.problem, Problem)
                assert comp_res.plan_back_conversion is not None
                sp = SequentialPlan(
                    [comp_res.problem.action("a")(), comp_res.problem.action("b")()]
                )
                ttp = comp_res.plan_back_conversion(sp)
                assert isinstance(ttp, TimeTriggeredPlan)
                ((a_start, _, a_duration), (b_start, _, b_duration)) = ttp.timed_actions
                self.assertEqual(a_start, 0)
                self.assertEqual(a_duration, expected_a_duration)
                self.assertEqual(b_start, expected_b_start)
                self.assertEqual(b_duration, 2)
                if discrete_time:
                    for start, _, duration in ttp.timed_actions:
                        self.assertEqual(Fraction(start).denominator, 1)
                        assert duration is not None
                        self.assertEqual(Fraction(duration).denominator, 1)

        check("fixed", lambda a, x, y: a.set_fixed_duration(2), 2, 3)
        check(
            "left_open",
            lambda a, x, y: a.set_left_open_duration_interval(5, 10),
            6,
            7,
        )
        check(
            "left_open_fluents",
            lambda a, x, y: a.set_left_open_duration_interval(x, y),
            6,
            7,
        )
        check(
            "closed_non_integer_lower",
            lambda a, x, y: a.set_closed_duration_interval(Fraction(5, 2), 4),
            3,
            4,
        )
        check(
            "left_open_non_integer_lower",
            lambda a, x, y: a.set_left_open_duration_interval(Fraction(11, 2), 10),
            6,
            7,
        )
        # the duration must be strictly positive: the smallest positive integer
        check(
            "negative_lower",
            lambda a, x, y: a.set_closed_duration_interval(-5, 10),
            1,
            2,
        )
        check(
            "zero_lower",
            lambda a, x, y: a.set_closed_duration_interval(0, 10),
            1,
            2,
        )
        check(
            "negative_lower_left_open",
            lambda a, x, y: a.set_left_open_duration_interval(-5, 10),
            1,
            2,
        )
        check(
            "epsilon_integer",
            lambda a, x, y: a.set_fixed_duration(2),
            2,
            4,
            epsilon=2,
        )
        check(
            "epsilon_non_integer",
            lambda a, x, y: a.set_fixed_duration(2),
            2,
            3,
            epsilon=Fraction(1, 2),
        )
        # continuous time keeps the 1/100 default step
        check(
            "continuous",
            lambda a, x, y: a.set_fixed_duration(2),
            2,
            Fraction(201, 100),
            discrete_time=False,
        )

    def test_logistic(self):
        problem = self.problems["logistic"].problem
        assert isinstance(problem, Problem)
        t2s = TimedToSequential()
        comp_res = t2s.compile(problem)
        assert isinstance(comp_res.problem, Problem)
        self.assertTrue(problem.kind.has_continuous_time())
        self.assertFalse(comp_res.problem.kind.has_continuous_time())

        # distance/velocity are only used in the move action's duration; the duration
        # must be positive, so they are kept in the compiled problem through that
        # precondition
        compiled_fluent_names = {f.name for f in comp_res.problem.fluents}
        self.assertIn("distance", compiled_fluent_names)
        self.assertIn("velocity", compiled_fluent_names)

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
        distance = problem.fluent("distance")
        velocity = problem.fluent("velocity")
        expected_move.add_precondition(
            LT(0, Div(distance(l_from, l_to), velocity(robot)))
        )
        expected_move.add_effect(robot_at(robot, l_from), False)
        expected_move.add_effect(robot_at(robot, l_to), True)
        self.assertEqual(compiled_move, expected_move)
        r1 = comp_res.problem.object("r1")
        p1 = comp_res.problem.object("p1")
        l1 = comp_res.problem.object("l1")
        l2 = comp_res.problem.object("l2")
        l3 = comp_res.problem.object("l3")
        compiled_load = comp_res.problem.action("load")
        compiled_unload = comp_res.problem.action("unload")
        mini_seq_plan = SequentialPlan(
            [
                compiled_load(p1, r1, l1),
                compiled_move(r1, l1, l2),
                compiled_unload(p1, r1, l2),
                compiled_move(r1, l2, l3),
            ]
        )
        assert comp_res.plan_back_conversion is not None
        mapped_back_ttp = comp_res.plan_back_conversion(mini_seq_plan)
        expected_ttp = TimeTriggeredPlan(
            [
                (Fraction(0), problem.action("load")(p1, r1, l1), None),
                (Fraction(1, 100), problem.action("move")(r1, l1, l2), Fraction(16)),
                (Fraction(1602, 100), problem.action("unload")(p1, r1, l2), None),
                (Fraction(1603, 100), problem.action("move")(r1, l2, l3), Fraction(10)),
            ]
        )
        self.assertEqual(expected_ttp, mapped_back_ttp)

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

    def test_interpreted_functions_in_durative_conditions(self):
        problem = self.problems["interpreted_functions_in_durative_conditions"].problem
        assert isinstance(problem, Problem)
        self.assertTrue(TimedToSequential.supports(problem.kind))
        t2s = TimedToSequential()
        comp_res = t2s.compile(problem)
        assert isinstance(comp_res.problem, Problem)

        original = problem.action("durative_action_i_f_condition")
        assert isinstance(original, DurativeAction)
        ione = problem.fluent("ione")
        itwo = problem.fluent("itwo")
        end_goal = problem.fluent("end_goal")
        all_conditions = [oc for ocl in original.conditions.values() for oc in ocl]
        funx = _get_interpreted_function(*all_conditions)

        # no start effects exist on this action, so the end-time conditions are
        # carried over unchanged (identity substitution) alongside the start-time ones
        expected = InstantaneousAction("durative_action_i_f_condition")
        expected.add_precondition(And(GE(ione, 10), Not(funx(itwo, itwo))))
        expected.add_precondition(funx(ione, itwo))
        expected.add_precondition(Not(And(GE(ione, 15), LE(itwo, 5))))
        expected.add_effect(end_goal, True)

        compiled = comp_res.problem.action("durative_action_i_f_condition")
        self.assertEqual(expected, compiled)

    def test_go_home_with_rain_and_interpreted_functions(self):
        problem = self.problems["go_home_with_rain_and_interpreted_functions"].problem
        assert isinstance(problem, Problem)
        self.assertTrue(TimedToSequential.supports(problem.kind))
        t2s = TimedToSequential()
        comp_res = t2s.compile(problem)
        assert isinstance(comp_res.problem, Problem)

        # normaltime is only used inside the interpreted function call that computes
        # gohome's duration; the duration must be positive, so it is kept in the
        # compiled problem through that precondition
        self.assertIn("normaltime", {f.name for f in comp_res.problem.fluents})

        original_gohome = problem.action("gohome")
        assert isinstance(original_gohome, DurativeAction)
        athome = problem.fluent("athome")
        atwork = problem.fluent("atwork")
        house_wet = problem.fluent("house_wet")
        wet_clothes = problem.fluent("wet_clothes")
        rain = problem.fluent("rain")
        have_umbrella = problem.fluent("have_umbrella")
        effect_values = [
            oe.value for oel in original_gohome.effects.values() for oe in oel
        ]
        wet_if = _get_interpreted_function(*effect_values)

        # the start effect wet_clothes := wet_if(rain, have_umbrella) has no matching
        # end effect on wet_clothes, so it is kept as-is; house_wet's end effect value
        # (wet_clothes) is substituted with that same interpreted-function expression
        expected_gohome = InstantaneousAction("gohome")
        expected_gohome.add_precondition(Not(athome))
        expected_gohome.add_precondition(atwork)
        expected_gohome.add_precondition(LT(0, original_gohome.duration.upper))
        expected_gohome.add_effect(athome, True)
        expected_gohome.add_effect(atwork, False)
        expected_gohome.add_effect(house_wet, wet_if(rain, have_umbrella))
        expected_gohome.add_effect(wet_clothes, wet_if(rain, have_umbrella))

        compiled_gohome = comp_res.problem.action("gohome")
        self.assertEqual(expected_gohome, compiled_gohome)

        sp = SequentialPlan(
            [
                comp_res.problem.action("takeumbrella")(),
                compiled_gohome(),
            ]
        )
        assert comp_res.plan_back_conversion is not None
        mapped_back = comp_res.plan_back_conversion(sp)
        expected_ttp = TimeTriggeredPlan(
            [
                (Fraction(0), problem.action("takeumbrella")(), Fraction(1)),
                (Fraction(101, 100), problem.action("gohome")(), Fraction(20)),
            ]
        )
        self.assertEqual(expected_ttp, mapped_back)
        with TimeTriggeredPlanValidator() as validator:
            val_result = validator.validate(problem, mapped_back)
        self.assertEqual(val_result.status, ValidationResultStatus.VALID)

    def test_interpreted_functions_in_durative_start_effects(self):
        problem = self.problems[
            "interpreted_functions_in_durative_start_effects"
        ].problem
        assert isinstance(problem, Problem)
        self.assertTrue(TimedToSequential.supports(problem.kind))
        t2s = TimedToSequential()
        comp_res = t2s.compile(problem)
        assert isinstance(comp_res.problem, Problem)
        # the resulting kind is a sound over-approximation of the compiled problem's kind
        self.assertTrue(
            comp_res.problem.kind
            <= TimedToSequential.resulting_problem_kind(problem.kind)
        )

        original_charge = problem.action("charge")
        assert isinstance(original_charge, DurativeAction)
        battery = problem.fluent("battery")
        charged = problem.fluent("charged")
        effect_values = [
            oe.value for oel in original_charge.effects.values() for oe in oel
        ]
        boost_if = _get_interpreted_function(*effect_values)

        # the start effect battery := boost_if(battery) is substituted into both the
        # end-time condition (now a precondition) and the end-time effect on charged
        expected_charge = InstantaneousAction("charge")
        expected_charge.add_precondition(LT(battery, 10))
        expected_charge.add_precondition(GE(boost_if(battery), 5))
        # the duration interval [charge_time(battery), 20] must not be empty, evaluated
        # before the start effect on battery
        expected_charge.add_precondition(LE(original_charge.duration.lower, 20))
        expected_charge.add_effect(charged, GE(boost_if(battery), 5))
        expected_charge.add_effect(battery, boost_if(battery))

        compiled_charge = comp_res.problem.action("charge")
        self.assertEqual(expected_charge, compiled_charge)

        sp = SequentialPlan([compiled_charge()])
        assert comp_res.plan_back_conversion is not None
        mapped_back = comp_res.plan_back_conversion(sp)
        expected_ttp = TimeTriggeredPlan(
            [(Fraction(0), problem.action("charge")(), Fraction(8))]
        )
        self.assertEqual(expected_ttp, mapped_back)
        with TimeTriggeredPlanValidator() as validator:
            val_result = validator.validate(problem, mapped_back)
        self.assertEqual(val_result.status, ValidationResultStatus.VALID)

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(general_numeric_kind))
    def test_logistic_with_planner_map_back_validity(self):
        original_problem = self.problems["logistic"].problem
        assert isinstance(original_problem, Problem)
        t2s = TimedToSequential()
        comp_res = t2s.compile(original_problem)
        assert isinstance(comp_res.problem, Problem)
        with OneshotPlanner(problem_kind=comp_res.problem.kind) as planner:
            plan_result = planner.solve(comp_res.problem)
        self.assertIn(
            plan_result.status,
            POSITIVE_OUTCOMES,
            f"Planner failed to solve the problem: {plan_result.log_messages}",
        )
        assert comp_res.plan_back_conversion is not None
        found_plan_mapped_back = comp_res.plan_back_conversion(plan_result.plan)
        with TimeTriggeredPlanValidator() as validator:
            val_result = validator.validate(original_problem, found_plan_mapped_back)
        self.assertEqual(val_result.status, ValidationResultStatus.VALID)

    def test_fluent_used_only_in_action_cost_metric_is_not_pruned(self):
        # get_unused_fluents() deliberately reports a fluent used only in a
        # MinimizeActionCosts cost as unused; without an explicit guard it would
        # wrongly be pruned away even though the metric still needs it
        problem = Problem("cost_over_static")
        rate = Fluent("rate", IntType())
        problem.add_fluent(rate)
        problem.set_initial_value(rate, 5)

        x = Fluent("x", IntType())
        problem.add_fluent(x, default_initial_value=0)
        mv = InstantaneousAction("mv")
        mv.add_increase_effect(x, 1)
        problem.add_action(mv)
        problem.add_quality_metric(MinimizeActionCosts({mv: rate}))

        t2s = TimedToSequential()
        comp_res = t2s.compile(problem)
        assert isinstance(comp_res.problem, Problem)
        self.assertIn("rate", {f.name for f in comp_res.problem.fluents})

    def test_object_fluent_nested_in_duration_resolves(self):
        # OBJECT_FLUENTS: a duration expression where a fluent is nested inside
        # another fluent's arguments (dist(l1, tgt(l1))) is kept in the compiled problem
        # by the positive duration precondition, and resolves correctly at map-back
        Location = UserType("Location")
        l1 = Object("l1", Location)
        l2 = Object("l2", Location)

        tgt = Fluent("tgt", Location, l=Location)
        dist = Fluent("dist", IntType(), a=Location, b=Location)

        problem = Problem("nested_duration")
        problem.add_objects([l1, l2])
        problem.add_fluent(tgt)
        problem.add_fluent(dist, default_initial_value=7)
        problem.set_initial_value(tgt(l1), l2)

        mv = DurativeAction("mv")
        mv.set_fixed_duration(dist(l1, tgt(l1)))
        problem.add_action(mv)

        t2s = TimedToSequential()
        t2s.skip_checks = True
        comp_res = t2s.compile(problem)
        assert isinstance(comp_res.problem, Problem)
        compiled_fluent_names = {f.name for f in comp_res.problem.fluents}
        self.assertIn("tgt", compiled_fluent_names)
        self.assertIn("dist", compiled_fluent_names)
        self.assertEqual(
            comp_res.problem.action("mv").preconditions, [LT(0, dist(l1, tgt(l1)))]
        )

        sp = SequentialPlan([comp_res.problem.action("mv")()])
        assert comp_res.plan_back_conversion is not None
        mapped_back = comp_res.plan_back_conversion(sp)
        expected_ttp = TimeTriggeredPlan([(Fraction(0), mv(), Fraction(7))])
        self.assertEqual(expected_ttp, mapped_back)

    def test_remove_unused_fluents_flag(self):
        # "log" is never used, so it is unreferenced in the compiled problem: the
        # default prunes it, remove_unused_fluents=False keeps it. "speed" is
        # only read by the duration, which must be positive: that precondition keeps
        # it either way. The duration must be reconstructed identically in both cases.
        problem = Problem("duration_only_fluent")
        speed = Fluent("speed", IntType())
        problem.add_fluent(speed)
        problem.set_initial_value(speed, 3)
        log = Fluent("log", IntType())
        problem.add_fluent(log, default_initial_value=0)
        done = Fluent("done", BoolType())
        problem.add_fluent(done, default_initial_value=False)

        act = DurativeAction("act")
        act.set_fixed_duration(speed())
        act.add_effect(EndTiming(), done, True)
        problem.add_action(act)
        problem.add_goal(done())

        self.assertTrue(TimedToSequential.supports(problem.kind))

        pruning_res = TimedToSequential().compile(problem)
        assert isinstance(pruning_res.problem, Problem)
        pruned_names = {f.name for f in pruning_res.problem.fluents}
        self.assertNotIn("log", pruned_names)
        self.assertIn("speed", pruned_names)
        self.assertEqual(
            pruning_res.problem.action("act").preconditions, [LT(0, speed())]
        )

        keeping_res = TimedToSequential(remove_unused_fluents=False).compile(problem)
        assert isinstance(keeping_res.problem, Problem)
        kept_names = {f.name for f in keeping_res.problem.fluents}
        self.assertIn("log", kept_names)
        self.assertIn("speed", kept_names)
        self.assertEqual(Int(3), keeping_res.problem.initial_value(speed()))
        self.assertTrue(keeping_res.problem.kind.has_int_fluents())

        expected_ttp = TimeTriggeredPlan([(Fraction(0), act(), Fraction(3))])
        for comp_res in (pruning_res, keeping_res):
            assert isinstance(comp_res.problem, Problem)
            assert comp_res.plan_back_conversion is not None
            sp = SequentialPlan([comp_res.problem.action("act")()])
            self.assertEqual(expected_ttp, comp_res.plan_back_conversion(sp))

    def test_duration_interval_preconditions(self):
        # a durative action can only start if its duration interval, evaluated in the
        # state before the start, contains a positive duration: the compiled action
        # must not be applicable otherwise
        def check(
            name,
            set_duration,
            x_value,
            y_value,
            expected_status,
            round_trip=False,
            start_effect_on_x=None,
        ):
            with self.subTest(name):
                problem = Problem(name)
                x = Fluent("x", IntType())
                y = Fluent("y", IntType())
                g = Fluent("g", BoolType())
                problem.add_fluent(x, default_initial_value=x_value)
                problem.add_fluent(y, default_initial_value=y_value)
                problem.add_fluent(g, default_initial_value=False)
                # x and y are written, so they are not static
                touch = InstantaneousAction("touch")
                touch.add_effect(x, x_value)
                touch.add_effect(y, y_value)
                problem.add_action(touch)
                tda = DurativeAction("tda")
                set_duration(tda, x, y)
                if start_effect_on_x is not None:
                    tda.add_effect(StartTiming(), x, start_effect_on_x)
                tda.add_effect(EndTiming(), g, True)
                problem.add_action(tda)
                problem.add_goal(g)

                comp_res = TimedToSequential().compile(problem)
                assert isinstance(comp_res.problem, Problem)
                sp = SequentialPlan([comp_res.problem.action("tda")()])
                with SequentialPlanValidator() as validator:
                    val_result = validator.validate(comp_res.problem, sp)
                self.assertEqual(val_result.status, expected_status)
                if round_trip:
                    assert comp_res.plan_back_conversion is not None
                    ttp = comp_res.plan_back_conversion(sp)
                    with TimeTriggeredPlanValidator() as validator:
                        original_result = validator.validate(problem, ttp)
                    self.assertEqual(original_result.status, expected_status)

        VALID = ValidationResultStatus.VALID
        INVALID = ValidationResultStatus.INVALID
        closed = lambda a, x, y: a.set_closed_duration_interval(x, y)
        left_open = lambda a, x, y: a.set_left_open_duration_interval(x, y)
        right_open = lambda a, x, y: a.set_right_open_duration_interval(x, y)
        fixed_x = lambda a, x, y: a.set_fixed_duration(x)
        check("empty_closed", closed, 5, 3, INVALID)
        check("non_empty_closed", closed, 3, 5, VALID, round_trip=True)
        check("point_closed", closed, 4, 4, VALID, round_trip=True)
        check("point_left_open", left_open, 4, 4, INVALID)
        check("point_right_open", right_open, 4, 4, INVALID)
        check("negative_upper", closed, -5, -1, INVALID)
        # the duration must be strictly positive: the compiled action puts the end of
        # the durative action strictly after its start
        check("zero_upper_closed", closed, -1, 0, INVALID)
        check("zero_upper_right_open", right_open, -1, 0, INVALID)
        check("fixed_negative", fixed_x, -1, 0, INVALID)
        check("fixed_zero", fixed_x, 0, 0, INVALID)
        check("positive_upper_closed", closed, -1, 1, VALID)
        # (a constant empty interval, or a constant upper bound <= 0, is already
        # rejected when the action is defined)
        # the duration is evaluated before the start effects: x := 20 at start must not
        # make [x, 10] empty
        check(
            "pre_start_state",
            lambda a, x, y: a.set_closed_duration_interval(x, 10),
            5,
            0,
            VALID,
            round_trip=True,
            start_effect_on_x=20,
        )

    def test_constant_duration_adds_no_precondition(self):
        problem = Problem("constant_duration")
        g = Fluent("g", BoolType())
        problem.add_fluent(g, default_initial_value=False)
        tda = DurativeAction("tda")
        tda.set_fixed_duration(3)
        tda.add_effect(EndTiming(), g, True)
        problem.add_action(tda)
        problem.add_goal(g)
        comp_res = TimedToSequential().compile(problem)
        assert isinstance(comp_res.problem, Problem)
        self.assertEqual(comp_res.problem.action("tda").preconditions, [])

    def test_default_duration(self):
        # a durative action without an explicit duration has fixed duration 1: it
        # compiles with no duration precondition and maps back to duration 1
        problem = Problem("default_duration")
        g = Fluent("g", BoolType())
        problem.add_fluent(g, default_initial_value=False)
        tda = DurativeAction("tda")
        tda.add_effect(EndTiming(), g, True)
        problem.add_action(tda)
        problem.add_goal(g)
        comp_res = TimedToSequential().compile(problem)
        assert isinstance(comp_res.problem, Problem)
        self.assertEqual(comp_res.problem.action("tda").preconditions, [])
        assert comp_res.plan_back_conversion is not None
        sp = SequentialPlan([comp_res.problem.action("tda")()])
        ttp = comp_res.plan_back_conversion(sp)
        assert isinstance(ttp, TimeTriggeredPlan)
        ((_, _, duration),) = ttp.timed_actions
        self.assertEqual(duration, 1)
        with TimeTriggeredPlanValidator() as validator:
            val_result = validator.validate(problem, ttp)
        self.assertEqual(val_result.status, ValidationResultStatus.VALID)

    def test_non_positive_constant_duration_raises(self):
        # a constant duration that admits no positive value can not be compiled, since
        # the compiled action puts the end of the durative action strictly after its
        # start. A literal constant upper bound <= 0 is already rejected when the
        # action is defined, so only constant expressions that simplify to <= 0 reach
        # the compilation.
        with self.assertRaises(UPProblemDefinitionError):
            DurativeAction("tda").set_fixed_duration(0)

        def check(name, set_duration):
            with self.subTest(name):
                problem = Problem(name)
                g = Fluent("g", BoolType())
                problem.add_fluent(g, default_initial_value=False)
                tda = DurativeAction("tda")
                set_duration(tda)
                tda.add_effect(EndTiming(), g, True)
                problem.add_action(tda)
                problem.add_goal(g)
                with self.assertRaises(UPUnsupportedProblemTypeError):
                    TimedToSequential().compile(problem)

        check("fixed_zero", lambda a: a.set_fixed_duration(Minus(1, 1)))
        check(
            "zero_upper_closed",
            lambda a: a.set_closed_duration_interval(-5, Minus(1, 1)),
        )
        check("negative_fixed", lambda a: a.set_fixed_duration(Minus(0, 1)))

    def test_resulting_problem_kind_duration_preconditions(self):
        # the duration bounds become preconditions: the fluents used only in durations
        # (not counted as INT_FLUENTS/REAL_FLUENTS in the input kind) and the bounds'
        # arithmetic (not checked for linearity in the input kind) reach the conditions
        def check(
            name, set_duration, expected_features, written=False, discrete_time=False
        ):
            with self.subTest(name):
                problem = Problem(name)
                problem.discrete_time = discrete_time
                i = Fluent("i", IntType())
                j = Fluent("j", IntType())
                r = Fluent("r", RealType())
                g = Fluent("g", BoolType())
                tda = DurativeAction("tda")
                set_duration(tda, i, j, r)
                tda.add_effect(EndTiming(), g, True)
                # declare only the fluents the duration uses: an unused numeric fluent
                # would set INT_FLUENTS/REAL_FLUENTS in the input kind by itself
                fve = problem.environment.free_vars_extractor
                used = {
                    fe.fluent()
                    for bound in (tda.duration.lower, tda.duration.upper)
                    for fe in fve.get(bound)
                }
                initial_values: Dict[Fluent, Fraction] = {
                    i: Fraction(2),
                    j: Fraction(3),
                    r: Fraction(5, 2),
                }
                for f in (i, j, r):
                    if f in used:
                        problem.add_fluent(f, default_initial_value=initial_values[f])
                problem.add_fluent(g, default_initial_value=False)
                if written:
                    # constant assignments make the fluents non-static (static ones are
                    # constants for the linearity check) and keep the input simple numeric
                    touch = InstantaneousAction("touch")
                    for f in used:
                        touch.add_effect(f, initial_values[f])
                    problem.add_action(touch)
                problem.add_action(tda)
                problem.add_goal(g)

                comp_res = TimedToSequential().compile(problem)
                assert isinstance(comp_res.problem, Problem)
                compiled_kind = comp_res.problem.kind
                for feature in expected_features:
                    self.assertIn(feature, compiled_kind.features)
                claimed = TimedToSequential.resulting_problem_kind(problem.kind)
                missing = set(compiled_kind.features) - set(claimed.features)
                self.assertEqual(missing, set())

        check(
            "int_fixed",
            lambda a, i, j, r: a.set_fixed_duration(i),
            ["INT_FLUENTS", "SIMPLE_NUMERIC_PLANNING"],
        )
        check(
            "real_interval",
            lambda a, i, j, r: a.set_closed_duration_interval(r, 10),
            ["REAL_FLUENTS", "SIMPLE_NUMERIC_PLANNING"],
        )
        # a real-typed bound made of int fluents only
        check(
            "real_typed_int_fluents",
            lambda a, i, j, r: a.set_fixed_duration(Div(i, j)),
            ["INT_FLUENTS"],
        )
        check(
            "non_linear",
            lambda a, i, j, r: a.set_closed_duration_interval(Times(i, j), 10),
            ["INT_FLUENTS", "GENERAL_NUMERIC_PLANNING"],
            written=True,
        )
        # with discrete time the integer bounds of the interval (i + 1, j - 1) are compared
        check(
            "discrete_time_open",
            lambda a, i, j, r: a.set_open_duration_interval(i, j),
            ["INT_FLUENTS"],
            discrete_time=True,
        )

    def test_discrete_time_duration_preconditions(self):
        # with discrete time every duration is an integer: a durative action can only
        # start if its duration interval contains a positive integer
        def check(
            name,
            set_duration,
            x_value,
            y_value,
            expected_status,
            expected_duration=None,
            discrete_time=True,
        ):
            with self.subTest(name):
                problem = Problem(name)
                problem.discrete_time = discrete_time
                x = Fluent("x", IntType())
                y = Fluent("y", IntType())
                g = Fluent("g", BoolType())
                problem.add_fluent(x, default_initial_value=x_value)
                problem.add_fluent(y, default_initial_value=y_value)
                problem.add_fluent(g, default_initial_value=False)
                # x and y are written, so they are not static
                touch = InstantaneousAction("touch")
                touch.add_effect(x, x_value)
                touch.add_effect(y, y_value)
                problem.add_action(touch)
                tda = DurativeAction("tda")
                set_duration(tda, x, y)
                tda.add_effect(EndTiming(), g, True)
                problem.add_action(tda)
                problem.add_goal(g)

                comp_res = TimedToSequential().compile(problem)
                assert isinstance(comp_res.problem, Problem)
                sp = SequentialPlan([comp_res.problem.action("tda")()])
                with SequentialPlanValidator() as validator:
                    val_result = validator.validate(comp_res.problem, sp)
                self.assertEqual(val_result.status, expected_status)
                if expected_duration is not None:
                    # the plan validator does not support discrete time, so the mapped
                    # back duration is checked directly
                    assert comp_res.plan_back_conversion is not None
                    ttp = comp_res.plan_back_conversion(sp)
                    assert isinstance(ttp, TimeTriggeredPlan)
                    ((_, _, duration),) = ttp.timed_actions
                    self.assertEqual(duration, expected_duration)

        VALID = ValidationResultStatus.VALID
        INVALID = ValidationResultStatus.INVALID
        closed = lambda a, x, y: a.set_closed_duration_interval(x, y)
        left_open = lambda a, x, y: a.set_left_open_duration_interval(x, y)
        right_open = lambda a, x, y: a.set_right_open_duration_interval(x, y)
        open_ = lambda a, x, y: a.set_open_duration_interval(x, y)
        fixed_x = lambda a, x, y: a.set_fixed_duration(x)
        constant_lower = lambda a, x, y: a.set_open_duration_interval(Fraction(5, 2), y)
        # non-empty as real intervals, but with no positive integer in them
        check("open_no_integer", open_, 2, 3, INVALID)
        check("left_open_point", left_open, 2, 2, INVALID)
        check("right_open_point", right_open, 2, 2, INVALID)
        check("closed_no_positive", closed, -5, 0, INVALID)
        check("fixed_zero", fixed_x, 0, 0, INVALID)
        check("constant_lower_no_integer", constant_lower, 0, 3, INVALID)
        # the mapped back duration is the smallest positive integer in the interval
        check("open", open_, 2, 4, VALID, expected_duration=3)
        check("right_open", right_open, 2, 3, VALID, expected_duration=2)
        check("closed_from_zero", closed, 0, 1, VALID, expected_duration=1)
        check("fixed_one", fixed_x, 1, 0, VALID, expected_duration=1)
        check("constant_lower", constant_lower, 0, 4, VALID, expected_duration=3)
        # continuous time only requires a positive value
        check("continuous_open", open_, 2, 3, VALID, discrete_time=False)

    def test_discrete_time_constant_duration_without_integer_raises(self):
        # with discrete time a constant duration interval with no positive integer in
        # it can not be compiled; with continuous time it is a valid duration
        def compile_with(set_duration, discrete_time):
            problem = Problem("constant_duration")
            problem.discrete_time = discrete_time
            g = Fluent("g", BoolType())
            problem.add_fluent(g, default_initial_value=False)
            tda = DurativeAction("tda")
            set_duration(tda)
            tda.add_effect(EndTiming(), g, True)
            problem.add_action(tda)
            problem.add_goal(g)
            return TimedToSequential().compile(problem)

        for name, set_duration in (
            ("open", lambda a: a.set_open_duration_interval(2, 3)),
            (
                "closed",
                lambda a: a.set_closed_duration_interval(
                    Fraction(11, 5), Fraction(14, 5)
                ),
            ),
            ("fixed", lambda a: a.set_fixed_duration(Fraction(5, 2))),
        ):
            with self.subTest(name):
                with self.assertRaises(UPUnsupportedProblemTypeError):
                    compile_with(set_duration, True)
                compile_with(set_duration, False)
        with self.subTest("with_integer"):
            comp_res = compile_with(
                lambda a: a.set_closed_duration_interval(Fraction(5, 2), 4), True
            )
            assert isinstance(comp_res.problem, Problem)
            self.assertEqual(comp_res.problem.action("tda").preconditions, [])

    def test_discrete_time_real_fluent_duration_raises(self):
        # with discrete time, whether a real-typed bound that is not constant admits an
        # integer can not be expressed, so it is not supported
        def compile_with(set_duration, discrete_time):
            problem = Problem("real_duration")
            problem.discrete_time = discrete_time
            x = Fluent("x", IntType())
            r = Fluent("r", RealType())
            g = Fluent("g", BoolType())
            problem.add_fluent(x, default_initial_value=4)
            problem.add_fluent(r, default_initial_value=Fraction(5, 2))
            problem.add_fluent(g, default_initial_value=False)
            touch = InstantaneousAction("touch")
            touch.add_effect(x, 4)
            touch.add_effect(r, Fraction(5, 2))
            problem.add_action(touch)
            tda = DurativeAction("tda")
            set_duration(tda, x, r)
            tda.add_effect(EndTiming(), g, True)
            problem.add_action(tda)
            problem.add_goal(g)
            return TimedToSequential().compile(problem)

        for name, set_duration in (
            ("real_fluent", lambda a, x, r: a.set_closed_duration_interval(r, 10)),
            (
                "real_typed_int_fluent",
                lambda a, x, r: a.set_closed_duration_interval(1, Div(x, 2)),
            ),
        ):
            with self.subTest(name):
                with self.assertRaises(UPUnsupportedProblemTypeError):
                    compile_with(set_duration, True)
                compile_with(set_duration, False)
