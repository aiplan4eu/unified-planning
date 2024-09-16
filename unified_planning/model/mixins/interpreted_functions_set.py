# Copyright 2021-2023 AIPlan4EU project
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

from warnings import warn
import unified_planning as up
from unified_planning.model.expression import ConstantExpression
from unified_planning.exceptions import UPProblemDefinitionError, UPValueError
from typing import Optional, List, Dict, Union, Iterable, Set


class InterpretedFunctionsSetMixin:
    """
    This class is a mixin that contains a `set` of `interpreted_functions` with some related methods.

    NOTE: when this mixin is used in combination with other mixins that share some
    of the attributes (e.g. `environment`, `add_user_type_method`, `has_name_method`), it is required
    to pass the very same arguments to the mixins constructors.
    """

    def __init__(
        self,
        environment,
        add_user_type_method,
        has_name_method,
        initial_defaults: Dict["up.model.types.Type", "ConstantExpression"] = {},
    ):
        self._env = environment
        self._add_user_type_method = add_user_type_method
        self._has_name_method = has_name_method
        self._interpreted_functions: List[
            "up.model.interpreted_function.InterpretedFunction"
        ] = []
        self._interpreted_functions_defaults: Dict[
            "up.model.interpreted_function.InterpretedFunction", "up.model.fnode.FNode"
        ] = {}
        self._initial_defaults: Dict["up.model.types.Type", "up.model.fnode.FNode"] = {}
        for k, v in initial_defaults.items():
            (v_exp,) = self.environment.expression_manager.auto_promote(v)
            self._initial_defaults[k] = v_exp
        # The field initial default optionally associates a type to a default value. When a new fluent is
        # created with no explicit default, it will be associated with the initial-default of his type, if any.

    @property
    def environment(self) -> "up.environment.Environment":
        """Returns the `problem` `Environment`."""
        return self._env

    @property
    def interpreted_functions(
        self,
    ) -> List["up.model.interpreted_function.InterpretedFunction"]:
        """Returns the `interpreted_functions` currently in the `problem`."""
        return self._interpreted_functions

    def interpreted_function(
        self, name: str
    ) -> "up.model.interpreted_function.InterpretedFunction":
        """
        Returns the `interpreted_function` with the given name.

        :param name: The `name` of the target `interpreted_function`:
        :return: The `interpreted_function` with the given `name`.
        """
        for f in self._interpreted_functions:
            if f.name == name:
                return f
        raise UPValueError(f"Interpreted function of name: {name} is not defined!")

    def has_interpreted_function(self, name: str) -> bool:
        """
        Returns `True` if the `interpreted_function` with the given `name` is in the `problem`,
        `False` otherwise.

        :param name: The `name` of the target `interpreted_function`.
        :return: `True` if the `interpreted_function` with the given `name` is in the `problem`,
            `False` otherwise.
        """
        for f in self._interpreted_functions:
            if f.name == name:
                return True
        return False

    def add_interpreted_functions(
        self,
        interpreted_functions: Iterable[
            "up.model.interpreted_function.InterpretedFunction"
        ],
    ):
        """
        Adds the given `interpreted_functions` to the `problem`.

        :param fluents: The `interpreted_functions` that must be added to the `problem`.
        """
        for interpreted_function in interpreted_functions:
            self.add_interpreted_function(interpreted_function)

    def add_interpreted_function(  ###### adding from name does not work yet
        self,
        interpreted_function_or_name: Union[
            "up.model.interpreted_function.InterpretedFunction", str
        ],
        return_type: Optional["up.model.types.Type"] = None,
        *,
        default_initial_value: Optional["ConstantExpression"] = None,
        **kwargs: "up.model.types.Type",
    ) -> "up.model.interpreted_function.InterpretedFunction":
        """Adds the given `interpreted_function` to the `problem`.

        If the first parameter is not a `InterpretedFunction`, the parameters will be passed to the `InterpretedFunction` constructor to create it.

        :param interpreted_function_or_name: `InterpretedFunction` instance or `name` of the `interpreted_function` to be constructed.
        :param return_type: If only the `name` of the `interpreted_function` is given, this is the `interpreted_function's return type` (passed to the `InterpretedFunction` constructor).
        :param default_initial_value: If provided, defines the default value taken in initial state by
                                      a state variable of this `interpreted_function` that has no explicit value.
        :param kwargs: If only the `name` of the `interpreted_function` is given, these are the `interpreted_function's parameters` (passed to the `InterpretedFunction` constructor).
        :return: The `interpreted_function` passed or constructed.

        """
        if isinstance(
            interpreted_function_or_name,
            up.model.interpreted_function.InterpretedFunction,
        ):
            assert len(kwargs) == 0 and return_type is None
            interpreted_function = interpreted_function_or_name
            assert (
                interpreted_function.environment == self._env
            ), "InterpretedFunction does not have the same environment of the problem"
        # else:
        #    interpreted_function = up.model.interpreted_function.InterpretedFunction(
        #        interpreted_function_or_name, return_type, None, environment=self.environment, **kwargs
        #    )
        if self._has_name_method(interpreted_function.name):
            msg = f"Name {interpreted_function.name} already defined! Different elements of a problem can have the same name if the environment flag error_used_name is disabled."
            if self._env.error_used_name or any(
                interpreted_function.name == f.name for f in self._interpreted_functions
            ):
                raise UPProblemDefinitionError(msg)
            else:
                warn(msg)
        self._interpreted_functions.append(interpreted_function)
        # if not default_initial_value is None:
        #    (v_exp,) = self.environment.expression_manager.auto_promote(
        #        default_initial_value
        #    )
        #    self._interpreted_functions_defaults[interpreted_function] = v_exp
        # elif interpreted_function.type in self._initial_defaults:
        #    self._interpreted_functions_defaults[
        #        interpreted_function
        #    ] = self._initial_defaults[interpreted_function.type]
        # if interpreted_function.type.is_user_type():
        #    self._add_user_type_method(interpreted_function.type)
        # for param in interpreted_function.signature:
        #    if param.type.is_user_type():
        #        self._add_user_type_method(param.type)

        return interpreted_function

    def clear_interpreted_functions(self):
        """
        Removes all the InterpretedFunctions from the current Problem, together with their default.
        """
        self._interpreted_functions = []
        self._interpreted_functions_defaults = {}

    @property
    def interpreted_functions_defaults(
        self,
    ) -> Dict[
        "up.model.interpreted_function.InterpretedFunction", "up.model.fnode.FNode"
    ]:
        """Returns the `problem's interpreted functions defaults`."""
        return self._interpreted_functions_defaults

    @property
    def initial_defaults(self) -> Dict["up.model.types.Type", "up.model.fnode.FNode"]:
        """Returns the `problem's fluents defaults` for each `type`."""
        return self._initial_defaults

    def __eq__(self, oth):
        # ignores default values as they may have no impact on the initial state
        if not isinstance(oth, InterpretedFunctionsSetMixin):
            return False
        if set(self._interpreted_functions) != set(oth._interpreted_functions):
            return False
        return True

    def __hash__(self):
        return sum(map(hash, self._interpreted_functions))

    def _clone_to(self, other: "InterpretedFunctionsSetMixin"):
        other._interpreted_functions = self._interpreted_functions.copy()
        other._initial_defaults = self._initial_defaults.copy()
        other._interpreted_functions_defaults = (
            self._interpreted_functions_defaults.copy()
        )

    # def get_static_fluents(self) -> Set["up.model.fluent.Fluent"]:
    #    """
    #    Returns the set of the `static fluents`.
    #
    #    `Static fluents` are those who can't change their values because they never
    #    appear in the :func:`fluent <unified_planning.model.Effect.fluent>` field of an `Effect`, therefore there are no :func:`Actions <unified_planning.model.Problem.actions>`
    #    in the `Problem` that can change their value.
    #    """
    #    return set()  # conservative default, should be overriden
    #
    # def get_unused_fluents(self) -> Set["up.model.fluent.Fluent"]:
    #    """
    #    Returns the set of `fluents` that are never used in the problem.
    #    """
    #    return set()  # conservative default, should be overriden
