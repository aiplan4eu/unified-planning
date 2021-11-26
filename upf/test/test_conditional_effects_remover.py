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


import upf
from upf.shortcuts import *
from upf.exceptions import UPFProblemDefinitionError
from upf.model import AbsoluteTiming
from upf.model.effect import ASSIGN
from upf.model.problem_kind import classical_kind, full_classical_kind, basic_temporal_kind
from upf.test import TestCase, main
from upf.test import skipIfNoPlanValidatorForProblemKind, skipIfNoOneshotPlannerForProblemKind, skipIfSolverNotAvailable
from upf.test.examples import get_example_problems
from upf.transformers import ConditionalEffectsRemover


class TestConditionalEffectsRemover(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    @skipIfNoPlanValidatorForProblemKind(full_classical_kind)
    def test_basic_conditional(self):
        problem = self.problems['basic_conditional'].problem
        cer = ConditionalEffectsRemover(problem)
        unconditional_problem = cer.get_rewritten_problem()
        u_actions = unconditional_problem.actions()
        a_x = problem.action("a_x")
        a_x_new_list = cer.get_transformed_actions(a_x)
        self.assertEqual(len(a_x_new_list), 1)
        new_action = unconditional_problem.action(a_x_new_list[0].name)
        y = FluentExp(problem.fluent("y"))
        a_x_e = a_x.effects()
        new_action_e = new_action.effects()

        self.assertEqual(len(u_actions), 2)
        self.assertEqual(problem.action("a_y"), unconditional_problem.action("a_y"))
        self.assertTrue(a_x.is_conditional())
        self.assertFalse(unconditional_problem.has_action("a_x"))
        self.assertFalse(new_action.is_conditional())
        self.assertIn(y, new_action.preconditions())
        self.assertNotIn(y, a_x.preconditions())
        for e, ue in zip(a_x_e, new_action_e):
            self.assertEqual(e.fluent(), ue.fluent())
            self.assertEqual(e.value(), ue.value())
            self.assertFalse(ue.is_conditional())

        self.assertTrue(problem.kind().has_conditional_effects())
        self.assertFalse(unconditional_problem.kind().has_conditional_effects())
        for a in unconditional_problem.actions():
            self.assertFalse(a.is_conditional())

        with OneshotPlanner(problem_kind=unconditional_problem.kind()) as planner:
            self.assertNotEqual(planner, None)
            uncond_plan = planner.solve(unconditional_problem)
            new_plan = cer.rewrite_back_plan(uncond_plan)
            with PlanValidator(problem_kind=problem.kind()) as pv:
                self.assertTrue(pv.validate(problem, new_plan))

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    @skipIfNoPlanValidatorForProblemKind(full_classical_kind)
    def test_complex_conditional(self):
        problem = self.problems['complex_conditional'].problem
        cer = ConditionalEffectsRemover(problem)
        unconditional_problem = cer.get_rewritten_problem()
        unconditional_problem_2 = cer.get_rewritten_problem()
        self.assertEqual(unconditional_problem, unconditional_problem_2)

        with OneshotPlanner(problem_kind=unconditional_problem.kind()) as planner:
            self.assertNotEqual(planner, None)
            uncond_plan = planner.solve(unconditional_problem)
            new_plan = cer.rewrite_back_plan(uncond_plan)
            with PlanValidator(problem_kind=problem.kind()) as pv:
                self.assertTrue(pv.validate(problem, new_plan))

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(basic_temporal_kind))
    def test_temporal_conditional(self):
        problem = self.problems['temporal_conditional'].problem

        cer = ConditionalEffectsRemover(problem)
        unconditional_problem = cer.get_rewritten_problem()

        with OneshotPlanner(problem_kind=unconditional_problem.kind()) as planner:
            self.assertNotEqual(planner, None)
            uncond_plan = planner.solve(unconditional_problem)
            new_plan = cer.rewrite_back_plan(uncond_plan)
            for (s, a, d), (s_1, a_1, d_1) in zip(new_plan.actions(), uncond_plan.actions()):
                self.assertEqual(s, s_1)
                self.assertEqual(d, d_1)
                self.assertIn(a.action(), problem.actions())

    def test_ad_hoc_1(self):
        ct = AbsoluteTiming(2)
        x = upf.model.Fluent('x')
        y = upf.model.Fluent('y')
        problem = upf.model.Problem('ad_hoc_1')
        problem.add_fluent(x, default_initial_value=True)
        problem.add_fluent(y, default_initial_value=True)
        problem.add_timed_effect(ct, y, Not(x), x)
        problem.add_goal(Not(y))
        cer = ConditionalEffectsRemover(problem)
        uncond_problem = cer.get_rewritten_problem()
        eff = uncond_problem.timed_effects()[ct][0]
        self.assertFalse(eff.is_conditional())
        self.assertEqual(FluentExp(y), eff.fluent())
        self.assertEqual(And(Not(x), y), eff.value())

    def test_mockup_1(self):
        ct = AbsoluteTiming(2)
        x = upf.model.Fluent('x', IntType())
        y = upf.model.Fluent('y')
        problem = upf.model.Problem('mockup_1')
        problem.add_fluent(x, default_initial_value=0)
        problem.add_fluent(y, default_initial_value=True)
        problem.add_timed_effect(ct, y, False)
        problem.add_timed_effect(ct, x, 5, y)
        cer = ConditionalEffectsRemover(problem)
        with self.assertRaises(UPFProblemDefinitionError) as e:
            cer.get_rewritten_problem()
        self.assertIn('The condition of effect: if y then x := 5\ncould not be removed without changing the problem.', str(e.exception))
