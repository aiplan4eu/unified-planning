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

    def test_compile_is_explicitly_not_implemented_yet(self):
        problem, possible_initial_states = self._build_problem_and_possible_states()
        compiler = Ks0Compiler(possible_initial_states=possible_initial_states)
        with self.assertRaises(NotImplementedError):
            compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

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
            with self.assertRaises(NotImplementedError):
                compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

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
                    plan = planner.solve(compiled_problem)
                self.assertIsNotNone(plan)
                self.assertEqual(
                    plan.status, PlanGenerationResultStatus.SOLVED_SATISFICING
                )

                # the expected plan moves left until it is certain that it is in l4,
                # then moves right once to be certain that it is in l3, and then ends.
                self.assertEqual(len(plan.actions), num_possible_initial_states + 1)
                for i in range(num_possible_initial_states - 1):
                    self.assertEqual(plan.actions[i].action.name, "move_left")

                self.assertEqual(
                    plan.actions[num_possible_initial_states - 1].action.name,
                    "move_right",
                )
                self.assertEqual(
                    plan.actions[num_possible_initial_states].action.name, "end"
                )
