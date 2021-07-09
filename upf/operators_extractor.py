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
import upf.operators as op
from upf.fnode import FNode
from typing import List, Set


class OperatorsExtractor(walkers.DagWalker):
    """This expression walker returns all the operators of a given expression."""

    def __init__(self):
        walkers.DagWalker.__init__(self)

    def get(self, expression: FNode) -> Set[int]:
        """Returns all the operators of the given expression."""
        return self.walk(expression)

    @walkers.handles(op.ALL_TYPES)
    def walk_all_types(self, expression: FNode, args: List[Set[int]]) -> Set[int]:
        return set(x for y in args for x in y) | {expression.node_type()}
