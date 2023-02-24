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


from typing import Dict, List, Optional
from itertools import product

import unified_planning as up
import unified_planning.environment
from unified_planning.exceptions import UPProblemDefinitionError
from unified_planning.model.fnode import FNode
from unified_planning.model.expression import Expression
from unified_planning.model.walkers.dag import DagWalker
from unified_planning.model.walkers.simplifier import Simplifier


class QuantifierSimplifier(Simplifier):
    """
    Same to the :class:`~unified_planning.model.walkers.Simplifier`, but does not expand quantifiers and solves them
    locally using the :class:`~unified_planning.model.Problem` given at construction time.
    """

    def __init__(
        self,
        environment: "unified_planning.environment.Environment",
        problem: "up.model.problem.Problem",
    ):
        DagWalker.__init__(self, True)
        self._env = environment
        self.manager = environment.expression_manager
        self._problem = problem
        self._assignments: Optional[Dict["Expression", "Expression"]] = None
        self._variable_assignments: Optional[Dict["Expression", "Expression"]] = None

    def qsimplify(
        self,
        expression: "FNode",
        assignments: Dict["Expression", "Expression"],
        variable_assignments: Dict["Expression", "Expression"],
    ):
        """
        Simplifies the expression and the quantifiers in it.
        The quantifiers are substituted with their grounded version using
        the :class:`~unified_planning.model.Problem` given at construction time.

        :param expression: The expression to simplify and to remove quantifiers from.
        :param assignments: The mapping from a `fluent` expression to it's `value`; every `fluent` expression
            in the given expression must have a `value`.
        :param variable_assignment: `Param` used for solving internal quantifiers.
        :return: The simplified expression without quantifiers.
        """
        assert self._problem is not None
        assert self._assignments is None
        assert self._variable_assignments is None
        self._assignments = assignments
        self._variable_assignments = variable_assignments
        r = self.walk(expression)
        self._assignments = None
        self._variable_assignments = None
        return r

    def _push_with_children_to_stack(self, expression: "FNode", **kwargs):
        """Add children to the stack."""
        if expression.is_forall() or expression.is_exists():
            self.stack.append((True, expression))
        else:
            super(Simplifier, self)._push_with_children_to_stack(expression, **kwargs)

    def _compute_node_result(self, expression: "FNode", **kwargs):
        """Apply function to the node and memoize the result.
        Note: This function assumes that the results for the children
              are already available.
        """
        key = self._get_key(expression, **kwargs)
        if key not in self.memoization:
            try:
                f = self.functions[expression.node_type]
            except KeyError:
                f = self.walk_error

            if not (expression.is_forall() or expression.is_exists()):
                args = [
                    self.memoization[self._get_key(s, **kwargs)]
                    for s in self._get_children(expression)
                ]
                self.memoization[key] = f(expression, args=args, **kwargs)
            else:
                self.memoization[key] = f(expression, args=expression.args, **kwargs)
        else:
            pass

    def _deep_subs_simplify(
        self,
        expression: "FNode",
        variables_assignments: Dict["Expression", "Expression"],
    ) -> "FNode":
        new_qsimplifier = QuantifierSimplifier(self._env, self._problem)
        assert self._variable_assignments is not None
        assert self._assignments is not None
        copy = self._variable_assignments.copy()
        copy.update(variables_assignments)
        r = new_qsimplifier.qsimplify(expression, self._assignments, copy)
        assert r.is_constant()
        return r

    def walk_exists(self, expression: "FNode", args: List["FNode"]) -> "FNode":
        assert self._problem is not None
        assert len(args) == 1
        if args[0].is_bool_constant():
            if args[0].bool_constant_value():
                return self.manager.TRUE()
            return self.manager.FALSE()
        vars = expression.variables()
        type_list = [v.type for v in vars]
        possible_objects: List[List["up.model.object.Object"]] = [
            list(self._problem.objects(t)) for t in type_list
        ]
        # product of n iterables returns a generator of tuples where
        # every tuple has n elements and the tuples make every possible
        # combination of 1 item for each iterable. For example:
        # product([1,2], [3,4], [5,6], [7]) =
        # (1,3,5,7) (1,3,6,7) (1,4,5,7) (1,4,6,7) (2,3,5,7) (2,3,6,7) (2,4,5,7) (2,4,6,7)
        for o in product(*possible_objects):
            subs: Dict["Expression", "Expression"] = dict(zip(vars, list(o)))
            result = self._deep_subs_simplify(args[0], subs)
            assert result.is_bool_constant()
            if result.bool_constant_value():
                return self.manager.TRUE()
        return self.manager.FALSE()

    def walk_forall(self, expression: "FNode", args: List["FNode"]) -> "FNode":
        assert self._problem is not None
        assert len(args) == 1
        if args[0].is_bool_constant():
            if args[0].bool_constant_value():
                return self.manager.TRUE()
            return self.manager.FALSE()
        vars = expression.variables()
        type_list = [v.type for v in vars]
        possible_objects: List[List["up.model.object.Object"]] = [
            list(self._problem.objects(t)) for t in type_list
        ]
        # product of n iterables returns a generator of tuples where
        # every tuple has n elements and the tuples make every possible
        # combination of 1 item for each iterable. For example:
        # product([1,2], [3,4], [5,6], [7]) =
        # (1,3,5,7) (1,3,6,7) (1,4,5,7) (1,4,6,7) (2,3,5,7) (2,3,6,7) (2,4,5,7) (2,4,6,7)
        for o in product(*possible_objects):
            subs: Dict["Expression", "Expression"] = dict(zip(vars, list(o)))
            result = self._deep_subs_simplify(args[0], subs)
            assert result.is_bool_constant()
            if not result.bool_constant_value():
                return self.manager.FALSE()
        return self.manager.TRUE()

    def walk_fluent_exp(self, expression: "FNode", args: List["FNode"]) -> "FNode":
        new_exp = self.manager.FluentExp(expression.fluent(), tuple(args))
        assert self._assignments is not None
        res = self._assignments.get(new_exp, None)
        if res is not None:
            (res,) = self.manager.auto_promote(res)
            assert type(res) is FNode
            return res
        else:
            raise UPProblemDefinitionError(
                f"Value of Fluent {str(new_exp)} not found in {str(self._assignments)}"
            )

    def walk_variable_exp(self, expression: "FNode", args: List["FNode"]) -> "FNode":
        assert self._variable_assignments is not None
        res = self._variable_assignments.get(expression.variable(), None)
        if res is not None:
            (res,) = self.manager.auto_promote(res)
            assert type(res) is FNode
            return res
        else:
            raise UPProblemDefinitionError(
                f"Value of Variable {str(expression)} not found in {str(self._variable_assignments)}"
            )

    def walk_param_exp(self, expression: "FNode", args: List["FNode"]) -> "FNode":
        assert self._assignments is not None
        res = self._assignments.get(expression.parameter(), None)
        if res is not None:
            (res,) = self.manager.auto_promote(res)
            assert type(res) is FNode
            return res
        else:
            raise UPProblemDefinitionError(
                f"Value of Parameter {str(expression)} not found in {str(self._assignments)}"
            )
