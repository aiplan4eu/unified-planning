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


class NaturalTransitionsSetMixin:
    """
    This class is a mixin that contains a `set` of `natural_transitions` with some related methods.

    NOTE: when this mixin is used in combination with other mixins that share some
    of the attributes (e.g. `environment`, `add_user_type_method`, `has_name_method`), it is required
    to pass the very same arguments to the mixins constructors.
    """

    def __init__(self, environment, add_user_type_method, has_name_method):
        self._env = environment
        self._add_user_type_method = add_user_type_method
        self._has_name_method = has_name_method
        self._natural_transitions: List[
            "up.model.natural_transition.NaturalTransition"
        ] = []

    @property
    def environment(self) -> "up.environment.Environment":
        """Returns the `Problem` environment."""
        return self._env

    @property
    def natural_transitions(
        self,
    ) -> List["up.model.natural_transition.NaturalTransition"]:
        """Returns the list of the `NaturalTransitions` in the `Problem`."""
        return self._natural_transitions

    def clear_natural_transitions(self):
        """Removes all the `Problem` `NaturalTransitions`."""
        self._natural_transitions = []

    @property
    def processes(self) -> Iterator["up.model.natural_transition.Process"]:
        """Returs all the processes of the problem.

        IMPORTANT NOTE: this property does some computation, so it should be called as
        seldom as possible."""
        for a in self._natural_transitions:
            if isinstance(a, up.model.natural_transition.Process):
                yield a

    @property
    def events(self) -> Iterator["up.model.natural_transition.Event"]:
        """Returs all the events of the problem.

        IMPORTANT NOTE: this property does some computation, so it should be called as
        seldom as possible."""
        for a in self._natural_transitions:
            if isinstance(a, up.model.natural_transition.Event):
                yield a

    def natural_transition(
        self, name: str
    ) -> "up.model.natural_transition.NaturalTransition":
        """
        Returns the `natural_transition` with the given `name`.

        :param name: The `name` of the target `natural_transition`.
        :return: The `natural_transition` in the `problem` with the given `name`.
        """
        for a in self._natural_transitions:
            if a.name == name:
                return a
        raise UPValueError(f"NaturalTransition of name: {name} is not defined!")

    def has_natural_transition(self, name: str) -> bool:
        """
        Returns `True` if the `problem` has the `natural_transition` with the given `name`,
        `False` otherwise.

        :param name: The `name` of the target `natural_transition`.
        :return: `True` if the `problem` has an `natural_transition` with the given `name`, `False` otherwise.
        """
        for a in self._natural_transitions:
            if a.name == name:
                return True
        return False

    def add_natural_transition(
        self, natural_transition: "up.model.natural_transition.NaturalTransition"
    ):
        """
        Adds the given `natural_transition` to the `problem`.

        :param natural_transition: The `natural_transition` that must be added to the `problem`.
        """
        assert (
            natural_transition.environment == self._env
        ), "NaturalTransition does not have the same environment of the problem"
        if self._has_name_method(natural_transition.name):
            msg = f"Name {natural_transition.name} already defined! Different elements of a problem can have the same name if the environment flag error_used_name is disabled."
            if self._env.error_used_name or any(
                natural_transition.name == a.name for a in self._natural_transitions
            ):
                raise UPProblemDefinitionError(msg)
            else:
                warn(msg)
        self._natural_transitions.append(natural_transition)
        for param in natural_transition.parameters:
            if param.type.is_user_type():
                self._add_user_type_method(param.type)

    def add_natural_transitions(
        self,
        natural_transitions: Iterable["up.model.natural_transition.NaturalTransition"],
    ):
        """
        Adds the given `natural_transitions` to the `problem`.

        :param natural_transitions: The `natural_transitions` that must be added to the `problem`.
        """
        for natural_transition in natural_transitions:
            self.add_natural_transition(natural_transition)
