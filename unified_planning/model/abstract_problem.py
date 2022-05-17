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
'''This module defines an abstract problem class.'''

import unified_planning as up
from typing import Optional


class AbstractProblem:
    '''This is an abstract class that represents a generic planning problem'''

    def __init__(self, name: str = None, env: 'up.environment.Environment' = None):
        self._env = up.environment.get_env(env)
        self._name = name

    @property
    def env(self) -> 'up.environment.Environment':
        '''Returns the problem environment.'''
        return self._env

    @property
    def name(self) -> Optional[str]:
        '''Returns the problem name.'''
        return self._name

    @name.setter
    def name(self, new_name: str):
        '''Sets the problem name.'''
        self._name = new_name

    @property
    def kind(self) -> 'up.model.problem_kind.ProblemKind':
        raise NotImplementedError

    def has_name(self, name: str) -> bool:
        raise NotImplementedError

    def normalize_plan(self, plan: 'up.plan.Plan')-> 'up.plan.Plan':
        raise NotImplementedError
