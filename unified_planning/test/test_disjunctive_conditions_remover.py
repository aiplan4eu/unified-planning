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


import unified_planning
from unified_planning.shortcuts import *
from unified_planning.model.problem_kind import (
    classical_kind,
    full_numeric_kind,
    full_classical_kind,
)
from unified_planning.test import (
    TestCase,
    skipIfNoPlanValidatorForProblemKind,
    skipIfNoOneshotPlannerForProblemKind,
    skipIfEngineNotAvailable,
)
from unified_planning.test.examples import get_example_problems
from unified_planning.engines import CompilationKind
from unified_planning.engines.compilers import DisjunctiveConditionsRemover


class TestDisjunctiveConditionsRemover(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfNoOneshotPlannerForProblemKind(classical_kind.union(full_numeric_kind))
    @skipIfNoPlanValidatorForProblemKind(full_classical_kind.union(full_numeric_kind))
    def test_robot_locations_visited(self):
        problem = self.problems["robot_locations_visited"].problem

        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING,
        ) as dnfr:
            res = dnfr.compile(problem, CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING)
            dnf_problem = res.problem

            res_2 = dnfr.compile(
                problem, CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING
            )
            dnf_problem_2 = res_2.problem

            self.assertEqual(dnf_problem, dnf_problem_2)

        self.assertEqual(len(problem.actions), 2)
        self.assertEqual(len(dnf_problem.actions), 3)

        with OneshotPlanner(problem_kind=dnf_problem.kind) as planner:
            self.assertNotEqual(planner, None)
            dnf_plan = planner.solve(dnf_problem).plan
            plan = dnf_plan.replace_action_instances(res.map_back_action_instance)
            for ai in plan.actions:
                a = ai.action
                self.assertEqual(a, problem.action(a.name))
            with PlanValidator(problem_kind=problem.kind, plan_kind=plan.kind) as pv:
                self.assertTrue(pv.validate(problem, plan))

    def test_ad_hoc_1(self):
        # mockup problem
        a = Fluent("a")
        b = Fluent("b")
        c = Fluent("c")
        d = Fluent("d")
        act = InstantaneousAction("act")
        # (a <-> (b -> c)) -> (a & d)
        # In Dnf:
        # (!a & !b) | (!a & c) | (a & b & !c) | (a & d)
        cond = Implies(Iff(a, Implies(b, c)), And(a, d))
        possible_conditions = [
            {Not(a), Not(b)},
            {Not(a), FluentExp(c)},
            {FluentExp(b), Not(c), FluentExp(a)},
            {FluentExp(a), FluentExp(d)},
        ]
        act.add_precondition(cond)
        act.add_effect(a, TRUE())
        problem = Problem("mockup")
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
        dnfr = DisjunctiveConditionsRemover()
        res = dnfr.compile(problem, CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING)
        dnf_problem = res.problem

        self.assertEqual(len(dnf_problem.actions), 4)
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
        # mockup problem
        a = Fluent("a")
        act = InstantaneousAction("act")
        cond = And(a, a)
        act.add_precondition(cond)
        act.add_effect(a, TRUE())
        problem = Problem("mockup")
        problem.add_fluent(a)
        problem.add_action(act)
        problem.set_initial_value(a, True)
        problem.add_goal(a)
        dnfr = DisjunctiveConditionsRemover()
        res = dnfr.compile(problem, CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING)
        dnf_problem = res.problem

        self.assertEqual(len(dnf_problem.actions), 1)

    @skipIfEngineNotAvailable("pyperplan")
    def test_ad_hoc_3(self):
        # mockup problem
        a = Fluent("a")
        b = Fluent("b")
        c = Fluent("c")
        act_a = InstantaneousAction("act_a")
        act_a.add_effect(a, TRUE())
        act_b = InstantaneousAction("act_b")
        act_b.add_effect(b, TRUE())
        act_c = InstantaneousAction("act_c")
        act_c.add_effect(c, TRUE())
        problem = Problem("mockup")
        problem.add_fluent(a)
        problem.add_fluent(b)
        problem.add_fluent(c)
        problem.add_action(act_a)
        problem.add_action(act_b)
        problem.add_action(act_c)
        problem.set_initial_value(a, False)
        problem.set_initial_value(b, False)
        problem.set_initial_value(c, False)
        problem.add_goal(And(a, Or(b, c)))
        dnfr = DisjunctiveConditionsRemover()
        res = dnfr.compile(problem, CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING)
        dnf_problem = res.problem

        self.assertEqual(len(dnf_problem.actions), 5)
        self.assertEqual(len(dnf_problem.goals), 1)
        self.assertTrue(dnf_problem.goals[0].is_fluent_exp())

        with OneshotPlanner(name="pyperplan") as planner:
            os_res = planner.solve(dnf_problem)
            with PlanValidator(name="sequential_plan_validator") as validator:
                valid_res = validator.validate(
                    problem,
                    os_res.plan.replace_action_instances(res.map_back_action_instance),
                )
                self.assertEqual(
                    valid_res.status, up.engines.results.ValidationResultStatus.VALID
                )

    def test_temporal_mockup_1(self):
        # temporal mockup
        a = Fluent("a")
        b = Fluent("b")
        c = Fluent("c")
        d = Fluent("d")
        act = DurativeAction("act")
        # !a => (b | ((c <-> d) & d))
        # In Dnf:
        # a | b | (c & d)
        exp = Implies(Not(a), Or(b, And(Iff(c, d), d)))
        act.add_condition(StartTiming(), exp)
        act.add_condition(StartTiming(1), exp)
        act.add_condition(ClosedTimeInterval(StartTiming(2), StartTiming(3)), exp)
        act.add_condition(ClosedTimeInterval(StartTiming(4), StartTiming(5)), exp)
        act.add_effect(StartTiming(6), a, TRUE())

        problem = Problem("temporal_mockup")
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
        dnfr = DisjunctiveConditionsRemover()
        res = dnfr.compile(problem, CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING)
        dnf_problem = res.problem
        self.assertEqual(len(dnf_problem.actions), 81)

    def test_temporal_mockup_2(self):
        # temporal mockup
        a = Fluent("a")
        b = Fluent("b")
        act = DurativeAction("act")
        exp = And(Not(a), b)
        act.add_condition(StartTiming(), exp)
        act.add_condition(StartTiming(1), exp)
        act.add_condition(ClosedTimeInterval(StartTiming(2), StartTiming(3)), exp)
        act.add_condition(ClosedTimeInterval(StartTiming(4), StartTiming(5)), exp)
        act.add_effect(StartTiming(6), a, TRUE())

        problem = Problem("temporal_mockup")
        problem.add_fluent(a)
        problem.add_fluent(b)
        problem.add_action(act)
        problem.set_initial_value(a, False)
        problem.set_initial_value(b, False)
        problem.add_goal(a)
        dnfr = DisjunctiveConditionsRemover()
        res = dnfr.compile(problem, CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING)
        dnf_problem = res.problem
        self.assertEqual(len(dnf_problem.actions), 1)

    @skipIfEngineNotAvailable("tamer")
    def test_temporal_mockup_3(self):
        # mockup problem
        a = Fluent("a")
        b = Fluent("b")
        c = Fluent("c")
        act_a = InstantaneousAction("act_a")
        act_a.add_effect(a, TRUE())
        act_b = InstantaneousAction("act_b")
        act_b.add_effect(b, True)
        act_c = InstantaneousAction("act_c")
        act_c.add_effect(c, TRUE())
        n_act_a = InstantaneousAction("n_act_a")
        n_act_a.add_effect(a, FALSE())
        n_act_b = InstantaneousAction("n_act_b")
        n_act_b.add_effect(b, False)
        n_act_c = InstantaneousAction("n_act_c")
        n_act_c.add_effect(c, FALSE())
        problem = Problem("mockup")
        problem.add_fluent(a)
        problem.add_fluent(b)
        problem.add_fluent(c)
        problem.add_action(act_a)
        problem.add_action(act_b)
        problem.add_action(act_c)
        problem.add_action(n_act_a)
        problem.add_action(n_act_b)
        problem.add_action(n_act_c)
        problem.set_initial_value(a, True)
        problem.set_initial_value(b, True)
        problem.set_initial_value(c, True)
        problem.add_timed_goal(StartTiming(5), Not(And(a, Or(b, c))))
        problem.add_goal(And(a, Or(b, c)))
        dnfr = DisjunctiveConditionsRemover()
        res = dnfr.compile(problem, CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING)
        dnf_problem = res.problem

        self.assertEqual(len(dnf_problem.actions), 10)
        self.assertEqual(len(dnf_problem.goals), 1)
        self.assertEqual(len(dnf_problem.timed_goals), 1)
        self.assertTrue(dnf_problem.goals[0].is_fluent_exp())
        for gl in dnf_problem.timed_goals.values():
            self.assertEqual(len(gl), 1)
            self.assertTrue(gl[0].is_fluent_exp())

        with OneshotPlanner(name="tamer") as planner:
            os_res = planner.solve(dnf_problem)
            with PlanValidator(name="tamer") as validator:
                valid_res = validator.validate(
                    problem,
                    os_res.plan.replace_action_instances(res.map_back_action_instance),
                )
                self.assertEqual(
                    valid_res.status, up.engines.results.ValidationResultStatus.VALID
                )
