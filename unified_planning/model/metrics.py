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
from typing import Dict, Optional


class PlanQualityMetric():
    '''This is the base class of any metric for plan quality'''
    pass

class MinimizeActionCosts(PlanQualityMetric):
    def __init__(self, costs: Dict['up.model.Action', 'up.model.FNode'],
                 default: Optional['up.model.FNode'] = None):
        self.costs = costs
        self.default = default

    def __repr__(self):
        costs = {a.name: c for a, c in self.costs.items()}
        costs['default'] = self.default
        return f'minimize actions-cost: {costs}'

    def get_action_cost(self, action: 'up.model.Action') -> Optional['up.model.FNode']:
        return self.costs.get(action, self.default)

class MinimizeSequentialPlanLength(PlanQualityMetric):
    def __repr__(self):
        return 'minimize sequential-plan-length'

class MinimizeMakespan(PlanQualityMetric):
    def __repr__(self):
        return 'minimize makespan'

class MinimizeExpressionOnFinalState(PlanQualityMetric):
    def __init__(self, expression: 'up.model.FNode'):
        self.expression = expression

    def __repr__(self):
        return f'minimize {self.expression}'

class MaximizeExpressionOnFinalState(PlanQualityMetric):
    def __init__(self, expression: 'up.model.FNode'):
        self.expression = expression

    def __repr__(self):
        return f'maximize {self.expression}'
