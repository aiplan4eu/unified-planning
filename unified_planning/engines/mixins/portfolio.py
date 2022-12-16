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

from warnings import warn
import unified_planning as up
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple


class OperationMode(Enum):
    ONESHOT_PLANNING = auto()
    PLAN_VALIDATION = auto()


class PortfolioSelectorMixin:
    """Base class that must be extended by an :class:`~unified_planning.engines.Engine` that is also a `PortfolioSelector`."""

    def __init__(self):
        pass

    @staticmethod
    def is_portfolio_selector() -> bool:
        return True

    @staticmethod
    def supports_operation_mode(operation_mode: OperationMode) -> bool:
        """
        :param operation_mode: The `operation_mode` that must be supported.
        :return: `True` if the `PortfolioSelector` implementation supports the given
            `optimality_guarantee`, `False` otherwise.
        """
        return False

    def get_best_engines(
        self,
        problem: "up.model.AbstractProblem",
        operation_mode: OperationMode,
        max_engines: Optional[int] = None,
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        This method takes an `AbstractProblem`, an operation_mode and optionally an integer
        and returns a Tuple of 2 elements:
        The first one is a list of names of engines that are currently installed and that can
        solve the problem; the list is ordered following some performance criteria, where
        the first element is the best one.

        The second one is a list of Dict[str, Any] and represents the parameters of the planners
        in the first list.

        For example, a result like this: (['tamer', 'enhsp-opt'], [{'weight': 0.8}, {}])
        shows that the best result is obtained with 'tamer' with paramseters: {'weight': 0.8}
        and the second best result is obtained with 'enhsp-opt' without parameters (represented by an empty dict)

        :param problem: the problem on which the performance of the different engines are tested.
        :param operation_mode: the Operation Mode used to test the engines.
        :param max_engines: if specified, gives a maximum length to the 2 returned lists.
        :return: 2 lists; the first contains the names of the chosen engines, the second one contains the
            parameters to give to the engines in the first list.
        """
        assert isinstance(self, up.engines.engine.Engine)
        problem_kind = problem.kind
        if not self.skip_checks and not self.supports(problem_kind):
            msg = f"{self.name} cannot solve this kind of problem!"
            if self.error_on_failed_checks:
                raise up.exceptions.UPUsageError(msg)
            else:
                warn(msg)
        if not self.skip_checks and not self.supports_operation_mode(operation_mode):
            msg = f"{self.name} does not support the {operation_mode}!"
            if self.error_on_failed_checks:
                raise up.exceptions.UPUsageError(msg)
            else:
                warn(msg)
        if max_engines is not None and max_engines <= 0:
            raise up.exceptions.UPUsageError(
                f"The specified number of max_engines must be > 0 but {max_engines} is given!"
            )
        return self._get_best_engines(problem, operation_mode, max_engines)

    def _get_best_engines(
        self,
        problem: "up.model.AbstractProblem",
        operation_mode: OperationMode,
        max_engines: Optional[int] = None,
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Method called by the PortfolioSelectorMixin.get_best_engines method."""
        raise NotImplementedError
