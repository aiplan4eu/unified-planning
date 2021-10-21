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
from upf.test import TestCase, main, skipIfSolverNotAvailable
from upf.test.examples import get_example_problems
from upf.transformers import QuantifiersRemover
from upf.pddl_solver import PDDLSolver
from upf.io.pddl_writer import PDDLWriter
from upf.environment import get_env
from upf.shortcuts import *
from typing import List


FILE_PATH = os.path.dirname(os.path.abspath(__file__))


class ENHSP(PDDLSolver):
    def __init__(self):
        PDDLSolver.__init__(self, False)

    def _get_cmd(self, domanin_filename: str, problem_filename: str, plan_filename: str) -> List[str]:
        return ['java', '-jar', os.path.join(FILE_PATH, '..', '..', '.planners', 'enhsp-20', 'enhsp.jar'),
                '-o', domanin_filename, '-f', problem_filename, '-sp', plan_filename]



class TestQuantifiersRemover(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()
        env = get_env()
        if os.path.isfile(os.path.join(FILE_PATH, '..', '..', '.planners', 'enhsp-20', 'enhsp.jar')):
            env.factory.add_solver('enhsp', 'upf.test.test_pddl_planner', 'ENHSP')

    @skipIfSolverNotAvailable('enhsp')
    def test_basic_exists(self):
        problem = self.problems['basic_exists'].problem
        qr = QuantifiersRemover(problem)
        uq_problem = qr.get_rewritten_problem()
        uq_problem_2 = qr.get_rewritten_problem()
        self.assertEqual(uq_problem, uq_problem_2)
        self.assertIn("Exists", str(problem))
        self.assertNotIn("Exists", str(uq_problem))

        with OneshotPlanner(name='enhsp') as planner:
            self.assertNotEqual(planner, None)
            plan = planner.solve(problem)
            uq_plan = planner.solve(uq_problem)
            self.assertEqual(str(plan), str(uq_plan))
            new_plan = qr.rewrite_back_plan(uq_plan)
            self.assertEqual(str(plan), str(new_plan))

    @skipIfSolverNotAvailable('enhsp')
    def test_basic_forall(self):
        problem = self.problems['basic_forall'].problem
        qr = QuantifiersRemover(problem)
        uq_problem = qr.get_rewritten_problem()
        self.assertIn("Forall", str(problem))
        self.assertNotIn("Forall", str(uq_problem))

        with OneshotPlanner(name='enhsp') as planner:
            self.assertNotEqual(planner, None)
            plan = planner.solve(problem)
            uq_plan = planner.solve(uq_problem)
            self.assertEqual(str(plan), str(uq_plan))
            new_plan = qr.rewrite_back_plan(uq_plan)
            self.assertEqual(str(plan), str(new_plan))

    @skipIfSolverNotAvailable('enhsp')
    def test_robot_locations_connected(self):
        problem = self.problems['robot_locations_connected'].problem
        qr = QuantifiersRemover(problem)
        uq_problem = qr.get_rewritten_problem()
        self.assertIn("Exists", str(problem))
        self.assertNotIn("Exists", str(uq_problem))

        with OneshotPlanner(name='enhsp') as planner:
            self.assertNotEqual(planner, None)
            plan = planner.solve(problem)
            uq_plan = planner.solve(uq_problem)
            self.assertEqual(str(plan), str(uq_plan))
            new_plan = qr.rewrite_back_plan(uq_plan)
            self.assertEqual(str(plan), str(new_plan))

    @skipIfSolverNotAvailable('enhsp')
    def test_robot_locations_visited(self):
        problem = self.problems['robot_locations_visited'].problem
        qr = QuantifiersRemover(problem)
        uq_problem = qr.get_rewritten_problem()
        self.assertIn("Exists", str(problem))
        self.assertNotIn("Exists", str(uq_problem))
        self.assertIn("Forall", str(problem))
        self.assertNotIn("Forall", str(uq_problem))

        with OneshotPlanner(name='enhsp') as planner:
            self.assertNotEqual(planner, None)
            plan = planner.solve(problem)
            uq_plan = planner.solve(uq_problem)
            self.assertEqual(str(plan), str(uq_plan))
            new_plan = qr.rewrite_back_plan(uq_plan)
            self.assertEqual(str(plan), str(new_plan))

    @skipIfSolverNotAvailable('tamer')
    def test_timed_connected_locations(self):
        problem = self.problems['timed_connected_locations'].problem
        plan = self.problems['timed_connected_locations'].plan
        qr = QuantifiersRemover(problem)
        uq_problem = qr.get_rewritten_problem()
        self.assertTrue(problem.has_quantifiers())
        self.assertFalse(uq_problem.has_quantifiers())

        with OneshotPlanner(name='tamer') as planner:
            self.assertNotEqual(planner, None)
            uq_plan = planner.solve(uq_problem)
            self.assertEqual(str(plan), str(uq_plan))
            new_plan = qr.rewrite_back_plan(uq_plan)
            self.assertEqual(str(plan), str(new_plan))
