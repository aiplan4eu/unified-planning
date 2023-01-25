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


from functools import reduce
from typing import List, Set
import unified_planning as up
import unified_planning.environment
import unified_planning.model.walkers as walkers
from unified_planning.model.fnode import FNode
import unified_planning.model.operators as op


class NamesExtractor(walkers.dag.DagWalker):
    """
    TODO
    """

    def __init__(
        self,
        env: "unified_planning.environment.Environment",
    ):
        walkers.dag.DagWalker.__init__(self)
        self.env = env
        self._defined_names: Set[str] = set()

    def extract_names(self, expression: FNode) -> Set[str]:
        """
        TODO
        Performs basic simplification of the given expression.

        If a :class:`~unified_planning.model.Problem` is given at the constructor, it also uses the static `fluents` of the `Problem` for
        a better simplification.

        :param expression: The target expression that must be simplified with constant propagation.
        :return: The simplified expression.
        """
        return self.walk(expression).copy()

    def _args_union(self, args: List[Set[str]], base: Set[str]) -> Set[str]:
        return reduce(lambda x, y: x.union(y), args, base)

    @walkers.handles(op.OperatorKind.EXISTS, op.OperatorKind.FORALL)
    def walk_quantifier(self, expression: FNode, args: List[Set[str]]) -> Set[str]:
        assert len(args) == 1
        vars_names = set((v.name for v in expression.variables()))
        return self._args_union(args, vars_names)

    def walk_fluent_exp(self, expression: FNode, args: List[Set[str]]) -> Set[str]:
        return self._args_union(args, {expression.fluent().name})

    def walk_param_exp(self, expression: FNode, args: List[Set[str]]) -> Set[str]:
        return self._args_union(args, {expression.parameter().name})

    def walk_variable_exp(self, expression: FNode, args: List[Set[str]]) -> Set[str]:
        return self._args_union(args, {expression.variable().name})

    def walk_object_exp(self, expression: FNode, args: List[Set[str]]) -> Set[str]:
        return self._args_union(args, {expression.object().name})

    def walk_dot(self, expression: FNode, args: List[Set[str]]) -> Set[str]:
        return self._args_union(args, {expression.agent().name})

    @walkers.handles(
        op.OperatorKind.AND,
        op.OperatorKind.OR,
        op.OperatorKind.NOT,
        op.OperatorKind.IMPLIES,
        op.OperatorKind.IFF,
        op.OperatorKind.TIMING_EXP,
        op.OperatorKind.BOOL_CONSTANT,
        op.OperatorKind.INT_CONSTANT,
        op.OperatorKind.REAL_CONSTANT,
        op.OperatorKind.PLUS,
        op.OperatorKind.MINUS,
        op.OperatorKind.TIMES,
        op.OperatorKind.DIV,
        op.OperatorKind.LE,
        op.OperatorKind.LT,
        op.OperatorKind.EQUALS,
    )
    def walk_union(self, expression: FNode, args: List[Set[str]]) -> Set[str]:
        return self._args_union(args, set())
