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
import unified_planning as up
from unified_planning.engines.compilers import Grounder, GrounderHelper
from unified_planning.engines.engine import Engine
from unified_planning.engines.mixins.simulator import Event, SimulatorMixin
from unified_planning.exceptions import UPUsageError
from unified_planning.model import COWState, ROState, UPCOWState, Problem
from unified_planning.model.walkers import StateEvaluator
from typing import Dict, Iterable, Iterator, List, Optional, Tuple, Union, cast


class InstantaneousEvent(Event):
    """Implements the Event class for an Instantaneous Action."""

    def __init__(
        self,
        conditions: List["up.model.FNode"],
        effects: List["up.model.Effect"],
        simulated_effect: Optional["up.model.SimulatedEffect"] = None,
    ):
        self._conditions = conditions
        self._effects = effects
        self._simulated_effect = simulated_effect

    @property
    def conditions(self) -> List["up.model.FNode"]:
        return self._conditions

    @property
    def effects(self) -> List["up.model.Effect"]:
        return self._effects

    @property
    def simulated_effect(self) -> Optional["up.model.SimulatedEffect"]:
        return self._simulated_effect


class SequentialSimulator(Engine, SimulatorMixin):
    """
    Sequential SimulatorMixin implementation.
    """

    def __init__(
        self, problem: "up.model.Problem", error_on_failed_checks: bool = True, **kwargs
    ):
        Engine.__init__(self)
        self.error_on_failed_checks = error_on_failed_checks
        SimulatorMixin.__init__(self, problem)
        pk = problem.kind
        assert Grounder.supports(pk)
        assert isinstance(self._problem, up.model.Problem)
        self._grounder = GrounderHelper(problem)
        self._actions = set(self._problem.actions)
        self._events: Dict[
            Tuple["up.model.Action", Tuple["up.model.FNode", ...]], List[Event]
        ] = {}
        self._se = StateEvaluator(self._problem)
        self._all_events_grounded: bool = False

    def _is_applicable(
        self, event: Union["Event", Iterable["Event"]], state: "ROState"
    ) -> bool:
        if not isinstance(event, Event):
            raise UPUsageError(
                f"SequentialSimulator accepts only an Event but {type(event)} is given!"
            )
        return (
            len(self.get_unsatisfied_conditions(event, state, early_termination=True))
            == 0
        )

    def _get_unsatisfied_conditions(
        self, event: "Event", state: "ROState", early_termination: bool = False
    ) -> List["up.model.FNode"]:
        """
        Returns the list of unsatisfied event conditions evaluated in the
        given state. If the flag `early_termination` is set, the method ends
        and returns at the first unsatisfied condition.

        :param state: The `State` in which the event conditions are evaluated.
        :param early_termination: Flag deciding if the method ends and returns
            at the first unsatisfied condition.
        :return: The list of all the event conditions that evaluated to `False`
            or the list containing the first condition evaluated to False if the
            flag `early_termination` is set.
        """
        return get_unsatisfied_conditions(self, event, state, early_termination)

    def _apply(
        self, event: Union["Event", Iterable["Event"]], state: "COWState"
    ) -> Optional["COWState"]:
        """
        Returns `None` if the event is not applicable in the given state,
        otherwise returns a new COWState,which is a copy of the given state
        but the applicable effects of the event are applied; therefore some
        fluent values are updated.

        :param state: the state where the event formulas are calculated.
        :param event: the event that has the information about the conditions
            to check and the effects to apply. An Iterable here is not accepted.
        :return: None if the event is not applicable in the given state, a new
            COWState with some updated values if the event is applicable.
        """
        if not isinstance(event, Event):
            raise UPUsageError(
                "The SequentialSimulator does not accept an ",
                "Iterator of Event, but only an Event.",
            )
        if not self.is_applicable(event, state):
            return None
        else:
            return self.apply_unsafe(event, state)

    def _apply_unsafe(
        self, event: Union["Event", Iterable["Event"]], state: "COWState"
    ) -> "COWState":
        """
        Returns a new COWState, which is a copy of the given state but the applicable effects of the event are applied; therefore
        some fluent values are updated.
        IMPORTANT NOTE: Assumes that self.is_applicable(state, event) returns True

        :param state: the state where the event formulas are evaluated.
        :param event: the event that has the information about the effects to apply; an Iterable here is not accepted.
        :return: A new COWState with some updated values.
        """
        if not isinstance(event, InstantaneousEvent):
            raise UPUsageError(
                f"SequentialSimulator accepts only ONE instance of InstantaneousEvent! {type(event)} was given"
            )
        updated_values, _ = self._get_updated_values_and_red_fluents(
            event, state, self._se
        )
        return state.make_child(updated_values)

    def _get_applicable_events(self, state: "ROState") -> Iterator["Event"]:
        """
        Returns a view over all the events that are applicable in the given State;
        an Event is considered applicable in a given State, when all the Event condition
        simplify as True when evaluated in the State.

        :param state: The state where the formulas are evaluated.
        :return: an Iterator of applicable Events.
        """
        # if the problem was never fully grounded before,
        # ground it and save all the new events. For every event
        # that is applicable, yield it.
        # Otherwise just return all the applicable events
        if not self._all_events_grounded:
            # perform total grounding
            self._all_events_grounded = True
            # for every grounded action, translate it in an Event
            for (
                original_action,
                params,
                grounded_action,
            ) in self._grounder.get_grounded_actions():
                for event in self._get_or_create_events(
                    original_action, params, grounded_action
                ):
                    if self.is_applicable(event, state):
                        yield event
        else:  # the problem has been fully grounded before, just check for event applicability
            for events in self._events.values():
                for event in events:
                    if self.is_applicable(event, state):
                        yield event

    def _get_events(
        self,
        action: "up.model.Action",
        parameters: Union[
            Tuple["up.model.Expression", ...], List["up.model.Expression"]
        ],
        duration: Optional[Union[Fraction, float, int]] = None,
    ) -> List["Event"]:
        """
        Returns a list containing all the events derived from the given action,
        grounded with the given parameters.

        :param action: The action containing the information to create the event.
        :param parameters: The parameters needed to ground the action.
        ·param duration: must be `None`, needed only for simulators that support
            temporal problems.
        :return: the List of Events derived from this action with these parameters.
        """
        # sanity checks
        if duration is not None:
            raise UPUsageError(
                "A duration is specified in the SequentialSimulator; ",
                "the duration of an Action is meaningful only for simulators ",
                "that support temporal problems.",
            )
        if action not in self._actions:
            raise UPUsageError(
                "The action given as parameter does not belong to the problem ",
                "given to the SequentialSimulator.",
            )
        params_exp = tuple(
            self._problem.env.expression_manager.auto_promote(parameters)
        )
        grounded_action = self._grounder.ground_action(action, params_exp)
        event_list = self._get_or_create_events(action, params_exp, grounded_action)
        return event_list

    def _get_unsatisfied_goals(
        self, state: "ROState", early_termination: bool = False
    ) -> List["up.model.FNode"]:
        """
        Returns the list of unsatisfied goals evaluated in the given state.
        If the flag "early_termination" is set, the method ends and returns at
        the first unsatisfied goal.

        :param state: The State in which the problem goals are evaluated.
        :param early_termination: Flag deciding if the method ends and returns
            at the first unsatisfied goal.
        :return: The list of all the goals that evaluated to False or the list
            containing the first goal evaluated to False if the flag
            "early_termination" is set.
        """
        return get_unsatisfied_goals(self, state, early_termination)

    def _get_initial_state(self) -> "COWState":
        """
        Returns the :class:`~unified_planning.model.UPCOWState` instance that represents
        the initial state of the given `problem`.
        """
        assert isinstance(self._problem, Problem)
        return UPCOWState(self._problem.initial_values)

    @property
    def name(self) -> str:
        return "sequential_simulator"

    @staticmethod
    def supported_kind() -> "up.model.ProblemKind":
        supported_kind = up.model.ProblemKind()
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_numbers("CONTINUOUS_NUMBERS")
        supported_kind.set_numbers("DISCRETE_NUMBERS")
        supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
        supported_kind.set_fluents_type("NUMERIC_FLUENTS")
        supported_kind.set_fluents_type("OBJECT_FLUENTS")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITY")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        supported_kind.set_effects_kind("INCREASE_EFFECTS")
        supported_kind.set_effects_kind("DECREASE_EFFECTS")
        supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= SequentialSimulator.supported_kind()

    def _get_or_create_events(
        self,
        original_action: "up.model.Action",
        params: Tuple["up.model.FNode", ...],
        grounded_action: Optional["up.model.Action"],
    ) -> List[Event]:
        """
        Support function that takes the `original Action`, the `parameters`
        used to ground the `grounded Action` and the `grounded Action` itself,
        and adds the corresponding `List of Events` to this `Simulator`. If the
        corresponding `Events` were already created, the same value is returned
        and no new `Events` are created.

        :param original_action: The `Action` of the :class:`~unified_planning.model.Problem`
            grounded with the given `params`.
        :param params: The expressions used to ground the `original_action`.
        :param grounded_action: The grounded action, result of the
            `original_action` grounded with the given `parameters`.
        :return: The retrieved or created `List of Events` corresponding to the
            `grounded_action`.
        """
        if isinstance(original_action, up.model.InstantaneousAction):
            # check if the event is already cached; if not: create it and cache it
            key = (original_action, params)
            event_list = self._events.get(key, None)
            if event_list is None:
                if (
                    grounded_action is None
                ):  # The grounded action is meaningless, no event associated
                    event_list = []
                else:
                    assert isinstance(grounded_action, up.model.InstantaneousAction)
                    event_list = [
                        InstantaneousEvent(
                            grounded_action.preconditions,
                            grounded_action.effects,
                            grounded_action.simulated_effect,
                        )
                    ]
                self._events[key] = event_list
            # sanity check
            assert len(event_list) < 2
            return event_list
        else:
            raise NotImplementedError(
                "The SequentialSimulator currently supports only InstantaneousActions."
            )


def get_unsatisfied_goals(
    simulator: SequentialSimulator, state: "ROState", early_termination: bool = False
) -> List["up.model.FNode"]:
    assert simulator._se is not None
    unsatisfied_goals = []
    for g in cast(up.model.Problem, simulator._problem).goals:
        g_eval = simulator._se.evaluate(g, state).bool_constant_value()
        if not g_eval:
            unsatisfied_goals.append(g)
            if early_termination:
                break
    return unsatisfied_goals


def get_unsatisfied_conditions(
    simulator: SequentialSimulator,
    event: "Event",
    state: "ROState",
    early_termination: bool = False,
) -> List["up.model.FNode"]:
    # Evaluate every condition and if the condition is False or the condition is not simplified as a
    # boolean constant in the given state, return False. Return True otherwise
    assert simulator._se is not None
    unsatisfied_conditions = []
    for c in event.conditions:
        evaluated_cond = simulator._se.evaluate(c, state)
        if (
            not evaluated_cond.is_bool_constant()
            or not evaluated_cond.bool_constant_value()
        ):
            unsatisfied_conditions.append(c)
            if early_termination:
                break
    return unsatisfied_conditions
