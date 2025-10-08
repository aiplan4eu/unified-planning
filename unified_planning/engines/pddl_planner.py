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

from abc import ABCMeta, abstractmethod
import asyncio
from asyncio.subprocess import PIPE
import select
import signal
import subprocess
import sys
import tempfile
import os
import re
import time
import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.engine import OperationMode
import unified_planning.engines.mixins as mixins
from unified_planning.engines.results import (
    LogLevel,
    LogMessage,
    PlanGenerationResult,
    PlanGenerationResultStatus,
)
from unified_planning.io import PDDLWriter, PDDLReader
from asyncio.subprocess import PIPE
from fractions import Fraction
from typing import IO, Any, Callable, Optional, List, Tuple, Union, cast

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


class PDDLPlanner(engines.engine.Engine, mixins.OneshotPlannerMixin):
    """
    This class is the interface of a generic PDDL :class:`OneshotPlanner <unified_planning.engines.mixins.OneshotPlannerMixin>`
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
        mixins.OneshotPlannerMixin.__init__(self)
        self._mode_running = OperationMode.ONESHOT_PLANNER
        self._needs_requirements = needs_requirements
        self._rewrite_bool_assignments = rewrite_bool_assignments
        self._process = None
        self._writer = None

    @abstractmethod
    def _get_cmd(
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

    def _get_engine_epsilon(self) -> Optional[Fraction]:
        """
        | Returns the epsilon used by the engine.
        | Note: must be implemented only if the engine supports temporal problems.
        """
        raise NotImplementedError

    def _plan_from_file(
        self,
        problem: "up.model.Problem",
        plan_filename: str,
        get_item_named: Callable[
            [str],
            "up.io.pddl_writer.WithName",
        ],
    ) -> "up.plans.Plan":
        """
        Takes a problem, a filename and a map of renaming and returns the plan parsed from the file.
        :param problem: The up.model.problem.Problem instance for which the plan is generated.
        :param plan_filename: The path of the file in which the plan is written.
        :param get_item_named: A function that takes a name and returns the original up.model element instance
            linked to that renaming.
        :return: The up.plans.Plan corresponding to the parsed plan from the file
        """
        with open(plan_filename, encoding="utf-8-sig") as plan:
            return self._plan_from_str(problem, plan.read(), get_item_named)

    def _plan_from_str(
        self,
        problem: "up.model.Problem",
        plan_str: str,
        get_item_named: Callable[
            [str],
            "up.io.pddl_writer.WithName",
        ],
    ) -> "up.plans.Plan":
        """
        Takes a problem, a string and a map of renaming and returns the plan parsed from the string.
        :param problem: The up.model.problem.Problem instance for which the plan is generated.
        :param plan_str: The plan in string.
        :param get_item_named: A function that takes a name and returns the original up.model element instance linked to that renaming.
        :return: The up.plans.Plan corresponding to the parsed plan from the string
        """
        reader = PDDLReader(problem.environment)
        return reader.parse_plan_string(problem, plan_str, get_item_named)

    def _solve(
        self,
        problem: "up.model.AbstractProblem",
        heuristic: Optional[Callable[["up.model.state.State"], Optional[float]]] = None,
        timeout: Optional[float] = None,
        output_stream: Optional[Union[Tuple[IO[str], IO[str]], IO[str]]] = None,
    ) -> "up.engines.results.PlanGenerationResult":
        assert isinstance(problem, up.model.Problem)
        self._writer = PDDLWriter(
            problem, self._needs_requirements, self._rewrite_bool_assignments
        )
        plan = None
        logs: List["up.engines.results.LogMessage"] = []
        with tempfile.TemporaryDirectory() as tempdir:
            domain_filename = os.path.join(tempdir, "domain.pddl")
            problem_filename = os.path.join(tempdir, "problem.pddl")
            plan_filename = os.path.join(tempdir, "plan.txt")
            self._writer.write_domain(domain_filename)
            self._writer.write_problem(problem_filename)
            if self._mode_running == OperationMode.ONESHOT_PLANNER:
                cmd = self._get_cmd(domain_filename, problem_filename, plan_filename)
            elif self._mode_running == OperationMode.ANYTIME_PLANNER:
                assert isinstance(
                    self, up.engines.pddl_anytime_planner.PDDLAnytimePlanner
                )
                cmd = self._get_anytime_cmd(
                    domain_filename, problem_filename, plan_filename
                )
            process_start = time.time()
            timeout_occurred, (proc_out, proc_err), retval = run_command(
                self, cmd, output_stream=output_stream, timeout=timeout
            )
            process_end = time.time()
            logs.append(up.engines.results.LogMessage(LogLevel.INFO, "".join(proc_out)))
            logs.append(
                up.engines.results.LogMessage(LogLevel.ERROR, "".join(proc_err))
            )
            if os.path.isfile(plan_filename):
                plan = self._plan_from_file(
                    problem, plan_filename, self._writer.get_item_named
                )
            metrics = {}
            metrics["engine_internal_time"] = str(process_end - process_start)
            if timeout_occurred and retval != 0:
                return PlanGenerationResult(
                    PlanGenerationResultStatus.TIMEOUT,
                    plan=plan,
                    engine_name=self.name,
                    log_messages=logs,
                    metrics=metrics,
                )
        status: PlanGenerationResultStatus = self._result_status(
            problem, plan, retval, logs
        )
        res = PlanGenerationResult(
            status,
            plan,
            engine_name=self.name,
            log_messages=logs,
            metrics=metrics,
        )
        problem_kind = problem.kind
        if problem_kind.has_continuous_time() or problem_kind.has_discrete_time():
            if isinstance(plan, up.plans.TimeTriggeredPlan) or plan is None:
                return up.engines.results.correct_plan_generation_result(
                    res, problem, self._get_engine_epsilon()
                )
        return res

    @abstractmethod
    def _result_status(
        self,
        problem: "up.model.Problem",
        plan: Optional["up.plans.Plan"],
        retval: int,
        log_messages: Optional[List[LogMessage]] = None,
    ) -> "up.engines.results.PlanGenerationResultStatus":
        """
        Takes a problem and a plan and returns the status that represents this plan.
        The possible status with their interpretation can be found in the up.engines.results file.

        :param problem: The up.model.problem.Problem for which the plan was generated.
        :param plan: The returned parsed plan by the planner; might be None
        :return: The up.engines.results.PlanGenerationResultStatus corresponding to the given plan.
            It mainly depends on the plan and on the planner capabilities."""
        raise NotImplementedError


def run_command(
    engine: PDDLPlanner,
    cmd: List[str],
    output_stream: Optional[Union[Tuple[IO[str], IO[str]], IO[str]]] = None,
    timeout: Optional[float] = None,
) -> Tuple[bool, Tuple[List[str], List[str]], int]:
    """
    Executed the specified command line, imposing the specified timeout and printing online the output on output_stream.
    The function returns a boolean flag telling if a timeout occurred, a pair of string lists containing the captured standard output and standard error and the return code of the command as an integer
    """
    if output_stream is None:
        # If we do not have an output stream to write to, we simply call
        # a subprocess and retrieve the final output and error with communicate
        kwargs = (
            {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}  # type: ignore
            if sys.platform == "win32"
            else {"start_new_session": True}
        )
        engine._process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs
        )
        timeout_occurred: bool = False
        proc_out: List[str] = []
        proc_err: List[str] = []
        try:
            out_err_bytes = engine._process.communicate(timeout=timeout)
            proc_out, proc_err = [[x.decode()] for x in out_err_bytes]
        except subprocess.TimeoutExpired:
            terminate_process(engine._process)  # Terminate the process
            timeout_occurred = True
        retval = engine._process.returncode
        engine._process = None
    else:
        if sys.platform == "win32":
            # On windows we have to use asyncio (does not work inside notebooks)
            try:
                loop = asyncio.ProactorEventLoop()
                exec_res = loop.run_until_complete(
                    run_command_asyncio(
                        engine, cmd, output_stream=output_stream, timeout=timeout
                    )
                )
            finally:
                loop.close()
        else:
            # On non-windows OSs, we can choose between asyncio and posix
            # select (see comment on USE_ASYNCIO_ON_UNIX variable for details)
            if USE_ASYNCIO_ON_UNIX:
                exec_res = asyncio.run(
                    run_command_asyncio(
                        engine, cmd, output_stream=output_stream, timeout=timeout
                    )
                )
            else:
                exec_res = run_command_posix_select(
                    engine, cmd, output_stream=output_stream, timeout=timeout
                )
        timeout_occurred, (proc_out, proc_err), retval = exec_res

    return timeout_occurred, (proc_out, proc_err), retval


async def run_command_asyncio(
    engine: PDDLPlanner,
    cmd: List[str],
    output_stream: Union[Tuple[IO[str], IO[str]], IO[str]],
    timeout: Optional[float] = None,
) -> Tuple[bool, Tuple[List[str], List[str]], int]:
    """
    Executed the specified command line using asyncio primitives, imposing the specified timeout and printing online the output on output_stream.
    The function returns a boolean flag telling if a timeout occurred, a pair of string lists containing the captured standard output and standard error and the return code of the command as an integer
    """
    start = time.time()
    kwargs = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}  # type: ignore
        if sys.platform == "win32"
        else {"start_new_session": True}
    )
    engine._process = await asyncio.create_subprocess_exec(
        *cmd, stdout=PIPE, stderr=PIPE, **kwargs
    )

    timeout_occurred = False
    process_output: Tuple[List[str], List[str]] = ([], [])  # stdout, stderr
    while True:
        lines = [b"", b""]
        oks = [True, True]
        for idx, stream in enumerate([engine._process.stdout, engine._process.stderr]):
            assert stream is not None
            try:
                lines[idx] = await asyncio.wait_for(stream.readline(), 0.01)
            except asyncio.TimeoutError:
                oks[idx] = False

        if all(oks) and (not lines[0] and not lines[1]):  # EOF
            break
        else:
            for idx in range(2):
                output_string = lines[idx].decode().replace("\r\n", "\n")
                if type(output_stream) is tuple:
                    assert len(output_stream) == 2
                    if output_stream[idx] is not None:
                        output_stream[idx].write(output_string)
                else:
                    cast(IO[str], output_stream).write(output_string)
                process_output[idx].append(output_string)
        if timeout is not None and time.time() - start >= timeout:
            terminate_process(engine._process)  # Terminate the process
            timeout_occurred = True
            break

    await engine._process.wait()  # Wait for the child process to exit
    retval = engine._process.returncode
    engine._process = None
    return timeout_occurred, process_output, cast(int, retval)


def run_command_posix_select(
    engine: PDDLPlanner,
    cmd: List[str],
    output_stream: Union[Tuple[IO[str], IO[str]], IO[str]],
    timeout: Optional[float] = None,
) -> Tuple[bool, Tuple[List[str], List[str]], int]:
    """
    Executed the specified command line using posix select, imposing the specified timeout and printing online the output on output_stream.
    The function returns a boolean flag telling if a timeout occurred, a pair of string lists containing the captured standard output and standard error and the return code of the command as an integer

    WARNING: this does not work under Windows because the select function only support sockets and not pipes
    WARNING: The resolution of the timeout parameter is ~ 1 second if output_stream is specified
    """
    proc_out: List[str] = []
    proc_err: List[str] = []
    proc_out_buff: List[str] = []
    proc_err_buff: List[str] = []

    engine._process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True
    )
    timeout_occurred: bool = False
    start_time = time.time()
    last_red_out, last_red_err = 0, 0  # Variables needed for the correct loop exit
    readable_streams: List[Any] = []
    # Exit loop condition: Both stream have nothing left to read or the planner is out of time
    while not timeout_occurred and (
        len(readable_streams) != 2 or last_red_out != 0 or last_red_err != 0
    ):
        readable_streams, _, _ = select.select(
            [engine._process.stdout, engine._process.stderr], [], [], 1.0
        )  # 1.0 is the timeout resolution
        if (
            timeout is not None and time.time() - start_time >= timeout
        ):  # Check if the planner is out of time.
            terminate_process(engine._process)  # Terminate the process
            timeout_occurred = True
        for readable_stream in readable_streams:
            out_in_bytes = readable_stream.readline()
            out_str = out_in_bytes.decode().replace("\r\n", "\n")
            if readable_stream == engine._process.stdout:
                if type(output_stream) is tuple:
                    assert len(output_stream) == 2
                    if output_stream[0] is not None:
                        output_stream[0].write(out_str)
                else:
                    cast(IO[str], output_stream).write(out_str)
                last_red_out = len(out_in_bytes)
                buff = proc_out_buff
                lst = proc_out
            else:
                if type(output_stream) is tuple:
                    assert len(output_stream) == 2
                    if output_stream[1] is not None:
                        output_stream[1].write(out_str)
                else:
                    cast(IO[str], output_stream).write(out_str)
                last_red_err = len(out_in_bytes)
                buff = proc_err_buff
                lst = proc_err
            buff.append(out_str)
            if "\n" in out_str:
                lines = "".join(buff).split("\n")
                for x in lines[:-1]:
                    lst.append(x + "\n")

                buff.clear()
                if lines[-1]:
                    buff.append(lines[-1])
        lastout = "".join(proc_out_buff)
        if lastout:
            proc_out.append(lastout + "\n")
        lasterr = "".join(proc_err_buff)
        if lasterr:
            proc_err.append(lasterr + "\n")

    engine._process.wait()
    retval = engine._process.returncode
    engine._process = None
    return timeout_occurred, (proc_out, proc_err), cast(int, retval)


def terminate_process(process):
    """
    Terminates the given process.
    This function sends a termination signal to the process, which is platform-dependent.
    :param process: The process to terminate.
    """
    try:
        if sys.platform == "win32":
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    except ProcessLookupError:
        pass
