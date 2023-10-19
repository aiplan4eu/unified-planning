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
from unified_planning.model.metrics import PlanQualityMetric
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
        if metric.environment != self._env:
            raise up.exceptions.UPUsageError(
                "The added metric does not have the same environment of the MetricsMixin"
            )
        self._metrics.append(metric)

    @property
    def quality_metrics(self) -> List["up.model.metrics.PlanQualityMetric"]:
        """Returns all the `quality metrics` in the `Problem`."""
        return self._metrics

    def clear_quality_metrics(self):
        """Removes all the `quality metrics` in the `Problem`."""
        self._metrics = []

    def __eq__(self, other):
        if not isinstance(other, MetricsMixin):
            return False
        return set(self._metrics) == set(other._metrics)

    def __hash__(self):
        return sum(map(hash, self._metrics))

    def _clone_to(self, other: "MetricsMixin", new_actions: Optional[ActionsSetMixin]):
        """Returns the list of cloned metric.
        We make sure that any action appearing in hte metric is from the new set passed as parameter."""
        cloned: List[PlanQualityMetric] = []
        for m in self._metrics:
            if m.is_minimize_action_costs():
                assert isinstance(m, up.model.metrics.MinimizeActionCosts)
                assert new_actions is not None
                costs: Dict["up.model.Action", "up.model.Expression"] = {
                    new_actions.action(a.name): c for a, c in m.costs.items()
                }
                cloned.append(
                    up.model.metrics.MinimizeActionCosts(
                        costs, default=m.default, environment=other._env
                    )
                )
            else:
                cloned.append(m)
        other._metrics = cloned
