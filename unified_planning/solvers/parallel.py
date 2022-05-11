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


from fractions import Fraction
import sys
import warnings
import unified_planning as up
import unified_planning.solvers as solvers
from unified_planning.plan import Plan
from unified_planning.model import ProblemKind
from unified_planning.exceptions import UPException
from unified_planning.solvers.results import LogLevel, PlanGenerationResultStatus, Result, ValidationResult, PlanGenerationResult
from typing import IO, Callable, Dict, List, Optional, Tuple, cast
from multiprocessing import Process, Queue


class Parallel(solvers.solver.Solver):
    """Create a parallel instance of multiple Solvers."""

    def __init__(self, solvers: List[Tuple[type, Dict[str, str]]]):
        self.solvers = solvers

    @property
    def name(self) -> str:
        return 'Parallel'

    @staticmethod
    def is_oneshot_planner() -> bool:
        raise UPException('The Parallel solver type depends on its actual solvers')

    @staticmethod
    def is_plan_validator() -> bool:
        raise UPException('The Parallel solver type depends on its actual solvers')

    @staticmethod
    def supports(problem_kind: 'ProblemKind') -> bool:
        raise UPException('The Parallel supported features depends on its actual solvers')

    def _run_parallel(self, fname, *args) -> List[Result]:
        signaling_queue: Queue = Queue()
        processes = []
        for idx, (solver_class, opts) in enumerate(self.solvers):
            options = opts
            _p = Process(name=str(idx),
                         target=_run,
                         args=(idx, solver_class, options,
                               signaling_queue, fname, *args))
            processes.append(_p)
            _p.start()
        processes_alive = len(processes)
        results: List[Result] = []
        definitive_result_found: bool = False
        while True:
            if processes_alive == 0: # Every planner gave a result
                break
            (idx, res) = signaling_queue.get(block=True)
            processes_alive -= 1
            if isinstance(res, BaseException):
                raise res
            else:
                assert isinstance(res, Result)
                # If the planner is sure about the result (optimality of the result or impossibility of the problem or the problem does not need optimality) exit the loop
                if res.is_definitive_result(*args):
                    definitive_result_found = True
                    break
                else:
                    results.append(res)
        for p in processes:
            p.terminate()
        if definitive_result_found: # A planner found a definitive result
            return [res]
        return results

    def solve(self, problem: 'up.model.AbstractProblem',
                    callback: Optional[Callable[['up.solvers.results.PlanGenerationResult'], None]] = None,
                    timeout: Optional[float] = None,
                    output_stream: Optional[IO[str]] = None) -> 'up.solvers.results.PlanGenerationResult':
        if callback is not None:
            warnings.warn('Parallel solvers do not support the callback system.', UserWarning)
        if output_stream is not None:
            warnings.warn('Parallel solvers do not support the output stream system.', UserWarning)

        final_reports = self._run_parallel('solve', problem, None, timeout, None)

        result_order: List[PlanGenerationResultStatus] = [
                    PlanGenerationResultStatus.SOLVED_OPTIMALLY,  # List containing the results in the order we prefer them
                    PlanGenerationResultStatus.UNSOLVABLE_PROVEN,
                    PlanGenerationResultStatus.SOLVED_SATISFICING,
                    PlanGenerationResultStatus.UNSOLVABLE_INCOMPLETELY,
                    PlanGenerationResultStatus.TIMEOUT,
                    PlanGenerationResultStatus.MEMOUT,
                    PlanGenerationResultStatus.INTERNAL_ERROR,
                    PlanGenerationResultStatus.UNSUPPORTED_PROBLEM]
        final_result: Optional[PlanGenerationResult] = None
        result_found: bool = False
        for ro in result_order:
            if result_found:
                break
            for r in final_reports:
                pgr = cast(PlanGenerationResult, r)
                if pgr.status == ro:
                    result_found = True
                    final_result = pgr
                    break
        logs = [up.solvers.LogMessage(LogLevel.INFO, str(fr)) for fr in final_reports]
        # if no results are given by the planner, we create a default one
        if final_result is None:
            return up.solvers.PlanGenerationResult(PlanGenerationResultStatus.UNSOLVABLE_INCOMPLETELY,
                                                   None, self.name, log_messages=logs)
        new_plan = problem.normalize_plan(final_result.plan) if final_result.plan is not None else None
        if final_result.log_messages is not None:
            logs = final_result.log_messages + logs
        return up.solvers.results.PlanGenerationResult(
            final_result.status,
            new_plan,
            final_result.engine_name,
            final_result.metrics,
            logs
        )

    def validate(self, problem: 'up.model.AbstractProblem', plan: Plan) -> 'up.solvers.results.ValidationResult':
        return cast(ValidationResult, self._run_parallel('validate', problem, plan)[0])

    def engine_credits(self, stream: Optional[IO[str]] = sys.stdout):
        if stream is not None: #TODO write credits
            stream.write("You are using the Parallel solver, which uses different solvers, here are their credits:")
            for (SolverClass, options) in self.solvers:
                with SolverClass(**options) as solver:
                    solver.engine_credits(stream)

    def destroy(self):
        pass


def _run(idx: int, SolverClass: type, options: Dict[str, str], signaling_queue: Queue, fname: str, *args):
    with SolverClass(**options) as s:
        try:
            local_res = getattr(s, fname)(*args)
        except Exception as ex:
            signaling_queue.put((idx, ex))
            return
        signaling_queue.put((idx, local_res))
