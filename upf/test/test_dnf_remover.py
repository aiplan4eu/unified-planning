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
from upf.dnf_remover import DnfRemover
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
        self.env = get_env()
        if not os.path.isfile(os.path.join(FILE_PATH, '..', '..', '.planners', 'enhsp-20', 'enhsp.jar')):
            self.skipTest('ENHSP not found!')
        self.env.factory.add_solver('enhsp', 'upf.test.test_pddl_planner', 'ENHSP')


    def test_charge_discharge(self):
        problem = self.problems['charge_discharge'].problem
        plan = self.problems['charge_discharge'].plan
        dnfr = DnfRemover(problem)
        dnf_problem = dnfr.get_rewritten_problem()

        with OneshotPlanner(name='enhsp') as planner:
            self.assertNotEqual(planner, None)
            dnf_plan = planner.solve(dnf_problem)
            self.assertNotEqual(str(plan), str(dnf_plan))
            new_plan = dnfr.rewrite_back_plan(dnf_plan)
            self.assertEqual(str(plan), str(new_plan))
            #self.assertEqual(plan, new_plan)# -> shouldn't they be Equal?
