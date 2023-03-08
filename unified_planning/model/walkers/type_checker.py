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


from fractions import Fraction
import unified_planning.model.types
import unified_planning.environment
import unified_planning.model.walkers as walkers
from unified_planning.model.types import BOOL, UNDEFINED, TIME, _IntType, _RealType
from unified_planning.model.fnode import FNode
from unified_planning.model.operators import OperatorKind
from unified_planning.exceptions import UPTypeError
from typing import List, Optional


class TypeChecker(walkers.dag.DagWalker):
    """Walker used to retrieve the `Type` of an expression."""

    def __init__(self, environment: "unified_planning.environment.Environment"):
        walkers.dag.DagWalker.__init__(self)
        self.environment = environment

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
        OperatorKind.DOT,
        OperatorKind.ALWAYS,
        OperatorKind.AT_MOST_ONCE,
        OperatorKind.SOMETIME,
        OperatorKind.SOMETIME_BEFORE,
        OperatorKind.SOMETIME_AFTER,
    )
    def walk_bool_to_bool(
        self, expression: FNode, args: List["unified_planning.model.types.Type"]
    ) -> Optional["unified_planning.model.types.Type"]:
        assert expression is not None
        error = False
        for x in args:
            if x.is_undefined_type():
                return x
            error |= x is None or x != BOOL
        if error:
            return None
        return BOOL

    def walk_fluent_exp(
        self, expression: FNode, args: List["unified_planning.model.types.Type"]
    ) -> Optional["unified_planning.model.types.Type"]:
        assert expression.is_fluent_exp()
        f = expression.fluent()
        error = len(args) != len(f.signature)
        for (param, arg) in zip(f.signature, args):
            if arg.is_undefined_type():
                return arg
            error |= not param.type.is_compatible(arg)
        if error:
            return None
        return f.type

    def walk_param_exp(
        self, expression: FNode, args: List["unified_planning.model.types.Type"]
    ) -> "unified_planning.model.types.Type":
        assert expression is not None
        assert len(args) == 0
        return expression.parameter().type

    def walk_variable_exp(
        self, expression: FNode, args: List["unified_planning.model.types.Type"]
    ) -> "unified_planning.model.types.Type":
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
        return self.environment.type_manager.RealType(
            expression.constant_value(), expression.constant_value()
        )

    @walkers.handles(OperatorKind.INT_CONSTANT)
    def walk_identity_int(self, expression, args):
        assert expression is not None
        assert len(args) == 0
        return self.environment.type_manager.IntType(
            expression.constant_value(), expression.constant_value()
        )

    def walk_plus(self, expression, args):
        has_real = False
        lower = None
        upper = None
        is_time = False
        error = False
        for x in args:
            if x == TIME:
                is_time = True
            elif x == UNDEFINED:
                return x
            error |= x is None or not (x.is_int_type() or x.is_real_type())
            if x.is_real_type():
                has_real = True
        if error:
            return None
        elif is_time:
            return TIME
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
            assert lower is None or isinstance(lower, Fraction)
            assert upper is None or isinstance(upper, Fraction)
            return self.environment.type_manager.RealType(lower, upper)
        else:
            assert lower is None or isinstance(lower, int)
            assert upper is None or isinstance(upper, int)
            return self.environment.type_manager.IntType(lower, upper)

    def walk_minus(self, expression, args):
        assert len(args) == 2
        has_real = False
        lower = None
        upper = None
        is_time = False
        error = False
        for x in args:
            if x == TIME:
                is_time = True
            elif x == UNDEFINED:
                return x
            error |= x is None or not (x.is_int_type() or x.is_real_type())
            if x.is_real_type():
                has_real = True
        if error:
            return None
        elif is_time:
            return TIME
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
            return self.environment.type_manager.RealType(lower, upper)
        else:
            return self.environment.type_manager.IntType(lower, upper)

    def walk_times(self, expression, args):
        has_real = False
        lower = None
        upper = None
        error = False
        for x in args:
            error |= x is None or not (x.is_int_type() or x.is_real_type())
            if x == UNDEFINED:
                return x
            elif x.is_real_type():
                has_real = True
        if error:
            return None
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
            return self.environment.type_manager.RealType(lower, upper)
        else:
            return self.environment.type_manager.IntType(lower, upper)

    def walk_div(self, expression, args):
        assert len(args) == 2
        has_real = False
        to_skip = False
        lower = None
        upper = None
        error = False
        for x in args:
            error |= x is None or not (x.is_int_type() or x.is_real_type())
            if x == UNDEFINED:
                return x
            elif x.is_real_type():
                has_real = True
            if x.lower_bound is None and x.upper_bound is None:
                to_skip = True
        if error:
            return None
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
            return self.environment.type_manager.RealType(lower, upper)
        else:
            return self.environment.type_manager.IntType(lower, upper)

    @walkers.handles(OperatorKind.LE, OperatorKind.LT)
    def walk_math_relation(self, expression, args):
        error = False
        for x in args:
            if x.is_undefined_type():
                return x
            error |= x is None or not (
                x.is_int_type() or x.is_real_type() or x.is_time_type()
            )
        if error:
            return None
        return BOOL

    def walk_equals(
        self, expression: FNode, args: List["unified_planning.model.types.Type"]
    ) -> Optional["unified_planning.model.types.Type"]:
        t_right = args[0]
        t_left = args[0]
        if t_right == UNDEFINED or t_left == UNDEFINED:
            return UNDEFINED
        if t_right is None or t_left is None:
            return None

        if t_right.is_bool_type() or t_left.is_bool_type():
            raise UPTypeError(
                "The expression '%s' is not well-formed."
                "Equality operator is not supported for Boolean"
                " terms. Use Iff instead." % str(expression)
            )
        elif (
            t_right.is_user_type()
            and t_right != t_left
            and not t_right.is_compatible(t_left)
            and not t_left.is_compatible(t_right)
        ):
            return None
        elif (t_right.is_int_type() or t_right.is_real_type()) and not (
            t_left.is_int_type() or t_left.is_real_type()
        ):
            return None
        return BOOL

    def walk_dot(
        self, expression: FNode, args: List["unified_planning.model.types.Type"]
    ) -> Optional["unified_planning.model.types.Type"]:
        assert expression.is_dot()
        if len(args) != 1:
            return None
        t = args[0]
        if t is None:
            return None
        elif t.is_undefined_type():
            return t
        fluent_exp = expression.args[0]
        if not fluent_exp.is_fluent_exp():
            return None
        fluent_name = fluent_exp.fluent().name
        a = expression.agent()
        if all(f.name != fluent_name for f in a.fluents):
            raise UPTypeError(
                f"The expression {expression} is not well-formed. ",
                f"The agent {a.name} does not have the fluent {fluent_name}.",
            )
        return t

    def walk_undefined(
        self, expression: FNode, args: List["unified_planning.model.types.Type"]
    ) -> Optional["unified_planning.model.types.Type"]:
        assert expression is not None
        assert not args
        return UNDEFINED
