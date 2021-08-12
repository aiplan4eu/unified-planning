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
"""
This module defines the Variable class.
A Variable has a name and a type.
"""

import upf
import upf.types


class Variable:
    """Represents a varible."""
    #NOTE Does this class really need a name?
    def __init__(self, name: str, typename: upf.types.Type):
        self._name = name
        self._typename = typename

    def __repr__(self) -> str:
        return f'{str(self.type())} {self.name()}'

    def name(self) -> str:
        """Returns the variable name."""
        return self._name

    def type(self) -> upf.types.Type:
        """Returns the variable type."""
        return self._typename
