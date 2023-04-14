# Copyright 2022 AIPlan4EU project
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

from abc import ABC, abstractmethod
from warnings import warn
import unified_planning as up
from typing import Any, Dict, List, Optional, Tuple


class PortfolioSelectorMixin(ABC):
    """Base class that must be extended by an :class:`~unified_planning.engines.Engine` that is also a `PortfolioSelector`."""

    def __init__(self):
        self.optimality_metric_required = False

    @staticmethod
    def is_portfolio_selector() -> bool:
        return True

    @staticmethod
    def satisfies(
        optimality_guarantee: "up.engines.mixins.oneshot_planner.OptimalityGuarantee",
    ) -> bool:
        """
        :param optimality_guarantee: The `optimality_guarantee` that must be satisfied.
        :return: `True` if the `PortfolioSelectorMixin` implementation satisfies the given
        `optimality_guarantee`, `False` otherwise.
        """
        return False

    def get_best_oneshot_planners(
        self,
        problem: "up.model.AbstractProblem",
        max_planners: Optional[int] = None,
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        This method takes an `AbstractProblem`, an operation_mode and optionally an integer
        and returns a Tuple of 2 elements:
        The first one is a list of names of oneshot planners that are currently installed and that can
        solve the problem; the list is ordered following some performance criteria, where
        the first element is the best one.

        The second one is a list of Dict[str, Any] and represents the parameters of the planners
        in the first list.

        For example, a result like this: (['tamer', 'enhsp-opt'], [{'weight': 0.8}, {}])
        shows that the best result is obtained with 'tamer' with paramseters: {'weight': 0.8}
        and the second best result is obtained with 'enhsp-opt' without parameters (represented by an empty dict)

        :param problem: the problem on which the performance of the different planners are tested.
        :param max_planners: if specified, gives a maximum length to the 2 returned lists.
        :return: 2 lists; the first contains the names of the chosen planners, the second one contains the
            parameters to give to the planners in the first list.
        """
        assert isinstance(self, up.engines.engine.Engine)
        problem_kind = problem.kind
        if not self.skip_checks and not self.supports(problem_kind):
            msg = f"{self.name} cannot solve this kind of problem!"
            if self.error_on_failed_checks:
                raise up.exceptions.UPUsageError(msg)
            else:
                warn(msg)
        if not problem_kind.has_quality_metrics() and self.optimality_metric_required:
            msg = f"The problem has no quality metrics but the planners are required to be optimal!"
            raise up.exceptions.UPUsageError(msg)
        if max_planners is not None and max_planners <= 0:
            raise up.exceptions.UPUsageError(
                f"The specified number of max_planners must be > 0 but {max_planners} is given!"
            )
        return self._get_best_oneshot_planners(problem, max_planners)

    @abstractmethod
    def _get_best_oneshot_planners(
        self,
        problem: "up.model.AbstractProblem",
        max_planners: Optional[int] = None,
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Method called by the PortfolioSelectorMixin.get_best_oneshot_planners method."""
        raise NotImplementedError
