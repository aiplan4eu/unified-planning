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


from collections import deque
from fractions import Fraction
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union
from warnings import warn
import unified_planning as up
from unified_planning.model import FNode, COWState, ROState
from unified_planning.model.walkers import StateEvaluator, FreeVarsExtractor
from unified_planning.exceptions import UPUsageError, UPConflictingEffectsException


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

    def __init__(self, problem: "up.model.AbstractProblem") -> None:
        """
        Takes an instance of a `problem` and eventually some parameters, that represent
        some specific settings of the `SimulatorMixin`.

        :param problem: the `problem` that defines the domain in which the simulation exists.
        """
        self._problem = problem
        self_class = type(self)
        assert issubclass(
            self_class, up.engines.engine.Engine
        ), "SimulatorMixin does not implement the up.engines.Engine class"
        assert isinstance(self, up.engines.engine.Engine)
        if not self.skip_checks and not self_class.supports(problem.kind):
            msg = f"We cannot establish whether {self.name} is able to handle this problem!"
            if self.error_on_failed_checks:
                raise UPUsageError(msg)
            else:
                warn(msg)
        self._fve: FreeVarsExtractor = problem.env.free_vars_extractor

    def is_applicable(
        self, event: Union["Event", Iterable["Event"]], state: "ROState"
    ) -> bool:
        """
        Returns `True` if the given `event conditions` are evaluated as `True` in the given `state`;
        returns `False` otherwise.

        :param state: the `state` where the `event conditions` are checked.
        :param event: the `event` whose `conditions` are checked.
        :return: Whether or not the `event` is applicable in the given `state`.
        """
        return self._is_applicable(event, state)

    def _is_applicable(
        self, event: Union["Event", Iterable["Event"]], state: "ROState"
    ) -> bool:
        raise NotImplementedError

    def get_unsatisfied_conditions(
        self, event: "Event", state: "ROState", early_termination: bool = False
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
        self, event: "Event", state: "ROState", early_termination: bool = False
    ) -> List["up.model.FNode"]:
        """
        Method called by the up.engines.mixins.simulator.SimulatorMixin.apply.
        """
        raise NotImplementedError

    def apply(
        self, event: Union["Event", Iterable["Event"]], state: "COWState"
    ) -> Optional["COWState"]:
        """
        Returns `None` if the `event` is not applicable in the given `state`, otherwise returns a new `COWState`,
        which is a copy of the given `state` where the `applicable effects` of the `event` are applied; therefore
        some `fluent values` are updated.

        :param state: the `state` where the event formulas are calculated.
        :param event: the `event` that has the information about the `conditions`
            to check and the `effects` to apply. If the given event is an
            iterator of events, all the given event's conditions are checked
            before applying all the event's effects.
        :return: `None` if the `event` is not applicable in the given `state`,
            a new `COWState` with some updated `values` if the `event` is applicable.
        """
        return self._apply(event, state)

    def _apply(
        self, event: Union["Event", Iterable["Event"]], state: "COWState"
    ) -> Optional["COWState"]:
        """
        Method called by the up.engines.mixins.simulator.SimulatorMixin.apply.
        """
        raise NotImplementedError

    def apply_unsafe(
        self, event: Union["Event", Iterable["Event"]], state: "COWState"
    ) -> "COWState":
        """
        Returns a new `COWState`, which is a copy of the given `state` but the applicable `effects` of the
        `event` are applied; therefore some `fluent` values are updated.
        IMPORTANT NOTE: Assumes that `self.is_applicable(state, event)` returns `True`.

        :param state: the `state` where the `event formulas` are evaluated.
        :param event: the `event` that has the information about the `effects`
            to apply; if an `Iterable` of `Event` is given, all the effects are
            applied at the same time.
        :return: A new `COWState` with some updated values.
        """
        return self._apply_unsafe(event, state)

    def _apply_unsafe(
        self, event: Union["Event", Iterable["Event"]], state: "COWState"
    ) -> "COWState":
        """
        Method called by the up.engines.mixins.simulator.SimulatorMixin.apply_unsafe.
        """
        raise NotImplementedError

    def get_applicable_events(self, state: "ROState") -> Iterable["Event"]:
        """
        Returns a view over all the `events` that are applicable in the given `State`;
        an `Event` is considered applicable in a given `State`, when all the `Event condition`
        simplify as `True` when evaluated in the `State`.

        :param state: the `state` where the formulas are evaluated.
        :return: an `Iterable` of applicable `Events`.
        """
        return self._get_applicable_events(state)

    def _get_applicable_events(self, state: "ROState") -> Iterable["Event"]:
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
        duration: Optional[Union[Fraction, float, int]] = None,
    ) -> List["Event"]:
        """
        Returns a list containing all the `events` derived from the given
        `action`, grounded with the given `parameters`.

        :param action: the `action` containing the information to create the
            `event`.
        :param parameters: the `parameters` needed to ground the `action`.
        :param duration: optionally, the duration of the action.
        :return: the `list` of `Events` derived from this `action` with these
            `parameters`. In the Temporal case, if the `duration` is specified,
            the returned `list` is guaranteed to be totally ordered .
        """
        if len(action.parameters) != len(parameters):
            raise UPUsageError(
                "The parameters given action do not have the same length of the given parameters."
            )
        return self._get_events(action, parameters, duration)

    def _get_events(
        self,
        action: "up.model.Action",
        parameters: Union[
            Tuple["up.model.Expression", ...], List["up.model.Expression"]
        ],
        duration: Optional[Union[Fraction, float, int]] = None,
    ) -> List["Event"]:
        """
        Method called by the up.engines.mixins.simulator.SimulatorMixin.get_events.
        """
        raise NotImplementedError

    @staticmethod
    def is_simulator():
        return True

    def is_goal(self, state: "ROState") -> bool:
        """
        Returns `True` if the given `state` satisfies the :class:`~unified_planning.model.AbstractProblem` :func:`goals <unified_planning.model.Problem.goals>`.

        :param state: the `State` in which the `problem goals` are evaluated.
        :return: `True` if the evaluation of every `goal` is `True`, `False` otherwise.
        """
        return self._is_goal(state)

    def _is_goal(self, state: "ROState") -> bool:
        """
        Method called by the up.engines.mixins.simulator.SimulatorMixin.is_goal.
        """
        return len(self.get_unsatisfied_goals(state, early_termination=True)) == 0

    def get_unsatisfied_goals(
        self, state: "ROState", early_termination: bool = False
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
        self, state: "ROState", early_termination: bool = False
    ) -> List["up.model.FNode"]:
        """
        Method called by the up.engines.mixins.simulator.SimulatorMixin.get_unsatisfied_goals.
        """
        raise NotImplementedError

    def get_initial_state(self) -> "COWState":
        """
        Returns the `COWState` representing the initial state of the `problem` given at construction time to the simulator.

        :return: the `COWState` representing the `problem`'s initial state.
        """
        return self._get_initial_state()

    def _get_initial_state(self) -> "COWState":
        """
        Method called by the up.engines.mixins.simulator.SimulatorMixin.get_initial_state.
        """
        raise NotImplementedError

    def _get_updated_values_and_red_fluents(
        self,
        event: Union["Event", Iterable["Event"]],
        state: "ROState",
        state_evaluator: StateEvaluator,
    ) -> Tuple[Dict[FNode, FNode], Set[FNode]]:
        """
        Utility method to return what an Event, or an Iterable of Event, updates
        (Dict updated_values) and which expressions it depends on (Set
        red_fluents).
        """
        updated_values: Dict["up.model.FNode", "up.model.FNode"] = {}
        assigned_fluent: Set["up.model.FNode"] = set()
        red_fluents: Set["up.model.FNode"] = set()
        em = self._problem.env.expression_manager
        if isinstance(event, Event):
            event = [event]
        for ev in event:
            for cond in ev.conditions:
                red_fluents.update(self._fve.get(cond))
            for e in ev.effects:
                evaluated_args = tuple(
                    state_evaluator.evaluate(a, state) for a in e.fluent.args
                )
                fluent = em.FluentExp(e.fluent.fluent(), evaluated_args)
                red_fluents.update(self._fve.get(e.condition))
                if state_evaluator.evaluate(e.condition, state).is_true():
                    for fluent_arg in e.fluent.args:
                        red_fluents.update(self._fve.get(fluent_arg))
                    red_fluents.update(self._fve.get(e.value))
                    if e.is_assignment():
                        if fluent in updated_values:
                            raise UPConflictingEffectsException(
                                f"The fluent {fluent} is modified by 2 assignments in the same event."
                            )
                        updated_values[fluent] = state_evaluator.evaluate(
                            e.value, state
                        )
                        assigned_fluent.add(fluent)
                    else:
                        red_fluents.add(
                            fluent
                        )  # increase or decrease read the written fluent.
                        if fluent in assigned_fluent:
                            raise UPConflictingEffectsException(
                                f"The fluent {fluent} is modified by an assignment and an increase/decrease in the same event."
                            )
                        # If the fluent is in updated_values, we take his modified value, (which was modified by another increase or deacrease)
                        # otherwisee we take it's evaluation in the state as it's value.
                        f_eval = updated_values.get(
                            fluent, state_evaluator.evaluate(fluent, state)
                        )
                        v_eval = state_evaluator.evaluate(e.value, state)
                        if e.is_increase():
                            updated_values[fluent] = em.auto_promote(
                                f_eval.constant_value() + v_eval.constant_value()
                            )[0]
                        elif e.is_decrease():
                            updated_values[fluent] = em.auto_promote(
                                f_eval.constant_value() - v_eval.constant_value()
                            )[0]
                        else:
                            raise NotImplementedError
            if ev.simulated_effect is not None:
                # TODO add to the red_fluents the whole state!
                # NOTE return None might mean "The whole state", but is quite counterintuitive,
                # Or the state needs an extra method that retrieves the whole state.
                for f, v in zip(
                    ev.simulated_effect.fluents,
                    ev.simulated_effect.function(self._problem, state, {}),
                ):
                    if f in updated_values:
                        raise UPConflictingEffectsException(
                            f"The fluent {f} is modified twice in the same event."
                        )
                    updated_values[f] = v
        return (updated_values, red_fluents)
