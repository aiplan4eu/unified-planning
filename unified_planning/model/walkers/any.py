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

import unified_planning.model.walkers as walkers
from unified_planning.model.fnode import FNode
from unified_planning.model.operators import OperatorKind
from typing import List, Callable, Set


class AnyChecker(walkers.dag.DagWalker):
    """This expression walker checks if any subexpression matches a given predicate."""

    def __init__(self, predicate: Callable[[FNode], bool]):
        walkers.dag.DagWalker.__init__(self)
        self._predicate = predicate

    def any(self, expression: FNode) -> bool:
        """
        Checks if any of the subexpression matches the predicate.

        :param expression: The tested expression.
        :return: True if any of the subexpression matches the predicate.
        """
        return self.walk(expression)

    @walkers.handles(OperatorKind)
    def walk_all_types(self, expression: FNode, args: List[bool]) -> bool:
        return self._predicate(expression) or any(x for x in args)


class AnyGetter(walkers.dag.DagWalker):
    """This expression walker returns any subexpression that matches the given predicate."""

    def __init__(self, predicate: Callable[[FNode], bool]):
        walkers.dag.DagWalker.__init__(self)
        self._predicate = predicate

    def get(self, expression: FNode) -> Set[FNode]:
        """
        Returns all the subexpressions matching the predicate given at the constructor.

        :param expression: The expression from where all the subexrepssions are extracted.
        :return: The set of the subexpressions matching the predicate.
        """
        return self.walk(expression)

    @walkers.handles(OperatorKind)
    def walk_all_types(self, expression: FNode, args: List[Set[FNode]]) -> Set[FNode]:
        ret_set: Set[FNode] = {expression} if self._predicate(expression) else set()
        for x in args:
            ret_set |= x
        return ret_set
