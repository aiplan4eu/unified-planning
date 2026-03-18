"""
Regression tests for two PDDLPlanner race conditions.

--- Race 1: self._writer cross-contamination (fixed in 62b035e3) ---

PDDLPlanner stores per-solve mutable state (self._writer, self._process) as
instance attributes.  When the same planner instance handles concurrent or
overlapping solves, a subsequent _solve() call overwrites self._writer,
causing _parse_planner_output (and _plan_from_file) to resolve plan action
names against the WRONG problem's naming map:

    UPException: The name <action> does not correspond to any item.

--- Race 2: shared output.sas CWD (fixed in 0377262c) ---

PDDLPlanner._solve() creates a per-invocation TemporaryDirectory for PDDL
files but previously called run_command() without a cwd argument.  Every
subprocess.Popen() therefore inherited the pytest runner's working directory
(typically the repo root).  Fast Downward writes its intermediate SAS file
as the relative path "output.sas", so concurrent or sequential FD invocations
collided on the same $REPO_ROOT/output.sas.  The fix passes cwd=tempdir to
run_command(), isolating each invocation in its own temporary directory.
"""

import os
import tempfile
from queue import Empty, Queue
from typing import List, Optional
from unittest.mock import MagicMock, patch

import pytest

import unified_planning as up
from unified_planning.engines.pddl_anytime_planner import PDDLAnytimePlanner, Writer
from unified_planning.engines.pddl_planner import PDDLPlanner
from unified_planning.engines.results import (
    LogMessage,
    PlanGenerationResultStatus,
)
from unified_planning.io import PDDLWriter
from unified_planning.model import ProblemKind
from unified_planning.shortcuts import (
    BoolType,
    Fluent,
    InstantaneousAction,
    Not,
    Object,
    Problem,
    UserType,
)


# ---------------------------------------------------------------------------
# Minimal concrete PDDLAnytimePlanner — no external engine required
# ---------------------------------------------------------------------------

class _StubAnytimePlanner(PDDLAnytimePlanner):
    """
    Bare-minimum implementation of PDDLAnytimePlanner that never actually
    launches a subprocess.  Only the stdout-parsing machinery is exercised.
    """

    @property
    def name(self) -> str:
        return "stub-anytime"

    def _get_cmd(
        self, domain_filename: str, problem_filename: str, plan_filename: str
    ) -> List[str]:
        raise NotImplementedError("stub — not meant to run a real solver")

    def _get_anytime_cmd(
        self, domain_filename: str, problem_filename: str, plan_filename: str
    ) -> List[str]:
        raise NotImplementedError("stub — not meant to run a real solver")

    def _result_status(
        self,
        problem: "up.model.Problem",
        plan: Optional["up.plans.Plan"],
        retval: int = 0,
        log_messages: Optional[List[LogMessage]] = None,
    ) -> PlanGenerationResultStatus:
        if plan is not None:
            return PlanGenerationResultStatus.SOLVED_SATISFICING
        return PlanGenerationResultStatus.INTERNAL_ERROR

    @staticmethod
    def supported_kind() -> "up.model.ProblemKind":
        supported_kind = up.model.ProblemKind(version=2)
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        return supported_kind

    @staticmethod
    def supports(problem_kind: "up.model.ProblemKind") -> bool:
        return problem_kind <= _StubAnytimePlanner.supported_kind()

    # -- stdout parsing markers (generic; same pattern as Fast Downward) --

    def _starting_plan_str(self) -> str:
        return "Plan found!"

    def _ending_plan_str(self) -> str:
        return "end-of-plan"

    def _parse_plan_line(self, plan_line: str) -> str:
        # Expect lines like "action_name p1 p2 (cost)" — strip cost, wrap.
        return "(%s)" % plan_line.split("(")[0].strip()


# ---------------------------------------------------------------------------
# Two minimal problems with disjoint action vocabularies
# ---------------------------------------------------------------------------

def _make_navigation_problem():
    """Domain A — a single 'move' action over Location objects."""
    problem = Problem("navigation")
    Location = UserType("Location")
    at = Fluent("at", BoolType(), loc=Location)

    move = InstantaneousAction("move", l_from=Location, l_to=Location)
    l_from = move.parameter("l_from")
    l_to = move.parameter("l_to")
    move.add_precondition(at(l_from))
    move.add_precondition(Not(at(l_to)))
    move.add_effect(at(l_from), False)
    move.add_effect(at(l_to), True)

    problem.add_fluent(at, default_initial_value=False)
    problem.add_action(move)
    l1 = Object("l1", Location)
    l2 = Object("l2", Location)
    problem.add_objects([l1, l2])
    problem.set_initial_value(at(l1), True)
    problem.add_goal(at(l2))
    return problem


def _make_painting_problem():
    """Domain B — a single 'paint' action over Color objects."""
    problem = Problem("painting")
    Color = UserType("Color")
    painted = Fluent("painted", BoolType(), c=Color)

    paint = InstantaneousAction("paint", c=Color)
    c = paint.parameter("c")
    paint.add_precondition(Not(painted(c)))
    paint.add_effect(painted(c), True)

    problem.add_fluent(painted, default_initial_value=False)
    problem.add_action(paint)
    red = Object("red", Color)
    problem.add_object(red)
    problem.add_goal(painted(red))
    return problem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_writer_with_renamings(problem: Problem) -> PDDLWriter:
    """Create a PDDLWriter and force it to populate its nto_renamings."""
    writer = PDDLWriter(problem)
    with tempfile.TemporaryDirectory() as tmpdir:
        writer.write_domain(os.path.join(tmpdir, "domain.pddl"))
        writer.write_problem(os.path.join(tmpdir, "problem.pddl"))
    return writer


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_writer_cross_contamination_anytime_path():
    """
    Simulates the race condition on the stdout-parsing (anytime) path.

    self._writer is set for Problem B while _parse_planner_output is
    processing Problem A's planner stdout.

    Expected (correct) behaviour:
        The plan "(move l1 l2)" is parsed using Problem A's namespace,
        producing a valid one-action SequentialPlan.

    Actual behaviour (the bug):
        self._writer belongs to Problem B, so get_item_named("move")
        raises UPException, and the test fails.
    """
    problem_a = _make_navigation_problem()
    problem_b = _make_painting_problem()

    planner = _StubAnytimePlanner()

    # --- set self._writer to Problem B's PDDLWriter (the "wrong" one) ---
    planner._writer = _make_writer_with_renamings(problem_b)

    # --- create a Writer for Problem A (the "in-flight" solve) ---
    q: Queue = Queue()
    writer_a = Writer(None, q, planner, problem_a)
    # The fixed _solve() stores the per-solve writer on the Writer object,
    # so _parse_planner_output uses writer_a.pddl_writer (Problem A's namespace)
    # instead of self._writer (Problem B's namespace).
    writer_a.pddl_writer = _make_writer_with_renamings(problem_a)

    # --- feed planner stdout for Problem A's solution, line by line ---
    # _parse_planner_output detects start/end markers and collects action
    # lines in between via _parse_plan_line.
    planner._parse_planner_output(writer_a, "Plan found!\n")
    planner._parse_planner_output(writer_a, "move l1 l2 (1)\n")

    # The end marker triggers plan parsing: _plan_from_str is called with
    # self._writer.get_item_named  →  Problem B's writer  →  no "move"
    # in that namespace  →  UPException.
    planner._parse_planner_output(writer_a, "end-of-plan\n")

    # --- verify the result (only reachable if the bug is absent) ---
    try:
        result = q.get_nowait()
    except Empty:
        pytest.fail("No plan result was produced by _parse_planner_output")

    assert result.plan is not None, "Parsed plan must not be None"
    assert len(result.plan.actions) == 1, (
        f"Expected 1 action, got {len(result.plan.actions)}"
    )
    assert result.plan.actions[0].action.name == "move", (
        f"Expected action 'move', got '{result.plan.actions[0].action.name}'"
    )


def test_writer_cross_contamination_file_path():
    """
    Verifies that _solve() attaches the per-solve PDDLWriter to
    output_stream.pddl_writer (when output_stream is a Writer), so that
    concurrent overwrites of self._writer cannot corrupt plan parsing.

    Expected (correct) behaviour after the fix:
        _solve() sets output_stream.pddl_writer = pddl_writer (local variable).
        Even after self._writer is overwritten (race), the per-Writer reference
        survives and resolves Problem A's actions correctly.

    Actual behaviour (the bug):
        _solve() only sets self._writer = pddl_writer, never touching the
        Writer object.  No per-solve reference exists, so _parse_planner_output
        and _plan_from_file both fall back to self._writer — which may be
        overwritten by a concurrent solve.
    """
    problem_a = _make_navigation_problem()
    problem_b = _make_painting_problem()

    planner = _StubAnytimePlanner()

    # Create a Writer as output_stream, exactly as _get_solutions does.
    q: Queue = Queue()
    writer_a = Writer(None, q, planner, problem_a)

    # Provide a stub _get_cmd (the stub class raises NotImplementedError) and
    # mock run_command so no subprocess is launched.
    planner._get_cmd = lambda domain, problem, plan: ["true"]
    with patch("unified_planning.engines.pddl_planner.run_command") as mock_run:
        mock_run.return_value = (False, ([], []), 0)
        planner._solve(problem_a, output_stream=writer_a)

    # After the fix: _solve() must have set writer_a.pddl_writer to
    # problem_a's PDDLWriter.  Without the fix, Writer.__init__ never
    # initialises pddl_writer and _solve() never sets it, so the attribute
    # is absent (or None).
    assert getattr(writer_a, "pddl_writer", None) is not None, (
        "_solve() must attach pddl_writer to the Writer output_stream "
        "(required for the race-condition fix)"
    )

    # Simulate the race: another concurrent solve overwrites self._writer.
    planner._writer = _make_writer_with_renamings(problem_b)

    # The per-Writer reference must still resolve Problem A's actions.
    item = writer_a.pddl_writer.get_item_named("move")
    assert item.name == "move", (
        f"writer_a.pddl_writer should resolve problem_a's 'move'; got '{item.name}'"
    )


# ---------------------------------------------------------------------------
# Race 2: shared output.sas CWD
# ---------------------------------------------------------------------------

class _StubOneshotPlanner(PDDLPlanner):
    """PDDLPlanner subclass that returns a no-op command.
    subprocess.Popen is patched in every test, so the command never runs."""

    @property
    def name(self) -> str:
        return "stub-oneshot"

    def _get_cmd(
        self, _domain: str, _problem: str, _plan: str
    ) -> List[str]:
        return ["true"]

    def _result_status(
        self,
        _problem: "up.model.Problem",
        _plan: Optional["up.plans.Plan"],
        _retval: int = 0,
        _log_messages: Optional[List[LogMessage]] = None,
    ) -> PlanGenerationResultStatus:
        return PlanGenerationResultStatus.UNSOLVABLE_PROVEN

    @staticmethod
    def supported_kind() -> ProblemKind:
        k = up.model.ProblemKind(version=2)
        k.set_problem_class("ACTION_BASED")
        k.set_typing("FLAT_TYPING")
        return k

    @staticmethod
    def supports(problem_kind: ProblemKind) -> bool:
        return problem_kind <= _StubOneshotPlanner.supported_kind()


def _make_trivial_problem() -> Problem:
    problem = Problem("trivial")
    done = Fluent("done")
    problem.add_fluent(done, default_initial_value=False)
    finish = InstantaneousAction("finish")
    finish.add_effect(done, True)
    problem.add_action(finish)
    problem.add_goal(done)
    return problem


def _make_mock_process() -> MagicMock:
    """Return a MagicMock that satisfies PDDLPlanner's use of the Popen object."""
    proc = MagicMock()
    proc.communicate.return_value = (b"", b"")
    proc.returncode = 0
    return proc


def test_popen_receives_non_none_cwd():
    """subprocess.Popen must be called with an explicit cwd, not None.

    Before the fix: run_command() was called without cwd, so Popen inherited
    the process CWD.  kwargs.get("cwd", None) returned None → assertion fails.
    After the fix: cwd=tempdir is forwarded all the way to Popen → not None.
    """
    problem = _make_trivial_problem()
    planner = _StubOneshotPlanner()

    captured_cwd: List = []

    def mock_popen(_cmd, *_args, **kwargs):
        captured_cwd.append(kwargs.get("cwd", None))
        return _make_mock_process()

    with patch("unified_planning.engines.pddl_planner.subprocess.Popen",
               side_effect=mock_popen):
        planner._solve(problem)

    assert len(captured_cwd) == 1, "Expected exactly one Popen call"
    assert captured_cwd[0] is not None, (
        "subprocess.Popen was called without cwd; "
        "FD would write output.sas to the shared repo-root CWD"
    )


def test_popen_cwd_differs_from_process_cwd():
    """The cwd passed to Popen must be an explicit path different from the
    test runner's working directory.

    Before the fix: no cwd is passed (cwd=None), so Popen silently inherits
    os.getcwd() — the assertion fails because cwd is None rather than a path.
    After the fix: cwd is the per-solve TemporaryDirectory, which is a real
    absolute path distinct from the runner CWD.
    """
    problem = _make_trivial_problem()
    planner = _StubOneshotPlanner()

    captured_cwd: List = []

    def mock_popen(_cmd, *_args, **kwargs):
        captured_cwd.append(kwargs.get("cwd", None))
        return _make_mock_process()

    with patch("unified_planning.engines.pddl_planner.subprocess.Popen",
               side_effect=mock_popen):
        planner._solve(problem)

    cwd = captured_cwd[0]
    assert cwd is not None and os.path.isabs(cwd) and cwd != os.getcwd(), (
        f"Popen cwd ({cwd!r}) is not a distinct absolute path from the runner "
        f"CWD ({os.getcwd()!r}); output.sas would land in the shared directory"
    )


def test_popen_cwd_is_the_per_solve_tempdir():
    """The cwd passed to Popen must be the same directory as the PDDL files.

    _solve() creates one TemporaryDirectory and uses it for domain.pddl,
    problem.pddl, and plan.txt.  The cwd forwarded to Popen must be that same
    directory, so that output.sas lands beside the other per-solve files.

    Before the fix: cwd is None (no cwd passed) → assertion fails.
    After the fix: cwd == os.path.dirname(domain_filename).
    """
    problem = _make_trivial_problem()
    planner = _StubOneshotPlanner()

    captured_cwd: List = []
    captured_domain_dir: List = []

    original_get_cmd = planner._get_cmd

    def intercepting_get_cmd(domain_filename, _problem, _plan):
        captured_domain_dir.append(os.path.dirname(os.path.abspath(domain_filename)))
        return original_get_cmd(domain_filename, _problem, _plan)

    planner._get_cmd = intercepting_get_cmd

    def mock_popen(_cmd, *_args, **kwargs):
        captured_cwd.append(kwargs.get("cwd", None))
        return _make_mock_process()

    with patch("unified_planning.engines.pddl_planner.subprocess.Popen",
               side_effect=mock_popen):
        planner._solve(problem)

    assert captured_cwd[0] is not None, "Popen received no cwd"
    assert os.path.abspath(captured_cwd[0]) == captured_domain_dir[0], (
        f"Popen cwd ({captured_cwd[0]!r}) is not the per-solve tempdir "
        f"({captured_domain_dir[0]!r}); output.sas would land in the wrong place"
    )
