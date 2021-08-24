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
from upf.simplifier import Simplifier
from typing import List, Dict, Tuple
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
        mapping_list = self._fill_mapping_list(expression)
        new_exp = self._recreate_expression(mapping_list)
        return new_exp

    def _recreate_expression(self, mapping_list: Dict[int, List[Tuple[bool, FNode, int]]]) -> FNode:
        #iterating a dict "d" from len(d) to 0
        x = range(0, len(mapping_list))
        l = list(x)
        l.reverse()
        #mapping_fnode contains "mapping_list" converted to expressions.
        mapping_fnode: Dict[int, List[FNode]] = {}
        for i in l:
            mapping_fnode[i] = []
            (mapping_list[i]).reverse()
            for p, e, s in mapping_list[i]:
                if e.is_and():
                    if p:
                        mapping_fnode[i].append(self.manager.Or(mapping_fnode[s]))
                    else:
                        mapping_fnode[i].append(self.manager.And(mapping_fnode[s]))
                elif e.is_or():
                    if p:
                        mapping_fnode[i].append(self.manager.And(mapping_fnode[s]))
                    else:
                        mapping_fnode[i].append(self.manager.Or(mapping_fnode[s]))
                else:
                    if p:
                        mapping_fnode[i].append(self.manager.Not(e))
                    else:
                        mapping_fnode[i].append(e)
        return mapping_fnode[0].pop(0)

    def _fill_mapping_list(self, expression:FNode) -> Dict[int, List[Tuple[bool, FNode, int]]]:
        #Polarity, expression, father
        stack: List[Tuple[bool, FNode, int]] = []
        #stack is a list containing the tuple(polarity, expression, father, sons)
        #where polarity indicates whether the whole expression is positive or negative
        #expression is used to keep track of the expression type
        #father indicates the number of the father (used to re-create the expression in nnf form)
        stack.append((False, expression, 0))
        mapping_list: Dict[int, List[Tuple[bool, FNode, int]]] = {}
        mapping_list[0] = []
        count = 1
        while len(stack) > 0:
            p, e, f = stack.pop()
            if e.is_not():
                stack.append((not p, e.args()[0], f))
                continue
            elif e.is_and() or e.is_or():
                for arg in e.args():
                    stack.append((p, arg, count))
                    mapping_list[count] = []
                mapping_list[f].append((p, e, count))
                count = count + 1
            elif e.is_implies():
                ne = self.manager.create_node(node_type=op.OR, args=())
                mapping_list[count] = []
                mapping_list[f].append((p, ne, count))
                stack.append((not p, e.args()[0], count))
                stack.append((p, e.args()[1], count))
                count = count + 1
            elif e.is_iff():
                #creates 2 fake operations Or and And used to reconstruct back the formula.
                ne_or = self.manager.create_node(node_type=op.OR, args=())
                ne_and = self.manager.create_node(node_type=op.AND, args=())
                #Initializes the 3 lists of mapping_list[count, cpunt+1, count+2] that will
                #be used into the algorithm later.
                mapping_list[count] = []
                mapping_list[count+1] = []
                mapping_list[count+2] = []
                #Appends in mapping_list[f] -> (The position of the father of the IFF operation)
                #the or operation, and the sons of the or will be the 2 ands in position
                #mapping_list[count].
                mapping_list[f].append((p, ne_or, count))
                mapping_list[count].append((p, ne_and, count + 2))
                mapping_list[count].append((p, ne_and, count + 1))
                #The sons of the positive And will be in mapping_list[count+1], while the sons
                #sons of the negative And will be in position mapping_list[count+2].
                stack.append((p, e.args()[0], count+1))
                stack.append((p, e.args()[1], count+1))
                stack.append((not p, e.args()[0], count+2))
                stack.append((not p, e.args()[1], count+2))
                count = count + 3
            else:
                mapping_list[f].append((p, e, -1))
        return mapping_list


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
        self._simplifier = Simplifier(self.env)

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
        new_args: List[List[FNode]] = []
        for a1 in args:
            for a2 in a1:
                new_args.append(a2)
        tuples = product(*new_args)
        new_args.clear()
        for na in tuples:
            new_args.append(list(na))
        print("And")
        print(new_args)
        return new_args

    def walk_or(self, expression: FNode, args: List[List[List[FNode]]], **kwargs) -> List[List[FNode]]:
        new_args: List[FNode] = []
        for a1 in args:
            for a2 in a1:
                for a3 in a2:
                    new_args.append(a3)
                #Second Try:
                #new_args.append(a2)
        #return new_args
        print("Or")
        print(new_args)
        return [new_args]

    @walkers.handles(set(op.ALL_TYPES) - set({op.AND, op.OR}))
    def walk_all(self, expression: FNode, args: List[List[List[FNode]]], **kwargs) -> List[List[FNode]]:
        return [[expression]]
