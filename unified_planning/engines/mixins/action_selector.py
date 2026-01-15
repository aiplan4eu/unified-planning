# Copyright 2023 AIPlan4EU project
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
from typing import Dict
from warnings import warn
from unified_planning.exceptions import UPUsageError


class ActionSelectorMixin:
    """
    This class defines the interface that an :class:`~unified_planning.engines.Engine`
    that is also an `ActionSelector` must implement.

    Important NOTE: The `AbstractProblem` instance is given at the constructor.
    """

    def __init__(self, problem: "up.model.AbstractProblem"):
        self._problem = problem
        self_class = type(self)
        assert issubclass(
            self_class, up.engines.engine.Engine
        ), "ActionSelectorMixin does not implement the up.engines.Engine class"
        assert isinstance(self, up.engines.engine.Engine)
        if not self.skip_checks and not self_class.supports(problem.kind):
            msg = f"We cannot establish whether {self.name} is able to handle this problem!"
            if self.error_on_failed_checks:
                raise UPUsageError(msg)
            else:
                warn(msg)

    @staticmethod
    def is_action_selector() -> bool:
        """
        Returns True if this engine is also an action selector, False otherwise.

        :return: True if this engine is also an action selector, False otherwise.
        """
        return True

    def get_action(self) -> "up.plans.ActionInstance":
        """
        Returns the next action to be taken in the current state of the problem.

        :return: An instance of `ActionInstance` representing the next action to be taken.
        """
        return self._get_action()

    def update(self, observation: Dict["up.model.FNode", "up.model.FNode"]):
        """
        Updates the internal state of the engine based on the given observation.

        :param observation: A dictionary from observed fluents to their observed values.
        """
        self._update(observation)

    def _get_action(self) -> "up.plans.ActionInstance":
        """
        Returns the next action to be taken in the current state of the problem. This method should be
        implemented by subclasses.

        :return: An instance of `ActionInstance` representing the next action to be taken.
        """
        raise NotImplementedError

    def _update(self, observation: Dict["up.model.FNode", "up.model.FNode"]):
        """
        Updates the internal state of the engine based on the given observation. This method should be
        implemented by subclasses.

        :param observation: A dictionary from observed fluents to their observed values.
        """
        raise NotImplementedError
