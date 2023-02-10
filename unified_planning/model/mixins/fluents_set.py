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

from warnings import warn
import unified_planning as up
from unified_planning.model.expression import ConstantExpression
from unified_planning.exceptions import UPProblemDefinitionError, UPValueError
from typing import Optional, List, Dict, Union


class FluentsSetMixin:
    """
    This class is a mixin that contains a `set` of `fluents` with some related methods.

    NOTE: when this mixin is used in combination with other mixins that share some
    of the attributes (e.g. `env`, `add_user_type_method`, `has_name_method`), it is required
    to pass the very same arguments to the mixins constructors.
    """

    def __init__(
        self,
        env,
        add_user_type_method,
        has_name_method,
        initial_defaults: Dict["up.model.types.Type", "ConstantExpression"] = {},
    ):
        self._env = env
        self._add_user_type_method = add_user_type_method
        self._has_name_method = has_name_method
        self._fluents: List["up.model.fluent.Fluent"] = []
        self._fluents_defaults: Dict[
            "up.model.fluent.Fluent", "up.model.fnode.FNode"
        ] = {}
        self._initial_defaults: Dict["up.model.types.Type", "up.model.fnode.FNode"] = {}
        for k, v in initial_defaults.items():
            (v_exp,) = self.env.expression_manager.auto_promote(v)
            self._initial_defaults[k] = v_exp
        # The field initial default optionally associates a type to a default value. When a new fluent is
        # created with no explicit default, it will be associated with the initial-default of his type, if any.

    @property
    def env(self) -> "up.environment.Environment":
        """Returns the `problem` `Environment`."""
        return self._env

    @property
    def fluents(self) -> List["up.model.fluent.Fluent"]:
        """Returns the `fluents` currently in the `problem`."""
        return self._fluents

    def fluent(self, name: str) -> "up.model.fluent.Fluent":
        """
        Returns the `fluent` with the given name.

        :param name: The `name` of the target `fluent`:
        :return: The `fluent` with the given `name`.
        """
        for f in self._fluents:
            if f.name == name:
                return f
        raise UPValueError(f"Fluent of name: {name} is not defined!")

    def has_fluent(self, name: str) -> bool:
        """
        Returns `True` if the `fluent` with the given `name` is in the `problem`,
        `False` otherwise.

        :param name: The `name` of the target `fluent`.
        :return: `True` if the `fluent` with the given `name` is in the `problem`,
            `False` otherwise.
        """
        for f in self._fluents:
            if f.name == name:
                return True
        return False

    def add_fluents(self, fluents: List["up.model.fluent.Fluent"]):
        """
        Adds the given `list` of `fluents` to the `problem`.

        :param fluents: The `list` of `fluents` that must be added to the `problem`.
        """
        for fluent in fluents:
            self.add_fluent(fluent)

    def add_fluent(
        self,
        fluent_or_name: Union["up.model.fluent.Fluent", str],
        typename: Optional["up.model.types.Type"] = None,
        *,
        default_initial_value: Optional["ConstantExpression"] = None,
        **kwargs: "up.model.types.Type",
    ) -> "up.model.fluent.Fluent":
        """Adds the given `fluent` to the `problem`.

        If the first parameter is not a `Fluent`, the parameters will be passed to the `Fluent` constructor to create it.

        :param fluent_or_name: `Fluent` instance or `name` of the `fluent` to be constructed.
        :param typename: If only the `name` of the `fluent` is given, this is the `fluent's type` (passed to the `Fluent` constructor).
        :param default_initial_value: If provided, defines the default value taken in initial state by
                                      a state variable of this `fluent` that has no explicit value.
        :param kwargs: If only the `name` of the `fluent` is given, these are the `fluent's parameters` (passed to the `Fluent` constructor).
        :return: The `fluent` passed or constructed.

        Example
        --------
        >>> from unified_planning.shortcuts import *
        >>> problem = Problem()
        >>> location = UserType("Location")
        >>> at_loc = Fluent("at_loc", BoolType(), l=location)  # creates a new fluent
        >>> problem.add_fluent(at_loc)  # adds it to the problem
        bool at_loc[l=Location]
        >>> problem.add_fluent("connected", BoolType(), l1=location, l2=location)  # creates a new fluent and add it to the problem.
        bool connected[l1=Location, l2=Location]
        >>>
        """
        if isinstance(fluent_or_name, up.model.fluent.Fluent):
            assert len(kwargs) == 0 and typename is None
            fluent = fluent_or_name
            assert (
                fluent.environment == self._env
            ), "Fluent does not have the same environment of the problem"
        else:
            fluent = up.model.fluent.Fluent(
                fluent_or_name, typename, None, env=self.env, **kwargs
            )
        if self._has_name_method(fluent.name):
            msg = f"Name {fluent.name} already defined!"
            if self._env.error_used_name or any(
                fluent.name == f.name for f in self._fluents
            ):
                raise UPProblemDefinitionError(msg)
            else:
                warn(msg)
        self._fluents.append(fluent)
        if not default_initial_value is None:
            (v_exp,) = self.env.expression_manager.auto_promote(default_initial_value)
            self._fluents_defaults[fluent] = v_exp
        elif fluent.type in self._initial_defaults:
            self._fluents_defaults[fluent] = self._initial_defaults[fluent.type]
        if fluent.type.is_user_type():
            self._add_user_type_method(fluent.type)
        for param in fluent.signature:
            if param.type.is_user_type():
                self._add_user_type_method(param.type)

        return fluent

    @property
    def fluents_defaults(
        self,
    ) -> Dict["up.model.fluent.Fluent", "up.model.fnode.FNode"]:
        """Returns the `problem's fluents defaults`."""
        return self._fluents_defaults

    @property
    def initial_defaults(self) -> Dict["up.model.types.Type", "up.model.fnode.FNode"]:
        """Returns the `problem's fluents defaults` for each `type`."""
        return self._initial_defaults
