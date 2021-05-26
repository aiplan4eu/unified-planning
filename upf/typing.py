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
"""This module defines all the types."""

class Type:
    """Basic class for representing a type."""

    def is_bool_type(self):
        """Returns true iff is boolean type."""
        return False

    def is_user_type(self):
        """Returns true iff is a user type."""
        return False


class _BoolType(Type):
    """Represents the boolean type."""

    def is_bool_type(self):
        """Returns true iff is boolean type."""
        return True


class _UserType(Type):
    """Represents the user type."""
    def __init__(self, name):
        self._name = name

    def name(self):
        """Returns the type name."""
        return self._name

    def is_user_type(self):
        """Returns true iff is a user type."""
        return True


BOOL = _BoolType()

class TypeManager:
    def __init__(self):
        self._bool = BOOL
        self._user_types = {}

    def BoolType(self):
        return self._bool

    def UserType(self, name):
        if name in self._user_types:
            return self._user_types[name]
        else:
            ut = _UserType(name)
            self._user_types[name] = ut
            return ut
