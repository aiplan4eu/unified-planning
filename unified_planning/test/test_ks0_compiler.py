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

from unified_planning.engines import CompilationKind
from unified_planning.engines.compilers import Ks0Compiler
from unified_planning.engines.results import CompilerResult, PlanGenerationResultStatus
from unified_planning.environment import Environment
from unified_planning.exceptions import UPUsageError
from unified_planning.model import UPState
from unified_planning.model.problem_kind import classical_kind
from unified_planning.plans import SequentialPlan
from unified_planning.shortcuts import *
from unified_planning.test import (
    unittest_TestCase,
    skipIfNoOneshotPlannerForProblemKind,
)


class TestKs0Compiler(unittest_TestCase):
    def _build_problem_and_possible_states(self, environment=None):
        problem = Problem("ks0_input", environment=environment)
        reachable = Fluent("reachable", environment=problem.environment)
        blocked = Fluent("blocked", environment=problem.environment)
        em = problem.environment.expression_manager
        reachable_exp = em.FluentExp(reachable)
        blocked_exp = em.FluentExp(blocked)

        unblock = InstantaneousAction("unblock", _env=problem.environment)
        unblock.add_precondition(em.Not(blocked_exp))
        unblock.add_effect(reachable, True)

        problem.add_fluent(reachable)
        problem.add_fluent(blocked)
        problem.add_action(unblock)
        problem.add_goal(reachable_exp)

        possible_initial_states = (
            UPState({reachable_exp: em.FALSE(), blocked_exp: em.FALSE()}, problem),
            UPState({reachable_exp: em.FALSE(), blocked_exp: em.TRUE()}, problem),
        )
        return problem, possible_initial_states

    def _build_nav_problem_and_possible_states(self):
        problem = Problem("nav")

        loc_type = UserType("location")

        at = Fluent("at", BoolType(), l=loc_type)
        adj_left = Fluent("adj_left", BoolType(), l1=loc_type, l2=loc_type)
        is_goal = Fluent("is_goal", BoolType(), l=loc_type)
        done = Fluent("done", BoolType())
        problem.add_fluent(at, default_initial_value=False)
        problem.add_fluent(adj_left, default_initial_value=False)
        problem.add_fluent(is_goal, default_initial_value=False)
        problem.add_fluent(done, default_initial_value=False)

        move_left = InstantaneousAction("move_left", l_from=loc_type, l_to=loc_type)
        move_left.add_precondition(adj_left(move_left.l_from, move_left.l_to))
        move_left.add_effect(
            at(move_left.l_from), False, condition=at(move_left.l_from)
        )
        move_left.add_effect(at(move_left.l_to), True, condition=at(move_left.l_from))
        problem.add_action(move_left)

        move_right = InstantaneousAction("move_right", l_from=loc_type, l_to=loc_type)
        move_right.add_precondition(adj_left(move_right.l_to, move_right.l_from))
        move_right.add_effect(
            at(move_right.l_from), False, condition=at(move_right.l_from)
        )
        move_right.add_effect(
            at(move_right.l_to), True, condition=at(move_right.l_from)
        )
        problem.add_action(move_right)

        end = InstantaneousAction("end", l=loc_type)
        end.add_precondition(at(end.l))
        end.add_precondition(is_goal(end.l))
        end.add_effect(done, True)
        problem.add_action(end)

        l1 = Object("l1", loc_type)
        l2 = Object("l2", loc_type)
        l3 = Object("l3", loc_type)
        l4 = Object("l4", loc_type)
        problem.add_objects([l1, l2, l3, l4])

        problem.set_initial_value(at(l1), True)
        problem.set_initial_value(adj_left(l1, l2), True)
        problem.set_initial_value(adj_left(l2, l3), True)
        problem.set_initial_value(adj_left(l3, l4), True)

        problem.set_initial_value(is_goal(l3), True)
        problem.add_goal(done())

        em = problem.environment.expression_manager

        # The possible initial states include all possible locations for the agent
        # with an identical goal and connectivity structure.
        possible_initial_states = (
            UPState(
                {
                    at(l1): em.TRUE(),
                    is_goal(l3): em.TRUE(),
                    adj_left(l1, l2): em.TRUE(),
                    adj_left(l2, l3): em.TRUE(),
                    adj_left(l3, l4): em.TRUE(),
                },
                problem,
            ),
            UPState(
                {
                    at(l2): em.TRUE(),
                    is_goal(l3): em.TRUE(),
                    adj_left(l1, l2): em.TRUE(),
                    adj_left(l2, l3): em.TRUE(),
                    adj_left(l3, l4): em.TRUE(),
                },
                problem,
            ),
            UPState(
                {
                    at(l3): em.TRUE(),
                    is_goal(l3): em.TRUE(),
                    adj_left(l1, l2): em.TRUE(),
                    adj_left(l2, l3): em.TRUE(),
                    adj_left(l3, l4): em.TRUE(),
                },
                problem,
            ),
            UPState(
                {
                    at(l4): em.TRUE(),
                    is_goal(l3): em.TRUE(),
                    adj_left(l1, l2): em.TRUE(),
                    adj_left(l2, l3): em.TRUE(),
                    adj_left(l3, l4): em.TRUE(),
                },
                problem,
            ),
        )

        return problem, possible_initial_states

    def _build_conditional_effect_problem_and_possible_states(self):
        problem = Problem("cond_eff")
        f1 = Fluent("f1")
        f2 = Fluent("f2")
        problem.add_fluent(f1, default_initial_value=False)
        problem.add_fluent(f2, default_initial_value=False)

        em = problem.environment.expression_manager
        a = InstantaneousAction("a")
        a.add_effect(f2, True, condition=em.FluentExp(f1))
        problem.add_action(a)
        problem.add_goal(em.FluentExp(f2))

        s0 = UPState(
            {em.FluentExp(f1): em.TRUE(), em.FluentExp(f2): em.FALSE()},
            problem,
        )
        return problem, (s0,)

    def test_supported_compilation(self):
        compiler = Ks0Compiler()
        self.assertTrue(
            compiler.supports_compilation(CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        )

    def test_compile_requires_possible_initial_states(self):
        problem, _ = self._build_problem_and_possible_states()
        compiler = Ks0Compiler()
        with self.assertRaises(UPUsageError):
            compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

    def test_compile_rejects_invalid_possible_initial_states(self):
        problem, _ = self._build_problem_and_possible_states()
        compiler = Ks0Compiler(possible_initial_states=[object()])  # type: ignore[list-item]
        with self.assertRaises(UPUsageError) as error:
            compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        self.assertEqual(
            str(error.exception),
            "Every element of `possible_initial_states` must be a "
            "`unified_planning.model.State`; found <class 'object'> at index 0.",
        )

    def test_compile_rejects_states_from_different_problem(self):
        problem1, possible_initial_states1 = self._build_problem_and_possible_states()
        _, possible_initial_states2 = self._build_nav_problem_and_possible_states()

        possible_initial_states1 += possible_initial_states2

        compiler = Ks0Compiler(possible_initial_states=possible_initial_states1)
        with self.assertRaises(UPUsageError) as error:
            compiler.compile(problem1, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        self.assertEqual(
            str(error.exception),
            "Every element of `possible_initial_states` must be defined "
            "for the same problem passed to `compile`; found a state from a "
            "different problem at index 2.",
        )

    def test_compile_rejects_states_from_different_environments(self):
        problem1, _ = self._build_problem_and_possible_states()
        _, possible_initial_states2 = self._build_problem_and_possible_states(
            Environment()
        )

        compiler = Ks0Compiler(possible_initial_states=possible_initial_states2)
        with self.assertRaises(UPUsageError) as error:
            compiler.compile(problem1, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        self.assertEqual(
            str(error.exception),
            "Every element of `possible_initial_states` must be defined "
            "in the same environment as the problem passed to `compile`; "
            "found a state from a different environment at index 0.",
        )

    def test_factory_instantiation_with_params(self):
        problem, possible_initial_states = self._build_problem_and_possible_states()
        with Compiler(
            name="up_ks0_compiler",
            params={"possible_initial_states": possible_initial_states},
        ) as compiler:
            self.assertTrue(
                compiler.supports_compilation(
                    CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
                )
            )

    def test_factory_instantiation_from_problem_kind(self):
        problem, _ = self._build_problem_and_possible_states()
        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.CONFORMANT_TO_CLASSICAL_KS0,
        ) as compiler:
            self.assertTrue(compiler.supports(problem.kind))
            with self.assertRaises(UPUsageError):
                compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

    def test_full_compilation_pipeline(self):
        problem, possible_initial_states = self._build_problem_and_possible_states()
        with Compiler(
            name="up_ks0_compiler",
            params={"possible_initial_states": possible_initial_states},
        ) as compiler:
            res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

        self.assertIsInstance(res, CompilerResult)
        self.assertIsNotNone(res.problem)
        self.assertTrue(res.problem.name.startswith("ks0_"))
        self.assertIsNotNone(res.plan_back_conversion)
        self.assertGreater(len(res.problem.fluents), 0)
        self.assertGreater(len(res.problem.actions), 0)
        self.assertGreater(len(res.problem.goals), 0)

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    def test_full_compilation_with_plan(self):
        for num_possible_initial_states in [1, 2, 3, 4]:
            with self.subTest(num_possible_initial_states=num_possible_initial_states):
                problem, possible_initial_states = (
                    self._build_nav_problem_and_possible_states()
                )
                possible_initial_states = possible_initial_states[
                    -num_possible_initial_states:
                ]
                with Compiler(
                    name="up_ks0_compiler",
                    params={"possible_initial_states": possible_initial_states},
                ) as compiler:
                    res = compiler.compile(
                        problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
                    )
                    compiled_problem = res.problem

                with OneshotPlanner(problem_kind=compiled_problem.kind) as planner:
                    plan_result = planner.solve(compiled_problem)

                self.assertIsNotNone(plan_result.plan)
                self.assertEqual(
                    plan_result.status, PlanGenerationResultStatus.SOLVED_SATISFICING
                )

                # Back-convert to original domain plan (drops merge actions)
                back_plan = res.plan_back_conversion(plan_result.plan)
                self.assertIsInstance(back_plan, SequentialPlan)
                self.assertGreater(len(back_plan.actions), 0)

                # Back-converted plan must contain no merge actions
                for ai in back_plan.actions:
                    self.assertFalse(
                        ai.action.name.startswith("merge_"),
                        f"Back-converted plan contains merge action: {ai.action.name}",
                    )

    # ------------------------------------------------------------------
    # Step 5: Validation edge case
    # ------------------------------------------------------------------

    def test_compile_rejects_empty_possible_initial_states(self):
        problem, _ = self._build_problem_and_possible_states()
        compiler = Ks0Compiler(possible_initial_states=())
        with self.assertRaises(UPUsageError):
            compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

    # ------------------------------------------------------------------
    # Step 6: Structural tests (all use _build_problem_and_possible_states)
    # ------------------------------------------------------------------

    def _compile_basic(self):
        problem, possible_initial_states = self._build_problem_and_possible_states()
        compiler = Ks0Compiler(possible_initial_states=possible_initial_states)
        res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        return problem, res

    def test_compiled_problem_name(self):
        _, res = self._compile_basic()
        self.assertEqual(res.problem.name, "ks0_ks0_input")

    def test_compiled_fluent_count(self):
        # 2 atoms × 2 literals × 3 tags (1 empty + 2 states) = 12
        _, res = self._compile_basic()
        self.assertEqual(len(res.problem.fluents), 12)

    def test_compiled_fluent_names(self):
        _, res = self._compile_basic()
        fluent_names = {f.name for f in res.problem.fluents}
        expected = {
            "K_reachable_empty", "K_not_reachable_empty",
            "K_reachable_s0", "K_not_reachable_s0",
            "K_reachable_s1", "K_not_reachable_s1",
            "K_blocked_empty", "K_not_blocked_empty",
            "K_blocked_s0", "K_not_blocked_s0",
            "K_blocked_s1", "K_not_blocked_s1",
        }
        self.assertEqual(fluent_names, expected)
        self.assertNotIn("reachable", fluent_names)
        self.assertNotIn("blocked", fluent_names)

    def test_compiled_initial_state_empty_tag_universal_literal(self):
        _, res = self._compile_basic()
        em = res.problem.environment.expression_manager
        K_not_reachable_empty = res.problem.fluent("K_not_reachable_empty")
        self.assertEqual(
            res.problem.initial_value(em.FluentExp(K_not_reachable_empty)),
            em.TRUE(),
        )

    def test_compiled_initial_state_empty_tag_non_universal_literal(self):
        _, res = self._compile_basic()
        em = res.problem.environment.expression_manager

        K_blocked_empty = res.problem.fluent("K_blocked_empty")
        val = res.problem.initial_value(em.FluentExp(K_blocked_empty))
        self.assertIn(val, (em.FALSE(), None))

        K_not_blocked_empty = res.problem.fluent("K_not_blocked_empty")
        val2 = res.problem.initial_value(em.FluentExp(K_not_blocked_empty))
        self.assertIn(val2, (em.FALSE(), None))

    def test_compiled_initial_state_per_tag(self):
        _, res = self._compile_basic()
        em = res.problem.environment.expression_manager

        K_not_blocked_s0 = res.problem.fluent("K_not_blocked_s0")
        self.assertEqual(
            res.problem.initial_value(em.FluentExp(K_not_blocked_s0)), em.TRUE()
        )

        K_blocked_s1 = res.problem.fluent("K_blocked_s1")
        self.assertEqual(
            res.problem.initial_value(em.FluentExp(K_blocked_s1)), em.TRUE()
        )

        K_not_blocked_s1 = res.problem.fluent("K_not_blocked_s1")
        val = res.problem.initial_value(em.FluentExp(K_not_blocked_s1))
        self.assertIn(val, (em.FALSE(), None))

    def test_compiled_goal_uses_empty_tag(self):
        problem, res = self._compile_basic()
        goal_fluents = {g.fluent() for g in res.problem.goals if g.is_fluent_exp()}
        K_reachable_empty = res.problem.fluent("K_reachable_empty")
        self.assertIn(K_reachable_empty, goal_fluents)
        reachable = problem.fluent("reachable")
        self.assertNotIn(reachable, goal_fluents)

    def test_compiled_action_count(self):
        # 1 original action (unblock) + 2 merge actions = 3
        _, res = self._compile_basic()
        self.assertEqual(len(res.problem.actions), 3)

    def test_compiled_action_preconditions_use_empty_tag(self):
        problem, res = self._compile_basic()
        compiled_unblock = res.problem.action("unblock")
        precondition_fluents = {
            p.fluent() for p in compiled_unblock.preconditions if p.is_fluent_exp()
        }
        K_not_blocked_empty = res.problem.fluent("K_not_blocked_empty")
        self.assertIn(K_not_blocked_empty, precondition_fluents)
        blocked = problem.fluent("blocked")
        self.assertNotIn(blocked, precondition_fluents)

    def test_compiled_unconditional_effect_generates_per_tag_effects(self):
        _, res = self._compile_basic()
        compiled_unblock = res.problem.action("unblock")
        # Unconditional add(reachable) → support + cancellation per tag × 3 tags = 6
        self.assertEqual(len(compiled_unblock.effects), 6)
        effect_fluent_names = {e.fluent.fluent().name for e in compiled_unblock.effects}
        self.assertIn("K_reachable_empty", effect_fluent_names)
        self.assertIn("K_reachable_s0", effect_fluent_names)
        self.assertIn("K_reachable_s1", effect_fluent_names)
        self.assertIn("K_not_reachable_empty", effect_fluent_names)
        self.assertIn("K_not_reachable_s0", effect_fluent_names)
        self.assertIn("K_not_reachable_s1", effect_fluent_names)

    def test_compiled_conditional_effect_generates_per_tag_conditions(self):
        problem, states = self._build_conditional_effect_problem_and_possible_states()
        compiler = Ks0Compiler(possible_initial_states=states)
        res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        compiled_action = res.problem.action("a")
        conditional_effects = [
            e for e in compiled_action.effects if not e.condition.is_true()
        ]
        self.assertGreater(len(conditional_effects), 0)
        condition_fluent_names = {
            e.condition.fluent().name
            for e in conditional_effects
            if e.condition.is_fluent_exp()
        }
        self.assertTrue(any("f1" in name for name in condition_fluent_names))

    def test_merge_actions_created_for_precondition_and_goal_literals(self):
        _, res = self._compile_basic()
        merge_actions = [a for a in res.problem.actions if a.name.startswith("merge_")]
        self.assertEqual(len(merge_actions), 2)
        merge_names = {a.name for a in merge_actions}
        self.assertTrue(any("not_blocked" in n for n in merge_names))
        self.assertTrue(any("reachable" in n and "not" not in n for n in merge_names))

    def test_merge_action_preconditions_require_all_state_tags(self):
        _, res = self._compile_basic()
        merge_not_blocked = next(
            a for a in res.problem.actions
            if a.name.startswith("merge_") and "not_blocked" in a.name
        )
        prec_fluent_names = {
            p.fluent().name for p in merge_not_blocked.preconditions if p.is_fluent_exp()
        }
        self.assertIn("K_not_blocked_s0", prec_fluent_names)
        self.assertIn("K_not_blocked_s1", prec_fluent_names)
        self.assertNotIn("K_not_blocked_empty", prec_fluent_names)

    def test_merge_action_effect_sets_empty_tag_fluent(self):
        _, res = self._compile_basic()
        em = res.problem.environment.expression_manager
        merge_not_blocked = next(
            a for a in res.problem.actions
            if a.name.startswith("merge_") and "not_blocked" in a.name
        )
        effect_fluent_names = {e.fluent.fluent().name for e in merge_not_blocked.effects}
        self.assertIn("K_not_blocked_empty", effect_fluent_names)
        for e in merge_not_blocked.effects:
            self.assertEqual(e.value, em.TRUE())

    def test_resulting_problem_kind_has_conditional_effects(self):
        problem, _ = self._build_problem_and_possible_states()
        resulting_kind = Ks0Compiler.resulting_problem_kind(
            problem.kind, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
        )
        self.assertTrue(resulting_kind.has_conditional_effects())

    def test_resulting_problem_kind_removes_undefined_initial_symbolic(self):
        problem, _ = self._build_problem_and_possible_states()
        resulting_kind = Ks0Compiler.resulting_problem_kind(
            problem.kind, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
        )
        self.assertFalse(resulting_kind.has_undefined_initial_symbolic())

    def test_compiled_problem_kind_removes_undefined_initial_symbolic(self):
        _, res = self._compile_basic()
        self.assertFalse(res.problem.kind.has_undefined_initial_symbolic())

    # ------------------------------------------------------------------
    # Step 7: Edge case tests
    # ------------------------------------------------------------------

    def test_duplicate_states_are_deduplicated(self):
        problem, possible_initial_states = self._build_problem_and_possible_states()
        s0 = possible_initial_states[0]

        compiler_single = Ks0Compiler(possible_initial_states=(s0,))
        compiler_dup = Ks0Compiler(possible_initial_states=(s0, s0))

        res_single = compiler_single.compile(
            problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
        )
        res_dup = compiler_dup.compile(
            problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
        )

        self.assertEqual(len(res_single.problem.fluents), len(res_dup.problem.fluents))

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    def test_single_state_compiled_problem_is_solvable(self):
        problem, possible_initial_states = self._build_problem_and_possible_states()
        # s0: blocked=False, reachable=False — unblock IS applicable from s0
        s0_only = possible_initial_states[:1]
        compiler = Ks0Compiler(possible_initial_states=s0_only)
        res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

        with OneshotPlanner(problem_kind=res.problem.kind) as planner:
            plan_result = planner.solve(res.problem)
        self.assertIsNotNone(plan_result.plan)
        self.assertEqual(
            plan_result.status, PlanGenerationResultStatus.SOLVED_SATISFICING
        )

    # ------------------------------------------------------------------
    # Step 8: Back-conversion test
    # ------------------------------------------------------------------

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    def test_plan_back_conversion_drops_merge_actions(self):
        problem, possible_initial_states = self._build_problem_and_possible_states()
        s0_only = possible_initial_states[:1]  # solvable with 1 state
        compiler = Ks0Compiler(possible_initial_states=s0_only)
        res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

        with OneshotPlanner(problem_kind=res.problem.kind) as planner:
            plan_result = planner.solve(res.problem)
        self.assertIsNotNone(plan_result.plan)

        back_plan = res.plan_back_conversion(plan_result.plan)
        self.assertIsInstance(back_plan, SequentialPlan)
        for ai in back_plan.actions:
            self.assertFalse(
                ai.action.name.startswith("merge_"),
                f"Back-converted plan still contains merge action: {ai.action.name}",
            )
