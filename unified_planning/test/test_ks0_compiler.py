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

    def _build_problem_and_possible_states(self, environment=None):
        """Build a minimal 2-fluent problem with 2 possible initial states.

        Problem "ks0_input":
          Fluents: ``reachable`` (goal), ``blocked`` (precondition guard).
          Action:  ``unblock`` — precondition: NOT blocked; effect: reachable := true.
          Goal:    ``reachable``.

        Possible initial states:
          s0: reachable=F, blocked=F  (unblock IS applicable)
          s1: reachable=F, blocked=T  (unblock is NOT applicable)

        Accepts an optional *environment* so tests can verify cross-environment
        rejection.

        Returns:
            (Problem, tuple[UPState, UPState])
        """
        problem = Problem("ks0_input", environment=environment)
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

        # Two possible worlds: blocked or not blocked
        possible_initial_states = (
            UPState({reachable(): em.FALSE(), blocked(): em.FALSE()}, problem),  # s0
            UPState({reachable(): em.FALSE(), blocked(): em.TRUE()}, problem),  # s1
        )
        return problem, possible_initial_states

    def _build_nav_problem_and_possible_states(self):
        """Build a 4-location navigation problem with typed parameters.

        Problem "nav":
          Types:   ``location``.
          Fluents: ``at(l)``, ``adj_left(l1,l2)``, ``is_goal(l)``, ``done``.
          Actions: ``move_left``, ``move_right`` (conditional on adjacency and
                   current position), ``end`` (marks done when at goal).
          Objects: l1 — l2 — l3 — l4 (linear chain, goal at l3).
          Goal:    ``done``.

        The problem can be viewed as a 4x1 grid with a single exit point:

                 done
                   ^
        ---------- | ----------------
        |      |      |      |      |
        |  l4     l3     l2     l1  |
        |      |      |      |      |
        -----------------------------

        Possible initial states (4):
          Each places the agent at a different location (l1..l4) while keeping
          the adjacency and goal structure fixed. Thus, a conformant plan must
          move left from l1 until it is certain it is in l4, then move right
          to l3 and end.

        Returns:
            (Problem, tuple[UPState, x 4])
        """
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
        """Build a minimal problem with a conditional effect.

        Problem "cond_eff":
          Fluents: ``f1``, ``f2``.
          Action:  ``a`` — effect: f2 := true **when** f1 is true.
          Goal:    ``f2``.

        Single possible initial state:
          s0: f1=T, f2=F (the conditional effect fires).

        Used to verify that the compiler correctly translates conditional
        effects into per-tag conditional effects in the compiled domain.

        Returns:
            (Problem, tuple[UPState])
        """
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
        """Build a problem that exposes a translation bug in ks0-cc.

        Problem "negated_disj":
          Fluents: ``a``, ``b``, ``goal``.
          Action:  ``act`` — precondition: ``Not(Or(a, b))``; effect: ``goal := True``.
          Goal:    ``goal``.

        The precondition ``Not(Or(a, b))`` is semantically equivalent to
        ``And(Not(a), Not(b))`` by De Morgan's law.  The two KS0 implementations
        translate this differently:

        **ks0-cc** handles ``Not(expr)`` where ``expr`` is not a plain fluent by
        recursing: ``Not(translate(Or(a, b)))`` → ``Not(Or(K_a_t, K_b_t))``.
        Under the empty tag, ``K_a_empty = F`` and ``K_b_empty = F`` (since neither
        fluent is known in all states), so the condition evaluates to
        ``Not(Or(F, F)) = True`` — the precondition appears satisfied and the
        planner finds a spurious plan.

        **ks0-codex** runs ``DisjunctiveConditionsRemover`` first (because the
        problem kind has ``DISJUNCTIVE_CONDITIONS``), turning the precondition into
        ``And(Not(a), Not(b))``.  After KS0 translation this becomes
        ``And(K_not_a_empty, K_not_b_empty) = And(F, T) = False`` — the precondition
        is correctly unsatisfied, and the problem is identified as unsolvable.

        Possible initial states:
          s0: a=T, b=F  →  Not(Or(T, F)) = False  →  ``act`` NOT applicable
          s1: a=F, b=F  →  Not(Or(F, F)) = True   →  ``act`` IS applicable

        The conformant problem is **not solvable**: there is no plan that achieves
        ``goal`` from every possible initial state, because ``act``'s precondition
        fails in s0.

        Returns:
            (Problem, tuple[UPState, UPState])
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
        """Compiling without providing any possible initial states must raise
        ``UPUsageError``.  This guards against accidental omission of the
        required conformant-planning input."""
        problem, _ = self._build_problem_and_possible_states()
        compiler = Ks0Compiler()
        with self.assertRaises(UPUsageError):
            compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

    def test_compile_rejects_invalid_possible_initial_states(self):
        """Non-State objects in the possible-states list must be rejected with a
        clear error message stating the offending type and index."""

        # check failure at index 0
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
        """States built for a *different* problem must be rejected: they cannot
        resolve this problem's fluent expressions."""
        problem1, possible_initial_states1 = self._build_problem_and_possible_states()
        _, possible_initial_states2 = self._build_nav_problem_and_possible_states()

        possible_initial_states1 += possible_initial_states2

        compiler = Ks0Compiler(possible_initial_states=possible_initial_states1)
        with self.assertRaises(UPUsageError) as error:
            compiler.compile(problem1, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        self.assertIn("at index 2", str(error.exception))

    def test_compile_rejects_states_from_different_environments(self):
        """States created under a different UP ``Environment`` must be rejected:
        their expressions cannot resolve this problem's fluent expressions."""
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
        """Verify the compiler can be instantiated through the UP ``Compiler``
        factory by name, passing ``possible_initial_states`` as a parameter."""
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
        """Verify the factory can select the KS0 compiler from a problem kind
        and compilation kind alone.  Compilation must still require states."""
        problem, _ = self._build_problem_and_possible_states()
        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.CONFORMANT_TO_CLASSICAL_KS0,
        ) as compiler:
            self.assertTrue(compiler.supports(problem.kind))
            with self.assertRaises(UPUsageError):
                compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

    # ==================================================================
    # End-to-end pipeline tests
    # ==================================================================

    def test_full_compilation_pipeline(self):
        """Compile the basic problem and verify the result contains a renamed
        problem with fluents, actions, goals, and a back-conversion function."""
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
        """End-to-end: compile the navigation problem with 1-4 possible initial
        states, solve the compiled classical problem, back-convert the plan,
        and verify no merge actions leak into the original-domain plan."""
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
        """An *empty* tuple of possible states must be rejected (at least one
        world is required for the KS0 compilation to be meaningful)."""
        problem, _ = self._build_problem_and_possible_states()
        compiler = Ks0Compiler(possible_initial_states=())
        with self.assertRaises(UPUsageError):
            compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

    # ------------------------------------------------------------------
    # Structural tests on the compiled problem
    #
    # All tests in this section use the minimal 2-fluent problem
    # (reachable, blocked) with 2 possible initial states (s0, s1).
    # The compiled problem therefore has 3 tags: empty, s0, s1.
    # ------------------------------------------------------------------

    def _compile_basic(self):
        """Compile the minimal 2-fluent problem and return both the original
        problem and the :class:`CompilerResult` for structural inspection."""
        problem, possible_initial_states = self._build_problem_and_possible_states()
        compiler = Ks0Compiler(possible_initial_states=possible_initial_states)
        res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        return problem, res

    def test_compiled_problem_name(self):
        """Compiled problem name must be prefixed with 'ks0_'."""
        _, res = self._compile_basic()
        self.assertEqual(res.problem.name, "ks0_ks0_input")

    def test_compiled_fluent_count(self):
        """Expect 2 atoms x 2 literals (positive & negated) x 3 tags = 12 K-fluents."""
        # 2 atoms × 2 literals × 3 tags (1 empty + 2 states) = 12
        _, res = self._compile_basic()
        self.assertEqual(len(res.problem.fluents), 12)

    def test_compiled_fluent_names(self):
        """Every K-fluent follows the K_{not_}<atom>_<tag> naming convention.
        Original fluent names must not appear in the compiled problem."""
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
        """A literal true in *all* possible states (not-reachable) must be set
        to TRUE under the empty (universal) tag in the initial state."""
        _, res = self._compile_basic()
        em = res.problem.environment.expression_manager
        K_not_reachable_empty = res.problem.fluent("K_not_reachable_empty")
        self.assertEqual(
            res.problem.initial_value(em.FluentExp(K_not_reachable_empty)),
            em.TRUE(),
        )

    def test_compiled_initial_state_empty_tag_non_universal_literal(self):
        """A literal that is NOT true in all possible states (blocked and
        not-blocked) must NOT be set to TRUE under the empty tag."""
        _, res = self._compile_basic()
        em = res.problem.environment.expression_manager

        K_blocked_empty = res.problem.fluent("K_blocked_empty")
        val = res.problem.initial_value(em.FluentExp(K_blocked_empty))
        self.assertIn(val, (em.FALSE(), None))

        K_not_blocked_empty = res.problem.fluent("K_not_blocked_empty")
        val2 = res.problem.initial_value(em.FluentExp(K_not_blocked_empty))
        self.assertIn(val2, (em.FALSE(), None))

    def test_compiled_initial_state_per_tag(self):
        """Per-state tags must reflect the truth value of each literal in the
        corresponding possible initial state.  s0 has blocked=F so
        K_not_blocked_s0 = T; s1 has blocked=T so K_blocked_s1 = T and
        K_not_blocked_s1 must be F."""
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
        """The compiled goal must reference the empty-tag K-fluent (universal
        knowledge), not the original fluent.  This ensures the plan achieves
        the goal regardless of which initial state is the true one."""
        problem, res = self._compile_basic()
        goal_fluents = {g.fluent() for g in res.problem.goals if g.is_fluent_exp()}
        K_reachable_empty = res.problem.fluent("K_reachable_empty")
        self.assertIn(K_reachable_empty, goal_fluents)
        reachable = problem.fluent("reachable")
        self.assertNotIn(reachable, goal_fluents)

    def test_compiled_action_count(self):
        """Expect 1 original action (unblock) + 2 merge actions = 3 total.
        Merge actions are generated for each literal that appears in a
        precondition or the goal."""
        # 1 original action (unblock) + 2 merge actions = 3
        _, res = self._compile_basic()
        self.assertEqual(len(res.problem.actions), 3)

    def test_compiled_action_preconditions_use_empty_tag(self):
        """Original action preconditions must be rewritten to reference the
        empty-tag K-fluent, not the original fluent.  This ensures the planner
        reasons about knowledge rather than specific states."""
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
        """An unconditional add-effect on ``reachable`` must generate both
        support (K_reachable_<tag> := T) and cancellation (K_not_reachable_<tag>
        := F) effects for every tag (empty + per-state), totaling 6 effects."""
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
        """A conditional effect (f2 := T when f1) must produce per-tag
        conditional effects whose conditions reference K_f1_<tag> fluents."""
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
        """Merge actions bridge per-state knowledge to universal knowledge.
        One merge action must exist for each literal appearing in a precondition
        or the goal: here, ``not_blocked`` (precondition) and ``reachable``
        (goal)."""
        _, res = self._compile_basic()
        merge_actions = [a for a in res.problem.actions if a.name.startswith("merge_")]
        self.assertEqual(len(merge_actions), 2)
        merge_names = {a.name for a in merge_actions}
        self.assertTrue(any("not_blocked" in n for n in merge_names))
        self.assertTrue(any("reachable" in n and "not" not in n for n in merge_names))

    def test_merge_action_preconditions_require_all_state_tags(self):
        """A merge action's preconditions must require the corresponding
        K-fluent to hold in *every* per-state tag (s0, s1) but must NOT
        reference the empty tag (that is the conclusion, not a premise)."""
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
        """The merge action's effect must set the empty-tag K-fluent to TRUE,
        thereby asserting universal knowledge once all per-state tags agree."""
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
        """The resulting problem kind must declare conditional effects because
        the KS0 translation introduces them for per-tag effect propagation."""
        problem, _ = self._build_problem_and_possible_states()
        resulting_kind = Ks0Compiler.resulting_problem_kind(
            problem.kind, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
        )
        self.assertTrue(resulting_kind.has_conditional_effects())

    def test_resulting_problem_kind_removes_undefined_initial_symbolic(self):
        """After compilation, the UNDEFINED_INITIAL_SYMBOLIC feature must be
        removed because all initial-state uncertainty has been encoded into
        the K-fluent structure."""
        problem, _ = self._build_problem_and_possible_states()
        resulting_kind = Ks0Compiler.resulting_problem_kind(
            problem.kind, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0
        )
        self.assertFalse(resulting_kind.has_undefined_initial_symbolic())

    def test_compiled_problem_kind_removes_undefined_initial_symbolic(self):
        """Verify the *actual compiled problem* (not just the static method)
        also lacks UNDEFINED_INITIAL_SYMBOLIC."""
        _, res = self._compile_basic()
        self.assertFalse(res.problem.kind.has_undefined_initial_symbolic())

    # ------------------------------------------------------------------
    # Edge-case tests
    # ------------------------------------------------------------------

    def test_duplicate_states_are_deduplicated(self):
        """Passing the same state twice must produce the same compiled problem
        as passing it once (duplicates should be silently removed)."""
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

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    def test_single_state_compiled_problem_is_solvable(self):
        """With only one possible state (s0, where blocked=F), the compiled
        problem is a trivial classical problem that must be solvable."""
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
    # Back-conversion test
    # ------------------------------------------------------------------

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    def test_plan_back_conversion_drops_merge_actions(self):
        """After solving the compiled problem, back-converting the plan must
        strip all internal merge actions, leaving only actions from the
        original domain."""
        problem, possible_initial_states = self._build_problem_and_possible_states()
        s0_only = possible_initial_states[:1]  # solvable single-state subset
        compiler = Ks0Compiler(possible_initial_states=s0_only)
        res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

        assert res.problem is not None
        with OneshotPlanner(problem_kind=res.problem.kind) as planner:
            plan_result = planner.solve(res.problem)
        self.assertIsNotNone(plan_result.plan)

        assert res.plan_back_conversion is not None
        back_plan = res.plan_back_conversion(plan_result.plan)
        self.assertIsInstance(back_plan, SequentialPlan)
        assert isinstance(back_plan, SequentialPlan)
        for ai in back_plan.actions:
            self.assertFalse(
                ai.action.name.startswith(
                    "merge_"
                ),  # merge actions are compiler-internal
                f"Back-converted plan still contains merge action: {ai.action.name}",
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
        """Each ViPlan-HH case must compile with one representative possible
        state and produce a validly named compiled problem."""
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
        """Each ViPlan-HH case must compile with its representative uncertain
        states and produce a valid compiled problem."""
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
        """For each ViPlan-HH case, a single representative state must support
        compile-solve-back-convert and reach the goal under simulation."""
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
        """For each ViPlan-HH case, a plan compiled from the representative
        uncertain states must reach the goal from every such state."""
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
        """Test each ViPlan-HH case over a small set of subsets of its possible
        states to exercise the basis-reduction and K-fluent construction logic."""
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
    # ks0-cc vs ks0-codex divergence test
    # ==================================================================

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    def test_negated_disjunction_precondition_not_conformantly_solvable(self):
        """Regression test for a translation bug in ks0-cc.

        The problem has precondition ``Not(Or(a, b))`` with possible states
        s0={a=T,b=F} and s1={a=F,b=F}.  Since s0 makes the precondition False
        the conformant problem is **unsolvable** — no plan achieves ``goal``
        in every possible initial state.

        ks0-cc **fails** this test: it translates ``Not(Or(a, b))`` under the
        empty tag as ``Not(Or(K_a_empty, K_b_empty))``.  Because neither
        ``K_a_empty`` nor ``K_b_empty`` is set in the initial knowledge state,
        this evaluates to ``Not(Or(F, F)) = True``, making the precondition
        appear satisfied.  The planner then finds a spurious plan ``[act]``.

        ks0-codex **passes** this test: it normalises ``Not(Or(a, b))`` to
        ``And(Not(a), Not(b))`` via ``DisjunctiveConditionsRemover`` before
        compilation.  The translated precondition becomes
        ``And(K_not_a_empty, K_not_b_empty) = And(F, T) = False``, the compiled
        problem is correctly unsolvable, and the planner returns no plan.
        """
        (
            problem,
            possible_initial_states,
        ) = self._build_negated_disjunction_precondition_problem()
        compiler = Ks0Compiler(possible_initial_states=possible_initial_states)
        res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)

        assert res.problem is not None
        with OneshotPlanner(problem_kind=res.problem.kind) as planner:
            plan_result = planner.solve(res.problem)

        # The problem is NOT conformantly solvable: in s0 (a=T, b=F) the
        # precondition Not(Or(a, b)) = Not(Or(T, F)) = False, so act can never
        # fire from that initial state.
        self.assertIsNone(
            plan_result.plan,
            "No conformant plan should exist: state s0 (a=T, b=F) makes "
            "precondition Not(Or(a, b)) False, so the goal cannot be achieved.",
        )
