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
#

from typing import cast
import warnings
import unified_planning
from unified_planning.shortcuts import *
from unified_planning.model.problem_kind import (
    classical_kind,
    full_classical_kind,
    simple_numeric_kind,
    general_numeric_kind,
    quantified_conditions_kind,
    basic_temporal_kind,
    hierarchical_kind,
)
from unified_planning.test import (
    unittest_TestCase,
    skipIfNoPlanValidatorForProblemKind,
    skipIfNoOneshotPlannerForProblemKind,
    skipIfEngineNotAvailable,
)
from unified_planning.test.examples import get_example_problems
from unified_planning.engines import CompilationKind
from unified_planning.engines.compilers import Grounder


class TestGrounder(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_basic(self):
        problem = self.problems["basic"].problem

        gro = Grounder()

        res = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem = res.problem
        assert isinstance(grounded_problem, Problem)
        res_2 = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem_2 = res_2.problem

        self.assertEqual(grounded_problem, grounded_problem_2)
        grounded_problem.name = problem.name
        self.assertEqual(grounded_problem, problem)

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(general_numeric_kind))
    @skipIfNoPlanValidatorForProblemKind(classical_kind.union(general_numeric_kind))
    def test_robot(self):
        problem = self.problems["robot"].problem

        gro = Grounder()
        res = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem = res.problem
        assert isinstance(grounded_problem, Problem)
        self.assertEqual(len(grounded_problem.actions), 2)
        for a in grounded_problem.actions:
            self.assertEqual(len(a.parameters), 0)

        with OneshotPlanner(problem_kind=grounded_problem.kind) as planner:
            self.assertNotEqual(planner, None)
            grounded_plan = planner.solve(grounded_problem).plan
            plan = grounded_plan.replace_action_instances(res.map_back_action_instance)
            for ai in plan.actions:
                a = ai.action
                self.assertEqual(a, problem.action(a.name))
            with PlanValidator(problem_kind=problem.kind, plan_kind=plan.kind) as pv:
                self.assertTrue(pv.validate(problem, plan))

    @skipIfNoOneshotPlannerForProblemKind(
        classical_kind.union(simple_numeric_kind).union(quantified_conditions_kind)
    )
    @skipIfNoPlanValidatorForProblemKind(
        classical_kind.union(simple_numeric_kind).union(quantified_conditions_kind)
    )
    def test_robot_locations_connected(self):
        problem = self.problems["robot_locations_connected"].problem

        gro = Grounder()
        res = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem = res.problem
        assert isinstance(grounded_problem, Problem)
        self.assertEqual(len(grounded_problem.actions), 28)
        for a in grounded_problem.actions:
            self.assertEqual(len(a.parameters), 0)

        with OneshotPlanner(problem_kind=grounded_problem.kind) as planner:
            self.assertNotEqual(planner, None)
            grounded_plan = planner.solve(grounded_problem).plan
            plan = grounded_plan.replace_action_instances(res.map_back_action_instance)
            for ai in plan.actions:
                a = ai.action
                self.assertEqual(a, problem.action(a.name))
            with PlanValidator(problem_kind=problem.kind, plan_kind=plan.kind) as pv:
                self.assertTrue(pv.validate(problem, plan))

    @skipIfNoOneshotPlannerForProblemKind(
        classical_kind.union(simple_numeric_kind).union(quantified_conditions_kind)
    )
    @skipIfNoPlanValidatorForProblemKind(
        classical_kind.union(simple_numeric_kind).union(quantified_conditions_kind)
    )
    def test_robot_locations_connected_from_factory(self):
        problem = self.problems["robot_locations_connected"].problem

        with Compiler(name="up_grounder") as grounder:
            self.assertTrue(grounder.supports(problem.kind))
            res = grounder.compile(problem, CompilationKind.GROUNDING)
            grounded_problem = res.problem
            assert isinstance(grounded_problem, Problem)
            self.assertEqual(len(grounded_problem.actions), 28)
            for a in grounded_problem.actions:
                self.assertEqual(len(a.parameters), 0)

            with OneshotPlanner(problem_kind=grounded_problem.kind) as planner:
                self.assertNotEqual(planner, None)
                grounded_plan = planner.solve(grounded_problem).plan
                plan = grounded_plan.replace_action_instances(
                    res.map_back_action_instance
                )
                for ai in plan.actions:
                    a = ai.action
                    self.assertEqual(a, problem.action(a.name))
                with PlanValidator(
                    problem_kind=problem.kind, plan_kind=plan.kind
                ) as pv:
                    self.assertTrue(pv.validate(problem, plan))

    @skipIfNoOneshotPlannerForProblemKind(
        classical_kind.union(simple_numeric_kind).union(quantified_conditions_kind)
    )
    @skipIfNoPlanValidatorForProblemKind(
        classical_kind.union(simple_numeric_kind).union(quantified_conditions_kind)
    )
    def test_robot_locations_connected_from_factory_with_problem_kind(self):
        problem = self.problems["robot_locations_connected"].problem
        kind = problem.kind

        with Compiler(
            problem_kind=kind, compilation_kind=CompilationKind.GROUNDING
        ) as embedded_grounder:
            self.assertTrue(embedded_grounder.supports(kind))
            ground_result = embedded_grounder.compile(
                problem, CompilationKind.GROUNDING
            )
            grounded_problem, rewrite_plan_funct = (
                ground_result.problem,
                ground_result.map_back_action_instance,
            )
            self.assertEqual(len(grounded_problem.actions), 28)
            for a in grounded_problem.actions:
                self.assertEqual(len(a.parameters), 0)

            with OneshotPlanner(problem_kind=grounded_problem.kind) as planner:
                self.assertNotEqual(planner, None)
                grounded_plan = planner.solve(grounded_problem).plan
                plan = grounded_plan.replace_action_instances(rewrite_plan_funct)
                for ai in plan.actions:
                    a = ai.action
                    self.assertEqual(a, problem.action(a.name))
                with PlanValidator(
                    problem_kind=problem.kind, plan_kind=plan.kind
                ) as pv:
                    self.assertTrue(pv.validate(problem, plan))

    @skipIfNoOneshotPlannerForProblemKind(hierarchical_kind)
    @skipIfNoPlanValidatorForProblemKind(hierarchical_kind)
    def test_hierarchical_blocks_world(self):
        problem = self.problems["hierarchical_blocks_world"].problem

        gro = Grounder()
        ground_result = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem = ground_result.problem
        assert isinstance(grounded_problem, Problem)
        self.assertEqual(len(grounded_problem.actions), 108)
        for a in grounded_problem.actions:
            self.assertEqual(len(a.parameters), 0)

        with OneshotPlanner(problem_kind=grounded_problem.kind) as planner:
            self.assertNotEqual(planner, None)
            grounded_plan = planner.solve(grounded_problem).plan
            plan = grounded_plan.replace_action_instances(
                ground_result.map_back_action_instance
            )
            for ai in plan.actions:
                a = ai.action
                self.assertEqual(a, problem.action(a.name))
            with PlanValidator(problem_kind=problem.kind, plan_kind=plan.kind) as pv:
                self.assertTrue(pv.validate(problem, plan))

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(basic_temporal_kind))
    @skipIfNoPlanValidatorForProblemKind(classical_kind.union(basic_temporal_kind))
    def test_matchcellar(self):
        problem = self.problems["matchcellar"].problem

        gro = Grounder()
        ground_result = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem = ground_result.problem
        assert isinstance(grounded_problem, Problem)
        self.assertEqual(len(grounded_problem.actions), 6)
        for a in grounded_problem.actions:
            self.assertEqual(len(a.parameters), 0)

        with OneshotPlanner(problem_kind=grounded_problem.kind) as planner:
            self.assertNotEqual(planner, None)
            grounded_plan = planner.solve(grounded_problem).plan
            plan = grounded_plan.replace_action_instances(
                ground_result.map_back_action_instance
            )
            for _, ai, _ in plan.timed_actions:
                a = ai.action
                self.assertEqual(a, problem.action(a.name))
            with PlanValidator(problem_kind=problem.kind, plan_kind=plan.kind) as pv:
                self.assertTrue(pv.validate(problem, plan))

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(basic_temporal_kind))
    @skipIfNoPlanValidatorForProblemKind(classical_kind.union(basic_temporal_kind))
    def test_matchcellar_grounder_from_factory(self):
        problem = self.problems["matchcellar"].problem

        gro = Grounder()
        ground_result = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem_test = ground_result.problem
        with Compiler(name="up_grounder") as grounder:
            self.assertTrue(grounder.supports(problem.kind))
            ground_result = grounder.compile(problem, CompilationKind.GROUNDING)
            grounded_problem_try, rewrite_back_plan_function = (
                ground_result.problem,
                ground_result.map_back_action_instance,
            )
            assert isinstance(grounded_problem_try, Problem)
            self.assertEqual(grounded_problem_test, grounded_problem_try)
            with OneshotPlanner(problem_kind=grounded_problem_try.kind) as planner:
                self.assertNotEqual(planner, None)
                grounded_plan = planner.solve(grounded_problem_try).plan
                plan = grounded_plan.replace_action_instances(
                    rewrite_back_plan_function
                )
                for _, ai, _ in plan.timed_actions:
                    a = ai.action
                    self.assertEqual(a, problem.action(a.name))
                with PlanValidator(
                    problem_kind=problem.kind, plan_kind=plan.kind
                ) as pv:
                    self.assertTrue(pv.validate(problem, plan))

    def test_timed_connected_locations(self):
        problem = self.problems["timed_connected_locations"].problem

        gro = Grounder()
        ground_result = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem = ground_result.problem
        assert isinstance(grounded_problem, Problem)
        self.assertEqual(len(grounded_problem.actions), 20)
        for a in grounded_problem.actions:
            self.assertEqual(len(a.parameters), 0)

    def test_matchcellar_static_duration(self):
        problem = self.problems["matchcellar_static_duration"].problem
        fvo = problem.environment.free_vars_oracle
        gro = Grounder()
        ground_result = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem = ground_result.problem
        assert isinstance(grounded_problem, Problem)
        self.assertEqual(len(grounded_problem.actions), 6)
        for a in grounded_problem.actions:
            a = cast(DurativeAction, a)
            self.assertEqual(len(a.parameters), 0)
            self.assertEqual(len(fvo.get_free_variables(a.duration.lower)), 0)
            self.assertEqual(len(fvo.get_free_variables(a.duration.upper)), 0)
        # the static fluents used as durations are simplified away to their values
        expected_durations = {
            "light_match_m1": 2,
            "light_match_m2": 3,
            "light_match_m3": 4,
            "mend_fuse_f1": 1,
            "mend_fuse_f2": 2,
            "mend_fuse_f3": 3,
        }
        for name, value in expected_durations.items():
            a = cast(DurativeAction, grounded_problem.action(name))
            self.assertEqual(a.duration.lower.constant_value(), value)
            self.assertEqual(a.duration.upper.constant_value(), value)

    def test_interpreted_functions_in_durations(self):
        problem = self.problems["interpreted_functions_undef_numeric_durative"].problem
        assert isinstance(problem, Problem)
        # regression guard: the Grounder must not reject interpreted functions in durations
        self.assertTrue(Grounder.supports(problem.kind))

        original_action = problem.action("undef_move")
        assert isinstance(original_action, DurativeAction)
        o = original_action.parameter("o")
        undef_o1 = problem.object("undef_o1")
        undef_o2 = problem.object("undef_o2")

        gro = Grounder()
        ground_result = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem = ground_result.problem
        assert isinstance(grounded_problem, Problem)
        self.assertEqual(len(grounded_problem.actions), 2)
        for a in grounded_problem.actions:
            self.assertEqual(len(a.parameters), 0)
        self.assertTrue(
            grounded_problem.kind <= Grounder.resulting_problem_kind(problem.kind)
        )

        # undef_durative_value(undef_o1) is defined (2), so the interpreted function call
        # in the duration is evaluated and replaced by its value
        move_o1 = cast(DurativeAction, grounded_problem.action("undef_move_undef_o1"))
        self.assertEqual(move_o1.duration.lower.constant_value(), 4)
        self.assertEqual(move_o1.duration.upper.constant_value(), 4)

        # undef_durative_value(undef_o2) is left undefined, so the interpreted function
        # call cannot be evaluated and is carried over, with its argument substituted
        move_o2 = cast(DurativeAction, grounded_problem.action("undef_move_undef_o2"))
        expected_duration = original_action.duration.lower.substitute(
            {o: problem.environment.expression_manager.ObjectExp(undef_o2)}
        )
        self.assertEqual(move_o2.duration.lower, expected_duration)
        self.assertEqual(move_o2.duration.upper, expected_duration)

        assert ground_result.map_back_action_instance is not None
        lifted = ground_result.map_back_action_instance(move_o1())
        assert lifted is not None
        self.assertEqual(lifted.action, original_action)
        self.assertEqual(
            lifted.actual_parameters,
            (problem.environment.expression_manager.ObjectExp(undef_o1),),
        )

    def test_interpreted_functions_in_duration_inequality(self):
        problem = self.problems[
            "interpreted_functions_in_durative_start_effects"
        ].problem
        assert isinstance(problem, Problem)
        self.assertTrue(Grounder.supports(problem.kind))

        original_action = problem.action("charge")
        assert isinstance(original_action, DurativeAction)

        gro = Grounder()
        ground_result = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem = ground_result.problem
        assert isinstance(grounded_problem, Problem)
        self.assertEqual(len(grounded_problem.actions), 1)

        # battery is not a static fluent, so the interpreted function call in the
        # lower bound cannot be evaluated and is carried over unchanged
        charge = cast(DurativeAction, grounded_problem.action("charge"))
        self.assertEqual(charge.duration.lower, original_action.duration.lower)
        self.assertEqual(charge.duration.upper, original_action.duration.upper)
        self.assertEqual(
            charge.duration.is_left_open(), original_action.duration.is_left_open()
        )
        self.assertEqual(
            charge.duration.is_right_open(), original_action.duration.is_right_open()
        )

    def test_empty_simplified_duration_drops_action(self):
        problem = Problem("empty_simplified_duration")
        Item = UserType("Item")
        a = Object("a", Item)
        b = Object("b", Item)
        static_lower = Fluent("static_lower", IntType(), x=Item)
        static_upper = Fluent("static_upper", IntType(), x=Item)
        done = Fluent("done")

        action = DurativeAction("act", x=Item)
        x = action.parameter("x")
        action.set_closed_duration_interval(static_lower(x), static_upper(x))
        action.add_effect(EndTiming(), done, True)

        problem.add_fluent(static_lower, default_initial_value=0)
        problem.add_fluent(static_upper, default_initial_value=0)
        problem.add_fluent(done, default_initial_value=False)
        # for "a" the interval [1, 5] is non-empty; for "b" the interval [5, 1] is empty
        problem.set_initial_value(static_lower(a), 1)
        problem.set_initial_value(static_upper(a), 5)
        problem.set_initial_value(static_lower(b), 5)
        problem.set_initial_value(static_upper(b), 1)
        problem.add_object(a)
        problem.add_object(b)
        problem.add_action(action)

        gro = Grounder()
        ground_result = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem = ground_result.problem
        assert isinstance(grounded_problem, Problem)
        self.assertEqual(len(grounded_problem.actions), 1)
        self.assertEqual(grounded_problem.actions[0].name, "act_a")

    def test_ad_hoc_1(self):
        problem = Problem("ad_hoc")
        Location = UserType("Location")
        visited = Fluent("at", BoolType(), position=Location)
        l1 = Object("l1", Location)
        visit = InstantaneousAction("visit", l_to=Location)
        l_to = visit.parameter("l_to")
        visit.add_effect(visited(l_to), True)
        visit_l1 = InstantaneousAction("visit_l1")
        visit_l1.add_effect(visited(l1), True)
        problem.add_fluent(visited)
        problem.set_initial_value(visited(l1), True)
        problem.add_object(l1)
        problem.add_action(visit)
        problem.add_action(visit_l1)
        gro = Grounder()
        ground_result = gro.compile(problem, CompilationKind.GROUNDING)
        grounded_problem = ground_result.problem
        assert isinstance(grounded_problem, Problem)
        self.assertEqual(len(grounded_problem.actions), 2)
        for a in grounded_problem.actions:
            self.assertEqual(len(a.parameters), 0)

    def test_static_bool_conditions_prune_same_object_once(self):
        problem = Problem("static_bool_conditions")
        item_type = UserType("Item")
        a = Object("a", item_type)
        b = Object("b", item_type)
        static_1 = Fluent("static_1", BoolType(), x=item_type)
        static_2 = Fluent("static_2", BoolType(), x=item_type)
        done = Fluent("done")
        action = InstantaneousAction("act", x=item_type)
        x = action.parameter("x")

        action.add_precondition(static_1(x))
        action.add_precondition(static_2(x))
        action.add_effect(done, True)

        problem.add_fluent(static_1, default_initial_value=False)
        problem.add_fluent(static_2, default_initial_value=False)
        problem.add_fluent(done, default_initial_value=False)
        problem.set_initial_value(static_1(a), True)
        problem.set_initial_value(static_2(a), True)
        problem.add_object(a)
        problem.add_object(b)
        problem.add_action(action)

        grounded_problem = (
            Grounder().compile(problem, CompilationKind.GROUNDING).problem
        )

        assert isinstance(grounded_problem, Problem)
        self.assertEqual(len(grounded_problem.actions), 1)
        self.assertEqual(grounded_problem.actions[0].name, "act_a")
        self.assertEqual(len(grounded_problem.actions[0].parameters), 0)

    def test_effect_target_arguments_are_simplified(self):
        # the effect's target fluent must be normalized like its value: f(x + 1) grounded
        # with x := 1 must become f(2), not the unevaluated f((1 + 1)). A second effect on
        # the constant f(2) makes x = 1 target the same fluent instance twice with different
        # values, so that grounding must be dropped as conflicting-effects, exactly like it
        # would be if the first effect had been written as f(2) directly.
        f = Fluent("f", IntType(), i=IntType(0, 3))
        action = InstantaneousAction("act", x=IntType(0, 2))
        x = action.parameter("x")
        action.add_effect(f(Plus(x, 1)), Plus(x, 1))
        action.add_effect(f(Int(2)), 99)

        problem = Problem("arith_target")
        problem.add_fluent(f, default_initial_value=0)
        problem.add_action(action)

        grounded_problem = (
            Grounder().compile(problem, CompilationKind.GROUNDING).problem
        )
        assert isinstance(grounded_problem, Problem)
        # act_1 (x = 1) is dropped: f(1 + 1) and f(2) conflict once both are simplified to f(2)
        self.assertEqual(len(grounded_problem.actions), 2)
        em = problem.environment.expression_manager
        for i in (0, 2):
            a = cast(InstantaneousAction, grounded_problem.action(f"act_{i}"))
            first_effect, second_effect = a.effects
            self.assertEqual(first_effect.fluent, f(em.Int(i + 1)))
            self.assertEqual(first_effect.value, em.Int(i + 1))
            self.assertEqual(second_effect.fluent, f(em.Int(2)))
            self.assertEqual(second_effect.value, em.Int(99))

    def test_zero_parameter_action_effect_target_is_normalized(self):
        # a zero-parameter action is never routed through create_action_with_given_subs
        # (there is nothing to substitute), so its effects must still be normalized
        # explicitly; otherwise a hand-written f(1 + 1) target survives grounding unevaluated.
        f = Fluent("f", IntType(), i=IntType(0, 3))
        action = InstantaneousAction("act")
        action.add_effect(f(Plus(Int(1), Int(1))), 1)

        problem = Problem("zero_param_arith_target")
        problem.add_fluent(f, default_initial_value=0)
        problem.add_action(action)

        grounded_problem = (
            Grounder().compile(problem, CompilationKind.GROUNDING).problem
        )
        assert isinstance(grounded_problem, Problem)
        self.assertEqual(len(grounded_problem.actions), 1)
        # the action keeps its original name: normalization must not reroute it through
        # get_fresh_name, which would rename it to "act_0".
        ga = cast(InstantaneousAction, grounded_problem.action("act"))
        em = problem.environment.expression_manager
        (effect,) = ga.effects
        self.assertEqual(effect.fluent, f(em.Int(2)))
        self.assertEqual(effect.value, em.Int(1))

    def test_zero_parameter_action_conflicting_effects_are_detected(self):
        # same shape as test_effect_target_arguments_are_simplified, but with zero
        # parameters: the un-normalized target of the first effect must not let the
        # conflict with the second effect's f(2) go undetected.
        f = Fluent("f", IntType(), i=IntType(0, 3))
        action = InstantaneousAction("act")
        action.add_effect(f(Plus(Int(1), Int(1))), 1)
        action.add_effect(f(Int(2)), 99)

        problem = Problem("zero_param_conflict")
        problem.add_fluent(f, default_initial_value=0)
        problem.add_action(action)

        grounded_problem = (
            Grounder().compile(problem, CompilationKind.GROUNDING).problem
        )
        assert isinstance(grounded_problem, Problem)
        self.assertEqual(len(grounded_problem.actions), 0)

    def test_zero_parameter_action_simulated_effect_survives_normalization(self):
        # normalizing effects clears and rebuilds the action's bookkeeping, which also
        # wipes any simulated effect; it must be restored afterwards.
        f = Fluent("f", IntType())
        x = Fluent("x", IntType())
        action = InstantaneousAction("act")
        action.add_effect(f(), 1)

        def fun(problem, state, actual_params):
            return [Int(0)]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            action.set_simulated_effect(SimulatedEffect([FluentExp(x)], fun))

        problem = Problem("zero_param_simulated")
        problem.add_fluent(f, default_initial_value=0)
        problem.add_fluent(x, default_initial_value=1)
        problem.add_action(action)

        grounded_problem = (
            Grounder().compile(problem, CompilationKind.GROUNDING).problem
        )
        assert isinstance(grounded_problem, Problem)
        self.assertEqual(len(grounded_problem.actions), 1)
        ga = cast(InstantaneousAction, grounded_problem.action("act"))
        self.assertIsNotNone(ga.simulated_effect)

    def test_zero_parameter_durative_action_effect_target_is_normalized(self):
        # durative-action variant of test_zero_parameter_action_effect_target_is_normalized:
        # the target must be normalized at its own timing, and the duration left untouched.
        f = Fluent("f", IntType(), i=IntType(0, 3))
        action = DurativeAction("act")
        action.set_fixed_duration(1)
        action.add_effect(EndTiming(), f(Plus(Int(1), Int(1))), 1)

        problem = Problem("zero_param_durative_arith_target")
        problem.add_fluent(f, default_initial_value=0)
        problem.add_action(action)

        grounded_problem = (
            Grounder().compile(problem, CompilationKind.GROUNDING).problem
        )
        assert isinstance(grounded_problem, Problem)
        self.assertEqual(len(grounded_problem.actions), 1)
        ga = cast(DurativeAction, grounded_problem.action("act"))
        self.assertEqual(ga.duration, action.duration)
        em = problem.environment.expression_manager
        (effect,) = ga.effects[EndTiming()]
        self.assertEqual(effect.fluent, f(em.Int(2)))
        self.assertEqual(effect.value, em.Int(1))

    @skipIfEngineNotAvailable("pyperplan")
    def test_pyperplan_grounder(self):
        problem = self.problems["robot_no_negative_preconditions"].problem
        for action in problem.actions:
            self.assertTrue(len(action.parameters) > 0)
        with Compiler(name="pyperplan") as grounder:
            ground_result = grounder.compile(problem, CompilationKind.GROUNDING)
            grounded_problem, rewrite_back_plan_function = (
                ground_result.problem,
                ground_result.map_back_action_instance,
            )
            for grounded_action in grounded_problem.actions:
                self.assertEqual(len(grounded_action.parameters), 0)
            with OneshotPlanner(problem_kind=grounded_problem.kind) as planner:
                self.assertNotEqual(planner, None)
                grounded_plan = planner.solve(grounded_problem).plan
                plan = grounded_plan.replace_action_instances(
                    rewrite_back_plan_function
                )
                for ai in plan.actions:
                    a = ai.action
                    self.assertEqual(a, problem.action(a.name))
                with PlanValidator(
                    problem_kind=problem.kind, plan_kind=plan.kind
                ) as pv:
                    self.assertTrue(pv.validate(problem, plan))

    @skipIfEngineNotAvailable("pyperplan")
    def test_pyperplan_grounder_mockup_problem(self):
        problem = Problem("mockup")
        Location = UserType("Location")
        at = Fluent("at", BoolType(), position=Location)
        at_l2 = Fluent("at_l2")
        l1 = Object("l1", Location)
        l2 = Object("l2", Location)
        move_to = InstantaneousAction("move_to", l_to=Location)
        l_to = move_to.parameter("l_to")
        move_to.add_effect(at(l_to), True)
        move_to_l2 = InstantaneousAction("move_to_l2")
        move_to_l2.add_effect(at_l2, True)
        problem.add_fluent(at, default_initial_value=False)
        problem.add_fluent(at_l2, default_initial_value=False)
        problem.add_object(l1)
        problem.add_object(l2)
        problem.add_action(move_to)
        problem.add_action(move_to_l2)
        problem.add_goal(at(l1))
        problem.add_goal(at(l2))
        problem.add_goal(at_l2)

        with Compiler(name="pyperplan") as grounder:
            ground_result = grounder.compile(problem, CompilationKind.GROUNDING)
            grounded_problem, rewrite_back_plan_function = (
                ground_result.problem,
                ground_result.map_back_action_instance,
            )
            for grounded_action in grounded_problem.actions:
                self.assertEqual(len(grounded_action.parameters), 0)
            with OneshotPlanner(problem_kind=grounded_problem.kind) as planner:
                self.assertNotEqual(planner, None)
                grounded_plan = planner.solve(grounded_problem).plan
                plan = grounded_plan.replace_action_instances(
                    rewrite_back_plan_function
                )
                for ai in plan.actions:
                    a = ai.action
                    self.assertEqual(a, problem.action(a.name))
                with PlanValidator(
                    problem_kind=problem.kind, plan_kind=plan.kind
                ) as pv:
                    self.assertTrue(pv.validate(problem, plan))
