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


from collections import OrderedDict
import upf.environment
from upf.walkers.identitydag import IdentityDagWalker
import upf.walkers as walkers
import upf.operators as op
from upf.fnode import FNode
from typing import List

class Substituter(IdentityDagWalker):
    """Performs substitution into an expression """
    def __init__(self, env: 'upf.environment.Environment'):
        IdentityDagWalker.__init__(self, env, True)

    def _get_key(self, expression, **kwargs):
        return expression

    def substitute(self, expression: FNode, substitutions: OrderedDict = None) -> FNode:
        """Performs substitution into the given expression."""
        if substitutions is None:
            return expression
        #CHECK CHE I TIPI SIANO COMPATIBILI!!!
        # else:
        #     for exp in substitutions.keys():
        #         if not self._is_compatible_type():
        return self.walk(expression, subs = substitutions)

    @walkers.handles(op.ALL_TYPES)
    def walk_replace_or_identity(self, expression: FNode, args: List[FNode], subs: OrderedDict = OrderedDict(), **kwargs) -> FNode:
        if expression in subs:
            return subs[expression]
        else:
            return IdentityDagWalker.super(self, expression, args, **kwargs)
