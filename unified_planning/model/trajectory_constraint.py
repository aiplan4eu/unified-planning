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
"""
This module defines the Trajectory Constraints base class and some of his extentions.
"""

import unified_planning as up
from unified_planning.environment import get_env, Environment
from unified_planning.exceptions import (
    UPTypeError,
    UPUnboundedVariablesError,
    UPProblemDefinitionError,
)
from fractions import Fraction
from typing import Dict, List, Union, Optional


class TrajectoryConstraint:
    """This is the trajectory constraint interface."""

    def __init__(
        self,
        _type: str,
        _parameters: "List[up.model.fnode.FNode]" = None,
        _env: Environment = None,
        **kwargs: "up.model.types.Type",
    ):
        self._env = get_env(_env)
        self._type = _type
        match self._type:
            case "always":
                assert (
                    len(_parameters) == 1
                ), "Always constraint require only one fluent"
                self._parameters = _parameters
            case "sometime":
                assert (
                    len(_parameters) == 1
                ), "Sometime constraint require only one fluent"
                self._parameters = _parameters
            case "at-most-once":
                assert (
                    len(_parameters) == 1
                ), "Sometime constraint require only one fluent"
                self._parameters = _parameters
            case "sometime-after":
                assert (
                    len(_parameters) == 2
                ), "Sometime-after constraint require only one fluent"
                self._parameters = _parameters
            case "sometime-before":
                assert (
                    len(_parameters) == 2
                ), "Sometime-before constraint require only one fluent"
                self._parameters = _parameters
            case _:
                raise Exception(
                    f"Insert not correct trajectory constraint. Insert {self._type}"
                )

    def __eq__(self, oth: object) -> bool:
        raise NotImplementedError

    def __hash__(self) -> int:
        raise NotImplementedError

    def clone(self):
        raise NotImplementedError

    @property
    def type(self) -> str:
        """Returns the type of trajectory constraint."""
        return self._type

    @type.setter
    def type(self, new_type: str):
        """Sets the type of trajectory constraint."""
        self._type = new_type

    @property
    def parameters(self) -> List["up.model.fluent.Fluent"]:
        """Returns the list of the action parameters."""
        return list(self._parameters)

    def __repr__(self) -> str:
        s = []
        s.append(f"{self.type} ")
        first = True
        for p in self.parameters:
            if first:
                s.append("(")
                first = False
            else:
                s.append(", ")
            s.append(str(p))
        s.append(")")
        return "".join(s)

    def __hash__(self) -> int:
        res = hash(self._type)
        for par in self._parameters():
            res += hash(par)
        return res
