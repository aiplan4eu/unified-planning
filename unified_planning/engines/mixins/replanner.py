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
from warnings import warn


class ReplannerMixin:
    """Base class that must be extended by an :class:`~unified_planning.engines.Engine` that is also a `Replanner`."""

    def __init__(self, problem: "up.model.AbstractProblem"):
        self._problem = problem.clone()
        self_class = type(self)
        assert issubclass(self_class, up.engines.engine.Engine)
        assert isinstance(self, up.engines.engine.Engine)
        if not self.skip_checks and not self_class.supports(problem.kind):
            msg = f"We cannot establish whether {self.name} is able to handle this problem!"
            if self.error_on_failed_checks:
                raise up.exceptions.UPUsageError(msg)
            else:
                warn(msg)

    @staticmethod
    def is_replanner() -> bool:
        return True

    @staticmethod
    def satisfies(
        optimality_guarantee: "up.engines.mixins.oneshot_planner.OptimalityGuarantee",
    ) -> bool:
        """
        Returns True iff the engine satisfies the given optimality guarantee.

        :param optimality_guarantee: the given optimality guarantee.
        :return: True iff the engine satisfies the given optimality guarantee.
        """
        return False

    def resolve(
        self,
        timeout: Optional[float] = None,
        output_stream: Optional[IO[str]] = None,
    ) -> "up.engines.results.PlanGenerationResult":
        """
        Resolves the problem that is given in the constructor and that can be
        updated through the other engine methods.

        :param timeout: the time in seconds that the planner has at max to resolve the problem, defaults to None.
        :param output_stream: a stream of strings where the planner writes his
            output (and also errors) while the planner is solving the problem, defaults to None.
        :return: the up.engines.results.PlanGenerationResult created by the planner;
            a data structure containing the up.plan.Plan found and some additional information about it.
        """
        return self._resolve(timeout, output_stream)

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
        """
        Updates the initial value for the given fluent.

        :param fluent: the fluent expression to which the value is updated.
        :param value: the new value of the given fluent expression.
        """
        return self._update_initial_value(fluent, value)

    def add_goal(
        self, goal: Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool]
    ):
        """
        Adds a goal.

        :param goal: the new goal to add to the problem.
        """
        return self._add_goal(goal)

    def remove_goal(
        self, goal: Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool]
    ):
        """
        Removes the given goal.

        :param goal: the goal to remove to the problem.
        """
        return self._remove_goal(goal)

    def add_action(self, action: "up.model.action.Action"):
        """
        Adds the given action.

        :param action: the new action to add to the problem.
        """
        return self._add_action(action)

    def remove_action(self, name: str):
        """
        Removes the given action.

        :param action: the action to remove to the problem.
        """
        return self._remove_action(name)

    def _resolve(
        self,
        timeout: Optional[float] = None,
        output_stream: Optional[IO[str]] = None,
    ) -> "up.engines.results.PlanGenerationResult":
        """
        Method called by the ReplannerMixin.resolve method that has to be implemented
        by the engines that implement this operation mode.
        """
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
        """
        Method called by the ReplannerMixin.update_initial_value method that has to be implemented
        by the engines that implement this operation mode.
        """
        raise NotImplementedError

    def _add_goal(
        self, goal: Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool]
    ):
        """
        Method called by the ReplannerMixin.add_goal method that has to be implemented
        by the engines that implement this operation mode.
        """
        raise NotImplementedError

    def _remove_goal(
        self, goal: Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool]
    ):
        """
        Method called by the ReplannerMixin.remove_goal method that has to be implemented
        by the engines that implement this operation mode.
        """
        raise NotImplementedError

    def _add_action(self, action: "up.model.action.Action"):
        """
        Method called by the ReplannerMixin.add_action method that has to be implemented
        by the engines that implement this operation mode.
        """
        raise NotImplementedError

    def _remove_action(self, name: str):
        """
        Method called by the ReplannerMixin.remove_action method that has to be implemented
        by the engines that implement this operation mode.
        """
        raise NotImplementedError
