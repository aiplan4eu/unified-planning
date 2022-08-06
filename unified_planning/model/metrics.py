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
from fractions import Fraction
from typing import Dict, Optional, Union


class PlanQualityMetric:
    """
    This is the base class of any metric for plan quality.

    The addition of a PlanQualityMetric in a Problem restricts the set of valid plans to only those who
    satisfy the semantic of the given metric, so a plan to be valid not only needs to satisfy all the
    problem goals, but also the problem's quality metric.
    """

    pass


class MinimizeActionCosts(PlanQualityMetric):
    """
    This metric means that only the plans minimizing the total cost of the actions are valid.

    The costs for each action of the problem is stored in this quality metric.
    """

    def __init__(
        self,
        costs: Dict["up.model.Action", "up.model.FNode"],
        default: Optional["up.model.FNode"] = None,
    ):
        self.costs = costs
        self.default = default

    def __repr__(self):
        costs = {a.name: c for a, c in self.costs.items()}
        costs["default"] = self.default
        return f"minimize actions-cost: {costs}"

    def get_action_cost(self, action: "up.model.Action") -> Optional["up.model.FNode"]:
        """
        Returns the cost of the given Action.

        :param action: The action of which cost must be retrieved.
        :return: The expression representing the cost of the given action. The retrieved cost might be None,
        meaning that #TODO: add meaning of a None action cost.
        """
        return self.costs.get(action, self.default)


class MinimizeSequentialPlanLength(PlanQualityMetric):
    """This metric means that the number of action in the resulting SequentialPlan must be minimized."""

    def __repr__(self):
        return "minimize sequential-plan-length"


class MinimizeMakespan(PlanQualityMetric):
    """This metric means #TODO: explaing what that metric means."""

    def __repr__(self):
        return "minimize makespan"


class MinimizeExpressionOnFinalState(PlanQualityMetric):
    """
    This metric means that the given expression must be minimized on the final state reached
    following the given plan.
    """

    def __init__(self, expression: "up.model.FNode"):
        self.expression = expression

    def __repr__(self):
        return f"minimize {self.expression}"


class MaximizeExpressionOnFinalState(PlanQualityMetric):
    """
    This metric means that the given expression must be minimized on the final state reached
    following the given plan.
    """

    def __init__(self, expression: "up.model.FNode"):
        self.expression = expression

    def __repr__(self):
        return f"maximize {self.expression}"


class Oversubscription(PlanQualityMetric):
    """
    This metric means that only the plans maximing the total gain of the achieved goals is valid.

    The gained value for each fullfilled goal of the problem is stored in this quality metric.
    """

    def __init__(self, goals: Dict["up.model.FNode", Union[Fraction, int]]):
        self.goals = goals

    def __repr__(self):
        return f"oversubscription planning goals: {self.goals}"
