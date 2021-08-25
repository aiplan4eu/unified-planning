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


import upf.environment
import upf.operators as op
import upf.walkers as walkers
from upf.walkers.dag import DagWalker
from upf.fnode import FNode
from typing import List, Tuple
from itertools import product


class Nnf():
    """Class used to transform a logic expression into the equivalent
    Negational Normal Form expression.

    This is done first by removing all the Implications and Equalities,
    then by pushing all the not to the leaves of the Tree representing the expression."""

    def __init__(self, env: 'upf.environment.Environment'):
        self.env = env
        self.manager = env.expression_manager

    def get_nnf_expression(self, expression: FNode) -> FNode:
        """Function used to transform a logic expression into the equivalent
        Negational Normal Form expression.

        This is done first by removing all the Implications and Equalities,
        and by pushing all the not to the leaves of the Tree representing the expression.

        For example, the form: !(a => (b && c)) becomes:
        a && (!b || !c), therefore it is a NNF."""
        stack: List[Tuple[bool, FNode, bool]] = []
        stack.append((True, expression, False))
        solved: List[FNode] = []
        while len(stack) > 0:
            p, e, status = stack.pop()
            if status:
                if e.is_and():
                    args = [solved.pop() for i in range(len(e.args()))]
                    if p:
                        new_e = self.manager.And(args)
                    else:
                        new_e = self.manager.Or(args)
                    solved.append(new_e)
                elif e.is_or():
                    args = [solved.pop() for i in range(len(e.args()))]
                    if p:
                        new_e = self.manager.Or(args)
                    else:
                        new_e = self.manager.And(args)
                    solved.append(new_e)
                else:
                    assert False
            else:
                if e.is_not():
                    stack.append((not p, e.arg(0), False))
                elif e.is_and() or e.is_or():
                    stack.append((p, e, True))
                    for arg in e.args():
                        stack.append((p, arg, False))
                elif e.is_implies():
                    na1 = self.manager.Not(e.arg(0))
                    new_e = self.manager.Or(na1, e.arg(1))
                    stack.append((p, new_e, True))
                    stack.append((not p, e.arg(0), False))
                    stack.append((p, e.arg(1), False))
                elif e.is_iff():
                    new_e = self.manager.Or(self.manager.And(e.arg(0), e.arg(1)),
                                            self.manager.And(self.manager.Not(e.arg(0)),
                                                             self.manager.Not(e.arg(1))))
                    stack.append((p, new_e, False))
                else:
                    if p:
                        solved.append(e)
                    else:
                        solved.append(self.manager.Not(e))
        return solved.pop()




class Dnf(DagWalker):
    """Class used to transform a logic expression into the equivalent
    Disjunctive Normal Form expression.

    This is done first by transforming the expression into a NNF expression,
    and then every And and Or are propagated to be a unique equivalent Or of
    Ands or Atomic expressions, where 'atomic expressions' could also be a
    Not of an atomic expression.
    """
    def __init__(self, env: 'upf.environment.Environment'):
        DagWalker.__init__(self, True)
        self.env = env
        self.manager = env.expression_manager
        self._nnf = Nnf(self.env)

    def get_dnf_expression(self, expression: FNode) -> FNode:
        """Function used to transform a logic expression into the equivalent
        Disjunctive Normal Form expression.

        This is done first by transforming the expression into a NNF expression,
        and then every And and Or are propagated to be a unique equivalent Or of
        Ands or Atomic expressions, where 'atomic expressions' could also be a
        Not of an atomic expression.

        For example, the form: !(a => (b && c)) becomes:
        a && (!b || !c), in NNF form, and then:
        (a && !b) || (a && !c), therefore a DNF expression."""
        nnf_exp = self._nnf.get_nnf_expression(expression)
        tuples = self.walk(nnf_exp)
        and_list: List[FNode] = []
        for and_args in tuples:
            and_list.append(self.manager.And(and_args))
        return self.manager.Or(and_list)

    def walk_and(self, expression: FNode, args: List[List[List[FNode]]], **kwargs) -> List[List[FNode]]:
        res: List[List[FNode]] = []
        tuples = product(*args)
        for na in tuples:
            nl: List[FNode] = []
            to_add = True
            for nat in na:
                for ne in nat:
                    if ne.is_not():
                        if ne.arg(0) in nl:
                            to_add = False
                            break
                    else:
                        if self.manager.Not(ne) in nl:
                            to_add = False
                            break
                    if ne not in nl:
                        nl.append(ne)
                if not to_add:
                    break
            if to_add:
                res.append(nl)
        return res

    def walk_or(self, expression: FNode, args: List[List[List[FNode]]], **kwargs) -> List[List[FNode]]:
        res: List[List[FNode]] = []
        for a1 in args:
            res.extend(a1)
        return res

    @walkers.handles(set(op.ALL_TYPES) - set({op.AND, op.OR}))
    def walk_all(self, expression: FNode, args: List[List[List[FNode]]], **kwargs) -> List[List[FNode]]:
        return [[expression]]
