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
This module defines the `Environment` class.
The `Environment` is a structure that contains multiple
singleton objects that are used throughout the system,
such as the :func:`ExpressionManager <unified_planning.Environment.expression_manager>`, :func:`TypeChecker <unified_planning.Environment.type_checker>`, :func:`ExpressionManager <unified_planning.Environment.expression_manager>`, :func:`TypeManager <unified_planning.Environment.type_manager>`.
"""


import sys
from typing import IO, Optional
import unified_planning


class Environment:
    """
    Represents the environment in the `unified_planning` library.

    The `Environment` is a structure that contains multiple
    singleton objects that are used throughout the system,
    such as the :func:`ExpressionManager <unified_planning.Environment.expression_manager>`, :func:`TypeChecker <unified_planning.Environment.type_checker>`, :func:`ExpressionManager <unified_planning.Environment.expression_manager>`, :func:`TypeManager <unified_planning.Environment.type_manager>`.

    """

    def __init__(self):
        import unified_planning.model
        import unified_planning.engines
        import unified_planning.model.walkers

        self._type_manager = unified_planning.model.TypeManager()
        self._factory = unified_planning.engines.Factory(self)
        self._tc = unified_planning.model.walkers.TypeChecker(self)
        self._expression_manager = unified_planning.model.ExpressionManager(self)
        self._free_vars_oracle = unified_planning.model.FreeVarsOracle()
        self._simplifier = unified_planning.model.walkers.Simplifier(self)
        self._substituter = unified_planning.model.walkers.Substituter(self)
        self._free_vars_extractor = unified_planning.model.walkers.FreeVarsExtractor()
        self._names_extractor = unified_planning.model.walkers.NamesExtractor()
        self._credits_stream: Optional[IO[str]] = sys.stdout
        self._error_used_name: bool = True

    # The getstate and setstate method are needed in the Parallel engine. The
    #  Parallel engine creates a deep copy of the Environment instance in
    #  another process by pickling the environment fields.
    # Since the IO[str] class is not picklable, we need to remove it from the
    #  state and then add it as None in the new process
    def __getstate__(self):
        state = self.__dict__.copy()
        # Don't pickle _credits_stream
        del state["_credits_stream"]
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        # Add _credits_stream back since it doesn't exist in the pickle
        self._credits_stream = None

    @property
    def error_used_name(self) -> bool:
        return self._error_used_name

    @error_used_name.setter
    def error_used_name(self, new_val: bool):
        """
        This flag determines if a problem in this environment can have the same
        name for different elements (like an Action and a Fluent). If it is
        True, this name duplication will raise an exception, if it is False it
        will only raise a warning.

        It always raise an exception to name in the same way 2 elements
        belonging to the same category, like 2 actions.
        """
        self._error_used_name = new_val

    @property
    def free_vars_oracle(self) -> "unified_planning.model.FreeVarsOracle":
        """Returns the environment's `FreeVarsOracle`."""
        return self._free_vars_oracle

    @property
    def expression_manager(self) -> "unified_planning.model.ExpressionManager":
        """Returns the environment's `ExpressionManager`."""
        return self._expression_manager

    @property
    def type_manager(self) -> "unified_planning.model.TypeManager":
        """Returns the environment's `TypeManager`."""
        return self._type_manager

    @property
    def type_checker(self) -> "unified_planning.model.walkers.TypeChecker":
        """Returns the environment's `TypeChecker`."""
        """Get the Type Checker"""
        return self._tc

    @property
    def factory(self) -> "unified_planning.engines.Factory":
        """Returns the environment's `Factory`."""
        return self._factory

    @property
    def simplifier(self) -> "unified_planning.model.walkers.Simplifier":
        """Returns the environment's `Simplifier`."""
        return self._simplifier

    @property
    def substituter(self) -> "unified_planning.model.walkers.Substituter":
        """Returns the environment's `Substituter`."""
        return self._substituter

    @property
    def free_vars_extractor(self) -> "unified_planning.model.walkers.FreeVarsExtractor":
        """Returns the environment's `FreeVarsExtractor`."""
        return self._free_vars_extractor

    @property
    def names_extractor(self) -> "unified_planning.model.walkers.NamesExtractor":
        return self._names_extractor

    @property
    def credits_stream(self) -> "Optional[IO[str]]":
        """Returns the stream where the :class:`Engines <unified_planning.engines.Engine>` :func:`credits <unified_planning.engines.Engine.get_credits>` are printed."""
        return self._credits_stream

    @credits_stream.setter
    def credits_stream(self, new_credits_stream: Optional[IO[str]]):
        """Sets the stream where the :class:`Engines <unified_planning.engines.Engine>` :func:`credits <unified_planning.engines.Engine.get_credits>` are printed."""
        self._credits_stream = new_credits_stream


GLOBAL_ENVIRONMENT: Optional[Environment] = None


def get_environment(environment: Optional[Environment] = None) -> Environment:
    """
    Returns the given environment if it is not `None`, returns the `GLOBAL_ENVIRONMENT` otherwise.

    :param environment: The environment to return.
    :return: The given `environment` if it is not `None`, the `GLOBAL_ENVIRONMENT` otherwise.
    """
    global GLOBAL_ENVIRONMENT
    if environment is None:
        if GLOBAL_ENVIRONMENT is None:
            GLOBAL_ENVIRONMENT = Environment()
        return GLOBAL_ENVIRONMENT
    else:
        return environment
