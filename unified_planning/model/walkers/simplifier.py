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

from fractions import Fraction
from collections import OrderedDict
from typing import List, Optional, FrozenSet, Union, cast
import unified_planning as up
import unified_planning.environment
import unified_planning.model.walkers as walkers
from unified_planning.model.fnode import FNode
from unified_planning.model.types import _UserType
import unified_planning.model.operators as op


class Simplifier(walkers.dag.DagWalker):
    """Performs basic simplifications of the input expression.

    Important NOTE:
    After the initialization, the :class:`~unified_planning.model.Problem` given as input can not be modified
    or the `Simplifier` behavior is undefined."""

    def __init__(
        self,
        environment: "unified_planning.environment.Environment",
        problem: Optional["unified_planning.model.problem.Problem"] = None,
    ):
        walkers.dag.DagWalker.__init__(self)
        self.environment = environment
        self.manager = environment.expression_manager
        if problem is not None:
            self.static_fluents = problem.get_static_fluents()
        else:
            self.static_fluents = set()
        self.problem: Optional["unified_planning.model.problem.Problem"] = problem

    def _number_to_fnode(self, value: Union[int, float, Fraction]) -> FNode:
        if isinstance(value, int):
            fnode = self.manager.Int(value)
        else:
            fnode = self.manager.Real(Fraction(value))
        return fnode

    def simplify(self, expression: FNode) -> FNode:
        """Performs basic simplification of the given expression.

        If a :class:`~unified_planning.model.Problem` is given at the constructor, it also uses the static `fluents` of the `Problem` for
        a better simplification.

        :param expression: The target expression that must be simplified with constant propagation.
        :return: The simplified expression.
        """
        return self.walk(expression)

    def walk_and(self, expression: FNode, args: List[FNode]) -> FNode:
        if len(args) == 2 and args[0] == args[1]:
            return args[0]

        new_args: OrderedDict[FNode, bool] = OrderedDict()
        for a in args:
            if a.is_true():
                continue
            if a.is_false():
                return self.manager.FALSE()
            if a.is_and():
                for s in a.args:
                    if self.walk_not(self.manager.Not(s), [s]) in new_args:
                        return self.manager.FALSE()
                    new_args[s] = True
            else:
                if self.walk_not(self.manager.Not(a), [a]) in new_args:
                    return self.manager.FALSE()
                new_args[a] = True

        if len(new_args) == 0:
            return self.manager.TRUE()
        elif len(new_args) == 1:
            return next(iter(new_args))
        else:
            return self.manager.And(new_args.keys())

    def walk_or(self, expression: FNode, args: List[FNode]) -> FNode:
        if len(args) == 2 and args[0] == args[1]:
            return args[0]

        new_args: OrderedDict[FNode, bool] = OrderedDict()
        for a in args:
            if a.is_false():
                continue
            if a.is_true():
                return self.manager.TRUE()
            if a.is_or():
                for s in a.args:
                    if self.walk_not(self.manager.Not(s), [s]) in new_args:
                        return self.manager.TRUE()
                    new_args[s] = True
            else:
                if self.walk_not(self.manager.Not(a), [a]) in new_args:
                    return self.manager.TRUE()
                new_args[a] = True

        if len(new_args) == 0:
            return self.manager.FALSE()
        elif len(new_args) == 1:
            return next(iter(new_args))
        else:
            return self.manager.Or(new_args.keys())

    def walk_not(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 1
        child = args[0]
        if child.is_bool_constant():
            l = child.bool_constant_value()
            return self.manager.Bool(not l)
        elif child.is_not():
            return child.arg(0)

        return self.manager.Not(child)

    def walk_iff(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 2

        sl = args[0]
        sr = args[1]

        if sl.is_bool_constant() and sr.is_bool_constant():
            l = sl.bool_constant_value()
            r = sr.bool_constant_value()
            return self.manager.Bool(l == r)
        elif sl.is_bool_constant():
            if sl.bool_constant_value():
                return sr
            else:
                return self.manager.Not(sr)
        elif sr.is_bool_constant():
            if sr.bool_constant_value():
                return sl
            else:
                return self.manager.Not(sl)
        elif sl == sr:
            return self.manager.TRUE()
        else:
            return self.manager.Iff(sl, sr)

    def walk_implies(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 2

        sl = args[0]
        sr = args[1]

        if sl.is_bool_constant():
            l = sl.bool_constant_value()
            if l:
                return sr
            else:
                return self.manager.TRUE()
        elif sr.is_bool_constant():
            r = sr.bool_constant_value()
            if r:
                return self.manager.TRUE()
            else:
                return self.manager.Not(sl)
        elif sl == sr:
            return self.manager.TRUE()
        else:
            return self.manager.Implies(sl, sr)

    def walk_exists(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 1
        free_vars: FrozenSet[
            "up.model.variable.Variable"
        ] = self.environment.free_vars_oracle.get_free_variables(args[0])
        vars = set(var for var in expression.variables() if var in free_vars)
        # Here we check if the arg is in the form:
        # phi(l_i) and l_i == x with phi and x general formulae and l_i a variable
        # bounded to this Exists.
        # if it is, it can be simplified with phi(x) and l_i is removed from the free variables.
        # this process is repeated until there are no more equalities with variables bounded to this
        # Exists
        new_arg, check_equality_simplification = args[0], True
        while check_equality_simplification:
            check_equality_simplification = False
            if new_arg.is_and():
                for i, and_arg in enumerate(new_arg.args):
                    if and_arg.is_equals():
                        variable, value = and_arg.args
                        if (
                            not variable.is_variable_exp()
                            or variable.variable() not in vars
                        ):
                            variable, value = value, variable
                        value_free_vars = (
                            self.environment.free_vars_oracle.get_free_variables(
                                args[0]
                            )
                        )
                        if (
                            variable.is_variable_exp()
                            and variable.variable() in vars
                            and variable not in value_free_vars
                        ):
                            check_equality_simplification = True
                            new_arg = self.manager.And(
                                *(a for j, a in enumerate(new_arg.args) if i != j)
                            )
                            new_arg = new_arg.substitute({variable: value})
                            vars.remove(variable.variable())
                            break
        if vars:
            return self.manager.Exists(new_arg, *vars)
        else:
            return new_arg

    def walk_forall(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 1
        free_vars: FrozenSet[
            "up.model.variable.Variable"
        ] = self.environment.free_vars_oracle.get_free_variables(args[0])
        vars = tuple(var for var in expression.variables() if var in free_vars)
        if len(vars) == 0:
            return args[0]
        return self.manager.Forall(args[0], *vars)

    def walk_always(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 1
        if args[0].is_true():
            return self.manager.TRUE()
        if args[0].is_false():
            return self.manager.FALSE()
        return self.manager.Always(args[0])

    def walk_at_most_once(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 1
        if args[0].is_true() or args[0].is_false():
            return self.manager.TRUE()
        return self.manager.AtMostOnce(args[0])

    def walk_sometime(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 1
        if args[0].is_true():
            return self.manager.TRUE()
        if args[0].is_false():
            return self.manager.FALSE()
        return self.manager.Sometime(args[0])

    def walk_sometime_before(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 2
        if args[0].is_false():
            return self.manager.TRUE()
        if args[0].is_true():
            return self.manager.FALSE()
        return self.manager.SometimeBefore(args[0], args[1])

    def walk_sometime_after(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 2
        if args[0].is_false():
            return self.manager.TRUE()
        if args[0].is_true():
            if args[1].is_true():
                return self.manager.TRUE()
            if args[1].is_false():
                return self.manager.FALSE()
        return self.manager.SometimeAfter(args[0], args[1])

    def walk_equals(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 2

        sl = args[0]
        sr = args[1]

        if sl.is_constant() and sr.is_constant():
            l = sl.constant_value()
            r = sr.constant_value()
            return self.manager.Bool(l == r)
        elif sl == sr:
            return self.manager.TRUE()
        elif sl.type.is_user_type() and sr.type.is_user_type():
            slt, srt = cast(_UserType, sl.type), cast(_UserType, sr.type)
            if not slt.is_compatible(srt) and not srt.is_compatible(slt):
                return self.manager.FALSE()
        return self.manager.Equals(sl, sr)

    def walk_le(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 2

        sl = args[0]
        sr = args[1]

        if sl.is_constant() and sr.is_constant():
            l = sl.constant_value()
            r = sr.constant_value()
            return self.manager.Bool(l <= r)
        return self.manager.LE(sl, sr)

    def walk_lt(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 2

        sl = args[0]
        sr = args[1]

        if sl.is_constant() and sr.is_constant():
            l = sl.constant_value()
            r = sr.constant_value()
            return self.manager.Bool(l < r)
        return self.manager.LT(sl, sr)

    def walk_fluent_exp(self, expression: FNode, args: List[FNode]) -> FNode:
        new_exp = self.manager.FluentExp(expression.fluent(), tuple(args))
        if expression.fluent() not in self.static_fluents:
            return new_exp
        else:
            assert self.problem is not None
            for a in args:
                if not a.is_constant():
                    return new_exp
            static_value = self.problem.initial_value(new_exp)
            if static_value is not None:
                return static_value
            else:  # value is static but is not defined in the initial state
                return new_exp

    def walk_interpreted_function_exp(  # code here is not clean but should work
        self, expression: FNode, args: List[FNode]
    ) -> FNode:
        new_exp = self.manager.InterpretedFunctionExp(
            expression.interpreted_function(), tuple(args)
        )
        newlist = []
        for a in args:
            if not a.is_constant():  # why always not (true) ?
                return new_exp
            else:
                v = a.constant_value()
                newlist.append(v)
        constantval = expression.interpreted_function().function(*newlist)
        if expression.interpreted_function().return_type.is_bool_type():
            constantval = self.manager.Bool(
                (expression.interpreted_function().function(*newlist))
            )

        elif expression.interpreted_function().return_type.is_int_type():

            constantval = self.manager.Int(
                (expression.interpreted_function().function(*newlist))
            )
        elif expression.interpreted_function().return_type.is_real_type():

            constantval = self.manager.Real(
                (expression.interpreted_function().function(*newlist))
            )
        elif (
            expression.interpreted_function().return_type.is_user_type()
        ):  # not sure this works and idk how to check

            constantval = self.manager.ObjectExp(
                (expression.interpreted_function().function(*newlist))
            )
        else:
            return new_exp
        return constantval

    def walk_dot(self, expression: FNode, args: List[FNode]) -> FNode:
        return self.manager.Dot(expression.agent(), args[0])

    def walk_plus(self, expression: FNode, args: List[FNode]) -> FNode:
        new_args_plus: List[FNode] = list()
        accumulator: Union[int, Fraction] = 0
        # divide constant FNode and accumulate their value into accumulator
        for a in args:
            if a.is_int_constant() or a.is_real_constant():
                accumulator += a.constant_value()
            elif a.is_plus():
                for s in a.args:
                    if s.is_int_constant() or s.is_real_constant():
                        accumulator += s.constant_value()
                    else:
                        new_args_plus.append(s)
            else:
                new_args_plus.append(a)
        # if accumulator != 0 create it as a constant FNode and then add all the non-constant FNodes found
        # else return 0 or all the non-constant FNodes found
        if accumulator != 0:
            fnode_acc = self.manager.Plus(
                *new_args_plus, self._number_to_fnode(accumulator)
            )
            return fnode_acc
        else:
            if len(new_args_plus) == 0:
                return self.manager.Int(0)
            else:
                return self.manager.Plus(new_args_plus)

    def walk_minus(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 2
        left, right = args
        value: Union[Fraction, int] = 0
        if (left.is_int_constant() or left.is_real_constant()) and (
            right.is_int_constant() or right.is_real_constant()
        ):
            value = left.constant_value() - right.constant_value()
            fnode_constant_values = self._number_to_fnode(value)
            return fnode_constant_values
        elif right.is_int_constant() or right.is_real_constant():
            if right.constant_value() < 0:
                value = -right.constant_value()
                fnode_constant_values = self._number_to_fnode(value)
                return self.manager.Plus(left, fnode_constant_values)
            else:
                return self.manager.Minus(left, right)
        else:
            return self.manager.Minus(left, right)

    def walk_times(self, expression: FNode, args: List[FNode]) -> FNode:
        new_args_times: List[FNode] = list()
        accumulator: Union[int, Fraction] = 1
        # divide constant FNode and accumulate their value into accumulator
        for a in args:
            if a.is_int_constant() or a.is_real_constant():
                if a.constant_value() == 0:
                    return self.manager.Int(0)
                else:
                    accumulator *= a.constant_value()
            elif a.is_times():
                for s in a.args:
                    if s.is_int_constant() or s.is_real_constant():
                        if s.constant_value() == 0:
                            return self.manager.Int(0)
                        else:
                            accumulator *= s.constant_value()
                    else:
                        new_args_times.append(s)
            else:
                new_args_times.append(a)
        # if accumulator != 1 create it as a constant FNode and then add all the non-constant FNodes found
        # else return  or all the non-constant FNodes found
        if accumulator != 1:
            fnode_acc = self._number_to_fnode(accumulator)
            return self.manager.Times(*new_args_times, fnode_acc)
        else:
            if len(new_args_times) == 0:
                return self.manager.Int(1)
            else:
                return self.manager.Times(new_args_times)

    def walk_div(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 2
        left, right = args
        value: Union[Fraction, int, float] = 0
        if left.is_int_constant() and right.is_int_constant():
            if (left.constant_value() % right.constant_value()) == 0:
                value = int(left.constant_value() / right.constant_value())
            else:
                value = Fraction(left.constant_value(), right.constant_value())
        elif (left.is_int_constant() or left.is_real_constant()) and (
            right.is_int_constant() or right.is_real_constant()
        ):
            assert right.constant_value() != 0
            value = Fraction(left.constant_value(), right.constant_value())
        else:
            return self.manager.Div(left, right)
        return self._number_to_fnode(value)

    @walkers.handles(op.CONSTANTS)
    @walkers.handles(
        op.OperatorKind.PARAM_EXP,
        op.OperatorKind.VARIABLE_EXP,
        op.OperatorKind.OBJECT_EXP,
        op.OperatorKind.TIMING_EXP,
    )
    def walk_identity(self, expression: FNode, args: List[FNode]) -> FNode:
        return expression
