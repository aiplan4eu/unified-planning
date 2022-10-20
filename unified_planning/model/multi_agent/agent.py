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
            ma_problem.env,
            ma_problem._add_user_type,
            self.has_name,
            ma_problem._initial_defaults,
        )
        ActionsSetMixin.__init__(
            self, ma_problem.env, ma_problem._add_user_type, self.has_name
        )
        self._env = ma_problem.env
        self._name: str = name
        self._goals: List["up.model.fnode.FNode"] = list()

    def __getstate__(self):
        state = self.__dict__.copy()
        # Don't pickle _add_user_type_method
        state["_add_user_type_method"] = None
        return state

    def has_name(self, name: str) -> bool:
        """
        Returns `True` if the given `name` is already in the `MultiAgentProblem`, `False` otherwise.

        :param name: The target name to find in the `MultiAgentProblem`.
        :return: `True` if the given `name` is already in the `MultiAgentProblem`, `False` otherwise."""
        return self.has_action(name) or self.has_fluent(name)

    @property
    def name(self) -> str:
        """Returns the `Agent` `name`."""
        return self._name

    @property
    def env(self) -> "up.Environment":
        """Returns this `Agent` `Environment`."""
        return self._env

    def add_goal(
            self, goal: Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool]
    ):
        """
        Adds the given `goal` to the `Agent`; a goal is an expression that must be evaluated to `True` at the
        end of the execution of a :class:`~unified_planning.plans.Plan`. If a `Plan` does not satisfy all the given `goals`, it is not valid.

        :param goal: The expression added to the `Agent` :func:`goals <unified_planning.model.multi_agent.agent.goals>`.
        """
        assert (
                isinstance(goal, bool) or goal.environment == self._env
        ), "goal does not have the same environment of the problem"
        (goal_exp,) = self._env.expression_manager.auto_promote(goal)
        assert self._env.type_checker.get_type(goal_exp).is_bool_type()
        if goal_exp != self._env.expression_manager.TRUE():
            self._goals.append(goal_exp)

    def add_goals(
            self, goals: List[Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool]]
    ):
        """
        Adds the given `goal` to the `Agent`.

        :param goals: The `list` of `goals` that must be added to the `Agent`.
        """
        for goal in goals:
            self.add_goal(goal)

    @property
    def goals(self) -> List["up.model.fnode.FNode"]:
        """Returns all the `goals` in the `Agent`."""
        return self._goals

    def clear_goals(self):
        """Removes all the `goals` from the `Agent`."""
        self._goals = []

    def __repr__(self) -> str:
        s = []
        s.append(f"Agent name = {str(self._name)}\n\n")
        s.append("fluents = [\n")
        for f in self._fluents:
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
        if set(self._actions) != set(oth._actions):
            return False
        return True

    def __hash__(self) -> int:
        res = hash(self._name)
        for f in self._fluents:
            res += hash(f)
        for a in self._actions:
            res += hash(a)
        return res
