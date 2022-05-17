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
'''This module defines the different plan classes.'''


import unified_planning as up
from typing import Callable, Optional, Tuple, List
from fractions import Fraction


class ActionInstance:
    '''Represents an action instance with the actual parameters.'''
    def __init__(self, action: 'up.model.Action', params: Tuple['up.model.FNode', ...] = tuple()):
        assert len(action.parameters) == len(params)
        self._action = action
        self._params = tuple(params)

    def __repr__(self) -> str:
        s = []
        if len(self._params) > 0:
            s.append('(')
            first = True
            for p in self._params:
                if not first:
                    s.append(', ')
                s.append(str(p))
                first = False
            s.append(')')
        return self._action.name + ''.join(s)

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, ActionInstance):
            return self.action == oth.action and self.actual_parameters == oth.actual_parameters
        else:
            return False

    @property
    def action(self) -> 'up.model.Action':
        '''Returns the action.'''
        return self._action

    @property
    def actual_parameters(self) -> Tuple['up.model.FNode', ...]:
        '''Returns the actual parameters.'''
        return self._params


class Plan:
    '''Represents a generic plan.'''
    def replace_action_instances(self, replace_function: Callable[[ActionInstance], ActionInstance]) -> 'Plan':
        '''This function takes a function from ActionInstance to ActionInstance and returns a new Plan
        that have the ActionInstance modified by the "replace_function" function.'''
        raise NotImplementedError


class SequentialPlan(Plan):
    '''Represents a sequential plan.'''
    def __init__(self, actions: List[ActionInstance]):
        self._actions = actions

    def __repr__(self) -> str:
        return str(self._actions)

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, SequentialPlan):
            return self.actions == oth.actions
        else:
            return False

    @property
    def actions(self) -> List[ActionInstance]:
        '''Returns the sequence of action instances.'''
        return self._actions

    def replace_action_instances(self, replace_function: Callable[[ActionInstance], ActionInstance]) -> 'Plan':
        return SequentialPlan([replace_function(ai) for ai in self._actions])


class TimeTriggeredPlan(Plan):
    '''Represents a time triggered plan.'''
    def __init__(self, actions: List[Tuple[Fraction, ActionInstance, Optional[Fraction]]]):
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
    def actions(self) -> List[Tuple[Fraction, ActionInstance, Optional[Fraction]]]:
        '''Returns the sequence of action instances.'''
        return self._actions

    def replace_action_instances(self, replace_function: Callable[[ActionInstance], ActionInstance]) -> 'Plan':
        return TimeTriggeredPlan([(s, replace_function(ai), d) for s, ai, d in self._actions])
