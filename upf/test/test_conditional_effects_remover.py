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
from upf.environment import get_env
from upf.shortcuts import *
from upf.test import TestCase, main
from upf.test.examples import get_example_problems
from upf.conditional_effects_remover import ConditionalEffectsRemover
from upf.pddl_solver import PDDLSolver


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
        a_x_0 = unconditional_problem.action("a_x_0")
        y = FluentExp(problem.fluent("y"))
        a_x_e = a_x.effects()
        a_x_0_e = a_x_0.effects()

        self.assertEqual(len(u_actions), 2)
        self.assertEqual(problem.action("a_y"), unconditional_problem.action("a_y"))
        self.assertTrue(a_x.has_conditional_effects())
        self.assertFalse(unconditional_problem.has_action("a_x"))
        self.assertFalse(a_x_0.has_conditional_effects())
        self.assertFalse(problem.has_action("a_x_0"))
        self.assertIn(y, a_x_0.preconditions())
        self.assertNotIn(y, a_x.preconditions())
        for e, ue in zip(a_x_e, a_x_0_e):
            self.assertEqual(e.fluent(), ue.fluent())
            self.assertEqual(e.value(), ue.value())
            self.assertFalse(ue.is_conditional())

        with OneshotPlanner(name='enhsp') as planner:
            self.assertNotEqual(planner, None)
            plan = planner.solve(problem)
            uncond_plan = planner.solve(unconditional_problem)
            self.assertNotEqual(str(plan), str(uncond_plan))
            new_plan = cer.rewrite_back_plan(plan)
            self.assertEqual(str(plan), str(new_plan))

    def test_complex_conditional(self):
        problem = self.problems['complex_conditional'].problem
        cer = ConditionalEffectsRemover(problem)
        unconditional_problem = cer.get_rewritten_problem()

        with OneshotPlanner(name='enhsp') as planner:
            self.assertNotEqual(planner, None)
            plan = planner.solve(problem)
            uncond_plan = planner.solve(unconditional_problem)
            self.assertNotEqual(str(plan), str(uncond_plan))
            new_plan = cer.rewrite_back_plan(plan)
            self.assertEqual(str(plan), str(new_plan))
