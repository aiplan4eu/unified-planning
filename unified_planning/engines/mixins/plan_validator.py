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

from abc import ABC, abstractmethod
from warnings import warn
import unified_planning as up


class PlanValidatorMixin(ABC):
    """Base class that must be extended by an :class:`~unified_planning.engines.Engine` that is also a `PlanValidator`."""

    @staticmethod
    def is_plan_validator() -> bool:
        return True

    @staticmethod
    @abstractmethod
    def supports_plan(plan_kind: "up.plans.PlanKind") -> bool:
        """
        :param plan_kind: The :func:`kind <unified_planning.plans.Plan.kind>` of the :class:`~unified_planning.plans.Plan` that must be supported.
        :return: `True` if the given `kind` of `Plan` is supported, False otherwise.
        """
        raise NotImplementedError

    def validate(
        self, problem: "up.model.AbstractProblem", plan: "up.plans.Plan"
    ) -> "up.engines.results.ValidationResult":
        """
        This method takes an`AbstractProblem`, a `Plan` and returns a `ValidationResult`,
        which contains information about the validity of the given `plan` for the given `problem`.

        :param problem: The `AbstractProblem` on which the given `plan` is validated.
        :param plan: The `Plan` that is validated on the given `problem`.
        :return: the `ValidationResult` returned by the `PlanValidator`; a data structure containing the
            :class:`ValidationResultStatus <unified_planning.engines.ValidationResultStatus>` and some additional information about it.
        """
        assert isinstance(self, up.engines.engine.Engine)
        if not self.skip_checks and not self.supports(problem.kind):
            msg = f"We cannot establish whether {self.name} can validate this problem!"
            if self.error_on_failed_checks:
                raise up.exceptions.UPUsageError(msg)
            else:
                warn(msg)
        if not self.skip_checks and not self.supports_plan(plan.kind):
            msg = f"{self.name} cannot validate this kind of plan!"
            if self.error_on_failed_checks:
                raise up.exceptions.UPUsageError(msg)
            else:
                warn(msg)
        return self._validate(problem, plan)

    @abstractmethod
    def _validate(
        self, problem: "up.model.AbstractProblem", plan: "up.plans.Plan"
    ) -> "up.engines.results.ValidationResult":
        """Method called by the PlanValidator.validate method."""
        raise NotImplementedError
