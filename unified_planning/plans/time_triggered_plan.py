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
from unified_planning.environment import Environment
from unified_planning.exceptions import UPUsageError
from typing import Callable, Optional, Tuple, List
from fractions import Fraction


class TimeTriggeredPlan(plans.plan.Plan):
    '''Represents a time triggered plan.'''
    def __init__(self, actions: List[Tuple[Fraction, 'plans.plan.ActionInstance', Optional[Fraction]]], environment: Optional['Environment'] = None):
        '''The first Fraction represents the absolute time in which the action
        Action starts, while the last Fraction represents the duration
        of the action to fullfill the problem goals.
        The Action can be an InstantaneousAction, this is represented with a duration set
        to None.
        '''
        plans.plan.Plan.__init__(self, environment)
        for _, ai, _ in actions: # check that given env and the env in the actions is the same
            if ai.action.env != self._environment:
                raise UPUsageError('The environment given to the plan is not the same of the actions in the plan.')
        self._actions = actions

    def __repr__(self) -> str:
        return str(self._actions)

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, TimeTriggeredPlan) and len(self._actions) == len(oth._actions):
            for (s, ai, d), (oth_s, oth_ai, oth_d) in zip(self._actions, oth._actions):
                if s != oth_s or ai.action != oth_ai.action or ai.actual_parameters != oth_ai.actual_parameters or d != oth_d:
                    return False
            return True
        else:
            return False

    def __hash__(self) -> int:
        count: int = 0
        for i, (s, ai, d) in enumerate(self._actions):
            count += i + hash(ai.action) + hash(ai.actual_parameters) + hash(s) + hash(d)
        return count

    def __contains__(self, item: object) -> bool:
        if isinstance(item, plans.plan.ActionInstance):
            return any(item.is_semantically_equivalent(a) for _, a, _ in self._actions)
        else:
            return False

    @property
    def actions(self) -> List[Tuple[Fraction, 'plans.plan.ActionInstance', Optional[Fraction]]]:
        '''Returns the sequence of tuples (start, action_instance, duration) where:
            start is when the action starts;
            action_instance is the action applied;
            duration is the (optional) duration of the action.'''
        return self._actions

    def replace_action_instances(self, replace_function: Callable[['plans.plan.ActionInstance'], 'plans.plan.ActionInstance']) -> 'plans.plan.Plan':
        new_ai = [(s, replace_function(ai), d) for s, ai, d in self._actions]
        new_env = self._environment
        if len(new_ai) > 0:
            _, ai, _ = new_ai[0]
            new_env = ai.action.env
        return TimeTriggeredPlan(new_ai, new_env)
