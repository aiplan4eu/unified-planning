# Copyright 2021-2023 AIPlan4EU project
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
"""This module defines an ma_environment class."""
import unified_planning as up
from unified_planning.model.mixins import (
    FluentsSetMixin,
)


class MAEnvironment(
    FluentsSetMixin,
):
    """
    This is an MAEnvironment class that represents a generic `MAEnvironment`.
    """

    def __init__(
        self,
        ma_problem: "up.model.multi_agent.ma_problem.MultiAgentProblem",
    ):
        FluentsSetMixin.__init__(
            self,
            ma_problem.environment,
            ma_problem._add_user_type,
            ma_problem.has_name,
            ma_problem._initial_defaults,
        )
        self._env = ma_problem.environment

    @property
    def environment(self) -> "up.Environment":
        """Returns this `MAEnvironment` `Environment`."""
        return self._env

    def has_name(self, name: str) -> bool:
        """
        Returns `True` if the given `name` is already in the `MultiAgentProblem`, `False` otherwise.

        :param name: The target name to find in the `MultiAgentProblem`.
        :return: `True` if the given `name` is already in the `MultiAgentProblem`, `False` otherwise.
        """
        return self.has_fluent(name)

    def __repr__(self) -> str:
        s = []
        s.append("fluents = [\n")
        for f in self._fluents:
            s.append(f" {str(f)}\n")
        s.append("]\n\n")
        return "".join(s)

    def __eq__(self, oth: object) -> bool:
        if not (isinstance(oth, MAEnvironment)) or self._env != oth._env:
            return False
        if set(self._fluents) != set(oth._fluents):
            return False
        return True

    def __hash__(self) -> int:
        res = 0
        for f in self._fluents:
            res += hash(f)
        return res
