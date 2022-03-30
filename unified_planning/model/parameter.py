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
'''
This module defines the Parameter class. Both actions and fluents use this class to represent their parameters.
'''


import unified_planning as up


class Parameter:
    '''Represents an action parameter or a fluent parameter.
    A parameter has a name, and a type.'''
    def __init__(self, name: str, typename: 'up.model.types.Type'):
        self._name = name
        self._typename = typename

    def __repr__(self) -> str:
        return f'{str(self.type)} {self.name}'

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, Parameter):
            return self._name == oth._name and self._typename == oth._typename
        else:
            return False

    def __hash__(self) -> int:
        return hash(self._name) + hash(self._typename)

    @property
    def name(self) -> str:
        '''Returns the parameter name.'''
        return self._name

    @property
    def type(self) -> 'up.model.types.Type':
        '''Returns the parameter type.'''
        return self._typename
