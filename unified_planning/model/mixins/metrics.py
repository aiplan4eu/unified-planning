from typing import List, Optional, Set, Tuple

from unified_planning.model.metrics import PlanQualityMetric
from unified_planning.model.problem_kind import ProblemKind

import unified_planning as up
from unified_planning.model.mixins import ActionsSetMixin


class MetricsMixin:
    """Problem mixin that adds the capabilities to manage quality metrics."""

    def __init__(self, environment: "up.environment.Environment"):
        self._env = environment
        self._metrics: List["up.model.metrics.PlanQualityMetric"] = []

    def add_quality_metric(self, metric: "up.model.metrics.PlanQualityMetric"):
        """
        Adds the given `quality metric` to the `Problem`; a `quality metric` defines extra requirements that a :class:`~unified_planning.plans.Plan`
        must satisfy in order to be valid.

        :param metric: The `quality metric` that a `Plan` of this `Problem` must satisfy in order to be valid.
        """
        self._metrics.append(metric)

    @property
    def quality_metrics(self) -> List["up.model.metrics.PlanQualityMetric"]:
        """Returns all the `quality metrics` in the `Problem`."""
        return self._metrics

    def clear_quality_metrics(self):
        """Removes all the `quality metrics` in the `Problem`."""
        self._metrics = []

    def _cloned_metrics(
        self, new_actions: Optional[ActionsSetMixin]
    ) -> List[PlanQualityMetric]:
        """Returns the list of cloned metric.
        We make sure that any action appearing in hte metric is from the new set passed as parameter."""
        cloned: List[PlanQualityMetric] = []
        for m in self._metrics:
            if isinstance(m, up.model.metrics.MinimizeActionCosts):
                assert new_actions is not None
                costs = {new_actions.action(a.name): c for a, c in m.costs.items()}
                cloned.append(up.model.metrics.MinimizeActionCosts(costs))
            else:
                cloned.append(m)
        return cloned

    def _update_kind_metric(
        self,
        kind: ProblemKind,
        linear_checker: "up.model.walkers.linear_checker.LinearChecker",
    ) -> Tuple[Set["up.model.Fluent"], Set["up.model.Fluent"]]:
        """Updates the kind object passed as parameter to account for given metrics.
        Return a pair for fluent sets that should respectively be only increased/decreased
        (necessary for checking numeric problem kind properties).
        """
        fluents_to_only_increase = set()
        fluents_to_only_decrease = set()
        for metric in self._metrics:
            if isinstance(metric, up.model.metrics.MinimizeExpressionOnFinalState):
                kind.set_quality_metrics("FINAL_VALUE")
                (
                    is_linear,
                    fnode_to_only_increase,  # positive fluents in minimize can only be increased
                    fnode_to_only_decrease,  # negative fluents in minimize can only be decreased
                ) = linear_checker.get_fluents(metric.expression)
                if is_linear:
                    fluents_to_only_increase = {
                        e.fluent() for e in fnode_to_only_increase
                    }
                    fluents_to_only_decrease = {
                        e.fluent() for e in fnode_to_only_decrease
                    }
                else:
                    kind.unset_problem_type("SIMPLE_NUMERIC_PLANNING")
            elif isinstance(metric, up.model.metrics.MaximizeExpressionOnFinalState):
                kind.set_quality_metrics("FINAL_VALUE")
                (
                    is_linear,
                    fnode_to_only_decrease,  # positive fluents in maximize can only be decreased
                    fnode_to_only_increase,  # negative fluents in maximize can only be increased
                ) = linear_checker.get_fluents(metric.expression)
                if is_linear:
                    fluents_to_only_increase = {
                        e.fluent() for e in fnode_to_only_increase
                    }
                    fluents_to_only_decrease = {
                        e.fluent() for e in fnode_to_only_decrease
                    }
                else:
                    kind.unset_problem_type("SIMPLE_NUMERIC_PLANNING")
            elif isinstance(metric, up.model.metrics.MinimizeActionCosts):
                kind.set_quality_metrics("ACTIONS_COST")
            elif isinstance(metric, up.model.metrics.MinimizeMakespan):
                kind.set_quality_metrics("MAKESPAN")
            elif isinstance(metric, up.model.metrics.MinimizeSequentialPlanLength):
                kind.set_quality_metrics("PLAN_LENGTH")
            elif isinstance(metric, up.model.metrics.Oversubscription):
                kind.set_quality_metrics("OVERSUBSCRIPTION")
            else:
                assert False, "Unknown quality metric"
        return fluents_to_only_increase, fluents_to_only_decrease
