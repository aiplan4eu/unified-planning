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

from upf.exceptions import UPFTypeError
from upf.expression import Expression
import upf.environment
from upf.walkers.identitydag import IdentityDagWalker
import upf.walkers as walkers
import upf.operators as op
from upf.fnode import FNode
from typing import List
import typing
from upf.type_checker import TypeChecker

class Substituter(IdentityDagWalker):
    """Performs substitution into an expression """
    def __init__(self, env: 'upf.environment.Environment'):
        IdentityDagWalker.__init__(self, env, True)
        self.env = env
        self.manager = env.expression_manager
        self.type_checker = TypeChecker(env)

    def _get_key(self, expression, **kwargs):
        return expression

    def substitute(self, expression: FNode, substitutions: typing.Dict[Expression, Expression] = {}) -> FNode:
        """Performs substitution into the given expression.

        Lets consider the examples:
        f = a & b
        subs = {a -> c, (c & b) -> d, (a & b) -> c}
        substitute(f, subs) = c

        f = a
        subs = {a -> c, c -> d}
        substitute(f, subs) = c

        f = a & b
        subs = {a -> 5, b -> c}
        substitute(f, subs) raises an UPFTypeError

        Note that, since subs is a dictionary:
        f = a
        subs = {a -> b, a -> c}
        substitute(f, subs) = c
        """

        if len(substitutions) == 0:
            return expression
        new_substitutions: typing.Dict[FNode, FNode] = {}
        new_keys = self.manager.auto_promote(substitutions.keys())
        new_values = self.manager.auto_promote(substitutions.values())
        new_substitutions = dict(zip(new_keys, new_values))
        for k, v in new_substitutions.items():
            if not self.type_checker.is_compatible_type(k, v):
                raise UPFTypeError(
                    f"The expression type of {str(k)} is not compatible with the given substitution {str(v)}")
        return self.walk(expression, subs = new_substitutions)

    @walkers.handles(op.ALL_TYPES)
    def walk_replace_or_identity(self, expression: FNode, args: List[FNode], subs: dict = {}, **kwargs) -> FNode:
        if expression in subs:
            return subs[expression]
        else:
            return IdentityDagWalker.super(self, expression, args, **kwargs)
