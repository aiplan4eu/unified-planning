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

import sys
from typing import IO, Optional
import unified_planning


class Environment:
    """Represents the environment."""
    def __init__(self):
        import unified_planning.model
        import unified_planning.solvers
        import unified_planning.walkers
        self._type_manager = unified_planning.model.TypeManager()
        self._factory = unified_planning.solvers.Factory()
        self._tc = unified_planning.walkers.TypeChecker(self)
        self._expression_manager = unified_planning.model.ExpressionManager(self)
        self._free_vars_oracle = unified_planning.model.FreeVarsOracle()


    @property
    def free_vars_oracle(self) -> 'unified_planning.model.FreeVarsOracle':
        return self._free_vars_oracle

    @property
    def expression_manager(self) -> 'unified_planning.model.ExpressionManager':
        return self._expression_manager

    @property
    def type_manager(self) -> 'unified_planning.model.TypeManager':
        return self._type_manager

    @property
    def type_checker(self) -> 'unified_planning.walkers.TypeChecker':
        """ Get the Type Checker """
        return self._tc

    @property
    def factory(self) -> 'unified_planning.solvers.Factory':
        return self._factory


GLOBAL_ENVIRONMENT: Optional[Environment] = None

def get_env(env: Environment = None) -> Environment:
    global GLOBAL_ENVIRONMENT
    if env is None:
        if GLOBAL_ENVIRONMENT is None:
            GLOBAL_ENVIRONMENT = Environment()
        return GLOBAL_ENVIRONMENT
    else:
        return env
