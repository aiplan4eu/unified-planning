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
import unified_planning.model
from unified_planning.environment import Environment, get_env
from unified_planning.model import FNode, Action, InstantaneousAction, Expression, Effect
from unified_planning.walkers import Substituter, Simplifier
from typing import Callable, Dict, Optional, Tuple


'''This module defines the different plan classes.'''


class ActionInstance:
    '''Represents an action instance with the actual parameters.

    NOTE: two action instances of the same action with the same parameters are
    considered different as it is possible to have the same action twice in a plan.'''
    def __init__(self, action: 'unified_planning.model.Action', params: Tuple['unified_planning.model.FNode', ...] = tuple()):
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


    @property
    def action(self) -> 'Action':
        '''Returns the action.'''
        return self._action

    @property
    def actual_parameters(self) -> Tuple['FNode', ...]:
        '''Returns the actual parameters.'''
        return self._params

    def is_semantically_equivalent(self, oth: 'ActionInstance') -> bool:
        '''This method returns True Iff the 2 Action Instances have the same semantic.

        NOTE: This is different from __eq__; there the 2 Action Instances need to be exactly the same object.'''
        return self.action == oth.action and self._params == oth._params


class Plan:
    '''Represents a generic plan.'''
    def __init__(self, environment: Optional['Environment'] = None) -> None:
        self._environment = get_env(environment)

    @property
    def environment(self) -> 'Environment':
        '''Return this plan environment.'''
        return self._environment

    def replace_action_instances(self, replace_function: Callable[[ActionInstance], ActionInstance]) -> 'Plan':
        '''This function takes a function from ActionInstance to ActionInstance and returns a new Plan
        that have the ActionInstance modified by the "replace_function" function.'''
        raise NotImplementedError
