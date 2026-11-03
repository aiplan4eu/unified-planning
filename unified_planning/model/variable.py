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
"""
This module defines the Variable class.
A Variable has a name and a type.
"""

from typing import List, Optional, FrozenSet
from unified_planning.environment import Environment, get_environment
from unified_planning.exceptions import UPTypeError
from unified_planning.model.fnode import FNode
from unified_planning.model.operators import OperatorKind
import unified_planning
import unified_planning.model.walkers as walkers
import unified_planning.model.operators as op


class Variable:
    """Represents a variable with a name, a type and optional integer bounds.

    Bounds are inclusive expressions that restrict the variable's range in
    addition to its type. They are only allowed for variables of integer type.
    """

    def __init__(
        self,
        name: str,
        typename: "unified_planning.model.types.Type",
        environment: Optional[Environment] = None,
        *,
        lower_bound: Optional["unified_planning.model.expression.Expression"] = None,
        upper_bound: Optional["unified_planning.model.expression.Expression"] = None,
    ):
        self._name = name
        self._typename = typename
        self._env = get_environment(environment)
        assert self._env.type_manager.has_type(typename), (
            "type of variable does not belong to the same environment of the variable"
        )
        if (
            lower_bound is not None or upper_bound is not None
        ) and not typename.is_int_type():
            raise UPTypeError(
                "Variable bounds are only supported for integer variables."
            )
        em = self._env.expression_manager
        self._lower_bound = (
            None if lower_bound is None else em.auto_promote(lower_bound)[0]
        )
        self._upper_bound = (
            None if upper_bound is None else em.auto_promote(upper_bound)[0]
        )
        for bound in (self._lower_bound, self._upper_bound):
            if bound is not None and not bound.type.is_int_type():
                raise UPTypeError("Variable bounds must be integer expressions.")

    def __repr__(self) -> str:
        if self.lower_bound is not None or self.upper_bound is not None:
            lower = "-inf" if self.lower_bound is None else str(self.lower_bound)
            upper = "inf" if self.upper_bound is None else str(self.upper_bound)
            return f"{str(self.type)} {self.name} in [{lower}, {upper}]"
        return f"{str(self.type)} {self.name}"

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, Variable):
            return (
                self._name == oth._name
                and self._typename == oth._typename
                and self._env == oth._env
                and self._lower_bound == oth._lower_bound
                and self._upper_bound == oth._upper_bound
            )
        else:
            return False

    def __hash__(self) -> int:
        return hash(
            (
                self._name,
                self._typename,
                self._env,
                self._lower_bound,
                self._upper_bound,
            )
        )

    @property
    def name(self) -> str:
        """Returns the `Variable` name."""
        return self._name

    @property
    def type(self) -> "unified_planning.model.types.Type":
        """Returns the `Variable` `Type`."""
        return self._typename

    @property
    def environment(self) -> "Environment":
        """Return the `Variable` `Environment`."""
        return self._env

    @property
    def lower_bound(self) -> Optional[FNode]:
        """Returns the optional inclusive lower bound as an expression."""
        return self._lower_bound

    @property
    def upper_bound(self) -> Optional[FNode]:
        """Returns the optional inclusive upper bound as an expression."""
        return self._upper_bound

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

    def __pos__(self):
        return self._env.expression_manager.Plus(0, self)

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

    def Not(self):
        return self._env.expression_manager.Not(self)

    def __invert__(self):
        return self._env.expression_manager.Not(self)

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

    def _get_children(self, expression: FNode):
        children = list(expression.args)
        if expression.is_variable_exp():
            variables: List[Variable] = [expression.variable()]
        elif expression.is_exists() or expression.is_forall():
            variables = expression.variables()
        else:
            return children
        # Bounds live on the variable, outside the expression's arguments.
        for variable in variables:
            for bound in (variable.lower_bound, variable.upper_bound):
                if bound is not None:
                    children.append(bound)
        return children

    def get_free_variables(self, expression: FNode) -> FrozenSet[Variable]:
        """Returns the FrozenSet of Symbols appearing free in the expression."""
        return self.walk(expression)

    @walkers.handles(OperatorKind.VARIABLE_EXP)
    def walk_variable_exp(
        self,
        expression: FNode,
        args: List[FrozenSet[Variable]],
        **kwargs,
    ) -> FrozenSet[Variable]:
        # pylint: disable=unused-argument
        return frozenset((expression.variable(),)).union(*args)

    @walkers.handles(OperatorKind.EXISTS, OperatorKind.FORALL)
    def walk_quantifier(
        self,
        expression: FNode,
        args: List[FrozenSet[Variable]],
        **kwargs,
    ) -> FrozenSet[Variable]:
        # pylint: disable=unused-argument
        return frozenset(v for variables in args for v in variables).difference(
            expression.variables()
        )

    @walkers.handles(op.CONSTANTS)
    def walk_constant(
        self,
        expression: FNode,
        args: List[FrozenSet[Variable]],
        **kwargs,
    ) -> FrozenSet[Variable]:
        # pylint: disable=unused-argument
        return frozenset()

    @walkers.handles(
        set(OperatorKind)
        - {
            OperatorKind.VARIABLE_EXP,
            OperatorKind.EXISTS,
            OperatorKind.FORALL,
        }
    )
    def walk_all(
        self,
        expression: FNode,
        args: List[FrozenSet[Variable]],
        **kwargs,
    ) -> FrozenSet[Variable]:
        return frozenset(v for s in args for v in s)
