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
"""This module defines the quantifiers remover class."""


import unified_planning.model
import unified_planning.walkers as walkers
from unified_planning.walkers.identitydag import IdentityDagWalker
from unified_planning.model import Object, FNode, operators as op
from unified_planning.model.expression import Expression
from typing import List, Dict
from itertools import product


class ExpressionQuantifiersRemover(IdentityDagWalker):
    def __init__(self, env):
        self._env = env
        IdentityDagWalker.__init__(self, self._env, True)
        self._substituter = walkers.Substituter(self._env)

    def remove_quantifiers(self, expression: FNode, problem: 'unified_planning.model.Problem'):
        self._problem = problem
        return self.walk(expression)

    def _help_walk_quantifiers(self, expression: FNode, args: List[FNode]) -> List[FNode]:
        vars = expression.variables()
        type_list = [v.type() for v in vars]
        possible_objects: List[List[Object]] = [self._problem.objects(t) for t in type_list]
        #product of n iterables returns a generator of tuples where
        # every tuple has n elements and the tuples make every possible
        # combination of 1 item for each iterable. For example:
        #product([1,2], [3,4], [5,6], [7]) =
        # (1,3,5,7) (1,3,6,7) (1,4,5,7) (1,4,6,7) (2,3,5,7) (2,3,6,7) (2,4,5,7) (2,4,6,7)
        subs_results = []
        for o in product(*possible_objects):
            subs: Dict[Expression, Expression] = dict(zip(vars, list(o)))
            subs_results.append(self._substituter.substitute(args[0], subs))
        return subs_results

    @walkers.handles(op.EXISTS)
    def walk_exists(self, expression: FNode, args: List[FNode], **kwargs) -> FNode:
        subs_results = self._help_walk_quantifiers(expression, args)
        return self._env.expression_manager.Or(subs_results)

    @walkers.handles(op.FORALL)
    def walk_forall(self, expression: FNode, args: List[FNode], **kwargs) -> FNode:
        subs_results = self._help_walk_quantifiers(expression, args)
        return self._env.expression_manager.And(subs_results)
