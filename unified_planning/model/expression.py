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
"""The ExpressionManager is used to create expressions.

All objects are memoized so that two syntactically equivalent expressions
are represented by the same object.
"""


import unified_planning as up
import unified_planning.model.types
from unified_planning.model.operators import OperatorKind
from unified_planning.exceptions import UPTypeError, UPExpressionDefinitionError
from fractions import Fraction
from typing import Iterable, List, Union, Dict, Tuple

Expression = Union['up.model.fnode.FNode', 'up.model.fluent.Fluent', 'up.model.object.Object', 'up.model.parameter.Parameter', 'up.model.variable.Variable', 'up.model.timing.Timing', bool, int, float, Fraction]
BoolExpression = Union['up.model.fnode.FNode', 'up.model.fluent.Fluent', 'up.model.parameter.Parameter', bool]
ConstantExpression = Union['up.model.fnode.FNode', 'up.model.object.Object', bool, int, float, Fraction]

class ExpressionManager(object):
    """ExpressionManager is responsible for the creation of all expressions."""

    def __init__(self, env: 'up.environment.Environment'):
        self.env = env
        self.expressions: Dict['up.model.fnode.FNodeContent', 'up.model.fnode.FNode'] = {}
        self._next_free_id = 1

        self.true_expression = self.create_node(node_type=OperatorKind.BOOL_CONSTANT,
                                                args=tuple(),
                                                payload=True)
        self.false_expression = self.create_node(node_type=OperatorKind.BOOL_CONSTANT,
                                                 args=tuple(),
                                                 payload=False)
        return

    def _polymorph_args_to_tuple(self, *args: Union[Expression, Iterable[Expression]]) -> Tuple[Expression, ...]:
        """ Helper function to return a tuple of arguments from args.
        This function is used to allow N-ary operators to express their arguments
        both as a list of arguments or as a tuple of arguments: e.g.,
           And([a,b,c]) and And(a,b,c)
        are both valid, and they are converted into a tuple (a,b,c) """

        res = []
        for p in args:
            if isinstance(p, Iterable):
                res.extend(list(p))
            else:
                res.append(p)
        return tuple(res)

    def auto_promote(self, *args: Union[Expression, Iterable[Expression]]) -> List['up.model.fnode.FNode']:
        tuple_args = self._polymorph_args_to_tuple(*args)
        res = []
        for e in tuple_args:
            if isinstance(e, up.model.fluent.Fluent):
                res.append(self.FluentExp(e))
            elif isinstance(e, up.model.parameter.Parameter):
                res.append(self.ParameterExp(e))
            elif isinstance(e, up.model.variable.Variable):
                res.append(self.VariableExp(e))
            elif isinstance(e, up.model.object.Object):
                res.append(self.ObjectExp(e))
            elif isinstance(e, up.model.timing.Timing):
                res.append(self.TimingExp(e))
            elif isinstance(e, bool):
                res.append(self.Bool(e))
            elif isinstance(e, int):
                res.append(self.Int(e))
            elif isinstance(e, float):
                res.append(self.Real(Fraction(e)))
            elif isinstance(e, Fraction):
                res.append(self.Real(e))
            else:
                res.append(e)
        return res

    def create_node(self, node_type: OperatorKind, args: Iterable['up.model.fnode.FNode'],
                    payload: Union['up.model.fluent.Fluent', 'up.model.object.Object', 'up.model.parameter.Parameter', 'up.model.variable.Variable', 'up.model.timing.Timing', bool, int, Fraction, Tuple['up.model.variable.Variable', ...]] = None) ->'up.model.fnode.FNode':
        content = up.model.fnode.FNodeContent(node_type, args, payload)
        if content in self.expressions:
            return self.expressions[content]
        else:
            assert all(a.environment == self.env for a in args), '2 FNode in the same expression have different environments'
            n = up.model.fnode.FNode(content, self._next_free_id, self.env)
            self._next_free_id += 1
            self.expressions[content] = n
            self.env.type_checker.get_type(n)
            return n

    def And(self, *args: Union[BoolExpression, Iterable[BoolExpression]]) -> 'up.model.fnode.FNode':
        """ Returns a conjunction of terms.
        This function has polimorphic n-arguments:
          - And(a,b,c)
          - And([a,b,c])
        Restriction: Arguments must be boolean
        """
        tuple_args = tuple(self.auto_promote(*args))

        if len(tuple_args) == 0:
            return self.TRUE()
        elif len(tuple_args) == 1:
            return tuple_args[0]
        else:
            return self.create_node(node_type=OperatorKind.AND,
                                    args=tuple_args)

    def Or(self, *args: Union[BoolExpression, Iterable[BoolExpression]]) ->'up.model.fnode.FNode':
        """ Returns an disjunction of terms.
        This function has polimorphic n-arguments:
          - Or(a,b,c)
          - Or([a,b,c])
        Restriction: Arguments must be boolean
        """
        tuple_args = tuple(self.auto_promote(*args))

        if len(tuple_args) == 0:
            return self.FALSE()
        elif len(tuple_args) == 1:
            return tuple_args[0]
        else:
            return self.create_node(node_type=OperatorKind.OR,
                                    args=tuple_args)

    def Not(self, expression: BoolExpression) ->'up.model.fnode.FNode':
        """ Creates an expression of the form:
                not expression
        Restriction: expression must be of boolean type
        """
        expression, = self.auto_promote(expression)
        if expression.is_not():
            return expression.arg(0)
        return self.create_node(node_type=OperatorKind.NOT, args=(expression,))

    def Implies(self, left: BoolExpression, right: BoolExpression) ->'up.model.fnode.FNode':
        """ Creates an expression of the form:
            left -> right
        Restriction: Left and Right must be of boolean type
        """
        left, right = self.auto_promote(left, right)
        return self.create_node(node_type=OperatorKind.IMPLIES, args=(left, right))

    def Iff(self, left: BoolExpression, right: BoolExpression) ->'up.model.fnode.FNode':
        """ Creates an expression of the form:
            left <-> right
        Restriction: Left and Right must be of boolean type
        """
        left, right = self.auto_promote(left, right)
        return self.create_node(node_type=OperatorKind.IFF, args=(left, right))

    def Exists(self, expression: BoolExpression, *vars: 'up.model.variable.Variable') ->'up.model.fnode.FNode':
        """ Creates an expression of the form:
            Exists (var[0]... var[n]) | expression
        Restriction: expression must be of boolean type and
                    vars must be of 'up.Variable' type
        """
        expressions = tuple(self.auto_promote(expression))
        if len(vars) == 0:
            raise UPExpressionDefinitionError(f"Exists of expression: {str(expression)} must be created with at least one variable, otherwise it is not needed.")
        for v in vars:
            if not isinstance(v, up.model.variable.Variable):
                raise UPTypeError("Expecting 'up.Variable', got %s", type(v))
        return self.create_node(node_type=OperatorKind.EXISTS, args=expressions, payload=vars)

    def Forall(self, expression: BoolExpression, *vars: 'up.model.variable.Variable') ->'up.model.fnode.FNode':
        """ Creates an expression of the form:
            Forall (var[0]... var[n]) | expression
        Restriction: expression must be of boolean type and
                    vars must be of 'up.Variable' type
        """
        expressions = tuple(self.auto_promote(expression))
        if len(vars) == 0:
            raise UPExpressionDefinitionError(f"Forall of expression: {str(expression)} must be created with at least one variable, otherwise it is not needed.")
        for v in vars:
            if not isinstance(v, up.model.variable.Variable):
                raise UPTypeError("Expecting 'up.Variable', got %s", type(v))
        return self.create_node(node_type=OperatorKind.FORALL, args=expressions, payload=vars)

    def FluentExp(self, fluent: 'up.model.fluent.Fluent', params: Tuple[Expression, ...] = tuple()) ->'up.model.fnode.FNode':
        """ Creates an expression for the given fluent and parameters.
        Restriction: parameters type must be compatible with the fluent signature
        """
        assert fluent.arity == len(params)
        assert fluent.environment == self.env
        params_exp = self.auto_promote(*params)
        return self.create_node(node_type=OperatorKind.FLUENT_EXP, args=tuple(params_exp), payload=fluent)

    def ParameterExp(self, param: 'up.model.parameter.Parameter') ->'up.model.fnode.FNode':
        """Returns an expression for the given action parameter."""
        return self.create_node(node_type=OperatorKind.PARAM_EXP, args=tuple(), payload=param)

    def VariableExp(self, var: 'up.model.variable.Variable') ->'up.model.fnode.FNode':
        """Returns an expression for the given variable."""
        assert var.environment == self.env
        return self.create_node(node_type=OperatorKind.VARIABLE_EXP, args=tuple(), payload=var)

    def ObjectExp(self, obj: 'up.model.object.Object') ->'up.model.fnode.FNode':
        """Returns an expression for the given object."""
        assert obj.environment == self.env
        return self.create_node(node_type=OperatorKind.OBJECT_EXP, args=tuple(), payload=obj)

    def TimingExp(self, obj: 'up.model.timing.Timing') -> 'up.model.fnode.FNode':
        """Returns an expression for the given timing."""
        return self.create_node(node_type=OperatorKind.TIMING_EXP, args=tuple(), payload=obj)

    def TRUE(self) ->'up.model.fnode.FNode':
        """Return the boolean constant True."""
        return self.true_expression

    def FALSE(self) ->'up.model.fnode.FNode':
        """Return the boolean constant False."""
        return self.false_expression

    def Bool(self, value: bool) ->'up.model.fnode.FNode':
        """Return a boolean constant."""
        if type(value) != bool:
            raise UPTypeError("Expecting bool, got %s" % type(value))

        if value:
            return self.true_expression
        else:
            return self.false_expression

    def Int(self, value: int) ->'up.model.fnode.FNode':
        """Return an int constant."""
        if type(value) != int:
            raise UPTypeError("Expecting int, got %s" % type(value))
        return self.create_node(node_type=OperatorKind.INT_CONSTANT, args=tuple(), payload=value)

    def Real(self, value: Fraction) ->'up.model.fnode.FNode':
        """Return a real constant."""
        if type(value) != Fraction:
            raise UPTypeError("Expecting Fraction, got %s" % type(value))
        return self.create_node(node_type=OperatorKind.REAL_CONSTANT, args=tuple(), payload=value)

    def Plus(self, *args: Union[Expression, Iterable[Expression]]) ->'up.model.fnode.FNode':
        """ Creates an expression of the form:
            args[0] + ... + args[n]
        """
        tuple_args = tuple(self.auto_promote(*args))

        if len(tuple_args) == 0:
            return self.Int(0)
        elif len(tuple_args) == 1:
            return tuple_args[0]
        else:
            return self.create_node(node_type=OperatorKind.PLUS,
                                    args=tuple_args)

    def Minus(self, left: Expression, right: Expression) ->'up.model.fnode.FNode':
        """ Creates an expression of the form: left - right."""
        left, right = self.auto_promote(left, right)
        return self.create_node(node_type=OperatorKind.MINUS, args=(left, right))

    def Times(self, *args: Union[Expression, Iterable[Expression]]) ->'up.model.fnode.FNode':
        """ Creates an expression of the form:
            args[0] * ... * args[n]
        """
        tuple_args = tuple(self.auto_promote(*args))

        if len(tuple_args) == 0:
            return self.Int(1)
        elif len(tuple_args) == 1:
            return tuple_args[0]
        else:
            return self.create_node(node_type=OperatorKind.TIMES,
                                    args=tuple_args)

    def Div(self, left: Expression, right: Expression) ->'up.model.fnode.FNode':
        """ Creates an expression of the form: left / right."""
        left, right = self.auto_promote(left, right)
        return self.create_node(node_type=OperatorKind.DIV, args=(left, right))

    def LE(self, left: Expression, right: Expression) ->'up.model.fnode.FNode':
        """ Creates an expression of the form: left <= right."""
        left, right = self.auto_promote(left, right)
        return self.create_node(node_type=OperatorKind.LE, args=(left, right))

    def GE(self, left: Expression, right: Expression) ->'up.model.fnode.FNode':
        """ Creates an expression of the form: left >= right."""
        left, right = self.auto_promote(left, right)
        return self.create_node(node_type=OperatorKind.LE, args=(right, left))

    def LT(self, left: Expression, right: Expression) ->'up.model.fnode.FNode':
        """ Creates an expression of the form: left < right."""
        left, right = self.auto_promote(left, right)
        return self.create_node(node_type=OperatorKind.LT, args=(left, right))

    def GT(self, left: Expression, right: Expression) ->'up.model.fnode.FNode':
        """ Creates an expression of the form: left > right."""
        left, right = self.auto_promote(left, right)
        return self.create_node(node_type=OperatorKind.LT, args=(right, left))

    def Equals(self, left: Expression, right: Expression) ->'up.model.fnode.FNode':
        """ Creates an expression of the form: left == right."""
        left, right = self.auto_promote(left, right)
        return self.create_node(node_type=OperatorKind.EQUALS, args=(left, right))
