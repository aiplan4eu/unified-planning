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
import unified_planning
from unified_planning.shortcuts import *
from unified_planning.model.problem_kind import classical_kind, full_numeric_kind, full_classical_kind
from unified_planning.test import TestCase, skipIfNoPlanValidatorForProblemKind, skipIfNoOneshotPlannerForProblemKind
from unified_planning.test.examples import get_example_problems
from unified_planning.transformers import DisjunctiveConditionsRemover
from unified_planning.exceptions import UPProblemDefinitionError


class TestDisjunctiveConditionsRemover(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(full_numeric_kind))
    @skipIfNoPlanValidatorForProblemKind(full_classical_kind.union(full_numeric_kind))
    def test_robot_locations_visited(self):
        problem = self.problems['robot_locations_visited'].problem

        dnfr = DisjunctiveConditionsRemover(problem)
        dnf_problem = dnfr.get_rewritten_problem()
        dnf_problem_2 = dnfr.get_rewritten_problem()
        self.assertEqual(dnf_problem, dnf_problem_2)

        is_connected = problem.fluent("is_connected")
        move = problem.action("move")
        robot, l_from, l_to = move.parameters
        self.assertEqual(len(problem.actions), 2)
        self.assertEqual(len(dnf_problem.actions), 3)

        cond = Or(is_connected(l_from, l_to), is_connected(l_to, l_from))
        self.assertIn(cond, move.preconditions)
        new_moves = dnfr.get_transformed_actions(move)
        for m in new_moves:
            self.assertNotIn(cond, m.preconditions)

        self.assertTrue(is_connected(l_from, l_to) in new_moves[0].preconditions or
                        is_connected(l_from, l_to) in new_moves[1].preconditions)
        if is_connected(l_from, l_to) in new_moves[0].preconditions:
            self.assertIn(is_connected(l_to, l_from), new_moves[1].preconditions)
            self.assertNotIn(is_connected(l_to, l_from), new_moves[0].preconditions)
            self.assertNotIn(is_connected(l_from, l_to), new_moves[1].preconditions)
        elif is_connected(l_from, l_to) in new_moves[1].preconditions:
            self.assertIn(is_connected(l_to, l_from), new_moves[0].preconditions)
            self.assertNotIn(is_connected(l_from, l_to), new_moves[0].preconditions)
            self.assertNotIn(is_connected(l_to, l_from), new_moves[1].preconditions)

        with OneshotPlanner(problem_kind=dnf_problem.kind) as planner:
            self.assertNotEqual(planner, None)
            dnf_plan = planner.solve(dnf_problem).plan
            plan = dnfr.rewrite_back_plan(dnf_plan)
            for ai in plan.actions:
                a = ai.action
                self.assertEqual(a, problem.action(a.name))
            with PlanValidator(problem_kind=problem.kind) as pv:
                self.assertTrue(pv.validate(problem, plan))

    def test_ad_hoc_1(self):
        #mockup problem
        a = Fluent('a')
        b = Fluent('b')
        c = Fluent('c')
        d = Fluent('d')
        act = InstantaneousAction('act')
        # (a <-> (b -> c)) -> (a & d)
        # In Dnf:
        # (!a & !b) | (!a & c) | (a & b & !c) | (a & d)
        cond = Implies(Iff(a, Implies(b, c)), And(a, d))
        possible_conditions = [{Not(a), Not(b)}, {Not(a), FluentExp(c)},
            {FluentExp(b), Not(c), FluentExp(a)}, {FluentExp(a), FluentExp(d)}]
        act.add_precondition(cond)
        act.add_effect(a, TRUE())
        problem = Problem('mockup')
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
        new_act = dnfr.get_transformed_actions(act)

        self.assertEqual(len(dnf_problem.actions), 4)
        self.assertEqual(len(new_act), 4)
        self.assertEqual(set(dnf_problem.actions), set(new_act))
        # Cycle over all actions. For every new action assume that the precondition is equivalent
        # to one in the possible_preconditions and that no other action has the same precondition.
        for i, new_action in enumerate(dnf_problem.actions):
            self.assertEqual(new_action.effects, act.effects)
            preconditions = set(new_action.preconditions)
            self.assertIn(preconditions, possible_conditions)
            for j, new_action_oth_acts in enumerate(dnf_problem.actions):
                preconditions_oth_acts = set(new_action_oth_acts.preconditions)
                if i != j:
                    self.assertNotEqual(preconditions, preconditions_oth_acts)

    def test_ad_hoc_2(self):
        #mockup problem
        a = Fluent('a')
        act = InstantaneousAction('act')
        cond = And(a, a)
        act.add_precondition(cond)
        act.add_effect(a, TRUE())
        problem = Problem('mockup')
        problem.add_fluent(a)
        problem.add_action(act)
        problem.set_initial_value(a, True)
        problem.add_goal(a)
        dnfr = DisjunctiveConditionsRemover(problem)
        dnf_problem = dnfr.get_rewritten_problem()
        new_act = dnfr.get_transformed_actions(act)

        self.assertEqual(len(dnf_problem.actions), 1)
        self.assertEqual(len(new_act), 1)
        self.assertEqual(set(dnf_problem.actions), set(new_act))
        new_action = new_act[0]
        self.assertEqual(new_action.effects, act.effects)
        preconditions = set(new_action.preconditions)
        self.assertEqual(preconditions, set((FluentExp(a), )))

    def test_temproal_mockup_1(self):
        # temporal mockup
        a = Fluent('a')
        b = Fluent('b')
        c = Fluent('c')
        d = Fluent('d')
        act = DurativeAction('act')
        # !a => (b | ((c <-> d) & d))
        # In Dnf:
        # a | b | (c & d)
        exp = Implies(Not(a), Or(b, And(Iff(c, d),d)))
        act.add_condition(StartTiming(), exp)
        act.add_condition(StartTiming(1), exp)
        act.add_condition(ClosedTimeInterval(StartTiming(2), StartTiming(3)), exp)
        act.add_condition(ClosedTimeInterval(StartTiming(4), StartTiming(5)), exp)
        act.add_effect(StartTiming(6), a, TRUE())

        problem = Problem('temporal_mockup')
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
        new_act = dnfr.get_transformed_actions(act)
        self.assertEqual(len(dnf_problem.actions), 81)
        self.assertEqual(len(new_act), 81)
        self.assertEqual(set(dnf_problem.actions), set(new_act))

    def test_temproal_mockup_2(self):
        # temporal mockup
        a = Fluent('a')
        b = Fluent('b')
        act = DurativeAction('act')
        exp = And(Not(a), b)
        act.add_condition(StartTiming(), exp)
        act.add_condition(StartTiming(1), exp)
        act.add_condition(ClosedTimeInterval(StartTiming(2), StartTiming(3)), exp)
        act.add_condition(ClosedTimeInterval(StartTiming(4), StartTiming(5)), exp)
        act.add_effect(StartTiming(6), a, TRUE())

        problem = Problem('temporal_mockup')
        problem.add_fluent(a)
        problem.add_fluent(b)
        problem.add_action(act)
        problem.set_initial_value(a, False)
        problem.set_initial_value(b, False)
        problem.add_goal(a)
        dnfr = DisjunctiveConditionsRemover(problem)
        dnf_problem = dnfr.get_rewritten_problem()
        new_act = dnfr.get_transformed_actions(act)
        self.assertEqual(len(dnf_problem.actions), 1)
        self.assertEqual(len(new_act), 1)
        self.assertEqual(set(dnf_problem.actions), set(new_act))
