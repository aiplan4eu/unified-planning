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

import unified_planning as up


class PlanValidatorMixin:

    @staticmethod
    def is_plan_validator() -> bool:
        return True

    @staticmethod
    def supports_plan(plan_kind: 'up.plans.PlanKind') -> bool:
        raise NotImplementedError

    def validate(self, problem: 'up.model.AbstractProblem',
                 plan: 'up.plans.Plan') -> 'up.engines.results.ValidationResult':
        assert isinstance(self, up.engines.engine.Engine)
        if not self.supports(problem.kind):
            raise up.exceptions.UPUsageError(f'{self.name} cannot validate this kind of problem!')
        if not self.supports_plan(plan.kind):
            raise up.exceptions.UPUsageError(f'{self.name} cannot validate this kind of plan!')
        return self._validate(problem, plan)

    def _validate(self, problem: 'up.model.AbstractProblem',
                  plan: 'up.plans.Plan') -> 'up.engines.results.ValidationResult':
        raise NotImplementedError
