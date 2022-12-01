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

from typing import Iterator, List, Optional, Tuple, Union
from warnings import warn
import unified_planning as up
from unified_planning.exceptions import UPUsageError


class Event:
    """This is an abstract class representing an event."""

    @property
    def conditions(self) -> List["up.model.FNode"]:
        """Returns the list of expressions that must be True in order for this event to be applicable."""
        raise NotImplementedError

    @property
    def effects(self) -> List["up.model.Effect"]:
        """Returns the list of effects linked to this event."""
        raise NotImplementedError

    @property
    def simulated_effect(self) -> Optional["up.model.SimulatedEffect"]:
        """Returns the list of simulated effects linked to this event."""
        raise NotImplementedError


class SimulatorMixin:
    """
    SimulatorMixin abstract class.
    This class defines the interface that an :class:`~unified_planning.engines.Engine`
    that is also a `Simulator` must implement.

    Important NOTE: The `AbstractProblem` instance is given at the constructor.
    """

    def __init__(
        self, problem: "up.model.AbstractProblem", error_on_failed_checks: bool = True
    ) -> None:
        """
        Takes an instance of a `problem` and eventually some parameters, that represent
        some specific settings of the `SimulatorMixin`.

        :param problem: the `problem` that defines the domain in which the simulation exists.
        :param error_on_failed_checks: flag that determines whether a failed check on the
            `problem.kind` should raise an Exception or just a warning.
        """
        self._problem = problem
        self_class = type(self)
        assert issubclass(
            self_class, up.engines.engine.Engine
        ), "SimulatorMixin does not implement the up.engines.Engine class"
        assert isinstance(self, up.engines.engine.Engine)
        if not self.skip_checks and not self_class.supports(problem.kind):
            msg = f"The problem named: {problem.name} is not supported by the {self_class}."
            if error_on_failed_checks:
                raise UPUsageError(msg)
            else:
                warn(msg)

    def is_applicable(self, event: "Event", state: "up.model.ROState") -> bool:
        """
        Returns `True` if the given `event conditions` are evaluated as `True` in the given `state`;
        returns `False` otherwise.

        :param state: the `state` where the `event conditions` are checked.
        :param event: the `event` whose `conditions` are checked.
        :return: Whether or not the `event` is applicable in the given `state`.
        """
        return self._is_applicable(event, state)

    def _is_applicable(self, event: "Event", state: "up.model.ROState") -> bool:
        return (
            len(self.get_unsatisfied_conditions(event, state, early_termination=True))
            == 0
        )

    def get_unsatisfied_conditions(
        self, event: "Event", state: "up.model.ROState", early_termination: bool = False
    ) -> List["up.model.FNode"]:
        """
        Returns the list of `unsatisfied event conditions` evaluated in the given `state`.
        If the flag `early_termination` is set, the method ends and returns at the first `unsatisfied condition`.

        :param state: The `State` in which the `event conditions` are evaluated.
        :param early_termination: Flag deciding if the method ends and returns at the first `unsatisfied condition`.
        :return: The list of all the `event conditions` that evaluated to `False` or the list containing the first
            `condition` evaluated to `False` if the flag `early_termination` is set.
        """
        return self._get_unsatisfied_conditions(
            event, state, early_termination=early_termination
        )

    def _get_unsatisfied_conditions(
        self, event: "Event", state: "up.model.ROState", early_termination: bool = False
    ) -> List["up.model.FNode"]:
        """
        Method called by the up.engines.mixins.simulator.SimulatorMixin.get_unsatisfied_conditions.
        """
        raise NotImplementedError

    def apply(
        self, event: "Event", state: "up.model.COWState"
    ) -> Optional["up.model.COWState"]:
        """
        Returns `None` if the `event` is not applicable in the given `state`, otherwise returns a new `COWState`,
        which is a copy of the given `state` where the `applicable effects` of the `event` are applied; therefore
        some `fluent values` are updated.

        :param state: the `state` where the event formulas are calculated.
        :param event: the `event` that has the information about the `conditions` to check and the `effects` to apply.
        :return: `None` if the `event` is not applicable in the given `state`, a new `COWState` with some updated `values`
            if the `event` is applicable.
        """
        return self._apply(event, state)

    def _apply(
        self, event: "Event", state: "up.model.COWState"
    ) -> Optional["up.model.COWState"]:
        """
        Method called by the up.engines.mixins.simulator.SimulatorMixin.apply.
        """
        raise NotImplementedError

    def apply_unsafe(
        self, event: "Event", state: "up.model.COWState"
    ) -> "up.model.COWState":
        """
        Returns a new `COWState`, which is a copy of the given `state` but the applicable `effects` of the
        `event` are applied; therefore some `fluent` values are updated.
        IMPORTANT NOTE: Assumes that `self.is_applicable(state, event)` returns `True`.

        :param state: the `state` where the `event formulas` are evaluated.
        :param event: the `event` that has the information about the `effects` to apply.
        :return: A new `COWState` with some updated values.
        """
        return self._apply_unsafe(event, state)

    def _apply_unsafe(
        self, event: "Event", state: "up.model.COWState"
    ) -> "up.model.COWState":
        """
        Method called by the up.engines.mixins.simulator.SimulatorMixin.apply_unsafe.
        """
        raise NotImplementedError

    def get_applicable_events(self, state: "up.model.ROState") -> Iterator["Event"]:
        """
        Returns a view over all the `events` that are applicable in the given `State`;
        an `Event` is considered applicable in a given `State`, when all the `Event condition`
        simplify as `True` when evaluated in the `State`.

        :param state: the `state` where the formulas are evaluated.
        :return: an `Iterator` of applicable `Events`.
        """
        return self._get_applicable_events(state)

    def _get_applicable_events(self, state: "up.model.ROState") -> Iterator["Event"]:
        """
        Method called by the up.engines.mixins.simulator.SimulatorMixin.get_applicable_events.
        """
        raise NotImplementedError

    def get_events(
        self,
        action: "up.model.Action",
        parameters: Union[
            Tuple["up.model.Expression", ...], List["up.model.Expression"]
        ],
    ) -> List["Event"]:
        """
        Returns a list containing all the `events` derived from the given `action`, grounded with the given `parameters`.

        :param action: the `action` containing the information to create the `event`.
        :param parameters: the `parameters` needed to ground the `action`.
        :return: the List of `Events` derived from this `action` with these `parameters`.
        """
        if len(action.parameters) != len(parameters):
            raise UPUsageError(
                "The parameters given action do not have the same length of the given parameters."
            )
        return self._get_events(action, parameters)

    def _get_events(
        self,
        action: "up.model.Action",
        parameters: Union[
            Tuple["up.model.Expression", ...], List["up.model.Expression"]
        ],
    ) -> List["Event"]:
        """
        Method called by the up.engines.mixins.simulator.SimulatorMixin.get_events.
        """
        raise NotImplementedError

    @staticmethod
    def is_simulator():
        return True

    def is_goal(self, state: "up.model.ROState") -> bool:
        """
        Returns `True` if the given `state` satisfies the :class:`~unified_planning.model.AbstractProblem` :func:`goals <unified_planning.model.Problem.goals>`.

        :param state: the `State` in which the `problem goals` are evaluated.
        :return: `True` if the evaluation of every `goal` is `True`, `False` otherwise.
        """
        return self._is_goal(state)

    def _is_goal(self, state: "up.model.ROState") -> bool:
        """
        Method called by the up.engines.mixins.simulator.SimulatorMixin.is_goal.
        """
        return len(self.get_unsatisfied_goals(state, early_termination=True)) == 0

    def get_unsatisfied_goals(
        self, state: "up.model.ROState", early_termination: bool = False
    ) -> List["up.model.FNode"]:
        """
        Returns the list of `unsatisfied goals` evaluated in the given `state`.
        If the flag `early_termination` is set, the method ends and returns at the first `unsatisfied goal`.

        :param state: The `State` in which the `problem goals` are evaluated.
        :param early_termination: Flag deciding if the method ends and returns at the first `unsatisfied goal`.
        :return: The list of all the `goals` that evaluated to `False` or the list containing the first `goal` evaluated to `False` if the flag `early_termination` is set.
        """
        return self._get_unsatisfied_goals(state, early_termination)

    def _get_unsatisfied_goals(
        self, state: "up.model.ROState", early_termination: bool = False
    ) -> List["up.model.FNode"]:
        """
        Method called by the up.engines.mixins.simulator.SimulatorMixin.get_unsatisfied_goals.
        """
        raise NotImplementedError
