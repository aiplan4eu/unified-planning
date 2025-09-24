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


from typing import Dict, List, Optional
import unified_planning as up
from unified_planning.model.fnode import FNode
from unified_planning.model.expression import Expression
from unified_planning.exceptions import UPProblemDefinitionError
from unified_planning.model.walkers.quantifier_simplifier import QuantifierSimplifier


class StateEvaluator(QuantifierSimplifier):
    """Same to the :class:`~unified_planning.model.walkers.QuantifierSimplifier`, but takes an instance of
    :class:`~unified_planning.model.State` instead of the `assignment` map."""

    def __init__(self, problem: "up.model.problem.Problem"):
        QuantifierSimplifier.__init__(self, problem.environment, problem)

    def evaluate(
        self,
        expression: "FNode",
        state: "up.model.state.State",
        _variable_assignments: Dict["Expression", "Expression"] = {},
    ) -> FNode:
        """
        Evaluates the given expression in the given `State`.

        :param expression: The expression that needs to be evaluated.
        :param state: The `State` where the expression needs to be evaluated.
        :param _variable_assignment: For internal use only. Parameter used to solve quantifiers.
        :return: The constant expression corresponding to the given expression evaluated in the
            given `State`.
        """
        assert self._problem is not None
        assert self._assignments is None
        assert self._variable_assignments is None
        self._variable_assignments: Optional[
            Dict["Expression", "Expression"]
        ] = _variable_assignments
        self._state = state
        r = self.walk(expression)
        self._variable_assignments = None
        assert r.is_constant()
        return r

    def _deep_subs_simplify(
        self,
        expression: "FNode",
        variables_assignments: Dict["Expression", "Expression"],
    ) -> "FNode":
        """
        This method needs to be updated from the QuantifierRemover in order to use the StateEvaluator inside the
        quantifiers and not the QuantifierSimplifier.
        """
        new_state_evaluator = StateEvaluator(self._problem)
        assert self._variable_assignments is not None
        copy = self._variable_assignments.copy()
        copy.update(variables_assignments)
        r = new_state_evaluator.evaluate(expression, self._state, copy)
        assert r.is_constant()
        return r

    def walk_fluent_exp(self, expression: "FNode", args: List["FNode"]) -> "FNode":
        new_exp = self.manager.FluentExp(expression.fluent(), tuple(args))
        return self._state.get_value(new_exp)

    def walk_param_exp(self, expression: "FNode", args: List["FNode"]) -> "FNode":
        raise UPProblemDefinitionError(
            f"The StateEvaluator.evaluate should only be called on grounded expressions."
        )
