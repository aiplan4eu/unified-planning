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
from unified_planning.exceptions import UPProblemDefinitionError, UPValueError
from typing import Iterator, List


class ActionsSet:
    def __init__(self, env, add_user_type_method, has_name_method):
        self._env = env
        self._add_user_type_method = add_user_type_method
        self._has_name_method = has_name_method
        self._actions: List['up.model.action.Action'] = []

    @property
    def env(self) -> 'up.environment.Environment':
        '''Returns the problem environment.'''
        return self._env

    @property
    def actions(self) -> List['up.model.action.Action']:
        '''Returns the list of the actions in the problem.'''
        return self._actions

    def clear_actions(self):
        '''Removes all the problem actions.'''
        self._actions = []

    @property
    def instantaneous_actions(self) -> Iterator['up.model.action.InstantaneousAction']:
        '''Returs all the instantaneous actions of the problem.

        IMPORTANT NOTE: this property does some computation, so it should be called as
        minimum time as possible.'''
        for a in self._actions:
            if isinstance(a, up.model.action.InstantaneousAction):
                yield a

    @property
    def durative_actions(self) -> Iterator['up.model.action.DurativeAction']:
        '''Returs all the durative actions of the problem.

        IMPORTANT NOTE: this property does some computation, so it should be called as
        minimum time as possible.'''
        for a in self._actions:
            if isinstance(a, up.model.action.DurativeAction):
                yield a

    @property
    def conditional_actions(self) -> List['up.model.action.Action']:
        '''Returns the conditional actions.

        IMPORTANT NOTE: this property does some computation, so it should be called as
        minimum time as possible.'''
        return [a for a in self._actions if a.is_conditional()]

    @property
    def unconditional_actions(self) -> List['up.model.action.Action']:
        '''Returns the conditional actions.

        IMPORTANT NOTE: this property does some computation, so it should be called as
        minimum time as possible.'''
        return [a for a in self._actions if not a.is_conditional()]

    def action(self, name: str) -> 'up.model.action.Action':
        '''Returns the action with the given name.'''
        for a in self._actions:
            if a.name == name:
                return a
        raise UPValueError(f'Action of name: {name} is not defined!')

    def has_action(self, name: str) -> bool:
        '''Returns True if the problem has the action with the given name .'''
        for a in self._actions:
            if a.name == name:
                return True
        return False

    def add_action(self, action: 'up.model.action.Action'):
        '''Adds the given action.'''
        if self._has_name_method(action.name):
            raise UPProblemDefinitionError('Name ' + action.name + ' already defined!')
        self._actions.append(action)
        for param in action.parameters:
            if param.type.is_user_type():
                self._add_user_type_method(param.type)
