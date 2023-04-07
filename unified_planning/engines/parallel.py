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


import warnings
import unified_planning as up
import unified_planning.engines as engines
from unified_planning.plans import Plan
from unified_planning.model import ProblemKind
from unified_planning.exceptions import UPUsageError
from unified_planning.engines.results import (
    LogLevel,
    PlanGenerationResultStatus,
    Result,
    ValidationResult,
    PlanGenerationResult,
)
from typing import IO, Dict, List, Optional, Tuple, Callable, cast
from multiprocessing import Process, Queue


class Parallel(
    engines.engine.Engine,
    engines.mixins.OneshotPlannerMixin,
    engines.mixins.PlanValidatorMixin,
):
    """
    Create a parallel instance of multiple :class:`Engines <unified_planning.engines.Engine>`.

    The `Engines` run the same command in parallel and the first definitive :class:`Result <unified_planning.engines.Result>` returned
    by the `Engine` is returned to the user.
    """

    def __init__(
        self,
        factory: "up.engines.factory.Factory",
        engines: List[Tuple[str, Dict[str, str]]],
    ):
        up.engines.engine.Engine.__init__(self)
        up.engines.mixins.OneshotPlannerMixin.__init__(self)
        up.engines.mixins.PlanValidatorMixin.__init__(self)
        # Since the parallel is always called by name, the errors become warnings by default
        self.error_on_failed_checks = False
        self.engines = engines
        self._factory = factory

    @property
    def name(self) -> str:
        return "Parallel"

    @staticmethod
    def supported_kind() -> ProblemKind:
        raise UPUsageError("The Parallel supported kind depends on its actual engines")

    @staticmethod
    def supports(problem_kind: "ProblemKind") -> bool:
        # The supported features depends on its actual engines
        return True

    @staticmethod
    def supports_plan(plan_kind: "up.plans.PlanKind") -> bool:
        # The supported plan depends on its actual engines
        return True

    def _run_parallel(self, fname, *args) -> List[Result]:
        signaling_queue: Queue = Queue()
        processes = []
        for idx, (engine_name, opts) in enumerate(self.engines):
            options = opts
            _p = Process(
                name=str(idx),
                target=_run,
                args=(
                    idx,
                    self._factory,
                    engine_name,
                    options,
                    self.skip_checks,
                    self.error_on_failed_checks,
                    signaling_queue,
                    fname,
                    *args,
                ),
            )
            processes.append(_p)
            _p.start()
        processes_alive = len(processes)
        results: List[Result] = []
        definitive_result_found: bool = False
        while True:
            if processes_alive == 0:  # Every planner gave a result
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
        if definitive_result_found:  # A planner found a definitive result
            return [res]
        return results

    def _solve(
        self,
        problem: "up.model.AbstractProblem",
        heuristic: Optional[Callable[["up.model.state.State"], Optional[float]]] = None,
        timeout: Optional[float] = None,
        output_stream: Optional[IO[str]] = None,
    ) -> "up.engines.results.PlanGenerationResult":
        for engine_name, _ in self.engines:
            engine = self._factory.engine(engine_name)
            assert issubclass(engine, engines.mixins.OneshotPlannerMixin)
        if output_stream is not None:
            warnings.warn(
                "Parallel engines do not support the output stream system.", UserWarning
            )

        final_reports = self._run_parallel("solve", problem, timeout, None)

        result_order: List[PlanGenerationResultStatus] = [
            PlanGenerationResultStatus.SOLVED_OPTIMALLY,  # List containing the results in the order we prefer them
            PlanGenerationResultStatus.UNSOLVABLE_PROVEN,
            PlanGenerationResultStatus.SOLVED_SATISFICING,
            PlanGenerationResultStatus.UNSOLVABLE_INCOMPLETELY,
            PlanGenerationResultStatus.TIMEOUT,
            PlanGenerationResultStatus.MEMOUT,
            PlanGenerationResultStatus.INTERNAL_ERROR,
            PlanGenerationResultStatus.UNSUPPORTED_PROBLEM,
        ]
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
        logs = [up.engines.LogMessage(LogLevel.INFO, str(fr)) for fr in final_reports]
        # if no results are given by the planner, we create a default one
        if final_result is None:
            return up.engines.PlanGenerationResult(
                PlanGenerationResultStatus.UNSOLVABLE_INCOMPLETELY,
                None,
                self.name,
                log_messages=logs,
            )
        new_plan = (
            problem.normalize_plan(final_result.plan)
            if final_result.plan is not None
            else None
        )
        if final_result.log_messages is not None:
            logs = final_result.log_messages + logs
        return up.engines.results.PlanGenerationResult(
            final_result.status,
            new_plan,
            final_result.engine_name,
            final_result.metrics,
            logs,
        )

    def _validate(
        self, problem: "up.model.AbstractProblem", plan: Plan
    ) -> "up.engines.results.ValidationResult":
        for engine_name, _ in self.engines:
            engine = self._factory.engine(engine_name)
            assert issubclass(engine, engines.mixins.PlanValidatorMixin)
            if not engine.supports(problem.kind):
                raise UPUsageError(
                    "Parallel engines cannot validate this kind of problem!"
                )
        return cast(ValidationResult, self._run_parallel("validate", problem, plan)[0])


def _run(
    idx: int,
    factory: "up.engines.factory.Factory",
    engine_name: str,
    options: Dict[str, str],
    skip_checks: bool,
    error_on_failed_checks: bool,
    signaling_queue: Queue,
    fname: str,
    *args,
):
    EngineClass = factory.engine(engine_name)
    with EngineClass(**options) as s:
        s.skip_checks = skip_checks
        s.error_on_failed_checks = error_on_failed_checks
        try:
            local_res = getattr(s, fname)(*args)
        except Exception as ex:
            signaling_queue.put((idx, ex))
            return
        signaling_queue.put((idx, local_res))
