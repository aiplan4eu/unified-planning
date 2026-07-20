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

import warnings

from unified_planning.engines import CompilationKind
from unified_planning.engines.compilers import Ks0Compiler
from unified_planning.engines.results import CompilerResult, PlanGenerationResultStatus
from unified_planning.environment import Environment
from unified_planning.exceptions import UPUsageError
from unified_planning.model import UPState
from unified_planning.model.contingent import ContingentProblem, SensingAction
from unified_planning.model.problem_kind import classical_kind
from unified_planning.plans import ActionInstance, SequentialPlan
from unified_planning.shortcuts import *
from unified_planning.test import (
    unittest_TestCase,
    skipIfNoOneshotPlannerForProblemKind,
)
from unified_planning.engines.sequential_simulator import UPSequentialSimulator
from unified_planning.test.pddl.viplan_hh.viplan_hh_cases import (
    VIPLAN_HH_CASES,
    parse_problem as parse_viplan_hh_problem,
    state_specs_to_upstates,
)


class TestKs0Compiler(unittest_TestCase):
    """Test suite for :class:`Ks0Compiler`.

    Covers input validation, structural properties of the compiled problem,
    full planning pipelines.
    """

    # ==================================================================
    # Helper builders – each returns (problem, possible_initial_states)
    # ==================================================================

    def _build_problem_and_possible_states(
        self, environment=None, problem_factory=Problem
    ):
        """Build a minimal 2-fluent problem with 2 possible initial states.

        Action `unblock` (precondition `Not(blocked)`, effect
        `reachable := True`) achieves the goal `reachable`; the states s0/s1
        differ on `blocked`.  With `problem_factory=ContingentProblem` the
        same uncertainty is declared on the problem itself instead.
        """
        problem = problem_factory("ks0_input", environment=environment)
        reachable = Fluent("reachable", environment=problem.environment)
        blocked = Fluent("blocked", environment=problem.environment)
        em = problem.environment.expression_manager

        # Action: succeed only when not blocked, then set reachable
        unblock = InstantaneousAction("unblock", _env=problem.environment)
        unblock.add_precondition(em.Not(blocked()))
        unblock.add_effect(reachable, True)

        problem.add_fluent(reachable)
        problem.add_fluent(blocked)
        problem.add_action(unblock)
        problem.add_goal(reachable())

        if isinstance(problem, ContingentProblem):
            problem.set_initial_value(reachable(), False)
            problem.add_unknown_initial_constraint(blocked())

        # Two possible worlds: blocked or not blocked
        possible_initial_states = (
            UPState({reachable(): em.FALSE(), blocked(): em.FALSE()}, problem),  # s0
            UPState({reachable(): em.FALSE(), blocked(): em.TRUE()}, problem),  # s1
        )
        return problem, possible_initial_states

    def _build_nav_problem_and_possible_states(self, problem_factory=Problem):
        """Build a 4-location linear-chain navigation problem (goal at l3).

        The agent's initial location (l1..l4) is uncertain, so a conformant
        plan must move left until the position is certain, then move right to
        l3 and `end`.  With `problem_factory=ContingentProblem` the
        position is a `oneof` initial constraint instead.
        """
        problem = problem_factory("nav")

        loc_type = UserType("location")

        at = Fluent("at", BoolType(), l=loc_type)
        adj_left = Fluent("adj_left", BoolType(), l1=loc_type, l2=loc_type)
        is_goal = Fluent("is_goal", BoolType(), l=loc_type)
        done = Fluent("done", BoolType())
        problem.add_fluent(at, default_initial_value=False)
        problem.add_fluent(adj_left, default_initial_value=False)
        problem.add_fluent(is_goal, default_initial_value=False)
        problem.add_fluent(done, default_initial_value=False)

        # move_left: move in the "left" direction along the adjacency chain
        move_left = InstantaneousAction("move_left", l_from=loc_type, l_to=loc_type)
        move_left.add_precondition(adj_left(move_left.l_from, move_left.l_to))
        move_left.add_effect(
            at(move_left.l_from), False, condition=at(move_left.l_from)
        )
        move_left.add_effect(at(move_left.l_to), True, condition=at(move_left.l_from))
        problem.add_action(move_left)

        # move_right: reverse direction (adjacency checked via adj_left(to, from))
        move_right = InstantaneousAction("move_right", l_from=loc_type, l_to=loc_type)
        move_right.add_precondition(adj_left(move_right.l_to, move_right.l_from))
        move_right.add_effect(
            at(move_right.l_from), False, condition=at(move_right.l_from)
        )
        move_right.add_effect(
            at(move_right.l_to), True, condition=at(move_right.l_from)
        )
        problem.add_action(move_right)

        # end: signal completion when the agent is at the goal location
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

        # Topology: l4 -- l3 -- l2 -- l1 (linear chain)
        if isinstance(problem, ContingentProblem):
            problem.add_oneof_initial_constraint([at(l1), at(l2), at(l3), at(l4)])
        else:
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
        """Build a minimal problem whose action sets `f2` only when `f1` holds."""
        problem = Problem("cond_eff")
        f1 = Fluent("f1")
        f2 = Fluent("f2")
        problem.add_fluent(f1, default_initial_value=False)
        problem.add_fluent(f2, default_initial_value=False)

        em = problem.environment.expression_manager
        # Action with a conditional effect: adds f2 only when f1 holds
        a = InstantaneousAction("a")
        a.add_effect(f2, True, condition=em.FluentExp(f1))
        problem.add_action(a)
        problem.add_goal(em.FluentExp(f2))

        s0 = UPState(
            {em.FluentExp(f1): em.TRUE(), em.FluentExp(f2): em.FALSE()},
            problem,
        )
        return problem, (s0,)

    def _build_negated_disjunction_precondition_problem(self):
        """Build an unsolvable problem with precondition `Not(Or(a, b))`.

        State s0 (a=T) falsifies the precondition, so no conformant plan
        achieves `goal`; a translation that does not normalize the negated
        disjunction before introducing knowledge fluents admits a spurious plan.
        """
        problem = Problem("negated_disj")
        a = Fluent("a")
        b = Fluent("b")
        goal = Fluent("goal")
        problem.add_fluent(a, default_initial_value=False)
        problem.add_fluent(b, default_initial_value=False)
        problem.add_fluent(goal, default_initial_value=False)

        em = problem.environment.expression_manager
        act = InstantaneousAction("act")
        act.add_precondition(em.Not(em.Or(em.FluentExp(a), em.FluentExp(b))))
        act.add_effect(goal, True)
        problem.add_action(act)
        problem.add_goal(em.FluentExp(goal))

        s0 = UPState(
            {
                em.FluentExp(a): em.TRUE(),
                em.FluentExp(b): em.FALSE(),
                em.FluentExp(goal): em.FALSE(),
            },
            problem,
        )
        s1 = UPState(
            {
                em.FluentExp(a): em.FALSE(),
                em.FluentExp(b): em.FALSE(),
                em.FluentExp(goal): em.FALSE(),
            },
            problem,
        )
        return problem, (s0, s1)

    def _build_pick_drop_problem_and_possible_states(self):
        """Build the pick/drop example of Palacios & Geffner 2009, Section 4.

        The object starts at l1 or l2 with the hand empty;
        `[pick(l1), drop(l3), pick(l2), drop(l3)]` is a conformant plan for
        `at(l3)` while `[pick(l1), pick(l2), drop(l3)]` is not.
        """
        problem = Problem("pick_drop")
        loc_type = UserType("loc")
        hold = Fluent("hold")
        at = Fluent("at", BoolType(), l=loc_type)
        problem.add_fluent(hold, default_initial_value=False)
        problem.add_fluent(at, default_initial_value=False)
        l1, l2, l3 = (Object(f"l{i}", loc_type) for i in (1, 2, 3))
        problem.add_objects([l1, l2, l3])

        em = problem.environment.expression_manager
        pick = InstantaneousAction("pick", l=loc_type)
        empty_handed_pick = em.And(em.Not(hold()), at(pick.l))
        pick.add_effect(hold, True, condition=empty_handed_pick)
        pick.add_effect(at(pick.l), False, condition=empty_handed_pick)
        pick.add_effect(hold, False, condition=hold())
        pick.add_effect(at(pick.l), True, condition=hold())
        problem.add_action(pick)

        drop = InstantaneousAction("drop", l=loc_type)
        drop.add_effect(hold, False, condition=hold())
        drop.add_effect(at(drop.l), True, condition=hold())
        problem.add_action(drop)

        problem.add_goal(at(l3))
        problem.set_initial_value(at(l1), True)

        states = tuple(
            UPState(
                {
                    hold(): em.FALSE(),
                    at(l1): em.TRUE() if loc is l1 else em.FALSE(),
                    at(l2): em.TRUE() if loc is l2 else em.FALSE(),
                    at(l3): em.FALSE(),
                },
                problem,
            )
            for loc in (l1, l2)
        )
        return problem, states

    def test_compile_with_existential_condition(self):
        problem = Problem("exists_input")
        loc_type = UserType("location")
        at = Fluent("at", BoolType(), l=loc_type)
        done = Fluent("done")
        problem.add_fluent(at, default_initial_value=False)
        problem.add_fluent(done, default_initial_value=False)

        l1 = Object("l1", loc_type)
        l2 = Object("l2", loc_type)
        problem.add_objects([l1, l2])
        problem.set_initial_value(at(l1), True)

        end = InstantaneousAction("end")
        x = Variable("x", loc_type)
        end.add_precondition(Exists(at(VariableExp(x)), x))
        end.add_effect(done, True)
        problem.add_action(end)
        problem.add_goal(done())

        self.assertTrue(problem.kind.has_existential_conditions())

        s0 = UPState({at(l1): TRUE(), at(l2): FALSE(), done(): FALSE()}, problem)
        compiler = Ks0Compiler(possible_initial_states=(s0,))
        res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        self.assertIsNotNone(res.problem)
        assert res.problem is not None
        self.assertFalse(res.problem.kind.has_existential_conditions())

    def test_compile_with_universal_condition(self):
        problem = Problem("forall_cond_input")
        loc_type = UserType("location")
        at = Fluent("at", BoolType(), l=loc_type)
        done = Fluent("done")
        problem.add_fluent(at, default_initial_value=False)
        problem.add_fluent(done, default_initial_value=False)

        l1 = Object("l1", loc_type)
        l2 = Object("l2", loc_type)
        problem.add_objects([l1, l2])
        problem.set_initial_value(at(l1), True)

        end = InstantaneousAction("end")
        x = Variable("x", loc_type)
        end.add_precondition(Forall(at(VariableExp(x)), x))
        end.add_effect(done, True)
        problem.add_action(end)
        problem.add_goal(done())

        self.assertTrue(problem.kind.has_universal_conditions())

        s0 = UPState({at(l1): TRUE(), at(l2): TRUE(), done(): FALSE()}, problem)
        compiler = Ks0Compiler(possible_initial_states=(s0,))
        res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        self.assertIsNotNone(res.problem)
        assert res.problem is not None
        self.assertFalse(res.problem.kind.has_universal_conditions())

    def test_compile_with_forall_effect(self):
        problem = Problem("forall_eff_input")
        loc_type = UserType("location")
        reachable = Fluent("reachable", BoolType(), o=loc_type)
        clear = Fluent("clear", BoolType(), o=loc_type)
        problem.add_fluent(reachable, default_initial_value=False)
        problem.add_fluent(clear, default_initial_value=False)

        l1 = Object("l1", loc_type)
        l2 = Object("l2", loc_type)
        problem.add_objects([l1, l2])
        problem.set_initial_value(clear(l1), True)
        problem.set_initial_value(clear(l2), True)

        mark_all = InstantaneousAction("mark_all")
        x = Variable("x", loc_type)
        mark_all.add_effect(reachable(VariableExp(x)), TRUE(), forall=[x])
        problem.add_action(mark_all)
        problem.add_goal(reachable(l1))

        self.assertTrue(problem.kind.has_forall_effects())

        s0 = UPState(
            {
                reachable(l1): FALSE(),
                reachable(l2): FALSE(),
                clear(l1): TRUE(),
                clear(l2): TRUE(),
            },
            problem,
        )
        compiler = Ks0Compiler(possible_initial_states=(s0,))
        res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        self.assertIsNotNone(res.problem)
        assert res.problem is not None
        self.assertFalse(res.problem.kind.has_forall_effects())

    def test_compile_with_equality_precondition(self):
        problem = Problem("eq_input")
        loc_type = UserType("location")
        at = Fluent("at", BoolType(), l=loc_type)
        done = Fluent("done")
        problem.add_fluent(at, default_initial_value=False)
        problem.add_fluent(done, default_initial_value=False)

        l1 = Object("l1", loc_type)
        l2 = Object("l2", loc_type)
        problem.add_objects([l1, l2])
        problem.set_initial_value(at(l1), True)

        check_eq = InstantaneousAction("check_eq", source=loc_type)
        check_eq.add_precondition(Equals(check_eq.source, l1))
        check_eq.add_effect(done, TRUE())
        problem.add_action(check_eq)
        problem.add_goal(done())

        self.assertTrue(problem.kind.has_equalities())

        s0 = UPState({at(l1): TRUE(), at(l2): FALSE(), done(): FALSE()}, problem)
        compiler = Ks0Compiler(possible_initial_states=(s0,))
        res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        self.assertIsNotNone(res.problem)
        assert res.problem is not None
        self.assertFalse(res.problem.kind.has_equalities())

    def test_compile_with_disjunctive_precondition(self):
        problem = Problem("disj_input")
        a = Fluent("a")
        b = Fluent("b")
        goal = Fluent("goal")
        problem.add_fluent(a, default_initial_value=False)
        problem.add_fluent(b, default_initial_value=False)
        problem.add_fluent(goal, default_initial_value=False)

        em = problem.environment.expression_manager
        act = InstantaneousAction("act")
        act.add_precondition(em.Or(em.FluentExp(a), em.FluentExp(b)))
        act.add_effect(goal, True)
        problem.add_action(act)
        problem.add_goal(em.FluentExp(goal))

        s0 = UPState(
            {
                em.FluentExp(a): em.FALSE(),
                em.FluentExp(b): em.TRUE(),
                em.FluentExp(goal): em.FALSE(),
            },
            problem,
        )
        s1 = UPState(
            {
                em.FluentExp(a): em.FALSE(),
                em.FluentExp(b): em.FALSE(),
                em.FluentExp(goal): em.FALSE(),
            },
            problem,
        )
        compiler = Ks0Compiler(possible_initial_states=(s0, s1))
        res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        self.assertIsNotNone(res.problem)
        assert res.problem is not None
        self.assertFalse(res.problem.kind.has_disjunctive_conditions())

    # ==================================================================
    # Compilation-kind support
    # ==================================================================

    def test_supported_compilation(self):
        """The compiler must advertise support for CONFORMANT_TO_CLASSICAL_KS0."""
        compiler = Ks0Compiler()
        self.assertTrue(
            compiler.supports_compilation(CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        )

    # ==================================================================
    # Input validation tests
    # ==================================================================

    def test_compile_requires_possible_initial_states(self):
        """Compiling without possible initial states must raise `UPUsageError`."""
        problem, _ = self._build_problem_and_possible_states()
        compiler = Ks0Compiler()
        with self.assertRaises(UPUsageError):
            compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

    def test_compile_rejects_invalid_possible_initial_states(self):
        """Non-State elements must be rejected with an error naming the index."""
        problem, possible_initial_states = self._build_problem_and_possible_states()
        compiler = Ks0Compiler(possible_initial_states=[object()])  # type: ignore[list-item]
        with self.assertRaises(UPUsageError) as error:
            compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        self.assertIn("at index 0", str(error.exception))

        compiler = Ks0Compiler(possible_initial_states=possible_initial_states + (object(),))  # type: ignore[list-item]
        with self.assertRaises(UPUsageError) as error:
            compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        self.assertIn("at index 2", str(error.exception))

    def test_compile_rejects_states_from_different_problem(self):
        """States built for a different problem must be rejected."""
        problem1, possible_initial_states1 = self._build_problem_and_possible_states()
        _, possible_initial_states2 = self._build_nav_problem_and_possible_states()

        possible_initial_states1 += possible_initial_states2

        compiler = Ks0Compiler(possible_initial_states=possible_initial_states1)
        with self.assertRaises(UPUsageError) as error:
            compiler.compile(problem1, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        self.assertIn("at index 2", str(error.exception))

    def test_compile_rejects_states_from_different_environments(self):
        """States created under a different `Environment` must be rejected."""
        problem1, _ = self._build_problem_and_possible_states()
        _, possible_initial_states2 = self._build_problem_and_possible_states(
            Environment()
        )

        compiler = Ks0Compiler(possible_initial_states=possible_initial_states2)
        with self.assertRaises(UPUsageError) as error:
            compiler.compile(problem1, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        self.assertIn("at index 0", str(error.exception))

    # ==================================================================
    # Factory integration tests
    # ==================================================================

    def test_factory_instantiation_with_params(self):
        """The factory must build the compiler by name with `possible_initial_states`."""
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
        """The factory must select the compiler from problem and compilation kind."""
        problem, _ = self._build_problem_and_possible_states()
        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.CONFORMANT_TO_CLASSICAL_KS0,
        ) as compiler:
            self.assertTrue(compiler.supports(problem.kind))
            with self.assertRaises(UPUsageError):
                compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

    # ==================================================================
    # ContingentProblem input tests
    # ==================================================================

    def _assert_equivalent_compilations(self, problem1, problem2):
        """Assert two compiled problems have the same fluents, actions, goals,
        and explicit initial values."""
        self.assertEqual(
            {f.name for f in problem1.fluents}, {f.name for f in problem2.fluents}
        )
        self.assertEqual(
            {a.name for a in problem1.actions}, {a.name for a in problem2.actions}
        )
        self.assertEqual(
            [str(g) for g in problem1.goals], [str(g) for g in problem2.goals]
        )
        self.assertEqual(
            {str(k): str(v) for k, v in problem1.explicit_initial_values.items()},
            {str(k): str(v) for k, v in problem2.explicit_initial_values.items()},
        )

    def test_contingent_problem_kind_supported(self):
        """The compiler must support the CONTINGENT class and remove it from
        the resulting problem kind."""
        problem, _ = self._build_nav_problem_and_possible_states(ContingentProblem)
        self.assertTrue(problem.kind.has_contingent())
        self.assertTrue(Ks0Compiler.supports(problem.kind))
        resulting_kind = Ks0Compiler.resulting_problem_kind(
            problem.kind, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
        )
        self.assertFalse(resulting_kind.has_contingent())
        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.CONFORMANT_TO_CLASSICAL_KS0,
        ) as compiler:
            self.assertIsInstance(compiler, Ks0Compiler)

    def test_contingent_unknown_matches_explicit_states(self):
        """An `unknown` constraint must compile like the two corresponding
        explicit states."""
        plain, states = self._build_problem_and_possible_states()
        contingent, _ = self._build_problem_and_possible_states(
            problem_factory=ContingentProblem
        )
        res_explicit = Ks0Compiler(possible_initial_states=states).compile(
            plain, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
        )
        res_contingent = Ks0Compiler().compile(
            contingent, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
        )
        self._assert_equivalent_compilations(
            res_explicit.problem, res_contingent.problem
        )

    def test_contingent_oneof_matches_explicit_states(self):
        """A `oneof` constraint must compile like the explicit four-state setup."""
        plain, states = self._build_nav_problem_and_possible_states()
        contingent, _ = self._build_nav_problem_and_possible_states(ContingentProblem)
        res_explicit = Ks0Compiler(possible_initial_states=states).compile(
            plain, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
        )
        res_contingent = Ks0Compiler().compile(
            contingent, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
        )
        self._assert_equivalent_compilations(
            res_explicit.problem, res_contingent.problem
        )

    def test_contingent_or_matches_explicit_states(self):
        """An `or` constraint must enumerate exactly the satisfying assignments."""

        def build(problem_factory):
            problem = problem_factory("or_input")
            a = Fluent("a", environment=problem.environment)
            b = Fluent("b", environment=problem.environment)
            g = Fluent("g", environment=problem.environment)
            problem.add_fluent(a, default_initial_value=False)
            problem.add_fluent(b, default_initial_value=False)
            problem.add_fluent(g, default_initial_value=False)
            act = InstantaneousAction("act", _env=problem.environment)
            act.add_precondition(a())
            act.add_effect(g, True)
            problem.add_action(act)
            problem.add_goal(g())
            return problem, a, b, g

        plain, a, b, g = build(Problem)
        em = plain.environment.expression_manager
        # The satisfying assignments of or(a, b) in enumeration order
        states = tuple(
            UPState(
                {a(): av, b(): bv, g(): em.FALSE()},
                plain,
            )
            for av, bv in (
                (em.FALSE(), em.TRUE()),
                (em.TRUE(), em.FALSE()),
                (em.TRUE(), em.TRUE()),
            )
        )
        contingent, ca, cb, _ = build(ContingentProblem)
        contingent.add_or_initial_constraint([ca(), cb()])

        res_explicit = Ks0Compiler(possible_initial_states=states).compile(
            plain, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
        )
        res_contingent = Ks0Compiler().compile(
            contingent, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
        )
        self._assert_equivalent_compilations(
            res_explicit.problem, res_contingent.problem
        )

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    def test_contingent_full_pipeline(self):
        """End-to-end on the contingent navigation problem: the plan must reach
        the goal from every state allowed by the `oneof` constraint."""
        problem, possible_states = self._build_nav_problem_and_possible_states(
            ContingentProblem
        )
        with Compiler(name="up_ks0_compiler") as compiler:
            res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

        with OneshotPlanner(problem_kind=res.problem.kind) as planner:
            plan_result = planner.solve(res.problem)
        self.assertIsNotNone(plan_result.plan)

        assert res.plan_back_conversion is not None
        back_plan = res.plan_back_conversion(plan_result.plan)
        self.assertIsInstance(back_plan, SequentialPlan)
        assert isinstance(back_plan, SequentialPlan)
        for ai in back_plan.actions:
            self.assertFalse(ai.action.name.startswith("merge_"))

        with warnings.catch_warnings():
            # The simulator's grounder does not declare CONTINGENT support
            warnings.simplefilter("ignore", UserWarning)
            sim = UPSequentialSimulator(problem, error_on_failed_checks=False)
        for i, init_state in enumerate(possible_states):
            cur_state: State = init_state
            for ai in back_plan.actions:
                next_state = sim.apply(cur_state, ai)
                assert next_state is not None
                self.assertIsNotNone(
                    next_state, f"Action {ai} not applicable from initial state {i}"
                )
                cur_state = next_state
            self.assertTrue(
                sim.is_goal(cur_state), f"Plan does not reach goal from state {i}"
            )

    def test_contingent_rejects_sensing_actions(self):
        """ContingentProblems with sensing actions must be rejected."""
        problem, _ = self._build_nav_problem_and_possible_states(ContingentProblem)
        sense = SensingAction("sense_done", _env=problem.environment)
        sense.add_observed_fluent(problem.fluent("done")())
        problem.add_action(sense)
        with self.assertRaises(UPUsageError):
            Ks0Compiler().compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

    def test_contingent_rejects_explicit_possible_states(self):
        """Providing both a ContingentProblem and constructor states must be rejected."""
        problem, states = self._build_problem_and_possible_states(
            problem_factory=ContingentProblem
        )
        compiler = Ks0Compiler(possible_initial_states=states)
        with self.assertRaises(UPUsageError):
            compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

    def test_contingent_rejects_unsatisfiable_constraints(self):
        """Unsatisfiable initial constraints must be rejected."""
        problem = ContingentProblem("unsat")
        blocked = Fluent("blocked", environment=problem.environment)
        problem.add_fluent(blocked, default_initial_value=False)
        problem.add_goal(blocked())
        em = problem.environment.expression_manager
        problem.add_oneof_initial_constraint([blocked()])
        problem.add_or_initial_constraint([em.Not(blocked())])
        with self.assertRaises(UPUsageError):
            Ks0Compiler().compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

    def test_contingent_rejects_undefined_non_hidden_fluent(self):
        """A non-hidden fluent without an initial value must be rejected."""
        problem = ContingentProblem("undef")
        known = Fluent("known_f", environment=problem.environment)
        hidden = Fluent("hidden_f", environment=problem.environment)
        problem.add_fluent(known)
        problem.add_fluent(hidden)
        problem.add_unknown_initial_constraint(hidden())
        problem.add_goal(hidden())
        with self.assertRaises(UPUsageError) as error:
            Ks0Compiler().compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        self.assertIn("known_f", str(error.exception))

    def test_contingent_rejects_non_ground_hidden_fluent(self):
        """A hidden fluent that is not a grounded fluent expression of the
        problem must be rejected."""
        problem = ContingentProblem("bad_hidden")
        known = Fluent("known_f", environment=problem.environment)
        problem.add_fluent(known, default_initial_value=False)
        stray = Fluent("stray_f", environment=problem.environment)
        problem.add_unknown_initial_constraint(stray())
        problem.add_goal(known())
        with self.assertRaises(UPUsageError) as error:
            Ks0Compiler().compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        self.assertIn("grounded", str(error.exception))

    # ==================================================================
    # End-to-end pipeline tests
    # ==================================================================

    def test_full_compilation_pipeline(self):
        """Compiling must produce a renamed problem with fluents, actions,
        goals, and a plan-back conversion."""
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
        """End-to-end: solve the compiled navigation problem and back-convert
        the plan without leaking merge actions."""
        for num_possible_initial_states in [1, 4]:
            with self.subTest(num_possible_initial_states=num_possible_initial_states):
                (
                    problem,
                    possible_initial_states,
                ) = self._build_nav_problem_and_possible_states()
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
                self.assertIn(
                    plan_result.status,
                    (
                        PlanGenerationResultStatus.SOLVED_SATISFICING,
                        PlanGenerationResultStatus.SOLVED_OPTIMALLY,
                    ),
                )

                # Back-convert to original domain plan (drops merge actions)
                back_plan = res.plan_back_conversion(plan_result.plan)
                self.assertIsInstance(back_plan, SequentialPlan)
                self.assertGreater(len(back_plan.actions), 0)  # plan is non-trivial

                # Back-converted plan must contain no merge actions
                for ai in back_plan.actions:
                    self.assertFalse(
                        ai.action.name.startswith(
                            "merge_"
                        ),  # merge actions are internal
                        f"Back-converted plan contains merge action: {ai.action.name}",
                    )

    # ------------------------------------------------------------------
    # Validation edge case
    # ------------------------------------------------------------------

    def test_compile_rejects_empty_possible_initial_states(self):
        """An empty tuple of possible states must be rejected."""
        problem, _ = self._build_problem_and_possible_states()
        compiler = Ks0Compiler(possible_initial_states=())
        with self.assertRaises(UPUsageError):
            compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

    def test_compile_rejects_non_boolean_fluents(self):
        """Problems with non-Boolean fluents must be rejected."""
        problem = Problem("non_bool")
        counter = Fluent("counter", IntType())
        problem.add_fluent(counter, default_initial_value=0)
        em = problem.environment.expression_manager
        s0 = UPState({em.FluentExp(counter): em.Int(0)}, problem)
        compiler = Ks0Compiler(possible_initial_states=(s0,))
        with self.assertRaises(UPUsageError):
            compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

    def test_compile_rejects_quality_metrics(self):
        """Problems with quality metrics must be rejected."""
        problem, possible_initial_states = self._build_problem_and_possible_states()
        problem.add_quality_metric(MinimizeSequentialPlanLength())
        compiler = Ks0Compiler(possible_initial_states=possible_initial_states)
        with self.assertRaises(UPUsageError):
            compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

    def test_compile_rejects_state_missing_a_fluent_value(self):
        """A state missing a value for some grounded fluent must be rejected."""
        problem, _ = self._build_problem_and_possible_states()
        em = problem.environment.expression_manager
        reachable = problem.fluent("reachable")
        partial_state = UPState({em.FluentExp(reachable): em.FALSE()}, problem)
        compiler = Ks0Compiler(possible_initial_states=(partial_state,))
        with self.assertRaises(UPUsageError) as error:
            compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        self.assertIn("blocked", str(error.exception))

    # ------------------------------------------------------------------
    # Structural tests on the compiled problem
    #
    # All tests in this section use the minimal 2-fluent problem
    # (reachable, blocked) with 2 possible initial states (s0, s1).
    # The compiled problem therefore has 3 tags: empty, s0, s1.
    # ------------------------------------------------------------------

    def _compile_basic(self):
        """Compile the minimal 2-fluent problem and return (problem, result)."""
        problem, possible_initial_states = self._build_problem_and_possible_states()
        compiler = Ks0Compiler(possible_initial_states=possible_initial_states)
        res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        return problem, res

    def test_compiled_problem_name(self):
        """Compiled problem name must be prefixed with 'ks0_'."""
        _, res = self._compile_basic()
        self.assertEqual(res.problem.name, "ks0_ks0_input")

    def test_compiled_fluent_names(self):
        """Every K-fluent follows the K_{not_}<atom>_<tag> naming convention;
        original fluent names must not appear in the compiled problem."""
        _, res = self._compile_basic()
        fluent_names = {f.name for f in res.problem.fluents}
        expected = {
            "K_reachable_empty",
            "K_not_reachable_empty",
            "K_reachable_s0",
            "K_not_reachable_s0",
            "K_reachable_s1",
            "K_not_reachable_s1",
            "K_blocked_empty",
            "K_not_blocked_empty",
            "K_blocked_s0",
            "K_not_blocked_s0",
            "K_blocked_s1",
            "K_not_blocked_s1",
        }
        self.assertEqual(fluent_names, expected)
        self.assertNotIn("reachable", fluent_names)
        self.assertNotIn("blocked", fluent_names)

    def test_compiled_initial_state_empty_tag_universal_literal(self):
        """A literal true in all possible states must start TRUE under the empty tag."""
        _, res = self._compile_basic()
        em = res.problem.environment.expression_manager
        K_not_reachable_empty = res.problem.fluent("K_not_reachable_empty")
        self.assertEqual(
            res.problem.initial_value(em.FluentExp(K_not_reachable_empty)),
            em.TRUE(),
        )

    def test_compiled_initial_state_empty_tag_non_universal_literal(self):
        """A literal not shared by all possible states must not start TRUE
        under the empty tag."""
        _, res = self._compile_basic()
        em = res.problem.environment.expression_manager

        K_blocked_empty = res.problem.fluent("K_blocked_empty")
        val = res.problem.initial_value(em.FluentExp(K_blocked_empty))
        self.assertIn(val, (em.FALSE(), None))

        K_not_blocked_empty = res.problem.fluent("K_not_blocked_empty")
        val2 = res.problem.initial_value(em.FluentExp(K_not_blocked_empty))
        self.assertIn(val2, (em.FALSE(), None))

    def test_compiled_initial_state_per_tag(self):
        """Per-state tags must reflect each literal's truth value in their state."""
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
        """The compiled goal must reference the empty-tag K-fluent, not the
        original fluent."""
        problem, res = self._compile_basic()
        goal_fluents = {g.fluent() for g in res.problem.goals if g.is_fluent_exp()}
        K_reachable_empty = res.problem.fluent("K_reachable_empty")
        self.assertIn(K_reachable_empty, goal_fluents)
        reachable = problem.fluent("reachable")
        self.assertNotIn(reachable, goal_fluents)

    def test_compiled_action_count(self):
        """Expect the original action plus one merge action per precondition
        and goal literal."""
        _, res = self._compile_basic()
        self.assertEqual(len(res.problem.actions), 3)

    def test_compiled_action_preconditions_use_empty_tag(self):
        """Original action preconditions must be rewritten on the empty tag."""
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
        """An unconditional effect must yield support and cancellation effects
        for every tag."""
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
        """A conditional effect's compiled conditions must reference per-tag
        K-fluents."""
        problem, states = self._build_conditional_effect_problem_and_possible_states()
        compiler = Ks0Compiler(possible_initial_states=states)
        res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        assert isinstance(res.problem, Problem)
        compiled_action = res.problem.action("a")
        assert isinstance(compiled_action, InstantaneousAction)
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
        """One merge action must exist per precondition and goal literal."""
        _, res = self._compile_basic()
        merge_actions = [a for a in res.problem.actions if a.name.startswith("merge_")]
        self.assertEqual(len(merge_actions), 2)
        merge_names = {a.name for a in merge_actions}
        self.assertTrue(any("not_blocked" in n for n in merge_names))
        self.assertTrue(any("reachable" in n and "not" not in n for n in merge_names))

    def test_merge_action_preconditions_require_all_state_tags(self):
        """Merge preconditions must require every per-state tag but not the
        empty tag."""
        _, res = self._compile_basic()
        merge_not_blocked = next(
            a
            for a in res.problem.actions
            if a.name.startswith("merge_") and "not_blocked" in a.name
        )
        prec_fluent_names = {
            p.fluent().name
            for p in merge_not_blocked.preconditions
            if p.is_fluent_exp()
        }
        self.assertIn("K_not_blocked_s0", prec_fluent_names)
        self.assertIn("K_not_blocked_s1", prec_fluent_names)
        self.assertNotIn("K_not_blocked_empty", prec_fluent_names)

    def test_merge_action_effect_sets_empty_tag_fluent(self):
        """The merge action's effect must set the empty-tag K-fluent to TRUE."""
        _, res = self._compile_basic()
        em = res.problem.environment.expression_manager
        merge_not_blocked = next(
            a
            for a in res.problem.actions
            if a.name.startswith("merge_") and "not_blocked" in a.name
        )
        effect_fluent_names = {
            e.fluent.fluent().name for e in merge_not_blocked.effects
        }
        self.assertIn("K_not_blocked_empty", effect_fluent_names)
        for e in merge_not_blocked.effects:
            self.assertEqual(e.value, em.TRUE())  # merge always sets to TRUE

    def test_resulting_problem_kind_has_conditional_effects(self):
        """The resulting kind must declare the conditional effects the
        translation introduces."""
        problem, _ = self._build_problem_and_possible_states()
        resulting_kind = Ks0Compiler.resulting_problem_kind(
            problem.kind, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
        )
        self.assertTrue(resulting_kind.has_conditional_effects())

    def test_resulting_problem_kind_removes_undefined_initial_symbolic(self):
        """Both the declared resulting kind and the compiled problem's kind
        must lack UNDEFINED_INITIAL_SYMBOLIC."""
        problem, _ = self._build_problem_and_possible_states()
        resulting_kind = Ks0Compiler.resulting_problem_kind(
            problem.kind, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
        )
        self.assertFalse(resulting_kind.has_undefined_initial_symbolic())
        _, res = self._compile_basic()
        self.assertFalse(res.problem.kind.has_undefined_initial_symbolic())

    # ------------------------------------------------------------------
    # Cancellation-rule semantics
    # ------------------------------------------------------------------

    def test_cancellation_rules_forget_conditional_knowledge(self):
        """On the pick/drop example, the merge for `at(l3)` must apply after
        the valid plan but not after the spurious one, whose second pick
        cancels the knowledge derived under the first tag."""
        problem, states = self._build_pick_drop_problem_and_possible_states()
        compiler = Ks0Compiler(possible_initial_states=states)
        res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        compiled_problem = res.problem
        assert isinstance(compiled_problem, Problem)

        sim = UPSequentialSimulator(compiled_problem)

        def apply_all(action_names):
            state = sim.get_initial_state()
            for name in action_names:
                next_state = sim.apply(
                    state, ActionInstance(compiled_problem.action(name))
                )
                if next_state is None:
                    return None
                state = next_state
            return state

        good_state = apply_all(
            ["pick_l1", "drop_l3", "pick_l2", "drop_l3", "merge_at_l3"]
        )
        self.assertIsNotNone(good_state)
        self.assertTrue(sim.is_goal(good_state))

        # The merge must be inapplicable: K_at(l3) was never derived under
        # the tag where the object starts at l1.
        bad_state = apply_all(["pick_l1", "pick_l2", "drop_l3", "merge_at_l3"])
        self.assertIsNone(bad_state)

    # ------------------------------------------------------------------
    # Edge-case tests
    # ------------------------------------------------------------------

    def test_duplicate_states_are_deduplicated(self):
        """Passing the same state twice must compile like passing it once."""
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

        assert isinstance(res_single.problem, Problem)
        assert isinstance(res_dup.problem, Problem)
        self.assertEqual(len(res_single.problem.fluents), len(res_dup.problem.fluents))

    def _build_dominated_state_problem(self):
        """Build a problem where the second possible state is dominated.

        Action `act` has the conditional effect `b -> a` and the goal is
        `a`, so the literals relevant to the only merge target are `a` and
        `b`; state s1 (a=T, b=T) makes a superset of the relevant literals
        of s0 (a=F, b=T) true and is dropped by the basis reduction.
        """
        problem = Problem("dominated")
        a = Fluent("a")
        b = Fluent("b")
        problem.add_fluent(a, default_initial_value=False)
        problem.add_fluent(b, default_initial_value=False)
        em = problem.environment.expression_manager
        act = InstantaneousAction("act")
        act.add_effect(a, True, condition=em.FluentExp(b))
        problem.add_action(act)
        problem.add_goal(em.FluentExp(a))
        s0 = UPState({a(): em.FALSE(), b(): em.TRUE()}, problem)
        s1 = UPState({a(): em.TRUE(), b(): em.TRUE()}, problem)
        return problem, (s0, s1)

    def test_basis_reduction_drops_dominated_state(self):
        """A state whose relevant literals are a superset of another's must be
        dropped: compiling both states must equal compiling the minimal one."""
        problem, (s0, s1) = self._build_dominated_state_problem()
        res_both = Ks0Compiler(possible_initial_states=(s0, s1)).compile(
            problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
        )
        res_minimal = Ks0Compiler(possible_initial_states=(s0,)).compile(
            problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
        )
        fluent_names = {f.name for f in res_both.problem.fluents}
        self.assertFalse(any(name.endswith("_s1") for name in fluent_names))
        self._assert_equivalent_compilations(res_both.problem, res_minimal.problem)

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    def test_basis_reduction_preserves_conformant_plans(self):
        """A plan for the reduced compilation must reach the goal from every
        original possible state, including the dropped one."""
        problem, possible_states = self._build_dominated_state_problem()
        compiler = Ks0Compiler(possible_initial_states=possible_states)
        res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

        with OneshotPlanner(problem_kind=res.problem.kind) as planner:
            plan_result = planner.solve(res.problem)
        self.assertIsNotNone(plan_result.plan)

        assert res.plan_back_conversion is not None
        back_plan = res.plan_back_conversion(plan_result.plan)
        self.assertIsInstance(back_plan, SequentialPlan)
        assert isinstance(back_plan, SequentialPlan)

        sim = UPSequentialSimulator(problem)
        for i, init_state in enumerate(possible_states):
            cur_state: State = init_state
            for ai in back_plan.actions:
                next_state = sim.apply(cur_state, ai)
                assert next_state is not None
                self.assertIsNotNone(
                    next_state, f"Action {ai} not applicable from initial state {i}"
                )
                cur_state = next_state
            self.assertTrue(
                sim.is_goal(cur_state), f"Plan does not reach goal from state {i}"
            )

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    def test_single_state_compiled_problem_is_solvable(self):
        """With a single possible state the compiled problem must be solvable."""
        problem, possible_initial_states = self._build_problem_and_possible_states()
        # s0: blocked=False, reachable=False — unblock IS applicable from s0
        s0_only = possible_initial_states[:1]
        compiler = Ks0Compiler(possible_initial_states=s0_only)
        res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

        assert res.problem is not None
        with OneshotPlanner(problem_kind=res.problem.kind) as planner:
            plan_result = planner.solve(res.problem)
        self.assertIsNotNone(plan_result.plan)
        self.assertIn(
            plan_result.status,
            (
                PlanGenerationResultStatus.SOLVED_SATISFICING,
                PlanGenerationResultStatus.SOLVED_OPTIMALLY,
            ),
        )

    # ------------------------------------------------------------------
    # ViPlan-HH integration tests
    #
    # These tests exercise the compiler against a realistic household
    # robotics domain (PDDL) from the iGibson simulator, verifying that
    # the KS0 compilation scales to real-world problem sizes and that
    # produced conformant plans are valid.
    # ------------------------------------------------------------------

    def test_viplan_hh_compile_single_possible_initial_state(self):
        """Each ViPlan-HH case must compile with one representative state."""
        for case in VIPLAN_HH_CASES.values():
            with self.subTest(case=case.name):
                problem = parse_viplan_hh_problem(case)
                possible_states = state_specs_to_upstates(
                    problem, case.representative_states[:1]
                )
                compiler = Ks0Compiler(possible_initial_states=possible_states)
                res = compiler.compile(
                    problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
                )
                self.assertIsInstance(res, CompilerResult)
                self.assertIsNotNone(res.problem)
                assert res.problem is not None
                assert res.problem.name is not None
                self.assertTrue(res.problem.name.startswith("ks0_"))

    def test_viplan_hh_compile_with_uncertainty(self):
        """Each ViPlan-HH case must compile with its representative uncertain states."""
        for case in VIPLAN_HH_CASES.values():
            with self.subTest(case=case.name):
                problem = parse_viplan_hh_problem(case)
                possible_states = state_specs_to_upstates(
                    problem, case.representative_states
                )
                compiler = Ks0Compiler(possible_initial_states=possible_states)
                res = compiler.compile(
                    problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
                )
                self.assertIsInstance(res, CompilerResult)
                self.assertIsNotNone(res.problem)
                assert res.problem is not None
                assert res.problem.name is not None
                self.assertTrue(res.problem.name.startswith("ks0_"))

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    def test_viplan_hh_full_pipeline_single_state(self):
        """Each ViPlan-HH case must compile, solve, back-convert, and reach the
        goal from its representative state."""
        for case in VIPLAN_HH_CASES.values():
            with self.subTest(case=case.name):
                problem = parse_viplan_hh_problem(case)
                possible_states = state_specs_to_upstates(
                    problem, case.representative_states[:1]
                )
                with Compiler(
                    name="up_ks0_compiler",
                    params={"possible_initial_states": possible_states},
                ) as compiler:
                    res = compiler.compile(
                        problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
                    )
                    compiled_problem = res.problem

                with OneshotPlanner(problem_kind=compiled_problem.kind) as planner:
                    plan_result = planner.solve(compiled_problem)

                self.assertIsNotNone(plan_result.plan)
                self.assertIn(
                    plan_result.status,
                    (
                        PlanGenerationResultStatus.SOLVED_SATISFICING,
                        PlanGenerationResultStatus.SOLVED_OPTIMALLY,
                    ),
                )
                back_plan = res.plan_back_conversion(plan_result.plan)
                self.assertIsInstance(back_plan, SequentialPlan)
                for ai in back_plan.actions:
                    self.assertFalse(
                        ai.action.name.startswith("merge_")
                    )  # no internal actions

                sim = UPSequentialSimulator(problem)
                cur_state: State = sim.get_initial_state()
                for ai in back_plan.actions:
                    next_state = sim.apply(cur_state, ai)
                    assert next_state is not None
                    self.assertIsNotNone(next_state)
                    cur_state = next_state
                self.assertTrue(sim.is_goal(cur_state))

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    def test_viplan_hh_full_pipeline_conformant_plan(self):
        """Each ViPlan-HH conformant plan must reach the goal from every
        representative state."""
        for case in VIPLAN_HH_CASES.values():
            with self.subTest(case=case.name):
                problem = parse_viplan_hh_problem(case)
                possible_states = state_specs_to_upstates(
                    problem, case.representative_states
                )
                with Compiler(
                    name="up_ks0_compiler",
                    params={"possible_initial_states": possible_states},
                ) as compiler:
                    res = compiler.compile(
                        problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
                    )
                    compiled_problem = res.problem

                with OneshotPlanner(problem_kind=compiled_problem.kind) as planner:
                    plan_result = planner.solve(compiled_problem)

                self.assertIsNotNone(plan_result.plan)
                assert res.plan_back_conversion is not None
                back_plan = res.plan_back_conversion(plan_result.plan)
                self.assertIsInstance(back_plan, SequentialPlan)
                assert isinstance(back_plan, SequentialPlan)

                sim = UPSequentialSimulator(problem)
                for i, init_state in enumerate(possible_states):
                    cur_state: State = init_state
                    for ai in back_plan.actions:
                        next_state = sim.apply(cur_state, ai)
                        assert next_state is not None
                        self.assertIsNotNone(
                            next_state,
                            f"Action {ai} not applicable from initial state {i}",
                        )
                        cur_state = next_state
                    self.assertTrue(
                        sim.is_goal(cur_state),
                        f"Plan does not reach goal from initial state {i}",
                    )

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    def test_subsets_of_viplan_hh_initial_states(self):
        """Subsets of each case's possible states must compile (and solve when
        small) to exercise the basis-reduction and K-fluent construction."""
        for case in VIPLAN_HH_CASES.values():
            with self.subTest(case=case.name):
                problem = parse_viplan_hh_problem(case)
                possible_state_specs = list(case.possible_state_specs())
                mid_index = len(possible_state_specs) // 2
                subsets = [
                    (),
                    possible_state_specs[:1],
                    possible_state_specs[:mid_index],
                    possible_state_specs,
                ]

                sim = UPSequentialSimulator(problem)
                for subset_index, subset in enumerate(subsets):
                    with self.subTest(
                        case=case.name,
                        subset_index=subset_index,
                        subset_size=len(subset),
                    ):
                        state_specs = list(subset) + [case.true_state]
                        states = state_specs_to_upstates(problem, state_specs)

                        compiler = Ks0Compiler(possible_initial_states=states)
                        res = compiler.compile(
                            problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
                        )
                        compiled_problem = res.problem
                        assert compiled_problem is not None

                        if len(subset) <= 1:
                            with OneshotPlanner(
                                problem_kind=compiled_problem.kind
                            ) as planner:
                                plan_result = planner.solve(compiled_problem)

                            self.assertIsNotNone(
                                plan_result.plan,
                                f"No plan found for case={case.name}, "
                                f"subset #{subset_index}",
                            )
                            assert res.plan_back_conversion is not None
                            back_plan = res.plan_back_conversion(plan_result.plan)
                            self.assertIsInstance(back_plan, SequentialPlan)
                            assert isinstance(back_plan, SequentialPlan)

                            cur_state: State = sim.get_initial_state()
                            for ai in back_plan.actions:
                                next_state = sim.apply(cur_state, ai)
                                assert next_state is not None
                                self.assertIsNotNone(next_state)
                                cur_state = next_state
                            self.assertTrue(
                                sim.is_goal(cur_state),
                                f"Plan does not reach the PDDL goal "
                                f"for case={case.name}, subset #{subset_index}",
                            )

    # ==================================================================
    # Negated disjunctive precondition regression test
    # ==================================================================

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    def test_negated_disjunction_precondition_not_conformantly_solvable(self):
        """Negated disjunctive preconditions must be normalized before
        knowledge fluents are introduced: the compiled problem must be
        unsolvable."""
        (
            problem,
            possible_initial_states,
        ) = self._build_negated_disjunction_precondition_problem()
        compiler = Ks0Compiler(possible_initial_states=possible_initial_states)
        res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

        assert res.problem is not None
        with OneshotPlanner(problem_kind=res.problem.kind) as planner:
            plan_result = planner.solve(res.problem)

        self.assertIsNone(
            plan_result.plan,
            "No conformant plan should exist: state s0 (a=T, b=F) makes "
            "precondition Not(Or(a, b)) False, so the goal cannot be achieved.",
        )
