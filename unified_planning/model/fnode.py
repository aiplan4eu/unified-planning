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
"""FNode are the building blocks of expressions."""

import unified_planning
import unified_planning.model.fluent
import collections
from unified_planning.environment import Environment
from unified_planning.model.operators import OperatorKind
from typing import Dict, List, Optional, Set, Union
from fractions import Fraction

FNodeContent = collections.namedtuple("FNodeContent", ["node_type", "args", "payload"])


class FNode(object):

    """
    The `FNode` class represents an `expression tree` in the `unified_planning` library.

    Since the `FNode` is immutable and the same `expression` can be used in more than one `expression tree`, it
    is actually a `DAG`, but the `single expression` can be seen as a `tree` for simplicity.

    All the expressions are managed by the :func:`ExpressionManager <unified_planning.Environment.expression_manager>` in the `Environment`, so this class should never
    be instantiated or modified by the user.
    """

    __slots__ = ["_content", "_node_id", "_env"]

    def __init__(self, content: FNodeContent, node_id: int, environment: Environment):
        self._content = content
        self._node_id = node_id
        self._env = environment
        return

    # __eq__ is left as default while __hash__ uses the node id. This
    # is because we always have shared FNodes, hence in a single
    # environment two nodes have always different ids, but in
    # different environments they can have the same id. This is not an
    # issue since, by default, equality coincides with identity.
    def __hash__(self) -> int:
        return self._node_id

    def get_nary_expression_string(self, op: str, args: List["FNode"]) -> str:
        p = []
        if len(args) > 0:
            p.append("(")
            p.append(str(args[0]))
            for x in args[1:]:
                p.append(op)
                p.append(str(x))
            p.append(")")
        return "".join(p)

    def __repr__(self) -> str:
        if self.is_bool_constant():
            return "true" if self.is_true() else "false"
        elif self.is_int_constant():
            return str(self.constant_value())
        elif self.is_real_constant():
            return str(self.constant_value())
        elif self.is_fluent_exp():
            return self.fluent().name + self.get_nary_expression_string(", ", self.args)
        elif self.is_dot():
            return f"{self.agent()}.{self.arg(0)}"
        elif self.is_parameter_exp():
            return self.parameter().name
        elif self.is_variable_exp():
            return self.variable().name
        elif self.is_object_exp():
            return self.object().name
        elif self.is_timing_exp():
            return str(self.timing())
        elif self.is_presence_exp():
            return str(self.presence())
        elif self.is_and():
            return self.get_nary_expression_string(" and ", self.args)
        elif self.is_or():
            return self.get_nary_expression_string(" or ", self.args)
        elif self.is_not():
            return f"(not {str(self.arg(0))})"
        elif self.is_implies():
            return self.get_nary_expression_string(" implies ", self.args)
        elif self.is_iff():
            return self.get_nary_expression_string(" iff ", self.args)
        elif self.is_exists():
            s = ", ".join(str(v) for v in self.variables())
            return f"Exists ({s}) {str(self.arg(0))}"
        elif self.is_always():
            return f"Always({str(self.arg(0))})"
        elif self.is_sometime():
            return f"Sometime({str(self.arg(0))})"
        elif self.is_sometime_before():
            s = ", ".join(str(v) for v in self.args)
            return f"Sometime-Before({str(s)})"
        elif self.is_sometime_after():
            s = ", ".join(str(v) for v in self.args)
            return f"Sometime-After({str(s)})"
        elif self.is_at_most_once():
            return f"At-Most-Once({str(self.arg(0))})"
        elif self.is_forall():
            s = ", ".join(str(v) for v in self.variables())
            return f"Forall ({s}) {str(self.arg(0))}"
        elif self.is_plus():
            return self.get_nary_expression_string(" + ", self.args)
        elif self.is_minus():
            return self.get_nary_expression_string(" - ", self.args)
        elif self.is_times():
            return self.get_nary_expression_string(" * ", self.args)
        elif self.is_div():
            return self.get_nary_expression_string(" / ", self.args)
        elif self.is_le():
            return self.get_nary_expression_string(" <= ", self.args)
        elif self.is_lt():
            return self.get_nary_expression_string(" < ", self.args)
        elif self.is_equals():
            return self.get_nary_expression_string(" == ", self.args)
        else:
            raise ValueError("Unknown FNode type found: " + str(self.node_type))

    @property
    def node_id(self) -> int:
        """Returns the `id` of this expression."""
        return self._node_id

    @property
    def node_type(self) -> OperatorKind:
        """Returns the `OperatorKind` that defines the semantic of this expression."""
        return self._content.node_type

    @property
    def environment(self) -> Environment:
        """Returns the `Environment` in which this expression exists."""
        return self._env

    @property
    def args(self) -> List["FNode"]:
        """Returns the subexpressions of this expression."""
        return self._content.args

    @property
    def type(self) -> "unified_planning.model.Type":
        """Returns the `Type` of this expression."""
        return self._env.type_checker.get_type(self)

    def get_contained_names(self) -> Set[str]:
        """Returns all the names contained in this expression."""
        return self._env.names_extractor.extract_names(self)

    def arg(self, idx: int) -> "FNode":
        """
        Return the given subexpression at the given position.

        :param idx: The `index` of the wanted subexpression.
        :return: The expression at the position `idx`.
        """
        return self._content.args[idx]

    def is_constant(self) -> bool:
        """Returns `True` if the expression is a constant, `False` otherwise."""
        return (
            self.node_type == OperatorKind.BOOL_CONSTANT
            or self.node_type == OperatorKind.INT_CONSTANT
            or self.node_type == OperatorKind.REAL_CONSTANT
            or self.node_type == OperatorKind.OBJECT_EXP
        )

    def constant_value(self) -> Union[bool, int, Fraction]:
        """Returns the constant value stored in this expression."""
        assert self.is_constant()
        return self._content.payload

    def bool_constant_value(self) -> bool:
        """Return constant `boolean` value stored in this expression."""
        assert self.is_bool_constant()
        return self._content.payload

    def int_constant_value(self) -> int:
        """Return constant `integer` value stored in this expression."""
        assert self.is_int_constant()
        return self._content.payload

    def real_constant_value(self) -> Fraction:
        """Return constant `real` value stored in this expression."""
        assert self.is_real_constant()
        return self._content.payload

    def fluent(self) -> "unified_planning.model.fluent.Fluent":
        """Return the `Fluent` stored in this expression."""
        assert self.is_fluent_exp()
        return self._content.payload

    def parameter(self) -> "unified_planning.model.parameter.Parameter":
        """Return the `Parameter` stored in this expression."""
        assert self.is_parameter_exp()
        return self._content.payload

    def variable(self) -> "unified_planning.model.variable.Variable":
        """Return the variable of the VariableExp."""
        assert self.is_variable_exp()
        return self._content.payload

    def variables(self) -> List["unified_planning.model.variable.Variable"]:
        """Return the `Variables` of the `Exists` or `Forall`."""
        assert self.is_exists() or self.is_forall()
        return list(self._content.payload)

    def object(self) -> "unified_planning.model.object.Object":
        """Return the `Object` stored in this expression."""
        assert self.is_object_exp()
        return self._content.payload

    def timing(self) -> "unified_planning.model.timing.Timing":
        """Return the `Timing` stored in this expression."""
        assert self.is_timing_exp()
        return self._content.payload

    def presence(self) -> "unified_planning.model.presence.Presence":
        """Return the `PresenceExpression` stored in this expression."""
        assert self.is_presence_exp()
        return self._content.payload

    def agent(self) -> str:
        """Return the name of the `Agent` stored in this expression."""
        assert self.is_dot()
        return self._content.payload

    def simplify(self) -> "FNode":
        """
        Returns the simplified version of this expression.

        The simplification is done just by constant propagation by the :class:`~unified_planning.model.walkers.Simplifier`
        """
        return self._env.simplifier.simplify(self)

    def substitute(
        self,
        substitutions: Dict[
            "unified_planning.model.expression.Expression",
            "unified_planning.model.expression.Expression",
        ],
    ):
        """
        Returns the version of this expression where every expression that is a key of the substitutions
        map is substituted with it's value in the map.

        NOTE: check the :class:`~unified_planning.model.walkers.Substituter` documentation for more details!

        :param substitutions: The mapping of expressions that must be substituted.
        :return: The expression where every instance of a key value in the substitutions map
            is substituted with it's value.
        """
        return self._env.substituter.substitute(self, substitutions)

    def is_bool_constant(self) -> bool:
        """Test whether the expression is a `boolean` constant."""
        return self.node_type == OperatorKind.BOOL_CONSTANT

    def is_int_constant(self) -> bool:
        """Test whether the expression is an `integer` constant."""
        return self.node_type == OperatorKind.INT_CONSTANT

    def is_real_constant(self) -> bool:
        """Test whether the expression is a `real` constant."""
        return self.node_type == OperatorKind.REAL_CONSTANT

    def is_true(self) -> bool:
        """Test whether the expression is the `True` Boolean constant."""
        return self.is_bool_constant() and self.constant_value() == True

    def is_false(self) -> bool:
        """Test whether the expression is the `False` Boolean constant."""
        return self.is_bool_constant() and self.constant_value() == False

    def is_and(self) -> bool:
        """Test whether the node is the `And` operator."""
        return self.node_type == OperatorKind.AND

    def is_or(self) -> bool:
        """Test whether the node is the `Or` operator."""
        return self.node_type == OperatorKind.OR

    def is_not(self) -> bool:
        """Test whether the node is the `Not` operator."""
        return self.node_type == OperatorKind.NOT

    def is_implies(self) -> bool:
        """Test whether the node is the `Implies` operator."""
        return self.node_type == OperatorKind.IMPLIES

    def is_iff(self) -> bool:
        """Test whether the node is the `Iff` operator."""
        return self.node_type == OperatorKind.IFF

    def is_exists(self) -> bool:
        """Test whether the node is the `Exists` operator."""
        return self.node_type == OperatorKind.EXISTS

    def is_always(self) -> bool:
        """Test whether the node is the Always constraint."""
        return self.node_type == OperatorKind.ALWAYS

    def is_sometime(self) -> bool:
        """Test whether the node is the Sometime constraint."""
        return self.node_type == OperatorKind.SOMETIME

    def is_at_most_once(self) -> bool:
        """Test whether the node is the At-Most-Once constraint."""
        return self.node_type == OperatorKind.AT_MOST_ONCE

    def is_sometime_before(self) -> bool:
        """Test whether the node is the Sometime-Before constraint."""
        return self.node_type == OperatorKind.SOMETIME_BEFORE

    def is_sometime_after(self) -> bool:
        """Test whether the node is the Sometime-After constraint."""
        return self.node_type == OperatorKind.SOMETIME_AFTER

    def is_forall(self) -> bool:
        """Test whether the node is the `Forall` operator."""
        return self.node_type == OperatorKind.FORALL

    def is_fluent_exp(self) -> bool:
        """Test whether the node is a :class:`~unified_planning.model.Fluent` Expression."""
        return self.node_type == OperatorKind.FLUENT_EXP

    def is_parameter_exp(self) -> bool:
        """Test whether the node is an :func:`action parameter <unified_planning.model.Action.parameters>`."""
        return self.node_type == OperatorKind.PARAM_EXP

    def is_variable_exp(self) -> bool:
        """Test whether the node is a :class:`~unified_planning.model.Variable` Expression."""
        return self.node_type == OperatorKind.VARIABLE_EXP

    def is_object_exp(self) -> bool:
        """Test whether the node is an :class:`~unified_planning.model.Object` Expression."""
        return self.node_type == OperatorKind.OBJECT_EXP

    def is_timing_exp(self) -> bool:
        """Test whether the node is a :class:`~unified_planning.model.Timing` Expression."""
        return self.node_type == OperatorKind.TIMING_EXP

    def is_presence_exp(self) -> bool:
        """Test whether the node is a :class:`~unified_planning.model.PresenceExpression` Expression."""
        return self.node_type == OperatorKind.IS_PRESENT_EXP

    def is_plus(self) -> bool:
        """Test whether the node is the `Plus` operator."""
        return self.node_type == OperatorKind.PLUS

    def is_minus(self) -> bool:
        """Test whether the node is the `Minus` operator."""
        return self.node_type == OperatorKind.MINUS

    def is_times(self) -> bool:
        """Test whether the node is the `Times` operator."""
        return self.node_type == OperatorKind.TIMES

    def is_div(self) -> bool:
        """Test whether the node is the `Div` operator."""
        return self.node_type == OperatorKind.DIV

    def is_equals(self) -> bool:
        """Test whether the node is the `Equals` operator."""
        return self.node_type == OperatorKind.EQUALS

    def is_le(self) -> bool:
        """Test whether the node is the `LE` operator."""
        return self.node_type == OperatorKind.LE

    def is_lt(self) -> bool:
        """Test whether the node is the `LT` operator."""
        return self.node_type == OperatorKind.LT

    def is_dot(self) -> bool:
        """Test whether the node is the `DOT` operator."""
        return self.node_type == OperatorKind.DOT

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
