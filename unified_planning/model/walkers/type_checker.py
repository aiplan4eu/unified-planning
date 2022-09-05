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


import unified_planning.model.types
import unified_planning.environment
import unified_planning.model.walkers as walkers
from unified_planning.model.types import BOOL, TIME, _IntType, _RealType
from unified_planning.model.fnode import FNode
from unified_planning.model.operators import OperatorKind
from unified_planning.exceptions import UPTypeError
from typing import List, Optional


class TypeChecker(walkers.dag.DagWalker):
    """Walker used to retrieve the `Type` of an expression."""

    def __init__(self, env: "unified_planning.environment.Environment"):
        walkers.dag.DagWalker.__init__(self)
        self.env = env

    def get_type(self, expression: FNode) -> "unified_planning.model.types.Type":
        """
        Returns the `Type` of the expression.

        :param expression: The expression of which the `Type` must be retrieved.
        :return: The expression `Type`.
        """
        res = self.walk(expression)
        if res is None:
            raise UPTypeError(
                "The expression '%s' is not well-formed" % str(expression)
            )
        return res

    @walkers.handles(
        OperatorKind.AND,
        OperatorKind.OR,
        OperatorKind.NOT,
        OperatorKind.IMPLIES,
        OperatorKind.IFF,
        OperatorKind.EXISTS,
        OperatorKind.FORALL,
    )
    def walk_bool_to_bool(
        self, expression: FNode, args: List["unified_planning.model.types.Type"]
    ) -> Optional["unified_planning.model.types.Type"]:
        assert expression is not None
        for x in args:
            if x is None or x != BOOL:
                return None
        return BOOL

    def walk_fluent_exp(
        self, expression: FNode, args: List["unified_planning.model.types.Type"]
    ) -> Optional["unified_planning.model.types.Type"]:
        assert expression.is_fluent_exp()
        f = expression.fluent()
        if len(args) != len(f.signature):
            return None
        for (arg, param) in zip(args, f.signature):
            if not arg.is_compatible(param.type):
                return None
        return f.type

    def walk_param_exp(
        self, expression: FNode, args: List["unified_planning.model.types.Type"]
    ) -> "unified_planning.model.types.Type":
        assert expression is not None
        assert len(args) == 0
        return expression.parameter().type

    def walk_always(self, expression: FNode, args: List['unified_planning.model.types.Type']) -> 'unified_planning.model.types.Type':
        assert expression is not None
        assert expression.is_always()
        assert len(expression.args) == 1
        return BOOL

    def walk_sometime(self, expression: FNode, args: List['unified_planning.model.types.Type']) -> 'unified_planning.model.types.Type':
        assert expression is not None
        assert expression.is_sometime()
        assert len(expression.args) == 1
        return BOOL

    def walk_at_most_once(self, expression: FNode, args: List['unified_planning.model.types.Type']) -> 'unified_planning.model.types.Type':
        assert expression is not None
        assert expression.is_at_most_once
        assert len(expression.args) == 1
        return BOOL

    def walk_sometime_before(self, expression: FNode, args: List['unified_planning.model.types.Type']) -> 'unified_planning.model.types.Type':
        assert expression is not None
        assert expression.is_sometime_before()
        assert len(expression.args) == 2
        return BOOL

    def walk_sometime_after(self, expression: FNode, args: List['unified_planning.model.types.Type']) -> 'unified_planning.model.types.Type':
        assert expression is not None
        assert expression.is_sometime_after()
        assert len(expression.args) == 2
        return BOOL

    def walk_variable_exp(self, expression: FNode, args: List['unified_planning.model.types.Type']) -> 'unified_planning.model.types.Type':
        assert expression is not None
        assert len(args) == 0
        return expression.variable().type

    def walk_object_exp(
        self, expression: FNode, args: List["unified_planning.model.types.Type"]
    ) -> "unified_planning.model.types.Type":
        assert expression is not None
        assert len(args) == 0
        return expression.object().type

    def walk_timing_exp(
        self, expression: FNode, args: List["unified_planning.model.types.Type"]
    ) -> "unified_planning.model.types.Type":
        assert expression is not None
        assert len(args) == 0
        return TIME

    @walkers.handles(OperatorKind.BOOL_CONSTANT)
    def walk_identity_bool(
        self, expression: FNode, args: List["unified_planning.model.types.Type"]
    ) -> Optional["unified_planning.model.types.Type"]:
        assert expression is not None
        assert len(args) == 0
        return BOOL

    @walkers.handles(OperatorKind.REAL_CONSTANT)
    def walk_identity_real(self, expression, args):
        assert expression is not None
        assert len(args) == 0
        return self.env.type_manager.RealType(
            expression.constant_value(), expression.constant_value()
        )

    @walkers.handles(OperatorKind.INT_CONSTANT)
    def walk_identity_int(self, expression, args):
        assert expression is not None
        assert len(args) == 0
        return self.env.type_manager.IntType(
            expression.constant_value(), expression.constant_value()
        )

    def walk_plus(self, expression, args):
        has_real = False
        lower = None
        upper = None
        for x in args:
            if x is None or not (x.is_int_type() or x.is_real_type()):
                return None
            if x.is_real_type():
                has_real = True
        for x in args:
            if x.lower_bound is None:
                lower = -float("inf")
            elif lower is None:
                lower = x.lower_bound
            else:
                lower += x.lower_bound
            if x.upper_bound is None:
                upper = float("inf")
            elif upper is None:
                upper = x.upper_bound
            else:
                upper += x.upper_bound
        if lower == -float("inf"):
            lower = None
        if upper == float("inf"):
            upper = None
        if has_real:
            return self.env.type_manager.RealType(lower, upper)
        else:
            return self.env.type_manager.IntType(lower, upper)

    def walk_minus(self, expression, args):
        assert len(args) == 2
        has_real = False
        lower = None
        upper = None
        for x in args:
            if x is None or not (x.is_int_type() or x.is_real_type()):
                return None
            if x.is_real_type():
                has_real = True
        left = args[0]
        right = args[1]
        left_lower = -float("inf") if left.lower_bound is None else left.lower_bound
        left_upper = float("inf") if left.upper_bound is None else left.upper_bound
        right_lower = -float("inf") if right.lower_bound is None else right.lower_bound
        right_upper = float("inf") if right.upper_bound is None else right.upper_bound
        lower = left_lower - right_upper
        upper = left_upper - right_lower
        if lower == -float("inf"):
            lower = None
        if upper == float("inf"):
            upper = None
        if has_real:
            return self.env.type_manager.RealType(lower, upper)
        else:
            return self.env.type_manager.IntType(lower, upper)

    def walk_times(self, expression, args):
        has_real = False
        lower = None
        upper = None
        for x in args:
            if x is None or not (x.is_int_type() or x.is_real_type()):
                return None
            if x.is_real_type():
                has_real = True
        for x in args:
            l = -float("inf") if x.lower_bound is None else x.lower_bound
            u = float("inf") if x.upper_bound is None else x.upper_bound
            if lower is None:
                lower = l
                upper = u
            else:
                lower = min(lower * l, lower * u, upper * l, upper * u)
                upper = max(lower * l, lower * u, upper * l, upper * u)
        if lower == -float("inf"):
            lower = None
        if upper == float("inf"):
            upper = None
        if has_real:
            return self.env.type_manager.RealType(lower, upper)
        else:
            return self.env.type_manager.IntType(lower, upper)

    def walk_div(self, expression, args):
        assert len(args) == 2
        has_real = False
        to_skip = False
        lower = None
        upper = None
        for x in args:
            if x is None or not (x.is_int_type() or x.is_real_type()):
                return None
            if x.is_real_type():
                has_real = True
            if x.lower_bound is None and x.upper_bound is None:
                to_skip = True
        left = args[0]
        right = args[1]
        if to_skip or right.lower_bound != right.upper_bound:
            pass
        else:
            left_lower = -float("inf") if left.lower_bound is None else left.lower_bound
            left_upper = float("inf") if left.upper_bound is None else left.upper_bound
            right = right.lower_bound
            lower = min(left_lower / right, left_upper / right)
            upper = max(left_lower / right, left_upper / right)
        if lower == -float("inf"):
            lower = None
        if upper == float("inf"):
            upper = None
        if has_real:
            return self.env.type_manager.RealType(lower, upper)
        else:
            return self.env.type_manager.IntType(lower, upper)

    @walkers.handles(OperatorKind.LE, OperatorKind.LT)
    def walk_math_relation(self, expression, args):
        for x in args:
            if x is None or not (
                x.is_int_type() or x.is_real_type() or x.is_time_type()
            ):
                return None
        return BOOL

    def walk_equals(
        self, expression: FNode, args: List["unified_planning.model.types.Type"]
    ) -> Optional["unified_planning.model.types.Type"]:
        t = args[0]
        if t is None:
            return None

        if t.is_bool_type():
            raise UPTypeError(
                "The expression '%s' is not well-formed."
                "Equality operator is not supported for Boolean"
                " terms. Use Iff instead." % str(expression)
            )
        for x in args:
            if x is None:
                return None
            elif t.is_user_type() and t != x:
                return None
            elif (t.is_int_type() or t.is_real_type()) and not (
                x.is_int_type() or x.is_real_type()
            ):
                return None
        return BOOL
