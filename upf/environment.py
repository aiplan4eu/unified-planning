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
This module defines the Environment class.
The Environment is a structure that contains multiple
singleton objects that are used throughout the system,
such as the ExpressionManager, TypeChecker, TypeManager.
"""

import upf.model.expression
import upf.factory
import upf.model.types
import upf.type_checker
import upf.model.variable


class Environment:
    """Represents the environment."""
    def __init__(self):
        self._type_manager = upf.model.types.TypeManager()
        self._factory = upf.factory.Factory()
        self._tc = upf.type_checker.TypeChecker(self)
        self._expression_manager = upf.model.expression.ExpressionManager(self)
        self._free_vars_oracle = upf.model.variable.FreeVarsOracle()


    @property
    def free_vars_oracle(self) -> upf.model.variable.FreeVarsOracle:
        return self._free_vars_oracle

    @property
    def expression_manager(self) -> upf.model.expression.ExpressionManager:
        return self._expression_manager

    @property
    def type_manager(self) -> upf.model.types.TypeManager:
        return self._type_manager

    @property
    def type_checker(self) -> upf.type_checker.TypeChecker:
        """ Get the Type Checker """
        return self._tc

    @property
    def factory(self) -> upf.factory.Factory:
        return self._factory


GLOBAL_ENVIRONMENT = Environment()

def get_env(env: Environment = None) -> Environment:
    if env is None:
        return GLOBAL_ENVIRONMENT
    else:
        return env
