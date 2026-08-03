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
from unified_planning.model.problem_kind import classical_kind
from unified_planning.engines.compilers.timed_to_sequential import TimedToSequential
from unified_planning.plans import SequentialPlan, TimeTriggeredPlan
from unified_planning.engines.results import (
    ValidationResultStatus,
    POSITIVE_OUTCOMES,
)
from unified_planning.engines.plan_validator import TimeTriggeredPlanValidator
from unified_planning.model.walkers import InterpretedFunctionsExtractor
from unified_planning.io import PDDLWriter
from fractions import Fraction


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

    def test_logistic(self):
        problem = self.problems["logistic"].problem
        assert isinstance(problem, Problem)
        t2s = TimedToSequential()
        comp_res = t2s.compile(problem)
        assert isinstance(comp_res.problem, Problem)
        self.assertTrue(problem.kind.has_continuous_time())
        self.assertFalse(comp_res.problem.kind.has_continuous_time())

        # distance/velocity are only used in the move action's duration, which is
        # dropped by this compilation; since they become unreferenced, they must be
        # pruned from the compiled problem
        compiled_fluent_names = {f.name for f in comp_res.problem.fluents}
        self.assertNotIn("distance", compiled_fluent_names)
        self.assertNotIn("velocity", compiled_fluent_names)

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
        # gohome's duration; once the duration is dropped it becomes unreferenced and
        # must be pruned, same as distance/velocity in test_logistic
        self.assertNotIn("normaltime", {f.name for f in comp_res.problem.fluents})

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

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
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

    def test_object_fluent_nested_in_duration_is_pruned_and_resolves(self):
        # OBJECT_FLUENTS: a duration expression where a fluent is nested inside
        # another fluent's arguments (dist(l1, tgt(l1))) must keep resolving
        # correctly at map-back time once both fluents are pruned
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
        self.assertNotIn("tgt", compiled_fluent_names)
        self.assertNotIn("dist", compiled_fluent_names)

        sp = SequentialPlan([comp_res.problem.action("mv")()])
        assert comp_res.plan_back_conversion is not None
        mapped_back = comp_res.plan_back_conversion(sp)
        expected_ttp = TimeTriggeredPlan([(Fraction(0), mv(), Fraction(7))])
        self.assertEqual(expected_ttp, mapped_back)

    def test_remove_unused_fluents_flag(self):
        # "speed" is only read by the duration expression, so it is unreferenced in the
        # compiled problem: the default prunes it, remove_unused_fluents=False keeps it.
        # Either way the duration must be reconstructed identically, from the original
        # problem's initial value when pruned and from the simulated state when not.
        problem = Problem("duration_only_fluent")
        speed = Fluent("speed", IntType())
        problem.add_fluent(speed)
        problem.set_initial_value(speed, 3)
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
        self.assertNotIn("speed", {f.name for f in pruning_res.problem.fluents})

        keeping_res = TimedToSequential(remove_unused_fluents=False).compile(problem)
        assert isinstance(keeping_res.problem, Problem)
        self.assertIn("speed", {f.name for f in keeping_res.problem.fluents})
        self.assertEqual(Int(3), keeping_res.problem.initial_value(speed()))
        # "speed" is now unreferenced by anything (no duration exists in the compiled
        # problem anymore) rather than duration-only, so it must contribute INT_FLUENTS
        self.assertTrue(keeping_res.problem.kind.has_int_fluents())

        expected_ttp = TimeTriggeredPlan([(Fraction(0), act(), Fraction(3))])
        for comp_res in (pruning_res, keeping_res):
            assert isinstance(comp_res.problem, Problem)
            assert comp_res.plan_back_conversion is not None
            sp = SequentialPlan([comp_res.problem.action("act")()])
            self.assertEqual(expected_ttp, comp_res.plan_back_conversion(sp))
