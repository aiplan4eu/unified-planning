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

from typing import Dict, Optional

from unified_planning.shortcuts import *
from unified_planning.model.problem_kind import (
    basic_classical_kind,
    oversubscription_kind,
    actions_cost_kind,
    simple_numeric_kind,
)
from unified_planning.test import unittest_TestCase, main
from unified_planning.test import skipIfNoOneshotPlannerForProblemKind
from unified_planning.test.examples import get_example_problems
from unified_planning.engines import CompilationKind
from unified_planning.engines.compilers import (
    NegativeConditionsRemover,
    ConditionalEffectsRemover,
    QuantifiersRemover,
    DisjunctiveConditionsRemover,
)
from unified_planning.engines.compilers.utils import updated_minimize_action_costs


class TestCompilersPipeline(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfNoOneshotPlannerForProblemKind(
        basic_classical_kind.union(oversubscription_kind)
    )
    def test_locations_connected_visited_oversubscription(self):
        example = self.problems["locations_connected_visited_oversubscription"]
        problem, test_plan = example.problem, example.valid_plans[0]
        with Compiler(
            problem_kind=problem.kind,
            compilation_kinds=[
                CompilationKind.GROUNDING,
                CompilationKind.QUANTIFIERS_REMOVING,
                CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING,
                CompilationKind.NEGATIVE_CONDITIONS_REMOVING,
            ],
        ) as compiler:
            res = compiler.compile(problem)
        new_problem = res.problem

        with OneshotPlanner(problem_kind=new_problem.kind) as planner:
            self.assertNotEqual(planner, None)

            solve_res = planner.solve(new_problem)
            plan = solve_res.plan
            new_plan = plan.replace_action_instances(res.map_back_action_instance)
            self.assertEqual(new_plan, test_plan)

    @skipIfNoOneshotPlannerForProblemKind(simple_numeric_kind.union(actions_cost_kind))
    def test_locations_connected_cost_minimize(self):
        example = self.problems["locations_connected_cost_minimize"]
        problem, test_plan = example.problem, example.valid_plans[0]
        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.GROUNDING,
        ) as compiler:
            res = compiler.compile(problem)
        new_problem = res.problem

        with OneshotPlanner(
            problem_kind=problem.kind,
            optimality_guarantee=OptimalityGuarantee.SOLVED_OPTIMALLY,
        ) as planner:
            self.assertNotEqual(planner, None)
            plan = planner.solve(new_problem).plan
            new_plan = plan.replace_action_instances(res.map_back_action_instance)
            self.assertEqual(new_plan, test_plan)


class TestUpdatedMinimizeActionCosts(unittest_TestCase):
    def _build_problem(self):
        a = Fluent("a")
        goal_f = Fluent("goal_f")
        act = InstantaneousAction("act")
        act.add_precondition(Not(a))
        act.add_effect(goal_f, True)
        problem = Problem("test")
        problem.add_fluent(a, default_initial_value=True)
        problem.add_fluent(goal_f, default_initial_value=False)
        problem.add_action(act)
        problem.add_goal(goal_f)
        problem.add_quality_metric(MinimizeActionCosts({act: 5}, default=99))
        return problem

    def test_default_is_preserved_across_compilers(self):
        compilers_and_kinds = [
            (NegativeConditionsRemover, CompilationKind.NEGATIVE_CONDITIONS_REMOVING),
            (ConditionalEffectsRemover, CompilationKind.CONDITIONAL_EFFECTS_REMOVING),
            (QuantifiersRemover, CompilationKind.QUANTIFIERS_REMOVING),
            (
                DisjunctiveConditionsRemover,
                CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING,
            ),
        ]
        for compiler_class, compilation_kind in compilers_and_kinds:
            with self.subTest(compiler=compiler_class.__name__):
                problem = self._build_problem()
                compiler = compiler_class()
                comp_res = compiler.compile(problem, compilation_kind)
                new_problem = comp_res.problem
                assert isinstance(new_problem, Problem)

                self.assertEqual(len(new_problem.quality_metrics), 1)
                new_metric = new_problem.quality_metrics[0]
                assert isinstance(new_metric, MinimizeActionCosts)
                self.assertEqual(new_metric.default, Int(99))
                new_action = new_problem.action("act")
                self.assertEqual(new_metric.get_action_cost(new_action), Int(5))

    def test_helper_preserves_default_and_zeroes_new_actions(self):
        old_act = InstantaneousAction("old")
        new_act = InstantaneousAction("new")
        fake_act = InstantaneousAction("fake")
        metric = MinimizeActionCosts({old_act: 5}, default=99)
        new_to_old: Dict[Action, Optional[Action]] = {
            new_act: old_act,
            fake_act: None,
        }
        updated = updated_minimize_action_costs(metric, new_to_old, get_environment())
        assert isinstance(updated, MinimizeActionCosts)
        self.assertEqual(updated.default, Int(99))
        self.assertEqual(updated.get_action_cost(new_act), Int(5))
        # Actions with no original counterpart (e.g. DisjunctiveConditionsRemover's
        # fake bookkeeping actions) must keep cost 0, not inherit the default: every
        # valid compiled plan applies exactly one of them, so a non-zero cost would
        # change the compiled problem's optimum relative to the original.
        self.assertEqual(updated.get_action_cost(fake_act), Int(0))
