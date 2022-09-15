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
from collections import OrderedDict
from typing import List, Optional, Set, Union
import unified_planning
import unified_planning.environment
import unified_planning.walkers as walkers
from unified_planning.model import FNode, operators as op


class Simplifier(walkers.DagWalker):
    """Performs basic simplifications of the input expression."""

    def __init__(self, env: "unified_planning.environment.Environment"):
        walkers.DagWalker.__init__(self)
        self.env = env
        self.manager = env.expression_manager

    def _number_to_fnode(self, value: Union[int, float, Fraction]) -> FNode:
        if isinstance(value, int):
            fnode = self.manager.Int(value)
        else:
            fnode = self.manager.Real(Fraction(value))
        return fnode

    def simplify(
        self,
        expression: FNode,
        problem: Optional["unified_planning.model.Problem"] = None,
    ) -> FNode:
        """Performs basic simplification of the given expression.

        If a problem is given, it also uses the static fluents of the problem for a better simplification."""
        if problem is not None:
            self.static_fluents = problem.get_static_fluents()
        else:
            self.static_fluents = set()
        self.problem: Optional["unified_planning.model.Problem"] = problem
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
        free_vars: Set[
            "unified_planning.model.Variable"
        ] = self.env.free_vars_oracle.get_free_variables(args[0])
        vars = tuple(var for var in expression.variables() if var in free_vars)
        if len(vars) == 0:
            return args[0]
        return self.manager.Exists(args[0], *vars)

    def walk_forall(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 1
        free_vars: Set[
            "unified_planning.model.Variable"
        ] = self.env.free_vars_oracle.get_free_variables(args[0])
        vars = tuple(var for var in expression.variables() if var in free_vars)
        if len(vars) == 0:
            return args[0]
        return self.manager.Forall(args[0], *vars)

    def walk_always(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 1
        return self.manager.Always(args[0])

    def walk_at_most_once(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 1
        return self.manager.At_Most_Once(args[0])

    def walk_sometime(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 1
        return self.manager.Sometime(args[0])

    def walk_sometime_before(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 2
        return self.manager.Sometime_Before(args[0], args[1])

    def walk_sometime_after(self, expression: FNode, args: List[FNode]) -> FNode:
        assert len(args) == 2
        return self.manager.Sometime_After(args[0], args[1])

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
        else:
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
        if expression.fluent() not in self.static_fluents:
            return self.manager.FluentExp(expression.fluent(), tuple(args))
        else:
            assert self.problem is not None
            for a in args:
                if not a.is_constant():
                    return self.manager.FluentExp(expression.fluent(), tuple(args))
            return self.problem.initial_value(
                self.manager.FluentExp(expression.fluent(), tuple(args))
            )

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
