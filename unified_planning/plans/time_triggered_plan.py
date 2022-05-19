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
import unified_planning.plans as plans
from typing import Callable, Optional, Tuple, List
from fractions import Fraction


class TimeTriggeredPlan(plans.plan.Plan):
    '''Represents a time triggered plan.'''
    def __init__(self, actions: List[Tuple[Fraction, 'plans.plan.ActionInstance', Optional[Fraction]]]):
        '''The first Fraction represents the absolute time in which the action
        Action starts, while the last Fraction represents the duration
        of the action to fullfill the problem goals.
        The Action can be an InstantaneousAction, this is represented with a duration set
        to None.
        '''
        self._actions = actions

    def __repr__(self) -> str:
        return str(self._actions)

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, TimeTriggeredPlan):
            return self.actions == oth.actions
        else:
            return False

    @property
    def actions(self) -> List[Tuple[Fraction, 'plans.plan.ActionInstance', Optional[Fraction]]]:
        '''Returns the sequence of action instances.'''
        return self._actions

    def replace_action_instances(self, replace_function: Callable[['plans.plan.ActionInstance'], 'plans.plan.ActionInstance']) -> 'plans.plan.Plan':
        return TimeTriggeredPlan([(s, replace_function(ai), d) for s, ai, d in self._actions])
