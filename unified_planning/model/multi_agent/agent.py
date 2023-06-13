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
"""This module defines an agent class."""

import unified_planning as up
from unified_planning.model.mixins import (
    ActionsSetMixin,
    FluentsSetMixin,
)
from typing import Optional, List, Union, Iterable
from unified_planning.model.expression import ConstantExpression


class Agent(
    FluentsSetMixin,
    ActionsSetMixin,
):
    """
    This is an agent class that represents a generic `agent`.
    """

    def __init__(
        self,
        name: str,
        ma_problem: "up.model.multi_agent.ma_problem.MultiAgentProblem",
    ):
        FluentsSetMixin.__init__(
            self,
            ma_problem.environment,
            ma_problem._add_user_type,
            self.has_name,
            ma_problem._initial_defaults,
        )
        ActionsSetMixin.__init__(
            self, ma_problem.environment, ma_problem._add_user_type, self.has_name
        )
        self._env = ma_problem.environment
        self._name: str = name
        self._public_fluents: List["up.model.fluent.Fluent"] = []
        self._ma_problem_has_name_not_in_agents = ma_problem.has_name_not_in_agents

    def __getstate__(self):
        state = self.__dict__.copy()
        # Don't pickle MultiAgentProblem methods
        state["_add_user_type_method"] = None
        state["_ma_problem_has_name_not_in_agents"] = None
        return state

    def has_name(self, name: str) -> bool:
        """
        Returns `True` if the given `name` is already in the `MultiAgentProblem`, `False` otherwise.

        :param name: The target name to find in the `MultiAgentProblem`.
        :return: `True` if the given `name` is already in the `MultiAgentProblem`, `False` otherwise.
        """
        return (
            self.has_action(name)
            or self.has_fluent(name)
            or self._ma_problem_has_name_not_in_agents(name)
        )

    def has_name_in_agent(self, name: str) -> bool:
        """
        Returns `True` if the given `name` is already in the `MultiAgentProblem`, `False` otherwise.

        :param name: The target name to find in the `MultiAgentProblem`.
        :return: `True` if the given `name` is already in the `MultiAgentProblem`, `False` otherwise.
        """
        return self.has_action(name) or self.has_fluent(name)

    @property
    def name(self) -> str:
        """Returns the `Agent` `name`."""
        return self._name

    @property
    def environment(self) -> "up.Environment":
        """Returns this `Agent` `Environment`."""
        return self._env

    def add_public_fluent(
        self,
        fluent_or_name: Union["up.model.fluent.Fluent", str],
        typename: Optional["up.model.types.Type"] = None,
        *,
        default_initial_value: Optional["ConstantExpression"] = None,
        **kwargs: "up.model.types.Type",
    ) -> "up.model.fluent.Fluent":
        """Adds the given `public fluent` to the `problem`.
        If the first parameter is not a `Fluent`, the parameters will be passed to the `Fluent` constructor to create it.
        :param fluent_or_name: `Fluent` instance or `name` of the `fluent` to be constructed.
        :param typename: If only the `name` of the `fluent` is given, this is the `fluent's type` (passed to the `Fluent` constructor).
        :param default_initial_value: If provided, defines the default value taken in initial state by
                                      a state variable of this `fluent` that has no explicit value.
        :param kwargs: If only the `name` of the `fluent` is given, these are the `fluent's parameters` (passed to the `Fluent` constructor).
        :return: The `fluent` passed or constructed.
        """
        fluent = self.add_fluent(
            fluent_or_name,
            typename,
            default_initial_value=default_initial_value,
            **kwargs,
        )
        self._public_fluents.append(fluent)
        return fluent

    def add_private_fluent(
        self,
        fluent_or_name: Union["up.model.fluent.Fluent", str],
        typename: Optional["up.model.types.Type"] = None,
        *,
        default_initial_value: Optional["ConstantExpression"] = None,
        **kwargs: "up.model.types.Type",
    ) -> "up.model.fluent.Fluent":
        """Adds the given `private fluent` to the `problem`.
        If the first parameter is not a `Fluent`, the parameters will be passed to the `Fluent` constructor to create it.
        :param fluent_or_name: `Fluent` instance or `name` of the `fluent` to be constructed.
        :param typename: If only the `name` of the `fluent` is given, this is the `fluent's type` (passed to the `Fluent` constructor).
        :param default_initial_value: If provided, defines the default value taken in initial state by
                                      a state variable of this `fluent` that has no explicit value.
        :param kwargs: If only the `name` of the `fluent` is given, these are the `fluent's parameters` (passed to the `Fluent` constructor).
        :return: The `fluent` passed or constructed.
        """
        return self.add_fluent(
            fluent_or_name,
            typename,
            default_initial_value=default_initial_value,
            **kwargs,
        )

    def add_public_fluents(self, fluents: Iterable["up.model.fluent.Fluent"]):
        """
        Adds the given `public fluents` to the `problem`.
        :param fluents: The `public fluents` that must be added to the `problem`.
        """
        for fluent in fluents:
            self.add_public_fluent(fluent)

    def add_private_fluents(self, fluents: Iterable["up.model.fluent.Fluent"]):
        """
        Adds the given `private fluents` to the `problem`.
        :param fluents: The `private fluents` that must be added to the `problem`.
        """
        for fluent in fluents:
            self.add_private_fluent(fluent)

    @property
    def public_fluents(self) -> List["up.model.fluent.Fluent"]:
        """Returns the `fluents` currently in the `problem`."""
        return self._public_fluents

    @property
    def private_fluents(self) -> List["up.model.fluent.Fluent"]:
        """Returns the `fluents` currently in the `problem`."""
        return [f for f in self._fluents if f not in self._public_fluents]

    def __repr__(self) -> str:
        s = []
        s.append(f"Agent name = {str(self._name)}\n\n")
        s.append("private fluents = [\n")
        for f in self.private_fluents:
            s.append(f" {str(f)}\n")
        s.append("]\n\n")
        s.append("public fluents = [\n")
        for f in self._public_fluents:
            s.append(f" {str(f)}\n")
        s.append("]\n\n")
        s.append("actions = [\n")
        for a in self._actions:
            s.append(f" {str(a)}\n")
        s.append("]\n\n")
        return "".join(s)

    def __eq__(self, oth: object) -> bool:
        if not (isinstance(oth, Agent)) or self._env != oth._env:
            return False
        if self._name != oth._name:
            return False
        if set(self._fluents) != set(oth._fluents):
            return False
        if set(self._public_fluents) != set(oth._public_fluents):
            return False
        if set(self._actions) != set(oth._actions):
            return False
        return True

    def __hash__(self) -> int:
        res = hash(self._name)
        for f in self._fluents:
            res += hash(f)
        for f in self._public_fluents:
            res += hash(f)
        for a in self._actions:
            res += hash(a)
        return res
