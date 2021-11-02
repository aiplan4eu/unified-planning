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


import upf.walkers as walkers

import upf.environment
from upf.walkers.identitydag import IdentityDagWalker
from upf.model import FNode, operators as op
from upf.type_checker import TypeChecker
from upf.exceptions import UPFTypeError
from upf.model import Expression
from typing import List, Dict


class Substituter(IdentityDagWalker):
    """Performs substitution into an expression """
    def __init__(self, env: 'upf.environment.Environment'):
        IdentityDagWalker.__init__(self, env, True)
        self.env = env
        self.manager = env.expression_manager
        self.type_checker = env.type_checker

    def _get_key(self, expression, **kwargs):
        return expression

    def substitute(self, expression: FNode, substitutions: Dict[Expression, Expression] = {}) -> FNode:
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
        new_substitutions: Dict[FNode, FNode] = {}
        for k, v in substitutions.items():
            new_k, new_v = self.manager.auto_promote(k, v)
            if self.type_checker.is_compatible_type(new_k, new_v):
                new_substitutions[new_k] = new_v
            else:
                raise UPFTypeError(
                    f"The expression type of {str(k)} is not compatible with the given substitution {str(v)}")
        return self.walk(expression, subs = new_substitutions)

    @walkers.handles(op.ALL_TYPES)
    def walk_replace_or_identity(self, expression: FNode, args: List[FNode], subs: Dict[FNode, FNode] = {}, **kwargs) -> FNode:
        res = subs.get(expression, None)
        if res is not None:
            return res
        else:
            return IdentityDagWalker.super(self, expression, args, **kwargs)
