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
"""This module defines an interface for a generic PDDL planner."""

from abc import abstractmethod
import os
from queue import Queue
from typing import IO, Callable, Iterator, Optional, List, Tuple, Union, cast
import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.engine import OperationMode
import unified_planning.engines.mixins as mixins
from unified_planning.engines.results import (
    PlanGenerationResult,
    PlanGenerationResultStatus,
)
from unified_planning.io import PDDLWriter
from unified_planning.plans import Plan

# This module implements two different mechanisms to execute a PDDL planner in a
# subprocess, processing the output in real-time and imposing a timeout.
# The first one uses the "select" module to process the output and error streams
# while the subprocess is running. This method does not require multi-threading
# as it relies on the POSIX select to monitor multiple streams. Unfortunately,
# this method does not work in Windows because the select function only works
# with sockets. So, a second implementation uses asyncio futures to deal with
# the parallelism. This second method also has a limitation: it does not work in
# an environment that already uses asyncio (most notably in a google colab or in
# a python notebook).
#
# By default, on non-Windows OSs we use the first method and on Windows we
# always use the second. It is possible to use asyncio under unix by setting
# the environment variable UP_USE_ASYNCIO_PDDL_PLANNER to true.
USE_ASYNCIO_ON_UNIX = False
ENV_USE_ASYNCIO = os.environ.get("UP_USE_ASYNCIO_PDDL_PLANNER")
if ENV_USE_ASYNCIO is not None:
    USE_ASYNCIO_ON_UNIX = ENV_USE_ASYNCIO.lower() in ["true", "1"]


class Writer(up.AnyBaseClass):
    def __init__(self, output_stream, res_queue, engine, problem):
        self._output_stream: IO[str] = output_stream
        self._engine: "PDDLAnytimePlanner" = engine
        self.problem = problem
        self.current_plan: List[str] = []
        self.storing: bool = False
        self.res_queue: Queue[PlanGenerationResult] = res_queue
        self.last_plan_found: Optional[Plan] = None

    def write(self, txt: str):
        if self._output_stream is not None:
            self._output_stream.write(txt)
        self._engine._parse_planner_output(self, txt)


class PDDLAnytimePlanner(engines.pddl_planner.PDDLPlanner, mixins.AnytimePlannerMixin):
    """
    This class is the interface of a generic PDDL :class:`AnytimePlanner <unified_planning.engines.mixins.AnytimePlannerMixin>`
    that can be invocated through a subprocess call.
    """

    def __init__(self, needs_requirements=True, rewrite_bool_assignments=False):
        """
        :param self: The PDDLEngine instance.
        :param needs_requirements: Flag defining if the Engine needs the PDDL requirements.
        :param rewrite_bool_assignments: Flag defining if the non-constant boolean assignments
            will be rewritten as conditional effects in the PDDL file submitted to the Engine.
        """
        engines.engine.Engine.__init__(self)
        mixins.AnytimePlannerMixin.__init__(self)
        engines.pddl_planner.PDDLPlanner.__init__(
            self, needs_requirements, rewrite_bool_assignments
        )

    @abstractmethod
    def _get_anytime_cmd(
        self, domain_filename: str, problem_filename: str, plan_filename: str
    ) -> List[str]:
        """
        Takes in input two filenames where the problem's domain and problem are written, a
        filename where to write the plan and returns a list of command to run the engine on the
        problem and write the plan on the file called plan_filename.

        :param domain_filename: The path of the PDDL domain file.
        :param problem_filename: The path of the PDDl problem file.
        :param plan_filename: The path where the generated plan will be written.
        :return: The list of commands needed to execute the planner from command line using the given
            paths.
        """
        raise NotImplementedError

    def _solve(
        self,
        problem: "up.model.AbstractProblem",
        heuristic: Optional[Callable[["up.model.state.State"], Optional[float]]] = None,
        timeout: Optional[float] = None,
        output_stream: Optional[Union[Tuple[IO[str], IO[str]], IO[str]]] = None,
        anytime: bool = False,
    ):
        if anytime:
            self._mode_running = OperationMode.ANYTIME_PLANNER
        else:
            self._mode_running = OperationMode.ONESHOT_PLANNER
        return super()._solve(problem, heuristic, timeout, output_stream)

    def _parse_planner_output(self, writer: "Writer", planner_output: str):
        """
        This method takes the output stream of a PDDLEngine and modifies the fields of the given
        writer.
        Those fields are:
        - writer.problem: The Problem being solved by the anytime planner.
        - writer.storing: Flag defining if the parsing is storing intermediate parts of a plan or not.
        - writer.res_queue: The Queue of PlanGenerationResult where every generated result must be added.
        - writer.current_plan: The List of ActionInstances (or Tuple[Fraction, ActionInstance, Optional[Fraction]]
            for temporal problems) that currently contains the plan being parsed; must be set to an empty when the
            plan is generated and added to the Queue.
        - writer.last_plan_found: The last complete plan found and parsed.
        """
        assert isinstance(self._writer, PDDLWriter)
        for l in planner_output.splitlines():
            if self._starting_plan_str() in l:
                writer.storing = True
            elif writer.storing and self._ending_plan_str() in l:
                plan_str = "\n".join(writer.current_plan)
                plan = self._plan_from_str(
                    writer.problem, plan_str, self._writer.get_item_named
                )
                res = PlanGenerationResult(
                    PlanGenerationResultStatus.INTERMEDIATE,
                    plan=plan,
                    engine_name=self.name,
                )
                writer.res_queue.put(res)
                writer.current_plan = []
                writer.storing = False
            elif writer.storing and l:
                writer.current_plan.append(self._parse_plan_line(l))

    def _starting_plan_str(self) -> str:
        """
        Returns the string representing the starting of a plan in the engine's output.
        """
        raise NotImplementedError

    def _ending_plan_str(self) -> str:
        """
        Returns the string representing the ending of a plan in the engine's output.
        """
        raise NotImplementedError

    def _parse_plan_line(self, plan_line: str) -> str:
        """
        Takes an engine's output line in between the starting_plan string and the engine_plan
        string and returns the string representing the parsed plan.
        The representation to obtain is:
        ``(action-name param1 param2 ... paramN)`` in each line for SequentialPlans
        ``start-time: (action-name param1 param2 ... paramN) [duration]`` in each line for TimeTriggeredPlans,
        where ``[duration]`` is optional and not specified for InstantaneousActions.
        """
        raise NotImplementedError

    def _generate_last_result(
        self,
        solve_result: PlanGenerationResult,
        last_result: Optional[PlanGenerationResult],
    ) -> PlanGenerationResult:
        """
        IMPORTANT FOR ENGINES IMPLEMENTING THIS CLASS

        This method takes the result returned by the _solve method, the last_plan_found
        by the engine  and the status of the last plan and returns a new PlanGenerationResult.
        If the engine writes his last plan to a file there is no need to overwrite this method;
        but if the engine does not write the last plan on a file or if the last result returned
        is not correct for some reason; this method allows an easy modification.

        :param solve_result: The PlanGenerationResult returned by the solve method.
        :param last_plan_found: The last plan found by the engine; obtained parsing the planner's
            output.
        :param last_status: The correct status of the last plan returned.
        :return: The PlanGenerationResult compatible with the engine semantic; defaults to the
            solve_result given in input.
        """
        if last_result is None or solve_result.plan is not None:
            return solve_result

        if solve_result.status in (
            PlanGenerationResultStatus.UNSOLVABLE_PROVEN,
            PlanGenerationResultStatus.UNSOLVABLE_INCOMPLETELY,
        ):
            new_status = PlanGenerationResultStatus.SOLVED_SATISFICING
        else:
            new_status = solve_result.status
        res = PlanGenerationResult(
            new_status,
            last_result.plan,
            solve_result.engine_name,
            solve_result.metrics,
            solve_result.log_messages,
        )
        return res

    def _get_solutions(
        self,
        problem: "up.model.AbstractProblem",
        timeout: Optional[float] = None,
        output_stream: Optional[IO[str]] = None,
    ) -> Iterator["up.engines.results.PlanGenerationResult"]:
        import threading

        q: Queue[PlanGenerationResult] = Queue()
        writer: IO[str] = Writer(output_stream, q, self, problem)

        def run():
            res = self._solve(
                problem, output_stream=writer, timeout=timeout, anytime=True
            )
            q.put(res)

        try:
            t = threading.Thread(target=run, daemon=True)
            t.start()
            status = PlanGenerationResultStatus.INTERMEDIATE
            last_res: Optional[PlanGenerationResult] = None
            while status == PlanGenerationResultStatus.INTERMEDIATE:
                res = q.get()
                status = res.status
                if status != PlanGenerationResultStatus.INTERMEDIATE:
                    res = self._generate_last_result(res, last_res)
                else:
                    last_res = res
                yield res
        finally:
            if self._process is not None:
                try:
                    self._process.kill()
                except OSError:
                    pass  # This can happen if the process is already terminated
            t.join()
