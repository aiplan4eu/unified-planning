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
from fractions import Fraction
from typing import IO, Optional, Union


class ReplannerMixin:
    def __init__(self, problem: "up.model.AbstractProblem"):
        self._problem = problem
        self_class = type(self)
        assert issubclass(self_class, up.engines.engine.Engine)
        if not self_class.supports(problem.kind):
            raise up.exceptions.UPUsageError(
                f"The problem named: {problem.name} is not supported by the {self_class}."
            )

    @staticmethod
    def is_replanner() -> bool:
        return True

    @staticmethod
    def satisfies(
        optimality_guarantee: "up.engines.mixins.oneshot_planner.OptimalityGuarantee",
    ) -> bool:
        return False

    def solve(
        self,
        timeout: Optional[float] = None,
        output_stream: Optional[IO[str]] = None,
    ) -> "up.engines.results.PlanGenerationResult":
        """Solves the problem that is given in the constructor and that can be
        updated through the other engine methods."""
        return self._solve(timeout, output_stream)

    def update_initial_value(
        self,
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: Union[
            "up.model.fnode.FNode",
            "up.model.fluent.Fluent",
            "up.model.object.Object",
            bool,
            int,
            float,
            Fraction,
        ],
    ):
        """Updates the initial value for the given fluent."""
        return self._update_initial_value(fluent, value)

    def add_goal(
        self, goal: Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool]
    ):
        """Adds a goal."""
        return self._add_goal(goal)

    def remove_goal(
        self, goal: Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool]
    ):
        """Removes the given goal."""
        return self._remove_goal(goal)

    def add_action(self, action: "up.model.action.Action"):
        """Adds the given action."""
        return self._add_action(action)

    def remove_action(self, name: str):
        """Removes the given action."""
        return self._remove_action(name)

    def _solve(
        self,
        timeout: Optional[float] = None,
        output_stream: Optional[IO[str]] = None,
    ) -> "up.engines.results.PlanGenerationResult":
        raise NotImplementedError

    def _update_initial_value(
        self,
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: Union[
            "up.model.fnode.FNode",
            "up.model.fluent.Fluent",
            "up.model.object.Object",
            bool,
            int,
            float,
            Fraction,
        ],
    ):
        raise NotImplementedError

    def _add_goal(
        self, goal: Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool]
    ):
        raise NotImplementedError

    def _remove_goal(
        self, goal: Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool]
    ):
        raise NotImplementedError

    def _add_action(self, action: "up.model.action.Action"):
        raise NotImplementedError

    def _remove_action(self, name: str):
        raise NotImplementedError
