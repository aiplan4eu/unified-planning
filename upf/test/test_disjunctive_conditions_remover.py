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
from upf.action import DurativeAction
from upf.environment import get_env
from upf.shortcuts import *
from upf.test import TestCase, main, skipIfSolverNotAvailable
from upf.test.examples import get_example_problems
from upf.transformers import DisjunctiveConditionsRemover
from upf.pddl_solver import PDDLSolver
from upf.plan_validator import SequentialPlanValidator as PV
from upf.exceptions import UPFProblemDefinitionError
from upf.timing import ClosedInterval
from upf.timing import StartTiming


class TestDisjunctiveConditionsRemover(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfSolverNotAvailable('enhsp')
    def test_charge_discharge(self):
        problem = self.problems['charge_discharge'].problem
        plan = self.problems['charge_discharge'].plan
        dnfr = DisjunctiveConditionsRemover(problem)
        dnf_problem = dnfr.get_rewritten_problem()

        with OneshotPlanner(problem_kind=dnf_problem.kind()) as planner:
            self.assertNotEqual(planner, None)
            dnf_plan = planner.solve(dnf_problem)
            self.assertNotEqual(str(plan), str(dnf_plan))
            new_plan = dnfr.rewrite_back_plan(dnf_plan)
            self.assertEqual(str(plan), str(new_plan))
            #self.assertEqual(plan, new_plan)# -> shouldn't they be Equal?

    def test_robot_locations_visited(self):
        problem = self.problems['robot_locations_visited'].problem
        dnfr = DisjunctiveConditionsRemover(problem)
        dnf_problem = dnfr.get_rewritten_problem()
        dnf_problem_2 = dnfr.get_rewritten_problem()
        is_connected = problem.fluent("is_connected")
        robot, l_from, l_to = problem.action("move").parameters()
        self.assertEqual(len(problem.actions()), 2)
        self.assertEqual(len(dnf_problem.actions()), 3)
        self.assertIn(Or(is_connected(l_from, l_to), is_connected(l_to, l_from)), problem.action("move").preconditions())
        self.assertNotIn(Or(is_connected(l_from, l_to), is_connected(l_to, l_from)), dnf_problem.action("move__0__").preconditions())
        self.assertNotIn(Or(is_connected(l_from, l_to), is_connected(l_to, l_from)), dnf_problem.action("move__1__").preconditions())
        self.assertIn(is_connected(l_from, l_to), dnf_problem.action("move__0__").preconditions())
        self.assertIn(is_connected(l_to, l_from), dnf_problem.action("move__1__").preconditions())
        self.assertEqual(dnf_problem, dnf_problem_2)

    def test_ad_hoc(self):

        #mockup problem
        a = upf.Fluent('a')
        b = upf.Fluent('b')
        c = upf.Fluent('c')
        d = upf.Fluent('d')
        act = upf.InstantaneousAction('act')
        # (a <-> (b -> c)) -> (a & d)
        # In Dnf:
        # (!a & !b) | (!a & c) | (a & b & !c) | (a & d)
        act.add_precondition(Implies(Iff(a, Implies(b, c)), And(a, d)))
        act.add_effect(a, TRUE())
        problem = upf.Problem('mockup')
        problem.add_fluent(a)
        problem.add_fluent(b)
        problem.add_fluent(c)
        problem.add_fluent(d)
        problem.add_action(act)
        problem.set_initial_value(a, True)
        problem.set_initial_value(b, False)
        problem.set_initial_value(c, True)
        problem.set_initial_value(d, False)
        problem.add_goal(a)
        dnfr = DisjunctiveConditionsRemover(problem)
        dnf_problem = dnfr.get_rewritten_problem()

        self.assertEqual(len(dnf_problem.actions()), 4)
        self.assertEqual([Not(a), Not(b)], dnf_problem.action("act__0__").preconditions())
        self.assertEqual([Not(a), FluentExp(c)], dnf_problem.action("act__1__").preconditions())
        self.assertEqual([FluentExp(b), Not(c), FluentExp(a)], dnf_problem.action("act__2__").preconditions())
        self.assertEqual([FluentExp(a), FluentExp(d)], dnf_problem.action("act__3__").preconditions())
        self.assertEqual(problem.action("act").effects(), dnf_problem.action("act__0__").effects())
        self.assertEqual(problem.action("act").effects(), dnf_problem.action("act__1__").effects())
        self.assertEqual(problem.action("act").effects(), dnf_problem.action("act__2__").effects())
        self.assertEqual(problem.action("act").effects(), dnf_problem.action("act__3__").effects())

    def test_raise_exceptions(self):

        #mockup problem
        a = upf.Fluent('a')
        b = upf.Fluent('b')
        c = upf.Fluent('c')
        d = upf.Fluent('d')
        act = upf.InstantaneousAction('act')
        # (a <-> (b -> c)) -> (a & d)
        # In Dnf:
        # (!a & !b) | (!a & c) | (a & b & !c) | (a & d)
        act.add_precondition(Implies(Iff(a, Implies(b, c)), And(a, d)))
        act.add_effect(a, TRUE())
        act_2 = upf.InstantaneousAction('act__1__')
        act_2.add_precondition(Implies(Iff(a, Implies(b, c)), And(a, d)))
        act_2.add_effect(a, TRUE())
        problem = upf.Problem('mockup')
        problem.add_fluent(a)
        problem.add_fluent(b)
        problem.add_fluent(c)
        problem.add_fluent(d)
        problem.add_action(act)
        problem.add_action(act_2)
        problem.set_initial_value(a, True)
        problem.set_initial_value(b, False)
        problem.set_initial_value(c, True)
        problem.set_initial_value(d, False)
        problem.add_goal(a)
        dnfr = DisjunctiveConditionsRemover(problem)
        with self.assertRaises(UPFProblemDefinitionError) as e:
            dnf_problem = dnfr.get_rewritten_problem()
        self.assertIn("InstantaneousAction: act__1__ of problem: mockup has invalid name. Double underscore '__' is reserved by the naming convention.",
        str(e.exception))

    def test_temproal_mockup(self):

        # temporal mockup
        a = upf.Fluent('a')
        b = upf.Fluent('b')
        c = upf.Fluent('c')
        d = upf.Fluent('d')
        act = upf.DurativeAction('act')
        # !a => (b | ((c <-> d) & d))
        # In Dnf:
        # a | b | (c & d)
        exp = Implies(Not(a), Or(b, And(Iff(c, d),d)))
        act.add_condition(StartTiming(), exp)
        act.add_condition(StartTiming(1), exp)
        act.add_durative_condition(ClosedInterval(StartTiming(2), StartTiming(3)), exp)
        act.add_durative_condition(ClosedInterval(StartTiming(4), StartTiming(5)), exp)
        act.add_effect(StartTiming(6), a, TRUE())

        problem = upf.Problem('temporal_mockup')
        problem.add_fluent(a)
        problem.add_fluent(b)
        problem.add_fluent(c)
        problem.add_fluent(d)
        problem.add_action(act)
        problem.set_initial_value(a, False)
        problem.set_initial_value(b, False)
        problem.set_initial_value(c, True)
        problem.set_initial_value(d, False)
        problem.add_goal(a)
        dnfr = DisjunctiveConditionsRemover(problem)
        dnf_problem = dnfr.get_rewritten_problem()
        self.assertEqual(len(dnf_problem.actions()), 81)
        self.assertEqual(len(problem.actions()), 1)
