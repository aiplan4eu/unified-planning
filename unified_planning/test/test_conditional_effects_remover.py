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
from unified_planning.exceptions import UPProblemDefinitionError
from unified_planning.model import GlobalStartTiming
from unified_planning.model.problem_kind import (
    classical_kind,
    full_classical_kind,
    basic_temporal_kind,
)
from unified_planning.test import unittest_TestCase, main
from unified_planning.test import (
    skipIfNoPlanValidatorForProblemKind,
    skipIfNoOneshotPlannerForProblemKind,
)
from unified_planning.test.examples import get_example_problems
from unified_planning.engines.compilers import ConditionalEffectsRemover
from unified_planning.engines import CompilationKind


class TestConditionalEffectsRemover(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_conflicting_conditional_assignments(self):
        # Both assignments fire when c1 and c2 hold, so the original action is not
        # applicable there and no compiled action may be applicable in that state.
        for first, second in ((3, 4), (4, 3)):
            x = Fluent("x", IntType(0, 5))
            c1 = Fluent("c1")
            c2 = Fluent("c2")
            problem = Problem("conflicting")
            problem.add_fluent(x, default_initial_value=0)
            problem.add_fluent(c1, default_initial_value=True)
            problem.add_fluent(c2, default_initial_value=True)
            a = InstantaneousAction("a")
            a.add_effect(x, first, c1)
            a.add_effect(x, second, c2)
            problem.add_action(a)
            problem.add_goal(GE(x, 3))

            compiled = (
                ConditionalEffectsRemover()
                .compile(problem, CompilationKind.CONDITIONAL_EFFECTS_REMOVING)
                .problem
            )
            assert isinstance(compiled, Problem)
            self.assertEqual(len(compiled.actions), 2)
            with SequentialSimulator(problem=compiled) as simulator:
                state = simulator.get_initial_state()
                for action in compiled.actions:
                    self.assertFalse(simulator.is_applicable(state, action))

    def test_conflicting_temporal_conditional_assignments(self):
        x = Fluent("x", IntType(0, 5))
        c1 = Fluent("c1")
        c2 = Fluent("c2")
        problem = Problem("conflicting_temporal")
        problem.add_fluent(x, default_initial_value=0)
        problem.add_fluent(c1, default_initial_value=True)
        problem.add_fluent(c2, default_initial_value=True)
        a = DurativeAction("a")
        a.set_fixed_duration(1)
        a.add_effect(EndTiming(), x, 3, c1)
        a.add_effect(EndTiming(), x, 4, c2)
        problem.add_action(a)
        problem.add_goal(GE(x, 3))

        compiled = (
            ConditionalEffectsRemover()
            .compile(problem, CompilationKind.CONDITIONAL_EFFECTS_REMOVING)
            .problem
        )
        assert isinstance(compiled, Problem)

        self.assertEqual(len(compiled.actions), 2)
        for action in compiled.actions:
            assert isinstance(action, DurativeAction)
            required: set[str] = set()
            for conditions in action.conditions.values():
                for condition in conditions:
                    args = condition.args if condition.is_and() else [condition]
                    required.update(str(arg) for arg in args if arg.is_fluent_exp())
            self.assertFalse({"c1", "c2"} <= required)

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    @skipIfNoPlanValidatorForProblemKind(full_classical_kind)
    def test_basic_conditional(self):
        problem = self.problems["basic_conditional"].problem
        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.CONDITIONAL_EFFECTS_REMOVING,
        ) as cer:
            res = cer.compile(problem, CompilationKind.CONDITIONAL_EFFECTS_REMOVING)
        unconditional_problem = res.problem

        self.assertTrue(problem.kind.has_conditional_effects())
        self.assertFalse(unconditional_problem.kind.has_conditional_effects())
        for a in unconditional_problem.actions:
            self.assertFalse(a.is_conditional())

        with OneshotPlanner(problem_kind=unconditional_problem.kind) as planner:
            self.assertNotEqual(planner, None)
            uncond_plan = planner.solve(unconditional_problem).plan
            new_plan = uncond_plan.replace_action_instances(
                res.map_back_action_instance
            )
            with PlanValidator(
                problem_kind=problem.kind, plan_kind=new_plan.kind
            ) as pv:
                self.assertTrue(pv.validate(problem, new_plan))

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    @skipIfNoPlanValidatorForProblemKind(full_classical_kind)
    def test_complex_conditional(self):
        problem = self.problems["complex_conditional"].problem
        with Compiler(name="up_conditional_effects_remover") as cer:
            res = cer.compile(problem, CompilationKind.CONDITIONAL_EFFECTS_REMOVING)
        unconditional_problem = res.problem
        res_2 = cer.compile(problem, CompilationKind.CONDITIONAL_EFFECTS_REMOVING)
        unconditional_problem_2 = res_2.problem
        self.assertEqual(unconditional_problem, unconditional_problem_2)

        with OneshotPlanner(problem_kind=unconditional_problem.kind) as planner:
            self.assertNotEqual(planner, None)
            uncond_plan = planner.solve(unconditional_problem).plan
            new_plan = uncond_plan.replace_action_instances(
                res.map_back_action_instance
            )
            with PlanValidator(
                problem_kind=problem.kind, plan_kind=new_plan.kind
            ) as pv:
                self.assertTrue(pv.validate(problem, new_plan))

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(basic_temporal_kind))
    def test_temporal_conditional(self):
        problem = self.problems["temporal_conditional"].problem

        with Compiler(name="up_conditional_effects_remover") as cer:
            res = cer.compile(problem, CompilationKind.CONDITIONAL_EFFECTS_REMOVING)
        unconditional_problem = res.problem

        with OneshotPlanner(problem_kind=unconditional_problem.kind) as planner:
            self.assertNotEqual(planner, None)
            uncond_plan = planner.solve(unconditional_problem).plan
            new_plan = uncond_plan.replace_action_instances(
                res.map_back_action_instance
            )
            for (s, a, d), (s_1, a_1, d_1) in zip(
                new_plan.timed_actions, uncond_plan.timed_actions
            ):
                self.assertEqual(s, s_1)
                self.assertEqual(d, d_1)
                self.assertIn(a.action, problem.actions)

    def test_ad_hoc_1(self):
        ct = GlobalStartTiming(2)
        x = unified_planning.model.Fluent("x")
        y = unified_planning.model.Fluent("y")
        problem = unified_planning.model.Problem("ad_hoc_1")
        problem.add_fluent(x, default_initial_value=True)
        problem.add_fluent(y, default_initial_value=True)
        problem.add_timed_effect(ct, y, Not(x), x)
        problem.add_goal(Not(y))
        cer = ConditionalEffectsRemover()
        res = cer.compile(problem, CompilationKind.CONDITIONAL_EFFECTS_REMOVING)
        uncond_problem = res.problem
        assert isinstance(uncond_problem, Problem)
        eff = uncond_problem.timed_effects[ct][0]
        self.assertFalse(eff.is_conditional())
        self.assertEqual(FluentExp(y), eff.fluent)
        self.assertEqual(And(Not(x), y), eff.value)

    def test_mockup_1(self):
        ct = GlobalStartTiming(2)
        x = unified_planning.model.Fluent("x", IntType())
        y = unified_planning.model.Fluent("y")
        problem = unified_planning.model.Problem("mockup_1")
        problem.add_fluent(x, default_initial_value=0)
        problem.add_fluent(y, default_initial_value=True)
        problem.add_timed_effect(ct, y, False)
        problem.add_timed_effect(ct, x, 5, y)
        cer = ConditionalEffectsRemover()
        with self.assertRaises(UPProblemDefinitionError) as e:
            cer.compile(problem, CompilationKind.CONDITIONAL_EFFECTS_REMOVING)
        self.assertIn(
            "The condition of effect: if y then x := 5\ncould not be removed without changing the problem.",
            str(e.exception),
        )
