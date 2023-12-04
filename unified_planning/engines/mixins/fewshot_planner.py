# Copyright 2022 AIPlan4EU project
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

from warnings import warn
import unified_planning as up
from abc import ABC, abstractmethod
from typing import IO, Optional, Callable, List


class FewshotPlannerMixin(ABC):
    """Base class to be extended by an :class:`~unified_planning.engines.Engine` that is also a `FewshotPlanner`."""

    @staticmethod
    def is_fewshot_planner() -> bool:
        return True

    def solve(
        self,
        problems: List["up.model.AbstractProblem"],
        heuristic: Optional[Callable[["up.model.state.State"], Optional[float]]] = None,
        timeout: Optional[float] = None,
        output_stream: Optional[IO[str]] = None,
    ) -> List["up.engines.results.PlanGenerationResult"]:
        """
        This method takes a list of `AbstractProblem`s and returns a list of `PlanGenerationResult`,
        which contains information about the solution to the problems given by the generalized planner.

        :param problems: is the list of `AbstractProblem`s to solve.
        :param heuristic: is a function that given a state returns its heuristic value or `None` if the state is a
                          dead-end, defaults to `None`.
        :param timeout: is the time in seconds the generalized planner has to solve all problems, defaults to `None`.
        :param output_stream: is a stream of strings where the planner writes his output (and also errors) while it is
                              solving the problem; defaults to `None`.
        :return: a list of `PlanGenerationResult` created by the generalized planner; a data structure containing the
                 :class:`~unified_planning.plans.Plan` found and some additional information about it.

        The only required parameter is `problems` but the generalized planner should warn the user if `heuristic`,
        `timeout` or `output_stream` are not `None` and the generalized planner ignores them.
        """
        assert isinstance(self, up.engines.engine.Engine)
        for problem in problems:
            # Check whether the GP planner supports each input problem
            if not self.skip_checks and not self.supports(problem.kind):
                msg = f"We cannot establish whether {self.name} can solve problem {problem.name}!"
                if self.error_on_failed_checks:
                    raise up.exceptions.UPUsageError(msg)
                else:
                    warn(msg)
        # Solve all problems
        return self._solve(problems, heuristic, timeout, output_stream)

    @abstractmethod
    def _solve(
        self,
        problems: List["up.model.AbstractProblem"],
        heuristic: Optional[Callable[["up.model.state.State"], Optional[float]]] = None,
        timeout: Optional[float] = None,
        output_stream: Optional[IO[str]] = None,
    ) -> List["up.engines.results.PlanGenerationResult"]:
        """Method called by the FewshotPlannerMixin.solve method."""
        raise NotImplementedError
