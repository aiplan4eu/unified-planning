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
This module defines the Fluent class.
A Fluent has a name, a type and a signature
that defines the types of its parameters.
"""

import unified_planning
from unified_planning.environment import get_env, Environment
from typing import List


class Fluent:
    """Represents a fluent."""
    def __init__(self, name: str, typename: 'unified_planning.model.types.Type' = None,
                 signature: List['unified_planning.model.types.Type'] = [], env: Environment = None):
        self._env = get_env(env)
        self._name = name
        if typename is None:
            self._typename = self._env.type_manager.BoolType()
        else:
            self._typename = typename
        self._signature = signature

    def __repr__(self) -> str:
        return f'{str(self.type())} {self.name()}{str(self.signature()) if self.arity() > 0 else ""}'

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, Fluent):
            return self._name == oth._name and self._typename == oth._typename and self._signature == oth._signature and self._env == oth._env
        else:
            return False

    def __hash__(self) -> int:
        res = hash(self._typename)
        for s in self._signature:
            res += hash(s)
        return res ^ hash(self._name)

    def name(self) -> str:
        """Returns the fluent name."""
        return self._name

    def type(self) -> 'unified_planning.model.types.Type':
        """Returns the fluent type."""
        return self._typename

    def signature(self) -> List['unified_planning.model.types.Type']:
        """Returns the fluent signature.
        The signature is the list of types of the fluent parameters.
        """
        return self._signature

    def arity(self) -> int:
        """Returns the fluent arity."""
        return len(self._signature)

    def __call__(self, *args: 'unified_planning.model.expression.Expression') -> 'unified_planning.model.fnode.FNode':
        """Returns a fluent expression with the given parameters."""
        return self._env.expression_manager.FluentExp(self, args)
