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


from fractions import Fraction
import os
from unified_planning.plans import ActionInstance
import unified_planning
from unified_planning.environment import get_environment
from unified_planning.shortcuts import *
from unified_planning.test import (
    unittest_TestCase,
    main,
    skipIfNoPlanValidatorForProblemKind,
    skipIfNoOneshotPlannerForProblemKind,
)
from unified_planning.test.examples import get_example_problems
from unified_planning.model.problem_kind import (
    basic_classical_kind,
    classical_kind,
    basic_temporal_kind,
    full_classical_kind,
)
from unified_planning.engines.compilers import NegativeConditionsRemover
from unified_planning.engines import SequentialPlanValidator as PV, CompilationKind
from unified_planning.exceptions import (
    UPExpressionDefinitionError,
    UPProblemDefinitionError,
)
import pytest


class TestNegativeConditionsRemover(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.environment = get_environment()
        self.problems = get_example_problems()

    @skipIfNoOneshotPlannerForProblemKind(basic_classical_kind)
    @skipIfNoPlanValidatorForProblemKind(classical_kind)
    def test_basic(self):
        problem = self.problems["basic"].problem
        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.NEGATIVE_CONDITIONS_REMOVING,
        ) as npr:
            res = npr.compile(problem, CompilationKind.NEGATIVE_CONDITIONS_REMOVING)
        positive_problem = res.problem
        assert isinstance(positive_problem, Problem)
        self.assertEqual(len(problem.fluents) + 1, len(positive_problem.fluents))
        self.assertTrue(problem.kind.has_negative_conditions())
        self.assertFalse(positive_problem.kind.has_negative_conditions())
        with OneshotPlanner(problem_kind=positive_problem.kind) as planner:
            self.assertNotEqual(planner, None)
            positive_plan = planner.solve(positive_problem).plan
            new_plan = positive_plan.replace_action_instances(
                res.map_back_action_instance
            )
            with PlanValidator(
                problem_kind=problem.kind, plan_kind=new_plan.kind
            ) as PV:
                self.assertTrue(PV.validate(problem, new_plan))

    @skipIfNoOneshotPlannerForProblemKind(basic_classical_kind)
    @skipIfNoPlanValidatorForProblemKind(classical_kind)
    def test_robot_loader_mod(self):
        problem = self.problems["robot_loader_mod"].problem
        npr = NegativeConditionsRemover()
        res = npr.compile(problem, CompilationKind.NEGATIVE_CONDITIONS_REMOVING)
        positive_problem = res.problem
        assert isinstance(positive_problem, Problem)
        res_2 = npr.compile(problem, CompilationKind.NEGATIVE_CONDITIONS_REMOVING)
        positive_problem_2 = res_2.problem
        self.assertEqual(positive_problem, positive_problem_2)
        self.assertEqual(len(problem.fluents) + 4, len(positive_problem.fluents))
        self.assertTrue(problem.kind.has_negative_conditions())
        self.assertFalse(positive_problem.kind.has_negative_conditions())
        with OneshotPlanner(problem_kind=positive_problem.kind) as planner:
            self.assertNotEqual(planner, None)
            positive_plan = planner.solve(positive_problem).plan
            new_plan = positive_plan.replace_action_instances(
                res.map_back_action_instance
            )
            with PlanValidator(
                problem_kind=problem.kind, plan_kind=new_plan.kind
            ) as PV:
                self.assertTrue(PV.validate(problem, new_plan))

    @skipIfNoOneshotPlannerForProblemKind(
        basic_classical_kind.union(basic_temporal_kind)
    )
    @skipIfNoPlanValidatorForProblemKind(classical_kind.union(basic_temporal_kind))
    def test_matchcellar(self):
        problem = self.problems["matchcellar"].problem
        npr = NegativeConditionsRemover()
        res = npr.compile(problem, CompilationKind.NEGATIVE_CONDITIONS_REMOVING)
        positive_problem = res.problem
        assert isinstance(positive_problem, Problem)
        self.assertTrue(problem.kind.has_negative_conditions())
        self.assertFalse(positive_problem.kind.has_negative_conditions())
        self.assertTrue(problem.kind.has_negative_conditions())
        self.assertFalse(positive_problem.kind.has_negative_conditions())
        with OneshotPlanner(problem_kind=positive_problem.kind) as planner:
            self.assertNotEqual(planner, None)
            positive_plan = planner.solve(positive_problem).plan
            new_plan = positive_plan.replace_action_instances(
                res.map_back_action_instance
            )
            with PlanValidator(
                problem_kind=problem.kind, plan_kind=new_plan.kind
            ) as PV:
                self.assertTrue(PV.validate(problem, new_plan))
        self.assertEqual(len(problem.fluents) + 1, len(positive_problem.fluents))
        light_match = problem.action("light_match")
        mend_fuse = problem.action("mend_fuse")
        m1 = problem.object("m1")
        m2 = problem.object("m2")
        m3 = problem.object("m3")
        f1 = problem.object("f1")
        f2 = problem.object("f2")
        f3 = problem.object("f3")
        light_m1 = ActionInstance(light_match, (ObjectExp(m1),))
        light_m2 = ActionInstance(light_match, (ObjectExp(m2),))
        light_m3 = ActionInstance(light_match, (ObjectExp(m3),))
        mend_f1 = ActionInstance(mend_fuse, (ObjectExp(f1),))
        mend_f2 = ActionInstance(mend_fuse, (ObjectExp(f2),))
        mend_f3 = ActionInstance(mend_fuse, (ObjectExp(f3),))
        expected_ai = [light_m1, light_m2, light_m3, mend_f1, mend_f2, mend_f3]
        self.assertEqual(len(new_plan.timed_actions), len(expected_ai))
        for ai in expected_ai:
            self.assertIn(ai, new_plan)

    @skipIfNoOneshotPlannerForProblemKind(full_classical_kind)
    @skipIfNoPlanValidatorForProblemKind(full_classical_kind)
    def test_basic_conditional(self):
        problem = self.problems["basic_conditional"].problem
        npr = NegativeConditionsRemover()
        res = npr.compile(problem, CompilationKind.NEGATIVE_CONDITIONS_REMOVING)
        positive_problem = res.problem
        assert isinstance(positive_problem, Problem)
        self.assertEqual(len(problem.fluents) + 2, len(positive_problem.fluents))
        self.assertTrue(problem.kind.has_negative_conditions())
        self.assertFalse(positive_problem.kind.has_negative_conditions())
        with OneshotPlanner(problem_kind=positive_problem.kind) as planner:
            self.assertNotEqual(planner, None)
            positive_plan = planner.solve(positive_problem).plan
            new_plan = positive_plan.replace_action_instances(
                res.map_back_action_instance
            )
            with PlanValidator(
                problem_kind=problem.kind, plan_kind=new_plan.kind
            ) as PV:
                self.assertTrue(PV.validate(problem, new_plan))

    def test_temporal_conditional(self):
        problem = self.problems["temporal_conditional"].problem
        npr = NegativeConditionsRemover()
        res = npr.compile(problem, CompilationKind.NEGATIVE_CONDITIONS_REMOVING)
        positive_problem = res.problem
        assert isinstance(positive_problem, Problem)
        self.assertEqual(len(problem.fluents) + 3, len(positive_problem.fluents))
        self.assertTrue(problem.kind.has_negative_conditions())
        self.assertFalse(positive_problem.kind.has_negative_conditions())

    def test_ad_hoc_1(self):
        x = Fluent("x")
        y = Fluent("y")
        a = InstantaneousAction("a")
        a.add_precondition(And(Not(x), Not(y)))
        a.add_effect(x, True)
        problem = Problem("ad_hoc")
        problem.add_fluent(x)
        problem.add_fluent(y)
        problem.add_action(a)
        problem.set_initial_value(x, False)
        problem.set_initial_value(y, False)
        problem.add_goal(x)
        problem.add_goal(Not(y))
        problem.add_goal(Not(Iff(x, y)))
        problem.add_timed_goal(GlobalStartTiming(5), x)
        problem.add_timed_goal(
            ClosedTimeInterval(GlobalStartTiming(3), GlobalStartTiming(4)), x
        )
        npr = NegativeConditionsRemover()
        res = npr.compile(problem, CompilationKind.NEGATIVE_CONDITIONS_REMOVING)
        assert isinstance(res.problem, Problem)
        self.assertFalse(res.problem.kind.has_negative_conditions())

    def test_ad_hoc_2(self):
        x = Fluent("x")
        y = Fluent("y")
        t = GlobalStartTiming(5)
        problem = Problem("ad_hoc")
        problem.add_fluent(x)
        problem.add_fluent(y)
        problem.add_timed_effect(t, y, x, Not(y))
        problem.set_initial_value(x, True)
        problem.set_initial_value(y, False)
        problem.add_goal(x)
        npr = NegativeConditionsRemover()
        res = npr.compile(problem, CompilationKind.NEGATIVE_CONDITIONS_REMOVING)
        positive_problem = res.problem
        assert isinstance(positive_problem, Problem)
        assert isinstance(positive_problem, Problem)
        self.assertEqual(len(problem.fluents) + 1, len(positive_problem.fluents))
        y__negated__ = Fluent("not_y")
        test_problem = Problem(positive_problem.name)
        test_problem.add_fluent(x)
        test_problem.add_fluent(y)
        test_problem.add_fluent(y__negated__)
        test_problem.add_timed_effect(t, y, x, y__negated__)
        test_problem.add_timed_effect(t, y__negated__, Not(x), y__negated__)
        test_problem.set_initial_value(x, True)
        test_problem.set_initial_value(y, False)
        test_problem.set_initial_value(y__negated__, True)
        test_problem.add_goal(x)
        self.assertEqual(positive_problem, test_problem)

    def test_objects(self):
        problem = Problem("wompwomp")
        ut = UserType("ut")
        u1 = Object("u1", ut)
        u2 = Object("u2", ut)
        u3 = Object("u3", ut)
        problem.add_objects([u1, u2, u3])
        ux = Fluent("lx", ut)
        uy = Fluent("ly", ut)
        b = Fluent("b", BoolType())
        problem.add_fluent(b)
        problem.add_fluent(ux)
        problem.add_fluent(uy)
        problem.set_initial_value(ux, u1)
        problem.set_initial_value(uy, u2)
        problem.set_initial_value(b, False)
        test_action = InstantaneousAction("test_action")
        test_action.add_precondition(Not(Equals(ux, uy)))
        test_action.add_effect(b, True)
        problem.add_action(test_action)
        problem.add_goal(Iff(b, True))
        compiled_action = test_action.clone()
        compiled_action.clear_preconditions()
        c1 = And(Equals(ux, u1), Equals(uy, u2))
        c2 = And(Equals(ux, u1), Equals(uy, u3))
        c3 = And(Equals(ux, u2), Equals(uy, u1))
        c4 = And(Equals(ux, u2), Equals(uy, u3))
        c5 = And(Equals(ux, u3), Equals(uy, u1))
        c6 = And(Equals(ux, u3), Equals(uy, u2))
        compiled_action.add_precondition(Or(c1, c2, c3, c4, c5, c6))
        ncr = NegativeConditionsRemover()
        comp_res = ncr.compile(problem, CompilationKind.NEGATIVE_CONDITIONS_REMOVING)
        assert isinstance(comp_res.problem, Problem)
        self.assertEqual(compiled_action, comp_res.problem.action("test_action"))

    def test_booleans(self):
        problem = Problem("wompwomp")
        bx = Fluent("bx", BoolType())
        by = Fluent("by", BoolType())
        bz = Fluent("bz", BoolType())
        b = Fluent("b", BoolType())
        problem.add_fluent(b)
        problem.add_fluent(bx)
        problem.add_fluent(by)
        problem.add_fluent(bz)
        problem.set_initial_value(bx, False)
        problem.set_initial_value(by, True)
        problem.set_initial_value(bz, True)
        problem.set_initial_value(b, False)
        and_action = InstantaneousAction("and_action")
        and_action.add_precondition(Not(And(bx, by, bz)))
        and_action.add_effect(b, True)
        iff_action = InstantaneousAction("iff_action")
        iff_action.add_precondition(Not(Iff(bx, by)))
        iff_action.add_effect(b, True)
        or_action = InstantaneousAction("or_action")
        or_action.add_precondition(Not(Or(bx, by, bz)))
        or_action.add_effect(b, True)
        not_chain_action = InstantaneousAction("not_chain_action")
        not_chain_action.add_precondition(Not(Not(Not(Not(Not(Not(bx)))))))
        not_chain_action.add_effect(b, True)
        problem.add_action(not_chain_action)
        problem.add_action(or_action)
        problem.add_action(iff_action)
        problem.add_action(and_action)
        problem.add_goal(Iff(b, True))
        bx__negated__ = Fluent("not_bx", BoolType())
        by__negated__ = Fluent("not_by", BoolType())
        bz__negated__ = Fluent("not_bz", BoolType())
        compiled_and_action = and_action.clone()
        compiled_and_action.clear_preconditions()
        compiled_and_action.add_precondition(
            Or(bx__negated__, by__negated__, bz__negated__)
        )
        compiled_or_action = or_action.clone()
        compiled_or_action.clear_preconditions()
        compiled_or_action.add_precondition(
            And(bx__negated__, by__negated__, bz__negated__)
        )
        compiled_iff_action = iff_action.clone()
        compiled_iff_action.clear_preconditions()
        compiled_iff_action.add_precondition(Iff(bx, by__negated__))
        compiled_not_chain_action = not_chain_action.clone()
        compiled_not_chain_action.clear_preconditions()
        compiled_not_chain_action.add_precondition(bx)
        ncr = NegativeConditionsRemover()
        comp_res = ncr.compile(problem, CompilationKind.NEGATIVE_CONDITIONS_REMOVING)
        assert isinstance(comp_res.problem, Problem)
        self.assertEqual(compiled_and_action, comp_res.problem.action("and_action"))
        self.assertEqual(compiled_or_action, comp_res.problem.action("or_action"))
        self.assertEqual(
            compiled_not_chain_action, comp_res.problem.action("not_chain_action")
        )
        self.assertEqual(compiled_iff_action, comp_res.problem.action("iff_action"))

    def test_numbers(self):
        problem = Problem("wompwomp")
        x = Fluent("x", IntType())
        y = Fluent("y", IntType())
        b = Fluent("b", BoolType())
        problem.add_fluent(b)
        problem.add_fluent(x)
        problem.add_fluent(y)
        problem.set_initial_value(x, 3)
        problem.set_initial_value(y, 5)
        problem.set_initial_value(b, False)
        equals_action = InstantaneousAction("equals_action")
        equals_action.add_precondition(Not(Equals(x, y)))
        equals_action.add_effect(b, True)
        gt_action = InstantaneousAction("gt_action")
        gt_action.add_precondition(Not(GT(x, y)))
        gt_action.add_effect(b, True)
        ge_action = InstantaneousAction("ge_action")
        ge_action.add_precondition(Not(GE(x, y)))
        ge_action.add_effect(b, True)
        lt_action = InstantaneousAction("lt_action")
        lt_action.add_precondition(Not(LT(x, y)))
        lt_action.add_effect(b, True)
        le_action = InstantaneousAction("le_action")
        le_action.add_precondition(Not(LE(x, y)))
        le_action.add_effect(b, True)
        problem.add_action(le_action)
        problem.add_action(lt_action)
        problem.add_action(ge_action)
        problem.add_action(gt_action)
        problem.add_action(equals_action)
        problem.add_goal(Iff(b, True))
        compiled_equals_action = equals_action.clone()
        compiled_equals_action.clear_preconditions()
        compiled_equals_action.add_precondition(Or(GT(x, y), LT(x, y)))
        compiled_gt_action = gt_action.clone()
        compiled_gt_action.clear_preconditions()
        compiled_gt_action.add_precondition(LE(x, y))
        compiled_ge_action = ge_action.clone()
        compiled_ge_action.clear_preconditions()
        compiled_ge_action.add_precondition(LT(x, y))
        compiled_lt_action = lt_action.clone()
        compiled_lt_action.clear_preconditions()
        compiled_lt_action.add_precondition(GE(x, y))
        compiled_le_action = le_action.clone()
        compiled_le_action.clear_preconditions()
        compiled_le_action.add_precondition(GT(x, y))
        ncr = NegativeConditionsRemover()
        comp_res = ncr.compile(problem, CompilationKind.NEGATIVE_CONDITIONS_REMOVING)
        assert isinstance(comp_res.problem, Problem)
        self.assertEqual(
            compiled_equals_action, comp_res.problem.action("equals_action")
        )
        self.assertEqual(compiled_gt_action, comp_res.problem.action("gt_action"))
        self.assertEqual(compiled_ge_action, comp_res.problem.action("ge_action"))
        self.assertEqual(compiled_lt_action, comp_res.problem.action("lt_action"))
        self.assertEqual(compiled_le_action, comp_res.problem.action("le_action"))

    def test_mixed(self):
        problem = Problem("wompwomp")
        x = Fluent("x", IntType())
        y = Fluent("y", IntType())
        bx = Fluent("bx", BoolType())
        by = Fluent("by", BoolType())
        b = Fluent("b", BoolType())
        problem.add_fluent(b)
        problem.add_fluent(x)
        problem.add_fluent(y)
        problem.add_fluent(bx)
        problem.add_fluent(by)
        problem.set_initial_value(x, 1)
        problem.set_initial_value(y, 2)
        problem.set_initial_value(bx, True)
        problem.set_initial_value(by, False)
        problem.set_initial_value(b, False)
        test_action = InstantaneousAction("test_action")
        test_action.add_precondition(Not(Or(bx, And(Equals(x, y), Not(by)))))
        test_action.add_effect(b, True)
        problem.add_action(test_action)
        problem.add_goal(Iff(b, True))
        bx__negated__ = Fluent("not_bx", BoolType())
        compiled_action = test_action.clone()
        compiled_action.clear_preconditions()
        compiled_action.add_precondition(
            And(bx__negated__, Or((Or(GT(x, y), LT(x, y))), by))
        )
        ncr = NegativeConditionsRemover()
        comp_res = ncr.compile(problem, CompilationKind.NEGATIVE_CONDITIONS_REMOVING)
        assert isinstance(comp_res.problem, Problem)
        self.assertEqual(compiled_action, comp_res.problem.action("test_action"))
