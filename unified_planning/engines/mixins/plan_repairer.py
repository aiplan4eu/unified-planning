# Copyright 2023 AIPlan4EU project
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


class PlanRepairerMixin:
    def __init__(self):
        self.optimality_metric_required = False

    @staticmethod
    def satisfies(
        optimality_guarantee: "up.engines.mixins.oneshot_planner.OptimalityGuarantee",
    ) -> bool:
        """
        Returns True iff the engine satisfies the given optimality guarantee.

        :param optimality_guarantee: the given optimality guarantee.
        :return: True iff the engine satisfies the given optimality guarantee.
        """
        return False

    @staticmethod
    def supports_plan(plan_kind: "up.plans.PlanKind") -> bool:
        """
        :param plan_kind: The :func:`kind <unified_planning.plans.Plan.kind>` of the :class:`~unified_planning.plans.Plan` that must be supported.
        :return: `True` if the given `kind` of `Plan` is supported, False otherwise.
        """
        raise NotImplementedError

    def repair(
        self, problem: "up.model.AbstractProblem", plan: "up.plans.Plan"
    ) -> "up.engines.results.PlanGenerationResult":
        assert isinstance(self, up.engines.engine.Engine)
        problem_kind = problem.kind
        if not self.skip_checks and not self.supports(problem_kind):
            msg = f"We cannot establish whether {self.name} can validate this problem!"
            if self.error_on_failed_checks:
                raise up.exceptions.UPUsageError(msg)
            else:
                warn(msg)
        if not self.skip_checks and not self.supports_plan(plan.kind):
            msg = f"{self.name} cannot handle this kind of plan!"
            if self.error_on_failed_checks:
                raise up.exceptions.UPUsageError(msg)
            else:
                warn(msg)
        if not problem_kind.has_quality_metrics() and self.optimality_metric_required:
            msg = f"The problem has no quality metrics but the engine is required to be optimal!"
            raise up.exceptions.UPUsageError(msg)
        return self._repair(problem, plan)

    def _repair(
        self, problem: "up.model.AbstractProblem", plan: "up.plans.Plan"
    ) -> "up.engines.results.PlanGenerationResult":
        raise NotImplementedError
