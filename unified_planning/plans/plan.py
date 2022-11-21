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


import unified_planning as up
from unified_planning.environment import Environment, get_env
from typing import Callable, Optional, Tuple
from enum import Enum, auto


"""This module defines the general `Plan` interface and the `ActionInstance` class."""


class ActionInstance:
    """
    Represents an action instance with the actual parameters.

    NOTE: two action instances of the same action with the same parameters are
    considered different as it is possible to have the same action twice in a `Plan`.
    """

    def __init__(
        self,
        action: "up.model.Action",
        params: Tuple["up.model.FNode", ...] = tuple(),
        agent: Optional["up.model.multi_agent.Agent"] = None,
    ):
        assert len(action.parameters) == len(params)
        self._agent = agent
        self._action = action
        self._params = tuple(params)

    def __repr__(self) -> str:
        s = []
        if len(self._params) > 0:
            s.append("(")
            first = True
            for p in self._params:
                if not first:
                    s.append(", ")
                s.append(str(p))
                first = False
            s.append(")")
        if self._agent is None:
            name = self._action.name
        else:
            name = f"{self._agent.name}.{self._action.name}"
        return name + "".join(s)

    @property
    def agent(self) -> Optional["up.model.multi_agent.Agent"]:
        """Returns the `Agent` of this `ActionInstance`."""
        return self._agent

    @property
    def action(self) -> "up.model.Action":
        """Returns the `Action` of this `ActionInstance`."""
        return self._action

    @property
    def actual_parameters(self) -> Tuple["up.model.FNode", ...]:
        """Returns the actual parameters used to ground the `Action` in this `ActionInstance`."""
        return self._params

    def is_semantically_equivalent(self, oth: "ActionInstance") -> bool:
        """
        This method returns `True` Iff the 2 `ActionInstances` have the same semantic.

        NOTE: This is different from __eq__; there the 2 `Action Instances` need to be exactly the same object.

        :param oth: The `ActionInstance` that must be tested for semantical equivalence with `self`.
        :return: `True` if the given `ActionInstance` is semantically equivalent to self, `False` otherwise.
        """
        return (
            self.agent == oth.agent
            and self.action == oth.action
            and self._params == oth._params
        )


class PlanKind(Enum):
    """
    Enum referring to the possible kinds of `Plans`.
    """

    SEQUENTIAL_PLAN = auto()
    TIME_TRIGGERED_PLAN = auto()
    PARTIAL_ORDER_PLAN = auto()
    CONTINGENT_PLAN = auto()


class Plan:
    """Represents a generic plan."""

    def __init__(
        self, kind: PlanKind, environment: Optional["Environment"] = None
    ) -> None:
        self._kind = kind
        self._environment = get_env(environment)

    @property
    def environment(self) -> "Environment":
        """Return this `plan's` `Environment`."""
        return self._environment

    @property
    def kind(self) -> PlanKind:
        """Returns the `Plan` `kind`"""
        return self._kind

    def replace_action_instances(
        self, replace_function: Callable[[ActionInstance], Optional[ActionInstance]]
    ) -> "Plan":
        """
        This function takes a function from `ActionInstance` to `ActionInstance` and returns a new `Plan`
        that have the `ActionInstance` modified by the `replace_function` function.

        If the returned `ActionInstance` is `None` it means that the `ActionInstance` should not go in the resulting `Plan`.

        :param replace_function: The function that must be used on the `ActionInstances` that must be replaced.
        :return: The new `Plan` in which every `ActionInstance` of the original `Plan` is modified by the given `replace_function`.
        """
        raise NotImplementedError
