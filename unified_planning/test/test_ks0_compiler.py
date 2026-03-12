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

import os
import re
from itertools import chain, combinations

from unified_planning.engines import CompilationKind
from unified_planning.engines.compilers import Ks0Compiler
from unified_planning.engines.results import CompilerResult, PlanGenerationResultStatus
from unified_planning.environment import Environment
from unified_planning.exceptions import UPUsageError
from unified_planning.io import PDDLReader
from unified_planning.model import UPState
from unified_planning.model.problem_kind import classical_kind
from unified_planning.plans import SequentialPlan
from unified_planning.shortcuts import *
from unified_planning.test import (
    unittest_TestCase,
    skipIfNoOneshotPlannerForProblemKind,
)
from unified_planning.engines.sequential_simulator import UPSequentialSimulator


# ---------------------------------------------------------------------------
# ViPlan-HH domain test data
#
# The constants below encode possible initial states for a "cleaning out
# drawers" household robotics task from the iGibson simulator.  Each state is
# a dict mapping ground predicate strings (e.g. "inside(bowl_1, cabinet_1)")
# to boolean values.  The 12 predicates track spatial relations (inside,
# ontop, nextto), reachability, whether the cabinet is open, and whether the
# robot is holding the bowl.
#
# VIPLAN_HH_POSSIBLE_STATES_STR: 16 *alternative* initial states representing
#   uncertainty about the bowl's location and the cabinet's state.  They are
#   used to exercise the compiler with varying amounts of initial-state
#   uncertainty.
#
# VIPLAN_HH_TRUE_INIT_STATE_STR: the single "ground truth" initial state that
#   must always be included so conformant plans are validated against it.
# ---------------------------------------------------------------------------
VIPLAN_HH_POSSIBLE_STATES_STR = [
    {
        "inside(bowl_1, cabinet_1)": False,
        "open(cabinet_1)": False,
        "ontop(bowl_1, sink_1)": False,
        "reachable(bowl_1)": False,
        "reachable(cabinet_1)": False,
        "reachable(sink_1)": True,
        "holding(bowl_1)": False,
        "ontop(bowl_1, bowl_1)": False,
        "ontop(bowl_1, cabinet_1)": False,
        "nextto(bowl_1, bowl_1)": True,
        "nextto(bowl_1, cabinet_1)": False,
        "nextto(bowl_1, sink_1)": False,
    },
    {
        "inside(bowl_1, cabinet_1)": False,
        "open(cabinet_1)": False,
        "ontop(bowl_1, sink_1)": False,
        "reachable(bowl_1)": False,
        "reachable(cabinet_1)": False,
        "reachable(sink_1)": True,
        "holding(bowl_1)": False,
        "ontop(bowl_1, bowl_1)": False,
        "ontop(bowl_1, cabinet_1)": False,
        "nextto(bowl_1, bowl_1)": True,
        "nextto(bowl_1, cabinet_1)": True,
        "nextto(bowl_1, sink_1)": False,
    },
    {
        "inside(bowl_1, cabinet_1)": False,
        "open(cabinet_1)": False,
        "ontop(bowl_1, sink_1)": False,
        "reachable(bowl_1)": False,
        "reachable(cabinet_1)": False,
        "reachable(sink_1)": True,
        "holding(bowl_1)": False,
        "ontop(bowl_1, bowl_1)": False,
        "ontop(bowl_1, cabinet_1)": True,
        "nextto(bowl_1, bowl_1)": True,
        "nextto(bowl_1, cabinet_1)": False,
        "nextto(bowl_1, sink_1)": False,
    },
    {
        "inside(bowl_1, cabinet_1)": False,
        "open(cabinet_1)": False,
        "ontop(bowl_1, sink_1)": False,
        "reachable(bowl_1)": False,
        "reachable(cabinet_1)": False,
        "reachable(sink_1)": True,
        "holding(bowl_1)": False,
        "ontop(bowl_1, bowl_1)": False,
        "ontop(bowl_1, cabinet_1)": True,
        "nextto(bowl_1, bowl_1)": True,
        "nextto(bowl_1, cabinet_1)": True,
        "nextto(bowl_1, sink_1)": False,
    },
    {
        "inside(bowl_1, cabinet_1)": False,
        "open(cabinet_1)": False,
        "ontop(bowl_1, sink_1)": False,
        "reachable(bowl_1)": False,
        "reachable(cabinet_1)": False,
        "reachable(sink_1)": True,
        "holding(bowl_1)": False,
        "ontop(bowl_1, bowl_1)": True,
        "ontop(bowl_1, cabinet_1)": False,
        "nextto(bowl_1, bowl_1)": True,
        "nextto(bowl_1, cabinet_1)": False,
        "nextto(bowl_1, sink_1)": False,
    },
    {
        "inside(bowl_1, cabinet_1)": False,
        "open(cabinet_1)": False,
        "ontop(bowl_1, sink_1)": False,
        "reachable(bowl_1)": False,
        "reachable(cabinet_1)": False,
        "reachable(sink_1)": True,
        "holding(bowl_1)": False,
        "ontop(bowl_1, bowl_1)": True,
        "ontop(bowl_1, cabinet_1)": False,
        "nextto(bowl_1, bowl_1)": True,
        "nextto(bowl_1, cabinet_1)": True,
        "nextto(bowl_1, sink_1)": False,
    },
    {
        "inside(bowl_1, cabinet_1)": False,
        "open(cabinet_1)": False,
        "ontop(bowl_1, sink_1)": False,
        "reachable(bowl_1)": False,
        "reachable(cabinet_1)": False,
        "reachable(sink_1)": True,
        "holding(bowl_1)": False,
        "ontop(bowl_1, bowl_1)": True,
        "ontop(bowl_1, cabinet_1)": True,
        "nextto(bowl_1, bowl_1)": True,
        "nextto(bowl_1, cabinet_1)": True,
        "nextto(bowl_1, sink_1)": False,
    },
    {
        "inside(bowl_1, cabinet_1)": False,
        "open(cabinet_1)": True,
        "ontop(bowl_1, sink_1)": False,
        "reachable(bowl_1)": False,
        "reachable(cabinet_1)": False,
        "reachable(sink_1)": True,
        "holding(bowl_1)": False,
        "ontop(bowl_1, bowl_1)": False,
        "ontop(bowl_1, cabinet_1)": False,
        "nextto(bowl_1, bowl_1)": True,
        "nextto(bowl_1, cabinet_1)": False,
        "nextto(bowl_1, sink_1)": False,
    },
    {
        "inside(bowl_1, cabinet_1)": False,
        "open(cabinet_1)": True,
        "ontop(bowl_1, sink_1)": False,
        "reachable(bowl_1)": False,
        "reachable(cabinet_1)": False,
        "reachable(sink_1)": True,
        "holding(bowl_1)": False,
        "ontop(bowl_1, bowl_1)": False,
        "ontop(bowl_1, cabinet_1)": False,
        "nextto(bowl_1, bowl_1)": True,
        "nextto(bowl_1, cabinet_1)": True,
        "nextto(bowl_1, sink_1)": False,
    },
    {
        "inside(bowl_1, cabinet_1)": False,
        "open(cabinet_1)": True,
        "ontop(bowl_1, sink_1)": False,
        "reachable(bowl_1)": False,
        "reachable(cabinet_1)": False,
        "reachable(sink_1)": True,
        "holding(bowl_1)": False,
        "ontop(bowl_1, bowl_1)": False,
        "ontop(bowl_1, cabinet_1)": True,
        "nextto(bowl_1, bowl_1)": True,
        "nextto(bowl_1, cabinet_1)": False,
        "nextto(bowl_1, sink_1)": False,
    },
    {
        "inside(bowl_1, cabinet_1)": False,
        "open(cabinet_1)": True,
        "ontop(bowl_1, sink_1)": False,
        "reachable(bowl_1)": False,
        "reachable(cabinet_1)": False,
        "reachable(sink_1)": True,
        "holding(bowl_1)": False,
        "ontop(bowl_1, bowl_1)": False,
        "ontop(bowl_1, cabinet_1)": True,
        "nextto(bowl_1, bowl_1)": True,
        "nextto(bowl_1, cabinet_1)": True,
        "nextto(bowl_1, sink_1)": False,
    },
    {
        "inside(bowl_1, cabinet_1)": False,
        "open(cabinet_1)": True,
        "ontop(bowl_1, sink_1)": False,
        "reachable(bowl_1)": False,
        "reachable(cabinet_1)": False,
        "reachable(sink_1)": True,
        "holding(bowl_1)": False,
        "ontop(bowl_1, bowl_1)": True,
        "ontop(bowl_1, cabinet_1)": False,
        "nextto(bowl_1, bowl_1)": True,
        "nextto(bowl_1, cabinet_1)": False,
        "nextto(bowl_1, sink_1)": False,
    },
    {
        "inside(bowl_1, cabinet_1)": False,
        "open(cabinet_1)": True,
        "ontop(bowl_1, sink_1)": False,
        "reachable(bowl_1)": False,
        "reachable(cabinet_1)": False,
        "reachable(sink_1)": True,
        "holding(bowl_1)": False,
        "ontop(bowl_1, bowl_1)": True,
        "ontop(bowl_1, cabinet_1)": False,
        "nextto(bowl_1, bowl_1)": True,
        "nextto(bowl_1, cabinet_1)": True,
        "nextto(bowl_1, sink_1)": False,
    },
    {
        "inside(bowl_1, cabinet_1)": False,
        "open(cabinet_1)": True,
        "ontop(bowl_1, sink_1)": False,
        "reachable(bowl_1)": False,
        "reachable(cabinet_1)": False,
        "reachable(sink_1)": True,
        "holding(bowl_1)": False,
        "ontop(bowl_1, bowl_1)": True,
        "ontop(bowl_1, cabinet_1)": True,
        "nextto(bowl_1, bowl_1)": True,
        "nextto(bowl_1, cabinet_1)": False,
        "nextto(bowl_1, sink_1)": False,
    },
    {
        "inside(bowl_1, cabinet_1)": False,
        "open(cabinet_1)": True,
        "ontop(bowl_1, sink_1)": False,
        "reachable(bowl_1)": False,
        "reachable(cabinet_1)": False,
        "reachable(sink_1)": True,
        "holding(bowl_1)": False,
        "ontop(bowl_1, bowl_1)": True,
        "ontop(bowl_1, cabinet_1)": True,
        "nextto(bowl_1, bowl_1)": True,
        "nextto(bowl_1, cabinet_1)": True,
        "nextto(bowl_1, sink_1)": False,
    },
    {
        "inside(bowl_1, cabinet_1)": False,
        "open(cabinet_1)": False,
        "ontop(bowl_1, sink_1)": False,
        "reachable(bowl_1)": False,
        "reachable(cabinet_1)": False,
        "reachable(sink_1)": True,
        "holding(bowl_1)": False,
        "ontop(bowl_1, bowl_1)": True,
        "ontop(bowl_1, cabinet_1)": True,
        "nextto(bowl_1, bowl_1)": True,
        "nextto(bowl_1, cabinet_1)": False,
        "nextto(bowl_1, sink_1)": False,
    },
]

VIPLAN_HH_TRUE_INIT_STATE_STR = {
    "inside(bowl_1, cabinet_1)": True,
    "open(cabinet_1)": False,
    "ontop(bowl_1, sink_1)": False,
    "reachable(bowl_1)": False,
    "reachable(cabinet_1)": False,
    "reachable(sink_1)": True,
    "holding(bowl_1)": False,
    "ontop(bowl_1, bowl_1)": False,
    "ontop(bowl_1, cabinet_1)": False,
    "nextto(bowl_1, bowl_1)": True,
    "nextto(bowl_1, cabinet_1)": False,
    "nextto(bowl_1, sink_1)": False,
}


def _powerset(iterable):
    """Return all subsets of *iterable* (the mathematical powerset).

    Used to generate every possible subset of ViPlan-HH initial states so we can
    verify the compiler produces a valid conformant plan for each one.
    """
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


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
            UPState({reachable(): em.FALSE(), blocked(): em.TRUE()}, problem),   # s1
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
        self.assertEqual(
            str(error.exception),
            "Every element of `possible_initial_states` must be a "
            "`unified_planning.model.State`; found <class 'object'> at index 0.",
        )

        compiler = Ks0Compiler(possible_initial_states=possible_initial_states + (object(),))  # type: ignore[list-item]
        with self.assertRaises(UPUsageError) as error:
            compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        self.assertEqual(
            str(error.exception),
            "Every element of `possible_initial_states` must be a "
            "`unified_planning.model.State`; found <class 'object'> at index 2.",
        )

    def test_compile_rejects_states_from_different_problem(self):
        """States built for a *different* problem must be rejected.  Mixing
        states from unrelated problems would silently produce nonsensical
        K-fluents."""
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
        """States created under a different UP ``Environment`` must be rejected.
        Environment mismatch can cause expression-manager identity issues."""
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
                self.assertGreater(len(back_plan.actions), 0)  # plan is non-trivial

                # Back-converted plan must contain no merge actions
                for ai in back_plan.actions:
                    self.assertFalse(
                        ai.action.name.startswith("merge_"),  # merge actions are internal
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
        """The merge action's effect must set the empty-tag K-fluent to TRUE,
        thereby asserting universal knowledge once all per-state tags agree."""
        _, res = self._compile_basic()
        em = res.problem.environment.expression_manager
        merge_not_blocked = next(
            a for a in res.problem.actions
            if a.name.startswith("merge_") and "not_blocked" in a.name
        )
        effect_fluent_names = {e.fluent.fluent().name for e in merge_not_blocked.effects}
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

        with OneshotPlanner(problem_kind=res.problem.kind) as planner:
            plan_result = planner.solve(res.problem)
        self.assertIsNotNone(plan_result.plan)
        self.assertEqual(
            plan_result.status, PlanGenerationResultStatus.SOLVED_SATISFICING
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

        with OneshotPlanner(problem_kind=res.problem.kind) as planner:
            plan_result = planner.solve(res.problem)
        self.assertIsNotNone(plan_result.plan)

        back_plan = res.plan_back_conversion(plan_result.plan)
        self.assertIsInstance(back_plan, SequentialPlan)
        for ai in back_plan.actions:
            self.assertFalse(
                ai.action.name.startswith("merge_"),  # merge actions are compiler-internal
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

    def _build_viplan_hh_problem_and_possible_states(self):
        """Parse the ViPlan-HH 'cleaning_out_drawers' PDDL domain and build two
        possible initial states representing uncertainty about the bowl's
        location.

        s0: bowl is inside the cabinet.
        s1: bowl is reachable and on top of the sink.

        Returns:
            (Problem, (UPState, UPState))
        """
        test_dir = os.path.dirname(__file__)
        domain_file = os.path.join(test_dir, "pddl", "viplan_hh", "domain.pddl")
        problem_file = os.path.join(
            test_dir, "pddl", "viplan_hh", "cleaning_out_drawers.pddl"
        )
        reader = PDDLReader()
        problem = reader.parse_problem(domain_file, problem_file)
        em = problem.environment.expression_manager

        bowl_1    = problem.object("bowl_1")
        cabinet_1 = problem.object("cabinet_1")
        sink_1    = problem.object("sink_1")
        inside    = problem.fluent("inside")
        reachable = problem.fluent("reachable")
        ontop     = problem.fluent("ontop")

        # s0: bowl is inside the cabinet (must open cabinet first)
        s0 = UPState({inside(bowl_1, cabinet_1): em.TRUE()}, problem)
        # s1: bowl is already reachable and on the sink
        s1 = UPState(
            {reachable(bowl_1): em.TRUE(), ontop(bowl_1, sink_1): em.TRUE()},
            problem,
        )
        return problem, (s0, s1)

    def _str_state_to_upstate(self, problem, str_state_dict):
        """Convert a string-keyed state dict (e.g. from VIPLAN_HH_POSSIBLE_STATES_STR)
        into a :class:`UPState` by parsing each "predicate(arg1, arg2)" key."""
        em = problem.environment.expression_manager
        values = {}
        for pred_str, val in str_state_dict.items():
            # Parse "predicate(arg1, arg2)" into fluent name and object names
            m = re.match(r'(\w+)\(([^)]+)\)', pred_str)
            fluent_name = m.group(1)
            obj_names = [o.strip() for o in m.group(2).split(",")]
            fluent = problem.fluent(fluent_name)
            objs = [problem.object(o) for o in obj_names]
            values[fluent(*objs)] = em.TRUE() if val else em.FALSE()
        return UPState(values, problem)

    def test_viplan_hh_compile_single_possible_initial_state(self):
        """Compiling the ViPlan-HH problem with a single possible state must
        succeed and produce a validly named compiled problem."""
        problem, (s0, _) = self._build_viplan_hh_problem_and_possible_states()
        compiler = Ks0Compiler(possible_initial_states=(s0,))
        res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        self.assertIsInstance(res, CompilerResult)
        self.assertIsNotNone(res.problem)
        self.assertTrue(res.problem.name.startswith("ks0_"))

    def test_viplan_hh_compile_with_uncertainty(self):
        """Compiling with two possible states (uncertainty about bowl location)
        must succeed and produce a valid compiled problem."""
        problem, possible_states = self._build_viplan_hh_problem_and_possible_states()
        compiler = Ks0Compiler(possible_initial_states=possible_states)
        res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        self.assertIsInstance(res, CompilerResult)
        self.assertIsNotNone(res.problem)
        self.assertTrue(res.problem.name.startswith("ks0_"))

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    def test_viplan_hh_full_pipeline_single_state(self):
        """End-to-end ViPlan-HH test with one possible state: compile, solve,
        back-convert, then simulate the plan to verify it reaches the goal.
        Merge actions must not appear in the back-converted plan."""
        problem, (s0, _) = self._build_viplan_hh_problem_and_possible_states()
        with Compiler(
            name="up_ks0_compiler",
            params={"possible_initial_states": (s0,)},
        ) as compiler:
            res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
            compiled_problem = res.problem

        with OneshotPlanner(problem_kind=compiled_problem.kind) as planner:
            plan_result = planner.solve(compiled_problem)

        self.assertIsNotNone(plan_result.plan)
        self.assertEqual(plan_result.status, PlanGenerationResultStatus.SOLVED_SATISFICING)
        back_plan = res.plan_back_conversion(plan_result.plan)
        self.assertIsInstance(back_plan, SequentialPlan)
        for ai in back_plan.actions:
            self.assertFalse(ai.action.name.startswith("merge_"))  # no internal actions

        # Simulate the back-converted plan to verify goal reachability
        sim = UPSequentialSimulator(problem)
        cur_state = sim.get_initial_state()
        for ai in back_plan.actions:
            cur_state = sim.apply(cur_state, ai)
            self.assertIsNotNone(cur_state)
        self.assertTrue(sim.is_goal(cur_state))

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    def test_viplan_hh_full_pipeline_conformant_plan(self):
        """End-to-end ViPlan-HH conformant test: compile with two possible states,
        solve, back-convert, then verify the plan reaches the goal from *every*
        possible initial state (the conformance guarantee)."""
        problem, possible_states = self._build_viplan_hh_problem_and_possible_states()
        with Compiler(
            name="up_ks0_compiler",
            params={"possible_initial_states": possible_states},
        ) as compiler:
            res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
            compiled_problem = res.problem

        with OneshotPlanner(problem_kind=compiled_problem.kind) as planner:
            plan_result = planner.solve(compiled_problem)

        self.assertIsNotNone(plan_result.plan)
        back_plan = res.plan_back_conversion(plan_result.plan)
        self.assertIsInstance(back_plan, SequentialPlan)

        # Verify the plan is truly conformant: reaches the goal from EVERY
        # possible initial state, not just the PDDL default.
        sim = UPSequentialSimulator(problem)
        for i, init_state in enumerate(possible_states):
            cur_state = init_state
            for ai in back_plan.actions:
                cur_state = sim.apply(cur_state, ai)
                self.assertIsNotNone(
                    cur_state,
                    f"Action {ai} not applicable from initial state {i}",
                )
            self.assertTrue(
                sim.is_goal(cur_state),
                f"Plan does not reach goal from initial state {i}",
            )

    @skipIfNoOneshotPlannerForProblemKind(classical_kind)
    def test_subsets_of_viplan_hh_initial_states(self):
        """Stress test: for many subsets of the 16 ViPlan-HH possible states
        (plus the true initial state), compile, solve, and verify that the
        resulting plan is valid from both the PDDL initial state and every
        possible initial state in the subset.

        Uses the first and last 200 elements of the powerset to cover small
        and large subsets without exhaustively enumerating all 2^16 = 65536."""
        test_dir = os.path.dirname(__file__)
        domain_file = os.path.join(test_dir, "pddl", "viplan_hh", "domain.pddl")
        problem_file = os.path.join(
            test_dir, "pddl", "viplan_hh", "cleaning_out_drawers.pddl"
        )
        reader = PDDLReader()
        problem = reader.parse_problem(domain_file, problem_file)

        # Build subsets from both ends of the powerset to cover edge cases
        # (empty/small subsets and large subsets) without full enumeration.
        subsets = (
            list(_powerset(VIPLAN_HH_POSSIBLE_STATES_STR))[:200]
            + list(_powerset(VIPLAN_HH_POSSIBLE_STATES_STR))[-200:]
        )

        for subset in subsets:
            with self.subTest(subset=subset):
                # Always include the true initial state so the plan is grounded
                states_str = list(subset) + [VIPLAN_HH_TRUE_INIT_STATE_STR]
                states = tuple(
                    self._str_state_to_upstate(problem, d) for d in states_str
                )

                # Compile the conformant problem to a classical one
                compiler = Ks0Compiler(possible_initial_states=states)
                res = compiler.compile(problem, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
                compiled_problem = res.problem

                with OneshotPlanner(problem_kind=compiled_problem.kind) as planner:
                    plan_result = planner.solve(compiled_problem)

                # A plan must exist for every tested subset
                self.assertIsNotNone(
                    plan_result.plan,
                    f"No plan found for subset:\n{subset}",
                )
                back_plan = res.plan_back_conversion(plan_result.plan)
                self.assertIsInstance(back_plan, SequentialPlan)

                # Validate against the PDDL-defined initial state
                sim = UPSequentialSimulator(problem)
                cur_state = sim.get_initial_state()
                for ai in back_plan.actions:
                    cur_state = sim.apply(cur_state, ai)
                    self.assertIsNotNone(cur_state)
                self.assertTrue(
                    sim.is_goal(cur_state),
                    f"Plan doesn't reach goal! subset:\n{subset}",
                )

                # Verify conformance: plan must work from EVERY possible state
                for i, init_state in enumerate(states):
                    cur_state = init_state
                    for ai in back_plan.actions:
                        cur_state = sim.apply(cur_state, ai)
                        self.assertIsNotNone(
                            cur_state,
                            f"Action {ai} not applicable from state {i}, subset:\n{subset}",
                        )
                    self.assertTrue(
                        sim.is_goal(cur_state),
                        f"Didn't reach goal from state {i}, subset:\n{subset}",
                    )
