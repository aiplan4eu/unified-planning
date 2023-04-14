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

import unified_planning as up
from unified_planning.environment import Environment, get_environment
from unified_planning.exceptions import UPProblemDefinitionError
from unified_planning.model.expression import NumericConstant, uniform_numeric_constant
from abc import ABCMeta
from fractions import Fraction
from typing import Dict, Optional, Union, Tuple


class PlanQualityMetric(metaclass=ABCMeta):
    """
    This is the base class of any metric for :class:`~unified_planning.model.Plan` quality.

    The addition of a `PlanQualityMetric` in a `Problem` restricts the set of valid `Plans` to only those who
    satisfy the semantic of the given metric, so a `Plan`, to be valid, not only needs to satisfy all the
    problem goals, but also the problem's quality metric.
    """

    def __init__(self, environment: Optional[Environment] = None):
        self._env = get_environment(environment)

    @property
    def environment(self) -> Environment:
        return self._env


class MinimizeActionCosts(PlanQualityMetric):
    """
    This metric means that only the :class:`~unified_planning.model.Plan` minimizing the total cost of the :class:`Actions <unified_planning.model.Action>` is valid.

    The costs for each `Action` of the problem is stored in this quality metric.
    """

    def __init__(
        self,
        costs: Dict["up.model.Action", "up.model.Expression"],
        default: Optional["up.model.Expression"] = None,
        environment: Optional[Environment] = None,
    ):
        PlanQualityMetric.__init__(self, environment)
        em = self._env.expression_manager
        self._costs: Dict["up.model.Action", "up.model.FNode"] = {}
        for action, cost in costs.items():
            cost_exp: Optional["up.model.FNode"] = None
            assert cost is not None, "Typing not respected"
            (cost_exp,) = em.auto_promote(cost)
            cost_type = cost_exp.type
            if not cost_type.is_int_type() and not cost_type.is_real_type():
                raise UPProblemDefinitionError(
                    "The costs of a MinimizeActionCosts must be numeric.",
                    f"{cost_type} is neither IntType or RealType.",
                )
            if cost_exp.environment != self._env:
                raise UPProblemDefinitionError(
                    f"The cost expression {cost_exp} and the metric don't have the same environment"
                )
            if action.environment != self._env:
                raise UPProblemDefinitionError(
                    f"The action {action.name} and the metric don't have the same environment"
                )
            self._costs[action] = cost_exp
        self._default: Optional["up.model.FNode"] = None
        if default is not None:
            default_exp: "up.model.FNode" = em.auto_promote(default)[0]
            default_type = default_exp.type
            if not default_type.is_int_type() and not default_type.is_real_type():
                raise UPProblemDefinitionError(
                    "The costs of a MinimizeActionCosts must be numeric.",
                    f"{default_type} is neither IntType or RealType.",
                )
            if default_exp.environment != self._env:
                raise UPProblemDefinitionError(
                    f"The default cost expression {default_exp} and the metric don't have the same environment"
                )

    def __repr__(self):
        costs: Dict[str, Optional["up.model.fnode.FNode"]] = {
            a.name: c for a, c in self._costs.items()
        }
        costs["default"] = self._default
        return f"minimize actions-cost: {costs}"

    def __eq__(self, other):
        return (
            isinstance(other, MinimizeActionCosts)
            and self._default == other._default
            and self._costs == other._costs
        )

    def __hash__(self):
        return hash(self.__class__.__name__)

    @property
    def costs(self) -> Dict["up.model.Action", "up.model.FNode"]:
        return self._costs

    @property
    def default(self) -> Optional["up.model.FNode"]:
        return self._default

    def get_action_cost(self, action: "up.model.Action") -> Optional["up.model.FNode"]:
        """
        Returns the cost of the given `Action`.

        :param action: The action of which cost must be retrieved.
        :return: The expression representing the cost of the given action.
            If the retrieved cost is `None` it means it is not set and therefore
            it's invalid; every action cost MUST be set, either with the cost mapping
            or with the default.
        """
        return self._costs.get(action, self._default)


class MinimizeSequentialPlanLength(PlanQualityMetric):
    """This metric means that the number of :func:`actions <unified_planning.plans.SequentialPlan.actions>` in the resulting :class:`~unified_planning.plans.SequentialPlan` must be minimized."""

    def __repr__(self):
        return "minimize sequential-plan-length"

    def __eq__(self, other):
        return isinstance(other, MinimizeSequentialPlanLength)

    def __hash__(self):
        return hash(self.__class__.__name__)


class MinimizeMakespan(PlanQualityMetric):
    """
    This metric means that the makespan must be minimized.
    The makespan is the time from the start of the plan to the end of the plan.
    """

    def __repr__(self):
        return "minimize makespan"

    def __eq__(self, other):
        return isinstance(other, MinimizeMakespan)

    def __hash__(self):
        return hash(self.__class__.__name__)


class MinimizeExpressionOnFinalState(PlanQualityMetric):
    """
    This metric means that the given expression must be minimized on the final state reached
    following the given :class:`~unified_planning.model.Plan`.
    """

    def __init__(
        self,
        expression: "up.model.Expression",
        environment: Optional[Environment] = None,
    ):
        PlanQualityMetric.__init__(self, environment)
        self.expression: "up.model.FNode" = self._env.expression_manager.auto_promote(
            expression
        )[0]
        exp_type = self.expression.type
        if not exp_type.is_int_type() and not exp_type.is_real_type():
            raise UPProblemDefinitionError(
                "The expression of a MinimizeExpressionOnFinalState must be numeric.",
                f"{exp_type} is neither IntType or RealType.",
            )
        if self.expression.environment != self._env:
            raise UPProblemDefinitionError(
                "The expression and the metric don't have the same environment"
            )

    def __repr__(self):
        return f"minimize {self.expression}"

    def __eq__(self, other):
        return (
            isinstance(other, MinimizeExpressionOnFinalState)
            and self.expression == other.expression
        )

    def __hash__(self):
        return hash(self.__class__.__name__)


class MaximizeExpressionOnFinalState(PlanQualityMetric):
    """
    This metric means that the given expression must be maximized on the final state reached
    following the given :class:`~unified_planning.model.Plan`.
    """

    def __init__(
        self,
        expression: "up.model.Expression",
        environment: Optional[Environment] = None,
    ):
        PlanQualityMetric.__init__(self, environment)
        self.expression: "up.model.FNode" = self._env.expression_manager.auto_promote(
            expression
        )[0]
        exp_type = self.expression.type
        if not exp_type.is_int_type() and not exp_type.is_real_type():
            raise UPProblemDefinitionError(
                "The expression of a MaximizeExpressionOnFinalState must be numeric.",
                f"{exp_type} is neither IntType or RealType.",
            )
        if self.expression.environment != self._env:
            raise UPProblemDefinitionError(
                "The expression and the metric don't have the same environment"
            )

    def __repr__(self):
        return f"maximize {self.expression}"

    def __eq__(self, other):
        return (
            isinstance(other, MaximizeExpressionOnFinalState)
            and self.expression == other.expression
        )

    def __hash__(self):
        return hash(self.__class__.__name__)


class Oversubscription(PlanQualityMetric):
    """
    This metric means that only the plans maximizing the total gain of the achieved `goals` is valid.

    The gained value for each fulfilled `goal` of the problem is stored in this quality metric.
    """

    def __init__(
        self,
        goals: Dict["up.model.BoolExpression", NumericConstant],
        environment: Optional[Environment] = None,
    ):
        PlanQualityMetric.__init__(self, environment)
        em = self._env.expression_manager
        self._goals: Dict["up.model.fnode.FNode", Union[Fraction, int]] = {}
        for goal, gain in goals.items():
            (g_exp,) = em.auto_promote(goal)
            if not g_exp.type.is_bool_type():
                raise UPProblemDefinitionError(
                    f"goal {g_exp} type is {g_exp.type}. Expected BoolType."
                )
            if g_exp.environment != self._env:
                raise UPProblemDefinitionError(
                    f"goal {g_exp} does not have the same environment given to the metric."
                )
            self._goals[g_exp] = uniform_numeric_constant(gain)

    def __repr__(self):
        return f"oversubscription planning goals: {self.goals}"

    def __eq__(self, other):
        return isinstance(other, Oversubscription) and self.goals == other.goals

    def __hash__(self):
        return hash(self.__class__.__name__)

    @property
    def goals(self) -> Dict["up.model.fnode.FNode", Union[Fraction, int]]:
        return self._goals


class TemporalOversubscription(PlanQualityMetric):
    """
    This metric means that only the plans maximizing the total gain of the achieved `goals` is valid.

    The gained value for each fulfilled `goal` of the problem is stored in this quality metric.
    """

    def __init__(
        self,
        goals: Dict[
            Tuple["up.model.timing.TimeInterval", "up.model.BoolExpression"],
            NumericConstant,
        ],
        environment: Optional[Environment] = None,
    ):
        PlanQualityMetric.__init__(self, environment)
        em = self._env.expression_manager
        self._goals: Dict[
            Tuple["up.model.timing.TimeInterval", "up.model.FNode"],
            Union[Fraction, int],
        ] = {}
        for (interval, goal), gain in goals.items():
            (g_exp,) = em.auto_promote(goal)
            if not g_exp.type.is_bool_type():
                raise UPProblemDefinitionError(
                    f"goal {g_exp} type is {g_exp.type}. Expected BoolType."
                )
            if g_exp.environment != self._env:
                raise UPProblemDefinitionError(
                    f"goal {g_exp} does not have the same environment given to the metric."
                )
            self._goals[(interval, g_exp)] = uniform_numeric_constant(gain)

    def __repr__(self):
        return f"oversubscription planning timed goals: {self.goals}"

    def __eq__(self, other):
        return isinstance(other, TemporalOversubscription) and self.goals == other.goals

    def __hash__(self):
        return hash(self.__class__.__name__)

    @property
    def goals(
        self,
    ) -> Dict[
        Tuple["up.model.timing.TimeInterval", "up.model.FNode"], Union[Fraction, int]
    ]:
        return self._goals
