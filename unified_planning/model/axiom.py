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
"""
This module defines the base class `Axiom'.
An `Axiom' has a `head' which is a single `Parameter' and a `body' which is a single `Condition'.
"""

import copy
import unified_planning as up
from unified_planning.environment import get_environment, Environment
from typing import Optional, Union


class Axiom:
    def __init__(
        self,
        _head: "up.model.fluent.Fluent",
        _body: Union[
            "up.model.fnode.FNode",
            "up.model.fluent.Fluent",
            "up.model.parameter.Parameter",
            bool,
        ],
        _env: Optional[Environment] = None,
    ):
        self._environment = get_environment(_env)
        self._head = _head
        self._body = self._environment.expression_manager.auto_promote(_body)[0]

    def __repr__(self) -> str:
        s = []
        s.append("axiom { \n")
        s.append(f"   head = {self._head}\n")
        s.append(f"   body = {self._body}\n")
        s.append("  }")
        return "".join(s)

    def __eq__(self, oth: object) -> bool:
        return (
            isinstance(oth, Axiom)
            and self._environment == oth._environment
            and self._head == oth._head
            and self._body == oth._body
        )

    def __hash__(self) -> int:
        return hash(self._head) + hash(self._body)

    @property
    def environment(self) -> Environment:
        """Returns this `Axiom` `Environment`."""
        return self._environment

    def head(self) -> "up.model.fluent.Fluent":
        """Returns this `Axiom` `Head`."""
        return self._head

    def body(self) -> "up.model.fnode.FNode":
        """Returns this `Axiom` `Body`."""
        return self._body

    def clone(self):
        new_head = copy.copy(self._head)
        new_body = copy.copy(self._body)
        return Axiom(new_head, new_body, self._environment)
