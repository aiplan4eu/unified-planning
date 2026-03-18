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
#


from io import StringIO
import unified_planning as up
from unified_planning.shortcuts import *
from unified_planning.engines import PlanGenerationResultStatus
from unified_planning.test import unittest_TestCase, main, skipIfEngineNotAvailable
from unified_planning.test.examples import get_example_problems

import os
import tempfile
from queue import Empty, Queue
from typing import List, Optional
from unittest.mock import MagicMock, patch

from unified_planning.engines.pddl_anytime_planner import PDDLAnytimePlanner, Writer
from unified_planning.engines.pddl_planner import PDDLPlanner
from unified_planning.engines.results import LogMessage
from unified_planning.io import PDDLWriter
from unified_planning.model import ProblemKind

VERYSMALL_TIMEOUT = 0.0001


# ---------------------------------------------------------------------------
# Helpers for race condition tests
# ---------------------------------------------------------------------------


class _StubAnytimePlanner(PDDLAnytimePlanner):
    """Bare-minimum PDDLAnytimePlanner that never launches a subprocess."""

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

    def _starting_plan_str(self) -> str:
        return "Plan found!"

    def _ending_plan_str(self) -> str:
        return "end-of-plan"

    def _parse_plan_line(self, plan_line: str) -> str:
        return "(%s)" % plan_line.split("(")[0].strip()


class _StubOneshotPlanner(PDDLPlanner):
    """PDDLPlanner subclass that returns a no-op command."""

    @property
    def name(self) -> str:
        return "stub-oneshot"

    def _get_cmd(self, _domain: str, _problem: str, _plan: str) -> List[str]:
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


def _make_navigation_problem() -> Problem:
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


def _make_painting_problem() -> Problem:
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


def _make_writer_with_renamings(problem: Problem) -> PDDLWriter:
    """Create a PDDLWriter and force it to populate its nto_renamings."""
    writer = PDDLWriter(problem)
    with tempfile.TemporaryDirectory() as tmpdir:
        writer.write_domain(os.path.join(tmpdir, "domain.pddl"))
        writer.write_problem(os.path.join(tmpdir, "problem.pddl"))
    return writer


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
    proc = MagicMock()
    proc.communicate.return_value = (b"", b"")
    proc.returncode = 0
    return proc


class TestPDDLPlanner(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_basic(self):
        problem = self.problems["basic"].problem
        a = problem.action("a")

        with OneshotPlanner(name="opt-pddl-planner") as planner:
            self.assertNotEqual(planner, None)

            final_report = planner.solve(problem)
            plan = final_report.plan
            self.assertEqual(
                final_report.status, PlanGenerationResultStatus.SOLVED_OPTIMALLY
            )
            self.assertEqual(len(plan.actions), 1)
            self.assertEqual(plan.actions[0].action, a)
            self.assertEqual(len(plan.actions[0].actual_parameters), 0)

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_basic_conditional(self):
        problem = self.problems["basic_conditional"].problem
        a_x = problem.action("a_x")
        a_y = problem.action("a_y")

        with OneshotPlanner(name="opt-pddl-planner") as planner:
            self.assertNotEqual(planner, None)

            final_report = planner.solve(problem)
            plan = final_report.plan
            self.assertEqual(
                final_report.status, PlanGenerationResultStatus.SOLVED_OPTIMALLY
            )
            self.assertEqual(len(plan.actions), 2)
            self.assertEqual(plan.actions[0].action, a_y)
            self.assertEqual(plan.actions[1].action, a_x)
            self.assertEqual(len(plan.actions[0].actual_parameters), 0)
            self.assertEqual(len(plan.actions[1].actual_parameters), 0)

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_robot_decrease(self):
        problem = self.problems["robot_decrease"].problem
        move = problem.action("move")

        with OneshotPlanner(name="opt-pddl-planner") as planner:
            self.assertNotEqual(planner, None)

            final_report = planner.solve(problem)
            plan = final_report.plan
            self.assertEqual(
                final_report.status, PlanGenerationResultStatus.SOLVED_OPTIMALLY
            )
            self.assertNotEqual(plan, None)
            self.assertEqual(len(plan.actions), 1)
            self.assertEqual(plan.actions[0].action, move)
            self.assertEqual(len(plan.actions[0].actual_parameters), 2)

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_robot_loader(self):
        problem = self.problems["robot_loader"].problem
        move = problem.action("move")
        load = problem.action("load")
        unload = problem.action("unload")

        with OneshotPlanner(name="opt-pddl-planner") as planner:
            self.assertNotEqual(planner, None)

            final_report = planner.solve(problem)
            plan = final_report.plan
            self.assertEqual(
                final_report.status, PlanGenerationResultStatus.SOLVED_OPTIMALLY
            )
            self.assertEqual(len(plan.actions), 4)
            self.assertEqual(plan.actions[0].action, move)
            self.assertEqual(plan.actions[1].action, load)
            self.assertEqual(plan.actions[2].action, move)
            self.assertEqual(plan.actions[3].action, unload)
            self.assertEqual(len(plan.actions[0].actual_parameters), 2)
            self.assertEqual(len(plan.actions[1].actual_parameters), 1)
            self.assertEqual(len(plan.actions[2].actual_parameters), 2)
            self.assertEqual(len(plan.actions[3].actual_parameters), 1)

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_robot_loader_adv(self):
        problem = self.problems["robot_loader_adv"].problem
        move = problem.action("move")
        load = problem.action("load")
        unload = problem.action("unload")

        with OneshotPlanner(name="opt-pddl-planner") as planner:
            self.assertNotEqual(planner, None)
            output = StringIO()
            final_report = planner.solve(problem, output_stream=output)
            plan = final_report.plan
            planner_output = output.getvalue()
            self.assertEqual(
                final_report.status, PlanGenerationResultStatus.SOLVED_OPTIMALLY
            )
            self.assertEqual(len(plan.actions), 5)
            self.assertEqual(plan.actions[0].action, move)
            self.assertEqual(plan.actions[1].action, load)
            self.assertEqual(plan.actions[2].action, move)
            self.assertEqual(plan.actions[3].action, unload)
            self.assertEqual(plan.actions[4].action, move)
            self.assertEqual(len(plan.actions[0].actual_parameters), 3)
            self.assertEqual(len(plan.actions[1].actual_parameters), 3)
            self.assertEqual(len(plan.actions[2].actual_parameters), 3)
            self.assertEqual(len(plan.actions[3].actual_parameters), 3)
            self.assertEqual(len(plan.actions[4].actual_parameters), 3)

            self.assertIn("Domain parsed\nProblem parsed", planner_output)
            self.assertIn("Problem Solved", planner_output)
            self.assertIn("Found Plan", planner_output)
            self.assertIn("Heuristic Time (msec):", planner_output)
            self.assertIn("Search Time (msec):", planner_output)
            self.assertIn("Expanded Nodes:", planner_output)

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_robot_loader_adv_with_timeout(self):
        problem, right_plan = (
            self.problems["robot_loader_adv"].problem,
            self.problems["robot_loader_adv"].valid_plans[0],
        )
        with OneshotPlanner(name="opt-pddl-planner") as planner:
            self.assertNotEqual(planner, None)

            final_report = planner.solve(problem, timeout=VERYSMALL_TIMEOUT)
            self.assertIn(
                final_report.status,
                [
                    PlanGenerationResultStatus.TIMEOUT,
                    PlanGenerationResultStatus.SOLVED_OPTIMALLY,
                ],
            )  # It could happen that the PDDL planner manages to solve the problem
            self.assertTrue(
                final_report.plan is None or final_report.plan == right_plan
            )

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_robot_loader_adv_with_long_timeout(self):
        problem = self.problems["robot_loader_adv"].problem
        move = problem.action("move")
        load = problem.action("load")
        unload = problem.action("unload")
        with OneshotPlanner(name="opt-pddl-planner") as planner:
            self.assertNotEqual(planner, None)

            final_report = planner.solve(problem, timeout=100)
            plan = final_report.plan
            self.assertEqual(
                final_report.status, PlanGenerationResultStatus.SOLVED_OPTIMALLY
            )
            self.assertEqual(len(plan.actions), 5)
            self.assertEqual(plan.actions[0].action, move)
            self.assertEqual(plan.actions[1].action, load)
            self.assertEqual(plan.actions[2].action, move)
            self.assertEqual(plan.actions[3].action, unload)
            self.assertEqual(plan.actions[4].action, move)
            self.assertEqual(len(plan.actions[0].actual_parameters), 3)
            self.assertEqual(len(plan.actions[1].actual_parameters), 3)
            self.assertEqual(len(plan.actions[2].actual_parameters), 3)
            self.assertEqual(len(plan.actions[3].actual_parameters), 3)
            self.assertEqual(len(plan.actions[4].actual_parameters), 3)

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_robot_loader_adv_with_long_timeout_and_output_stream(self):
        problem = self.problems["robot_loader_adv"].problem
        move = problem.action("move")
        load = problem.action("load")
        unload = problem.action("unload")
        output_stream = StringIO()
        with OneshotPlanner(name="opt-pddl-planner") as planner:
            self.assertNotEqual(planner, None)

            final_report = planner.solve(
                problem, timeout=100, output_stream=output_stream
            )
            plan = final_report.plan
            planner_output = output_stream.getvalue()
            self.assertEqual(
                final_report.status, PlanGenerationResultStatus.SOLVED_OPTIMALLY
            )
            self.assertEqual(len(plan.actions), 5)
            self.assertEqual(plan.actions[0].action, move)
            self.assertEqual(plan.actions[1].action, load)
            self.assertEqual(plan.actions[2].action, move)
            self.assertEqual(plan.actions[3].action, unload)
            self.assertEqual(plan.actions[4].action, move)
            self.assertEqual(len(plan.actions[0].actual_parameters), 3)
            self.assertEqual(len(plan.actions[1].actual_parameters), 3)
            self.assertEqual(len(plan.actions[2].actual_parameters), 3)
            self.assertEqual(len(plan.actions[3].actual_parameters), 3)
            self.assertEqual(len(plan.actions[4].actual_parameters), 3)

            self.assertIn("Domain parsed\nProblem parsed", planner_output)
            self.assertIn("Problem Solved", planner_output)
            self.assertIn("Found Plan", planner_output)
            self.assertIn("Heuristic Time (msec):", planner_output)
            self.assertIn("Search Time (msec):", planner_output)
            self.assertIn("Expanded Nodes:", planner_output)

            for lm in final_report.log_messages:
                if lm.level == up.engines.LogLevel.INFO:
                    self.assertEqual(planner_output, lm.message)
                else:
                    self.assertEqual(lm.level, up.engines.LogLevel.ERROR)
                    self.assertEqual(lm.message, "")

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_robot_loader_adv_with_short_timeout_and_output_stream(self):
        problem, right_plan = (
            self.problems["robot_loader_adv"].problem,
            self.problems["robot_loader_adv"].valid_plans[0],
        )
        output_stream = StringIO()
        with OneshotPlanner(name="opt-pddl-planner") as planner:
            self.assertNotEqual(planner, None)

            final_report = planner.solve(
                problem, timeout=VERYSMALL_TIMEOUT, output_stream=output_stream
            )
            plan = final_report.plan
            planner_output = output_stream.getvalue()
            self.assertTrue(plan is None or plan == right_plan)

            for lm in final_report.log_messages:
                if lm.level == up.engines.LogLevel.INFO:
                    self.assertEqual(planner_output, lm.message)
                else:
                    self.assertEqual(lm.level, up.engines.LogLevel.ERROR)
                    self.assertEqual(lm.message, "")

    # -----------------------------------------------------------------------
    # Race 1: self._writer cross-contamination
    # -----------------------------------------------------------------------

    def test_writer_cross_contamination_anytime_path(self):
        """
        Simulates the race condition on the stdout-parsing (anytime) path.

        self._writer is set for Problem B while _parse_planner_output is
        processing Problem A's planner stdout.  The fix stores a per-solve
        pddl_writer on the Writer object so _parse_planner_output uses
        writer_a.pddl_writer (Problem A's namespace) instead of self._writer.
        """
        problem_a = _make_navigation_problem()
        problem_b = _make_painting_problem()

        planner = _StubAnytimePlanner()
        planner._writer = _make_writer_with_renamings(problem_b)

        q: Queue = Queue()
        writer_a = Writer(None, q, planner, problem_a)
        writer_a.pddl_writer = _make_writer_with_renamings(problem_a)

        planner._parse_planner_output(writer_a, "Plan found!\n")
        planner._parse_planner_output(writer_a, "move l1 l2 (1)\n")
        planner._parse_planner_output(writer_a, "end-of-plan\n")

        try:
            result = q.get_nowait()
        except Empty:
            self.fail("No plan result was produced by _parse_planner_output")

        self.assertIsNotNone(result.plan, "Parsed plan must not be None")
        self.assertEqual(len(result.plan.actions), 1)
        self.assertEqual(result.plan.actions[0].action.name, "move")

    def test_writer_cross_contamination_file_path(self):
        """
        Verifies that _solve() attaches the per-solve PDDLWriter to
        output_stream.pddl_writer (when output_stream is a Writer).
        """
        problem_a = _make_navigation_problem()
        problem_b = _make_painting_problem()

        planner = _StubAnytimePlanner()

        q: Queue = Queue()
        writer_a = Writer(None, q, planner, problem_a)

        planner._get_cmd = lambda domain, problem, plan: ["true"]
        with patch("unified_planning.engines.pddl_planner.run_command") as mock_run:
            mock_run.return_value = (False, ([], []), 0)
            planner._solve(problem_a, output_stream=writer_a)

        self.assertIsNotNone(
            getattr(writer_a, "pddl_writer", None),
            "_solve() must attach pddl_writer to the Writer output_stream",
        )

        planner._writer = _make_writer_with_renamings(problem_b)
        item = writer_a.pddl_writer.get_item_named("move")
        self.assertEqual(item.name, "move")

    # -----------------------------------------------------------------------
    # Race 2: shared output.sas CWD
    # -----------------------------------------------------------------------

    def test_popen_receives_non_none_cwd(self):
        """subprocess.Popen must be called with an explicit cwd, not None."""
        problem = _make_trivial_problem()
        planner = _StubOneshotPlanner()

        captured_cwd: List = []

        def mock_popen(_cmd, *_args, **kwargs):
            captured_cwd.append(kwargs.get("cwd", None))
            return _make_mock_process()

        with patch(
            "unified_planning.engines.pddl_planner.subprocess.Popen",
            side_effect=mock_popen,
        ):
            planner._solve(problem)

        self.assertEqual(len(captured_cwd), 1, "Expected exactly one Popen call")
        self.assertIsNotNone(
            captured_cwd[0],
            "subprocess.Popen was called without cwd; "
            "FD would write output.sas to the shared repo-root CWD",
        )

    def test_popen_cwd_differs_from_process_cwd(self):
        """The cwd passed to Popen must be a distinct absolute path from the runner CWD."""
        problem = _make_trivial_problem()
        planner = _StubOneshotPlanner()

        captured_cwd: List = []

        def mock_popen(_cmd, *_args, **kwargs):
            captured_cwd.append(kwargs.get("cwd", None))
            return _make_mock_process()

        with patch(
            "unified_planning.engines.pddl_planner.subprocess.Popen",
            side_effect=mock_popen,
        ):
            planner._solve(problem)

        cwd = captured_cwd[0]
        self.assertIsNotNone(cwd, "Popen received no cwd")
        self.assertTrue(
            os.path.isabs(cwd), f"Popen cwd {cwd!r} is not an absolute path"
        )
        self.assertNotEqual(
            cwd,
            os.getcwd(),
            f"Popen cwd ({cwd!r}) equals runner CWD; output.sas would collide",
        )

    def test_popen_cwd_is_the_per_solve_tempdir(self):
        """The cwd passed to Popen must be the same directory as the PDDL files."""
        problem = _make_trivial_problem()
        planner = _StubOneshotPlanner()

        captured_cwd: List = []
        captured_domain_dir: List = []

        original_get_cmd = planner._get_cmd

        def intercepting_get_cmd(domain_filename, _problem, _plan):
            captured_domain_dir.append(
                os.path.dirname(os.path.abspath(domain_filename))
            )
            return original_get_cmd(domain_filename, _problem, _plan)

        planner._get_cmd = intercepting_get_cmd

        def mock_popen(_cmd, *_args, **kwargs):
            captured_cwd.append(kwargs.get("cwd", None))
            return _make_mock_process()

        with patch(
            "unified_planning.engines.pddl_planner.subprocess.Popen",
            side_effect=mock_popen,
        ):
            planner._solve(problem)

        self.assertIsNotNone(captured_cwd[0], "Popen received no cwd")
        self.assertEqual(
            os.path.abspath(captured_cwd[0]),
            captured_domain_dir[0],
            f"Popen cwd ({captured_cwd[0]!r}) is not the per-solve tempdir "
            f"({captured_domain_dir[0]!r}); output.sas would land in the wrong place",
        )
