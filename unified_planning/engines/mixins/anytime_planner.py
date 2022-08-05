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
from typing import IO, Optional, Iterator


class AnytimePlannerMixin:
    @staticmethod
    def is_anytime_planner() -> bool:
        return True

    def solve(
        self,
        problem: "up.model.AbstractProblem",
        timeout: Optional[float] = None,
        output_stream: Optional[IO[str]] = None,
    ) -> Iterator["up.engines.results.PlanGenerationResult"]:
        """This method takes a up.model.AbstractProblem and returns an iterator of up.engines.results.PlanGenerationResult,
        which contains information about the solution to the problem given by the planner.

        :param problem: is the up.model.AbstractProblem to solve.
        :param timeout: is the time in seconds that the planner has at max to solve the problem, defaults to None.
        :param output_stream: is a stream of strings where the planner writes his
        output (and also errors) while the planner is solving the problem, defaults to None
        :return: an iterator of up.engines.results.PlanGenerationResult created by the planner.

        The only required parameter is "problem" but the planner should warn the user if timeout or
        output_stream are not None and the planner ignores them."""
        assert isinstance(self, up.engines.engine.Engine)
        if not self.supports(problem.kind):
            raise up.exceptions.UPUsageError(
                f"{self.name} cannot solve this kind of problem!"
            )
        for res in self._solve(problem, timeout, output_stream):
            yield res

    def _solve(
        self,
        problem: "up.model.AbstractProblem",
        timeout: Optional[float] = None,
        output_stream: Optional[IO[str]] = None,
    ) -> Iterator["up.engines.results.PlanGenerationResult"]:
        """
        Method called by the AnytimePlannerMixin.solve method that has to be implemented
        by the engines that implement this operation mode.
        """
        raise NotImplementedError
