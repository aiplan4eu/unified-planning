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
#
"""This module defines an interface for a generic PDDL planner."""

from abc import abstractmethod
import os
import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.engine import OperationMode
import unified_planning.engines.mixins as mixins
from unified_planning.engines.results import (
    PlanGenerationResult,
    PlanGenerationResultStatus,
)
from typing import IO, Callable, Iterator, Optional, List, Tuple, Union

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

    @abstractmethod
    def _parse_planner_output(self, writer: up.AnyBaseClass, planner_output: str):
        raise NotImplementedError

    def _get_solutions(
        self,
        problem: "up.model.AbstractProblem",
        timeout: Optional[float] = None,
        output_stream: Optional[IO[str]] = None,
    ) -> Iterator["up.engines.results.PlanGenerationResult"]:
        import threading
        import queue

        q: queue.Queue = queue.Queue()

        class Writer(up.AnyBaseClass):
            def __init__(self, output_stream, res_queue, engine):
                self._output_stream = output_stream
                self._res_queue = res_queue
                self._engine = engine
                self._plan = []
                self._storing = False
                self._sequential_plan = None

            def write(self, txt: str):
                if self._output_stream is not None:
                    self._output_stream.write(txt)
                self._engine._parse_planner_output(self, txt)

        def run():
            writer: IO[str] = Writer(output_stream, q, self)
            res = self._solve(problem, output_stream=writer, anytime=True)
            q.put(res)

        try:
            t = threading.Thread(target=run, daemon=True)
            t.start()
            status = PlanGenerationResultStatus.INTERMEDIATE
            while status == PlanGenerationResultStatus.INTERMEDIATE:
                res = q.get()
                status = res.status
                yield res
        finally:
            if self._process is not None:
                try:
                    self._process.kill()
                except OSError:
                    pass  # This can happen if the process is already terminated
            t.join()
