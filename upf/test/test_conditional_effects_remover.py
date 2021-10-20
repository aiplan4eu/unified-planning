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

import os
import upf
from upf.effect import Effect
from upf.environment import get_env
from upf.shortcuts import *
from upf.temporal import AbsoluteTiming
from upf.test import TestCase, main
from upf.test.examples import get_example_problems
from upf.transformers import ConditionalEffectsRemover
from upf.pddl_solver import PDDLSolver
from upf.plan_validator import PlanValidator as PV

FILE_PATH = os.path.dirname(os.path.abspath(__file__))


class ENHSP(PDDLSolver):
    def __init__(self):
        PDDLSolver.__init__(self, False)

    def _get_cmd(self, domanin_filename: str, problem_filename: str, plan_filename: str) -> List[str]:
        return ['java', '-jar', os.path.join(FILE_PATH, '..', '..', '.planners', 'enhsp-20', 'enhsp.jar'),
                '-o', domanin_filename, '-f', problem_filename, '-sp', plan_filename]


class TestConditionalEffectsRemover(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()
        env = get_env()
        if not os.path.isfile(os.path.join(FILE_PATH, '..', '..', '.planners', 'enhsp-20', 'enhsp.jar')):
            self.skipTest('ENHSP not found!')
        env.factory.add_solver('enhsp', 'upf.test.test_pddl_planner', 'ENHSP')


    def test_basic_conditional(self):
        problem = self.problems['basic_conditional'].problem
        cer = ConditionalEffectsRemover(problem)
        unconditional_problem = cer.get_rewritten_problem()
        u_actions = list(unconditional_problem.actions().values())
        a_x = problem.action("a_x")
        a_x__0__ = unconditional_problem.action("a_x__0__")
        y = FluentExp(problem.fluent("y"))
        a_x_e = a_x.effects()
        a_x__0__e = a_x__0__.effects()

        self.assertEqual(len(u_actions), 2)
        self.assertEqual(problem.action("a_y"), unconditional_problem.action("a_y"))
        self.assertTrue(a_x.is_conditional())
        self.assertFalse(unconditional_problem.has_action("a_x"))
        self.assertFalse(a_x__0__.is_conditional())
        self.assertFalse(problem.has_action("a_x_0"))
        self.assertIn(y, a_x__0__.preconditions())
        self.assertNotIn(y, a_x.preconditions())
        for e, ue in zip(a_x_e, a_x__0__e):
            self.assertEqual(e.fluent(), ue.fluent())
            self.assertEqual(e.value(), ue.value())
            self.assertFalse(ue.is_conditional())

        with OneshotPlanner(name='enhsp') as planner:
            self.assertNotEqual(planner, None)
            plan = planner.solve(problem)
            uncond_plan = planner.solve(unconditional_problem)
            self.assertNotEqual(str(plan), str(uncond_plan))
            new_plan = cer.rewrite_back_plan(uncond_plan)
            # with PlanValidator(problem_kind=problem.kind()) as validator:
            #     self.assertNotEqual(validator, None)

            #     res = validator.validate(problem, plan)
            #     self.assertTrue(res)
            #     res = validator.validate(unconditional_problem, uncond_plan)
            #     self.assertTrue(res)
            #     res = validator.validate(problem, new_plan)
            #     self.assertTrue(res)

    def test_complex_conditional(self):
        problem = self.problems['complex_conditional'].problem
        plan = self.problems['complex_conditional'].plan
        cer = ConditionalEffectsRemover(problem)
        unconditional_problem = cer.get_rewritten_problem()
        unconditional_problem_2 = cer.get_rewritten_problem()
        self.assertEqual(unconditional_problem, unconditional_problem_2)

        with OneshotPlanner(problem_kind=unconditional_problem.kind()) as planner:
            self.assertNotEqual(planner, None)
            uncond_plan = planner.solve(unconditional_problem)
            self.assertNotEqual(str(plan), str(uncond_plan))
            new_plan = cer.rewrite_back_plan(uncond_plan)
            self.assertEqual(str(plan), str(new_plan))
            # with PlanValidator(problem_kind=problem.kind()) as validator:
            #     self.assertNotEqual(validator, None)

            #     res = validator.validate(problem, plan)
            #     self.assertTrue(res)
            #     res = validator.validate(unconditional_problem, uncond_plan)
            #     self.assertTrue(res)
            #     res = validator.validate(problem, new_plan)
            #     self.assertTrue(res)

    def test_temporal_conditional(self):
        problem = self.problems['temporal_conditional'].problem
        plan = self.problems['temporal_conditional'].plan

        cer = ConditionalEffectsRemover(problem)
        unconditional_problem = cer.get_rewritten_problem()

        with OneshotPlanner(name='tamer', params={'weight': 0.8}) as planner:
            self.assertNotEqual(planner, None)
            unconditional_plan = planner.solve(unconditional_problem)
            self.assertNotEqual(str(plan), str(unconditional_plan))
            conditional_plan = cer.rewrite_back_plan(unconditional_plan)
            self.assertEqual(str(plan), str(conditional_plan))

    def test_ad_hoc_1(self):
        ct = AbsoluteTiming(2)
        x = upf.Fluent('x')
        y = upf.Fluent('y')
        problem = upf.Problem('ad_hoc_1')
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
