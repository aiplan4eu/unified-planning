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

import unified_planning as up
from enum import Enum, auto
from typing import IO, Optional, Iterator


class AnytimeGuarantee(Enum):
    INCREASING_QUALITY = auto()
    OPTIMAL_PLANS = auto()


class AnytimePlannerMixin:
    """Base class that must be extended by an :class:`~unified_planning.engines.Engine` that is also a `AnytimePlanner`."""

    def __init__(self):
        self.optimality_metric_required = False

    @staticmethod
    def is_anytime_planner() -> bool:
        return True

    @staticmethod
    def ensures(anytime_guarantee: AnytimeGuarantee) -> bool:
        """
        :param anytime_guarantee: The `anytime_guarantee` that must be satisfied.
        :return: `True` if the `AnytimePlannerMixin` implementation ensures the given
        `anytime_guarantee`, `False` otherwise.
        """
        return False

    def get_solutions(
        self,
        problem: "up.model.AbstractProblem",
        timeout: Optional[float] = None,
        output_stream: Optional[IO[str]] = None,
    ) -> Iterator["up.engines.results.PlanGenerationResult"]:
        """
        This method takes a `AbstractProblem` and returns an iterator of `PlanGenerationResult`,
        which contains information about the solution to the problem given by the planner.

        :param problem: is the `AbstractProblem` to solve.
        :param timeout: is the time in seconds that the planner has at max to solve the problem, defaults to `None`.
        :param output_stream: is a stream of strings where the planner writes his
            output (and also errors) while it is solving the problem; defaults to `None`.
        :return: an iterator of `PlanGenerationResult` created by the planner.

        The only required parameter is `problem` but the planner should warn the user if `timeout` or
        `output_stream` are not `None` and the planner ignores them."""
        assert isinstance(self, up.engines.engine.Engine)
        problem_kind = problem.kind
        if not self.skip_checks and not self.supports(problem_kind):
            msg = f"We cannot establish whether {self.name} can solve this problem!"
            if self.error_on_failed_checks:
                raise up.exceptions.UPUsageError(msg)
            else:
                warn(msg)
        if not problem_kind.has_quality_metrics() and self.optimality_metric_required:
            msg = f"The problem has no quality metrics but the engine is required to satisfies some optimality guarantee!"
            raise up.exceptions.UPUsageError(msg)
        for res in self._get_solutions(problem, timeout, output_stream):
            yield res

    def _get_solutions(
        self,
        problem: "up.model.AbstractProblem",
        timeout: Optional[float] = None,
        output_stream: Optional[IO[str]] = None,
    ) -> Iterator["up.engines.results.PlanGenerationResult"]:
        """
        Method called by the AnytimePlannerMixin.get_solutions method that has to be implemented
        by the engines that implement this operation mode.
        """
        raise NotImplementedError
