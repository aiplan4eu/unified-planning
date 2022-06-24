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
"""
This module defines the Variable class.
A Variable has a name and a type.
"""


from typing import List, Set
from unified_planning.environment import Environment, get_env
from unified_planning.model.fnode import FNode
from unified_planning.model.operators import OperatorKind
import unified_planning
import unified_planning.model.walkers as walkers
import unified_planning.model.operators as op



class Variable:
    """Represents a varible."""
    def __init__(self, name: str, typename: 'unified_planning.model.types.Type', env: Environment = None):
        self._name = name
        self._typename = typename
        self._env = get_env(env)

    def __repr__(self) -> str:
        return f'{str(self.type)} {self.name}'

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, Variable):
            return self._name == oth._name and self._typename == oth._typename
        else:
            return False

    def __hash__(self) -> int:
        return hash(self._name) + hash(self._typename)

    @property
    def name(self) -> str:
        """Returns the variable name."""
        return self._name

    @property
    def type(self) -> 'unified_planning.model.types.Type':
        """Returns the variable type."""
        return self._typename

    @property
    def env(self) -> 'Environment':
        """Return the object environment"""
        return self._env

    #
    # Infix operators
    #

    def __add__(self, right):
        return self._env.expression_manager.Plus(self, right)

    def __radd__(self, left):
        return self._env.expression_manager.Plus(left, self)

    def __sub__(self, right):
        return self._env.expression_manager.Minus(self, right)

    def __rsub__(self, left):
        return self._env.expression_manager.Minus(left, self)

    def __mul__(self, right):
        return self._env.expression_manager.Times(self, right)

    def __rmul__(self, left):
        return self._env.expression_manager.Times(left, self)

    def __truediv__(self, right):
        return self._env.expression_manager.Div(self, right)

    def __rtruediv__(self, left):
        return self._env.expression_manager.Div(left, self)

    def __floordiv__(self, right):
        return self._env.expression_manager.Div(self, right)

    def __rfloordiv__(self, left):
        return self._env.expression_manager.Div(left, self)

    def __gt__(self, right):
        return self._env.expression_manager.GT(self, right)

    def __ge__(self, right):
        return self._env.expression_manager.GE(self, right)

    def __lt__(self, right):
        return self._env.expression_manager.LT(self, right)

    def __le__(self, right):
        return self._env.expression_manager.LE(self, right)

    def __neg__(self):
        return self._env.expression_manager.Minus(0, self)

    def Equals(self, right):
        return self._env.expression_manager.Equals(self, right)

    def And(self, *other):
        return self._env.expression_manager.And(self, *other)

    def __and__(self, *other):
        return self._env.expression_manager.And(self, *other)

    def __rand__(self, *other):
        return self._env.expression_manager.And(*other, self)

    def Or(self, *other):
        return self._env.expression_manager.Or(self, *other)

    def __or__(self, *other):
        return self._env.expression_manager.Or(self, *other)

    def __ror__(self, *other):
        return self._env.expression_manager.Or(*other, self)

    def Xor(self, *other):
        em = self._env.expression_manager
        return em.And(em.Or(self, *other), em.Not(em.And(self, *other)))

    def __xor__(self, *other):
        em = self._env.expression_manager
        return em.And(em.Or(self, *other), em.Not(em.And(self, *other)))

    def __rxor__(self, other):
        em = self._env.expression_manager
        return em.And(em.Or(*other, self), em.Not(em.And(*other, self)))

    def Implies(self, right):
        return self._env.expression_manager.Implies(self, right)

    def Iff(self, right):
        return self._env.expression_manager.Iff(self, right)


class FreeVarsOracle(walkers.DagWalker):
    # We have only few categories for this walker.
    #
    # - Quantifiers need to exclude bounded variables
    # - Other operators need to return the union of all their sons
    # - Constants have no impact

    def get_free_variables(self, expression: FNode) -> Set[Variable]:
        """Returns the set of Symbols appearing free in the expression."""
        return self.walk(expression)

    @walkers.handles(OperatorKind.VARIABLE_EXP)
    def walk_variable_exp(self, expression: FNode, args: List[Set[Variable]], **kwargs) -> Set[Variable]:
        #pylint: disable=unused-argument
        return {expression.variable()}

    @walkers.handles(OperatorKind.EXISTS, OperatorKind.FORALL)
    def walk_quantifier(self, expression: FNode, args: List[Set[Variable]], **kwargs) -> Set[Variable]:
        #pylint: disable=unused-argument
        return args[0].difference(expression.variables())

    @walkers.handles(op.CONSTANTS)
    def walk_constant(self, expression: FNode, args: List[Set[Variable]], **kwargs) -> Set[Variable]:
        #pylint: disable=unused-argument
        return set()

    @walkers.handles(set(OperatorKind) - {OperatorKind.VARIABLE_EXP, OperatorKind.EXISTS, OperatorKind.FORALL})
    def walk_all(self, expression: FNode, args: List[Set[Variable]], **kwargs) -> Set[Variable]:
        return {v for s in args for v in s}
