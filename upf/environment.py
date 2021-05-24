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
"""This module defines the environment."""

import upf.expression
import upf.typing
import upf.type_checker


class Environment:
    """Represents the environment."""
    def __init__(self):
        self._stc = upf.type_checker.SimpleTypeChecker()
        self._expression_manager = upf.expression.ExpressionManager(self)
        self._type_manager = upf.typing.TypeManager()

    @property
    def expression_manager(self):
        return self._expression_manager

    @property
    def type_manager(self):
        return self._type_manager

    @property
    def stc(self):
        """ Get the Simple Type Checker """
        return self._stc


ENVIRONMENT = Environment()

def get_env(env=None):
    if env is None:
        return ENVIRONMENT
    else:
        return env
