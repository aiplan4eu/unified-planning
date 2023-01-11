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


import unified_planning.environment
import unified_planning.model.walkers as walkers
from unified_planning.exceptions import UPUnreachableCodeError
from unified_planning.model.fnode import FNode
from unified_planning.model.operators import OperatorKind
from typing import List, Tuple
from itertools import product


class Nnf:
    """
    Class used to transform a logic expression into the equivalent
    Negation Normal Form expression.

    This is done first by removing all the Implications and Equalities,
    then by pushing all the not to the leaves of the Tree representing the expression.
    """

    def __init__(self, environment: "unified_planning.environment.Environment"):
        self.environment = environment
        self.manager = environment.expression_manager

    def get_nnf_expression(self, expression: FNode) -> FNode:
        """Function used to transform a logic expression into the equivalent
        Negational Normal Form expression.

        This is done first by removing all the Implications and Equalities,
        and by pushing all the not to the leaves of the Tree representing the expression.

        For example, the form: !(a => (b && c)) becomes:
        a && (!b || !c), therefore it is a NNF.

        :param expression: The expression that must be returned in NNF form.
        :return: The expression semantically equivalent to the given expression, but in NNF form.
        """
        stack: List[Tuple[bool, FNode, bool]] = []
        stack.append((True, expression, False))
        solved: List[FNode] = []
        while len(stack) > 0:
            p, e, status = stack.pop()
            if status:
                if e.is_and():
                    args = [solved.pop() for _ in range(len(e.args))]
                    if p:
                        new_e = self.manager.And(args)
                    else:
                        new_e = self.manager.Or(args)
                    solved.append(new_e)
                elif e.is_or():
                    args = [solved.pop() for _ in range(len(e.args))]
                    if p:
                        new_e = self.manager.Or(args)
                    else:
                        new_e = self.manager.And(args)
                    solved.append(new_e)
                else:
                    raise UPUnreachableCodeError(
                        "This code branch should never be reached!"
                    )
            else:
                if e.is_not():
                    stack.append((not p, e.arg(0), False))
                elif e.is_and() or e.is_or():
                    stack.append((p, e, True))
                    for arg in e.args:
                        stack.append((p, arg, False))
                elif e.is_implies():
                    na1 = self.manager.Not(e.arg(0))
                    new_e = self.manager.Or(na1, e.arg(1))
                    # stack.append((p, new_e, False)) would be enough.
                    # but this requires more iterations on the stack
                    # while the arguments can be expanded in this
                    # iteration.
                    stack.append((p, new_e, True))
                    stack.append((not p, e.arg(0), False))
                    stack.append((p, e.arg(1), False))
                elif e.is_iff():
                    na1 = self.manager.Not(e.arg(0))
                    na2 = self.manager.Not(e.arg(1))
                    e1 = self.manager.And(e.arg(0), e.arg(1))
                    e2 = self.manager.And(na1, na2)
                    new_e = self.manager.Or(e1, e2)
                    # stack.append((p, new_e, False)) would be enough.
                    # but this requires more iterations on the stack
                    # while the arguments can be expanded in this
                    # iteration.
                    stack.append((p, new_e, True))
                    stack.append((p, e1, True))
                    stack.append((p, e.arg(0), False))
                    stack.append((p, e.arg(1), False))
                    stack.append((p, e2, True))
                    stack.append((not p, e.arg(0), False))
                    stack.append((not p, e.arg(1), False))
                else:
                    if p:
                        solved.append(e)
                    else:
                        solved.append(self.manager.Not(e))
        assert len(solved) == 1  # sanity check
        return solved.pop()


class Dnf(walkers.dag.DagWalker):
    """Class used to transform a logic expression into the equivalent
    Disjunctive Normal Form expression.

    This is done first by transforming the expression into a NNF expression,
    and then every And and Or are propagated to be a unique equivalent Or of
    Ands or Atomic expressions, where 'atomic expressions' could also be a
    Not of an atomic expression.
    """

    def __init__(self, environment: "unified_planning.environment.Environment"):
        walkers.dag.DagWalker.__init__(self, True)
        self.environment = environment
        self.manager = environment.expression_manager
        self._nnf = Nnf(self.environment)
        self._simplifier = walkers.simplifier.Simplifier(self.environment)

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
        return self.manager.Or(self.manager.And(and_args) for and_args in tuples)

    def walk_and(
        self, expression: FNode, args: List[List[List[FNode]]], **kwargs
    ) -> List[List[FNode]]:
        res: List[List[FNode]] = []
        tuples = product(*args)
        # tuples is an iterable of tuples, where each tuple
        # represents one son of the resulting Or.
        # list will contain each son of the resulting And.
        # for example:
        #   tuples = ([a, b], [c]) ([d])
        # will result in
        #   Or(And(a, b, c), And(d))
        for conj_list in tuples:
            big_conjunction = [lit for conj in conj_list for lit in conj]
            simp = self._simplifier.simplify(self.manager.And(big_conjunction))
            if simp.is_true():
                return []
            elif simp.is_false():
                pass
            elif simp.is_and():
                res.append(simp.args)
            else:
                res.append([simp])
        return res

    def walk_or(
        self, expression: FNode, args: List[List[List[FNode]]], **kwargs
    ) -> List[List[FNode]]:
        return [conjunction for disjunction in args for conjunction in disjunction]

    @walkers.handles(set(OperatorKind) - set({OperatorKind.AND, OperatorKind.OR}))
    def walk_all(
        self, expression: FNode, args: List[List[List[FNode]]], **kwargs
    ) -> List[List[FNode]]:
        return [[expression]]
