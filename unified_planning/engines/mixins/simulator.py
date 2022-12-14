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


from fractions import Fraction
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union, Iterator, cast
from warnings import warn
import unified_planning as up
from unified_planning.model import FNode, ROState, Action
from unified_planning.model.walkers import StateEvaluator, FreeVarsExtractor
from unified_planning.exceptions import UPUsageError, UPConflictingEffectsException


class Event:
    """This is an abstract class representing an event."""

    @property
    def action(self) -> Optional["up.model.Action"]:
        """Returns the Action that generated this event."""
        raise NotImplementedError

    @property
    def actual_parameters(self) -> Optional[Tuple["up.model.FNode", ...]]:
        """Returns the tuple of expressions used to ground the Action to obtain this Event."""
        raise NotImplementedError

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
        Returns `True` if the given `events` are applicable in the given `state`;
        returns `False` otherwise.

<<<<<<< HEAD
        :param state: the `state` where the `events` are checked.
        :param event: the `event` or `Iterable[Event]` that are checked.
        :return: Whether or not the `event` is/are applicable in the given `state`.
=======
        :param state: the `state` where the `event conditions` are checked.
        :param event: the `event` or `Iterable[Event]` whose `conditions` are checked.
        :return: Whether or not the `event` is applicable in the given `state`.
>>>>>>> 0e38b318 (Added some documentation)
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
        Method called by the up.engines.mixins.simulator.SimulatorMixin.get_unsatisfied_conditions.
        """
        raise NotImplementedError

    def apply(
        self, event: Union["Event", Iterable["Event"]], state: "ROState"
    ) -> Optional["ROState"]:
        """
        Returns `None` if the `event` is not applicable in the given `state`, otherwise returns a new `ROState`,
        which is a copy of the given `state` where the `applicable effects` of the `event` are applied; therefore
        some `fluent values` are updated.

        :param state: the `state` where the event formulas are calculated.
        :param event: the `event` that has the information about the `conditions`
            to check and the `effects` to apply. If the given event is an
            iterable of events, all the given event's conditions are checked
            before applying all the event's effects.
        :return: `None` if the `event` is not applicable in the given `state`,
            a new `ROState` with some updated `values` if the `event` is applicable.
        """
        return self._apply(event, state)

    def _apply(
        self, event: Union["Event", Iterable["Event"]], state: "ROState"
    ) -> Optional["ROState"]:
        """
        Method called by the up.engines.mixins.simulator.SimulatorMixin.apply.
        """
        raise NotImplementedError

    def apply_unsafe(
        self, event: Union["Event", Iterable["Event"]], state: "ROState"
    ) -> "ROState":
        """
        Returns a new `ROState`, which is a copy of the given `state` but the applicable `effects` of the
        `event` are applied; therefore some `fluent` values are updated.
        IMPORTANT NOTE: Assumes that `self.is_applicable(state, event)` returns `True`.

        :param state: the `state` where the `event formulas` are evaluated.
        :param event: the `event` that has the information about the `effects`
            to apply; if an `Iterable` of `Event` is given, all the effects are
            applied at the same time.
        :return: A new `ROState` with some updated values.
        """
        return self._apply_unsafe(event, state)

    def _apply_unsafe(
        self, event: Union["Event", Iterable["Event"]], state: "ROState"
    ) -> "ROState":
        """
        Method called by the up.engines.mixins.simulator.SimulatorMixin.apply_unsafe.
        """
        raise NotImplementedError

    def get_applicable_events(
        self,
        state: "up.model.ROState",
        durations_map: Optional[
            Dict[Tuple[Action, Tuple[FNode]], Union[int, Fraction]]
        ] = None,
    ) -> Iterator["Event"]:
        """
        Returns a view over all the `events` that are applicable in the given `State`;
        an `Event` is considered applicable in a given `State`, when all the `Event condition`
        simplify as `True` when evaluated in the `State`.

        :param state: the `state` where the formulas are evaluated.
        :param durations_map: optionally, the mapping from the Tuple[Action + grounding_parameters]
            to the duration of said action.
        :return: an `Iterator` of applicable `Events`.
        """
        return self._get_applicable_events(state, durations_map)

    def _get_applicable_events(
        self,
        state: "up.model.ROState",
        durations_map: Optional[
            Dict[Tuple[Action, Tuple[FNode]], Union[int, Fraction]]
        ] = None,
    ) -> Iterator["Event"]:
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

    def get_initial_state(self) -> "ROState":
        """
        Returns the `ROState` representing the initial state of the `problem` given at construction time to the simulator.

        :return: the `ROState` representing the `problem`'s initial state.
        """
        return self._get_initial_state()

    def _get_initial_state(self) -> "ROState":
        """
        Method called by the up.engines.mixins.simulator.SimulatorMixin.get_initial_state.
        """
        raise NotImplementedError

    def _get_updated_values_and_red_fluents(
        self,
        event: Union["Event", Iterable["Event"]],
        state: "ROState",
        state_evaluator: StateEvaluator,
        all_possible_assignments: Set[FNode],
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
            for eff in ev.effects:
                evaluated_args = tuple(
                    state_evaluator.evaluate(a, state) for a in eff.fluent.args
                )
                fluent = em.FluentExp(eff.fluent.fluent(), evaluated_args)
                red_fluents.update(self._fve.get(eff.condition))
                if state_evaluator.evaluate(eff.condition, state).is_true():
                    for fluent_arg in eff.fluent.args:
                        red_fluents.update(self._fve.get(fluent_arg))
                    red_fluents.update(self._fve.get(eff.value))
                    if eff.is_assignment():
                        if fluent in updated_values:
                            raise UPConflictingEffectsException(
                                f"The fluent {fluent} is modified by 2 assignments in the same event."
                            )
                        updated_values[fluent] = state_evaluator.evaluate(
                            eff.value, state
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
                        v_eval = state_evaluator.evaluate(eff.value, state)
                        if eff.is_increase():
                            updated_values[fluent] = em.auto_promote(
                                f_eval.constant_value() + v_eval.constant_value()
                            )[0]
                        elif eff.is_decrease():
                            updated_values[fluent] = em.auto_promote(
                                f_eval.constant_value() - v_eval.constant_value()
                            )[0]
                        else:
                            raise NotImplementedError
            if ev.simulated_effect is not None:
                assert ev.action is not None
                assert ev.actual_parameters is not None
                grounding_parameters = dict(
                    zip(ev.action.parameters, ev.actual_parameters)
                )
                red_fluents.update(all_possible_assignments)
                for f, v in zip(
                    ev.simulated_effect.fluents,
                    ev.simulated_effect.function(
                        self._problem, state, grounding_parameters
                    ),
                ):
                    if f in updated_values:
                        raise UPConflictingEffectsException(
                            f"The fluent {f} is modified twice in the same event."
                        )
                    updated_values[f] = v
        return (updated_values, red_fluents)

    def _get_unsatisfied_goals_mixin(
        self,
        state: "ROState",
        state_evaluator: StateEvaluator,
        early_termination: bool = False,
    ) -> List["up.model.FNode"]:
        unsatisfied_goals = []
        assert isinstance(self, up.engines.engine.Engine)
        if not self.skip_checks and not isinstance(self._problem, up.model.Problem):
            msg = "Given problem is not an up.model.Problem"
            if self.error_on_failed_checks:
                raise UPUsageError(msg)
            else:
                warn(msg)
        for g in cast(up.model.Problem, self._problem).goals:
            g_eval = state_evaluator.evaluate(g, state).bool_constant_value()
            if not g_eval:
                unsatisfied_goals.append(g)
                if early_termination:
                    break
        return unsatisfied_goals

    def _get_unsatisfied_conditions_mixin(
        self,
        event: "Event",
        state: "ROState",
        state_evaluator: StateEvaluator,
        early_termination: bool = False,
    ) -> List["up.model.FNode"]:
        # Evaluate every condition and if the condition is False or the condition is not simplified as a
        # boolean constant in the given state, return False. Return True otherwise
        unsatisfied_conditions = []
        for c in event.conditions:
            evaluated_cond = state_evaluator.evaluate(c, state)
            if (
                not evaluated_cond.is_bool_constant()
                or not evaluated_cond.bool_constant_value()
            ):
                unsatisfied_conditions.append(c)
                if early_termination:
                    break
        return unsatisfied_conditions
