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
from typing import Iterator, List, Iterable, Union


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
        self._events: List["up.model.natural_transition.Event"] = []
        self._processes: List["up.model.natural_transition.Process"] = []

    @property
    def environment(self) -> "up.environment.Environment":
        """Returns the `Problem` environment."""
        return self._env

    @property
    def processes(
        self,
    ) -> List["up.model.natural_transition.Process"]:
        """Returns the list of the `Processes` in the `Problem`."""
        return self._processes

    @property
    def events(
        self,
    ) -> List["up.model.natural_transition.Event"]:
        """Returns the list of the `Events` in the `Problem`."""
        return self._events

    @property
    def natural_transitions(
        self,
    ) -> List[
        Union[
            "up.model.natural_transition.Event", "up.model.natural_transition.Process"
        ]
    ]:
        """Returns the list of the `Processes` and `Events` in the `Problem`."""
        ntlist: List[
            Union[
                up.model.natural_transition.Event, up.model.natural_transition.Process
            ]
        ] = []
        ntlist.extend(self.processes)
        ntlist.extend(self.events)
        return ntlist

    def clear_events(self):
        """Removes all the `Problem` `Events`."""
        self._events = []

    def clear_processes(self):
        """Removes all the `Problem` `Processes`."""
        self._processes = []

    def process(self, name: str) -> "up.model.natural_transition.Process":
        """
        Returns the `Process` with the given `name`.

        :param name: The `name` of the target `process`.
        :return: The `process` in the `problem` with the given `name`.
        """
        for a in self._processes:
            if a.name == name:
                return a
        raise UPValueError(f"Process of name: {name} is not defined!")

    def event(self, name: str) -> "up.model.natural_transition.Event":
        """
        Returns the `event` with the given `name`.

        :param name: The `name` of the target `event`.
        :return: The `event` in the `problem` with the given `name`.
        """
        for a in self._events:
            if a.name == name:
                return a
        raise UPValueError(f"NaturalTransition of name: {name} is not defined!")

    def has_process(self, name: str) -> bool:
        """
        Returns `True` if the `problem` has the `process` with the given `name`,
        `False` otherwise.

        :param name: The `name` of the target `process`.
        :return: `True` if the `problem` has an `process` with the given `name`, `False` otherwise.
        """
        for a in self._processes:
            if a.name == name:
                return True
        return False

    def has_event(self, name: str) -> bool:
        """
        Returns `True` if the `problem` has the `event` with the given `name`,
        `False` otherwise.

        :param name: The `name` of the target `event`.
        :return: `True` if the `problem` has an `event` with the given `name`, `False` otherwise.
        """
        for a in self._events:
            if a.name == name:
                return True
        return False

    def add_process(self, process: "up.model.natural_transition.Process"):
        """
        Adds the given `process` to the `problem`.

        :param natural_transition: The `process` that must be added to the `problem`.
        """
        assert (
            process.environment == self._env
        ), "Process does not have the same environment of the problem"
        if self._has_name_method(process.name):
            msg = f"Name {process.name} already defined! Different elements of a problem can have the same name if the environment flag error_used_name is disabled."
            if self._env.error_used_name or any(
                process.name == a.name for a in self._processes
            ):
                raise UPProblemDefinitionError(msg)
            else:
                warn(msg)
        self._processes.append(process)
        for param in process.parameters:
            if param.type.is_user_type():
                self._add_user_type_method(param.type)

    def add_event(self, event: "up.model.natural_transition.Event"):
        """
        Adds the given `event` to the `problem`.

        :param event: The `event` that must be added to the `problem`.
        """
        assert (
            event.environment == self._env
        ), "Event does not have the same environment of the problem"
        if self._has_name_method(event.name):
            msg = f"Name {event.name} already defined! Different elements of a problem can have the same name if the environment flag error_used_name is disabled."
            if self._env.error_used_name or any(
                event.name == a.name for a in self._events
            ):
                raise UPProblemDefinitionError(msg)
            else:
                warn(msg)
        self._events.append(event)
        for param in event.parameters:
            if param.type.is_user_type():
                self._add_user_type_method(param.type)

    def add_processes(
        self,
        processes: Iterable["up.model.natural_transition.Process"],
    ):
        """
        Adds the given `processes` to the `problem`.

        :param processes: The `processes` that must be added to the `problem`.
        """
        for process in processes:
            self.add_process(process)

    def add_events(
        self,
        events: Iterable["up.model.natural_transition.Event"],
    ):
        """
        Adds the given `events` to the `problem`.

        :param events: The `events` that must be added to the `problem`.
        """
        for event in events:
            self.add_event(event)
