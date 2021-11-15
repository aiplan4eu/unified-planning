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


from fractions import Fraction
import os
from upf.plan import ActionInstance
import upf
from upf.environment import get_env
from upf.shortcuts import *
from upf.test import TestCase, main, skipIfNoPlanValidatorForProblemKind, skipIfNoOneshotPlannerForProblemKind
from upf.test.examples import get_example_problems
from upf.model import AbsoluteTiming, ClosedInterval, Effect
from upf.model.problem_kind import basic_classical_kind, classical_kind, basic_temporal_kind
from upf.transformers import NegativeConditionsRemover
from upf.solvers import SequentialPlanValidator as PV
from upf.exceptions import UPFExpressionDefinitionError, UPFProblemDefinitionError


class TestNegativeConditionsRemover(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.env = get_env()
        self.problems = get_example_problems()

    @skipIfNoOneshotPlannerForProblemKind(basic_classical_kind)
    @skipIfNoPlanValidatorForProblemKind(classical_kind)
    def test_basic(self):
        problem = self.problems['basic'].problem
        plan = self.problems['basic'].plan
        npr = NegativeConditionsRemover(problem)
        positive_problem = npr.get_rewritten_problem()
        self.assertEqual(len(problem.fluents()) + 1, len(positive_problem.fluents()))
        self.assertTrue(problem.kind().has_negative_conditions())
        self.assertFalse(positive_problem.kind().has_negative_conditions())
        with OneshotPlanner(problem_kind=positive_problem.kind()) as planner:
            self.assertNotEqual(planner, None)
            positive_plan = planner.solve(positive_problem)
            new_plan = npr.rewrite_back_plan(positive_plan)
            with PlanValidator(problem_kind=problem.kind()) as PV:
                self.assertTrue(PV.validate(problem, new_plan))

    @skipIfNoOneshotPlannerForProblemKind(basic_classical_kind)
    @skipIfNoPlanValidatorForProblemKind(classical_kind)
    def test_robot_loader_mod(self):
        problem = self.problems['robot_loader_mod'].problem
        plan = self.problems['robot_loader_mod'].plan
        npr = NegativeConditionsRemover(problem)
        positive_problem = npr.get_rewritten_problem()
        positive_problem_2 = npr.get_rewritten_problem()
        self.assertEqual(positive_problem, positive_problem_2)
        self.assertEqual(len(problem.fluents()) + 4, len(positive_problem.fluents()))
        self.assertTrue(problem.kind().has_negative_conditions())
        self.assertFalse(positive_problem.kind().has_negative_conditions())
        with OneshotPlanner(problem_kind=positive_problem.kind()) as planner:
            self.assertNotEqual(planner, None)
            positive_plan = planner.solve(positive_problem)
            new_plan = npr.rewrite_back_plan(positive_plan)
            with PlanValidator(problem_kind=problem.kind()) as PV:
                self.assertTrue(PV.validate(problem, new_plan))

    @skipIfNoOneshotPlannerForProblemKind(basic_classical_kind.union(basic_temporal_kind))
    @skipIfNoPlanValidatorForProblemKind(classical_kind.union(basic_temporal_kind))
    def test_matchcellar(self):
        problem = self.problems['matchcellar'].problem
        plan = self.problems['matchcellar'].plan
        npr = NegativeConditionsRemover(problem)
        positive_problem = npr.get_rewritten_problem()
        self.assertTrue(problem.kind().has_negative_conditions())
        self.assertFalse(positive_problem.kind().has_negative_conditions())
        self.assertTrue(problem.kind().has_negative_conditions())
        self.assertFalse(positive_problem.kind().has_negative_conditions())
        with OneshotPlanner(problem_kind=positive_problem.kind()) as planner:
            self.assertNotEqual(planner, None)
            positive_plan = planner.solve(positive_problem)
            new_plan = npr.rewrite_back_plan(positive_plan)
            with PlanValidator(problem_kind=problem.kind()) as PV:
                self.assertTrue(PV.validate(problem, new_plan))
        self.assertEqual(len(problem.fluents()) + 1, len(positive_problem.fluents()))
        light_match = problem.action('light_match')
        mend_fuse = problem.action('mend_fuse')
        m1 = problem.object('m1')
        m2 = problem.object('m2')
        m3 = problem.object('m3')
        f1 = problem.object('f1')
        f2 = problem.object('f2')
        f3 = problem.object('f3')
        light_m1 = ActionInstance(light_match, (ObjectExp(m1), ))
        light_m2 = ActionInstance(light_match, (ObjectExp(m2), ))
        light_m3 = ActionInstance(light_match, (ObjectExp(m3), ))
        mend_f1 = ActionInstance(mend_fuse, (ObjectExp(f1), ))
        mend_f2 = ActionInstance(mend_fuse, (ObjectExp(f2), ))
        mend_f3 = ActionInstance(mend_fuse, (ObjectExp(f3), ))
        npa = [a for s, a, d in new_plan.actions()]
        self.assertIn(light_m1, npa)
        self.assertIn(light_m2, npa)
        self.assertIn(light_m3, npa)
        self.assertIn(mend_f1, npa)
        self.assertIn(mend_f2, npa)
        self.assertIn(mend_f3, npa)


    def test_ad_hoc(self):
        x = Fluent('x')
        y = Fluent('y')
        a = InstantaneousAction('a')
        a.add_precondition(And(Not(x), Not(y)))
        a.add_effect(x, True)
        problem = Problem('ad_hoc')
        problem.add_fluent(x)
        problem.add_fluent(y)
        problem.add_action(a)
        problem.set_initial_value(x, False)
        problem.set_initial_value(y, False)
        problem.add_goal(x)
        problem.add_goal(Not(y))
        problem.add_goal(Not(Iff(x, y)))
        problem.add_timed_goal(AbsoluteTiming(5), x)
        problem.add_maintain_goal(ClosedInterval(AbsoluteTiming(3), AbsoluteTiming(4)), x)
        npr = NegativeConditionsRemover(problem)
        with self.assertRaises(UPFExpressionDefinitionError) as e:
            positive_problem = npr.get_rewritten_problem()
        self.assertIn(f"Expression: {Not(Iff(x, y))} is not in NNF.", str(e.exception))
