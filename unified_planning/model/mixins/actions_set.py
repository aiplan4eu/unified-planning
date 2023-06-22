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
from unified_planning.exceptions import UPProblemDefinitionError, UPValueError
from typing import Iterator, List, Iterable


class ActionsSetMixin:
    """
    This class is a mixin that contains a `set` of `actions` with some related methods.

    NOTE: when this mixin is used in combination with other mixins that share some
    of the attributes (e.g. `environment`, `add_user_type_method`, `has_name_method`), it is required
    to pass the very same arguments to the mixins constructors.
    """

    def __init__(self, environment, add_user_type_method, has_name_method):
        self._env = environment
        self._add_user_type_method = add_user_type_method
        self._has_name_method = has_name_method
        self._actions: List["up.model.action.Action"] = []

    @property
    def environment(self) -> "up.environment.Environment":
        """Returns the `Problem` environment."""
        return self._env

    @property
    def actions(self) -> List["up.model.action.Action"]:
        """Returns the list of the `Actions` in the `Problem`."""
        return self._actions

    def clear_actions(self):
        """Removes all the `Problem` `Actions`."""
        self._actions = []

    @property
    def instantaneous_actions(self) -> Iterator["up.model.action.InstantaneousAction"]:
        """
        Returns all the `InstantaneousActions` of the `Problem`.

        IMPORTANT NOTE: this property does some computation, so it should be called as
        seldom as possible.
        """
        for a in self._actions:
            if isinstance(a, up.model.action.InstantaneousAction):
                yield a

    @property
    def sensing_actions(self) -> Iterator["up.model.action.SensingAction"]:
        """Returs all the sensing actions of the problem.

        IMPORTANT NOTE: this property does some computation, so it should be called as
        seldom as possible."""
        for a in self._actions:
            if isinstance(a, up.model.action.SensingAction):
                yield a

    @property
    def durative_actions(self) -> Iterator["up.model.action.DurativeAction"]:
        """
        Returns all the `DurativeActions` of the `Problem`.

        IMPORTANT NOTE: this property does some computation, so it should be called as
        seldom as possible.
        """
        for a in self._actions:
            if isinstance(a, up.model.action.DurativeAction):
                yield a

    @property
    def conditional_actions(self) -> List["up.model.action.Action"]:
        """
        Returns the `conditional Actions`.

        IMPORTANT NOTE: this property does some computation, so it should be called as
        seldom as possible.
        """
        return [a for a in self._actions if a.is_conditional()]

    @property
    def unconditional_actions(self) -> List["up.model.action.Action"]:
        """
        Returns the `unconditional Actions`.

        IMPORTANT NOTE: this property does some computation, so it should be called as
        seldom as possible.
        """
        return [a for a in self._actions if not a.is_conditional()]

    def action(self, name: str) -> "up.model.action.Action":
        """
        Returns the `action` with the given `name`.

        :param name: The `name` of the target `action`.
        :return: The `action` in the `problem` with the given `name`.
        """
        for a in self._actions:
            if a.name == name:
                return a
        raise UPValueError(f"Action of name: {name} is not defined!")

    def has_action(self, name: str) -> bool:
        """
        Returns `True` if the `problem` has the `action` with the given `name`,
        `False` otherwise.

        :param name: The `name` of the target `action`.
        :return: `True` if the `problem` has an `action` with the given `name`, `False` otherwise.
        """
        for a in self._actions:
            if a.name == name:
                return True
        return False

    def add_action(self, action: "up.model.action.Action"):
        """
        Adds the given `action` to the `problem`.

        :param action: The `action` that must be added to the `problem`.
        """
        assert (
            action.environment == self._env
        ), "Action does not have the same environment of the problem"
        if self._has_name_method(action.name):
            msg = f"Name {action.name} already defined! Different elements of a problem can have the same name if the environment flag error_used_named is disabled."
            if self._env.error_used_name or any(
                action.name == a.name for a in self._actions
            ):
                raise UPProblemDefinitionError(msg)
            else:
                warn(msg)
        self._actions.append(action)
        for param in action.parameters:
            if param.type.is_user_type():
                self._add_user_type_method(param.type)

    def add_actions(self, actions: Iterable["up.model.action.Action"]):
        """
        Adds the given `actions` to the `problem`.

        :param actions: The `actions` that must be added to the `problem`.
        """
        for action in actions:
            self.add_action(action)
