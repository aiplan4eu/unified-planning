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


from enum import Enum, auto
import unified_planning as up
from unified_planning.model import (
    InstantaneousAction,
    DurativeAction,
    FNode,
    Effect,
    Timing,
    Action,
    TimeInterval,
    StartTiming,
    EndTiming,
    SimulatedEffect,
    TemporalState,
)
from unified_planning.engines.compilers import Grounder, GrounderHelper
from unified_planning.engines.engine import Engine
from unified_planning.engines.sequential_simulator import InstantaneousEvent
from unified_planning.engines.mixins.simulator import Event, SimulatorMixin
from unified_planning.exceptions import UPUsageError, UPConflictingEffectsException
from unified_planning.model.walkers import StateEvaluator
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple, Union, cast


class TemporalEventKind(Enum):
    START_ACTION = auto()
    END_ACTION = auto()
    START_CONDITION = auto()
    END_CONDITION = auto()
    INTERMEDIATE_CONDITION_EFFECT = auto()


class TemporalEvent(InstantaneousEvent):
    """Implements the Event class for the temporal scenario."""

    def __init__(
        self,
        kind: TemporalEventKind,
        timing: Timing,
        timing_included: bool,
        committed_events: List["TemporalEvent"],  # eventi della start_action
        conditions: List["up.model.FNode"],
        effects: List["up.model.Effect"],
        simulated_effect: Optional["up.model.SimulatedEffect"] = None,
    ):
        InstantaneousEvent.__init__(self, conditions, effects, simulated_effect)
        self._kind = kind
        self._action = action
        self._timing = timing
        self._timing_included = timing_included
        self._parameters = parameters

    @property
    def kind(self) -> TemporalEventKind:
        return self._kind

    @property
    def action(self) -> Action:
        return self._kind

    @property
    def timing(self) -> Timing:
        return self._timing

    @property
    def timing_included(self) -> bool:
        return self._timing_included

    @property
    def parameters(self) -> Tuple[FNode]:
        return self._parameters


class TemporalSimulator(Engine, SimulatorMixin):
    """
    Sequential SimulatorMixin implementation.
    """

    def __init__(self, problem: "up.model.Problem"):
        Engine.__init__(self)
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

    def _get_unsatisfied_conditions(
        self, event: "Event", state: "up.model.ROState", early_termination: bool = False
    ) -> List["up.model.FNode"]:
        """
        Returns the list of unsatisfied event conditions evaluated in the given state.
        If the flag `early_termination` is set, the method ends and returns at the first unsatisfied condition.

        :param state: The `State` in which the event conditions are evaluated.
        :param early_termination: Flag deciding if the method ends and returns at the first unsatisfied condition.
        :return: The list of all the event conditions that evaluated to `False` or the list containing the first
            condition evaluated to False if the flag `early_termination` is set.
        """
        # Evaluate every condition and if the condition is False or the condition is not simplified as a
        # boolean constant in the given state, return False. Return True otherwise
        unsatisfied_conditions = []
        for c in event.conditions:
            evaluated_cond = self._se.evaluate(c, state)
            if (
                not evaluated_cond.is_bool_constant()
                or not evaluated_cond.bool_constant_value()
            ):
                unsatisfied_conditions.append(c)
                if early_termination:
                    break
        return unsatisfied_conditions

    def _apply(
        self, event: "Event", state: "up.model.COWState"
    ) -> Optional["up.model.COWState"]:
        """
        Returns `None` if the event is not applicable in the given state, otherwise returns a new COWState,
        which is a copy of the given state but the applicable effects of the event are applied; therefore
        some fluent values are updated.

        :param state: the state where the event formulas are calculated.
        :param event: the event that has the information about the conditions to check and the effects to apply.
        :return: None if the event is not applicable in the given state, a new COWState with some updated values
            if the event is applicable.
        """
        if not self.is_applicable(event, state):
            return None
        else:
            return self.apply_unsafe(event, state)

    def _apply_unsafe(
        self, events: Iterable["TemporalEvent"], state: "TemporalState"
    ) -> "TemporalState":
        """
        Returns a new COWState, which is a copy of the given state but the applicable effects of the event are applied; therefore
        some fluent values are updated.
        IMPORTANT NOTE: Assumes that self.is_applicable(state, event) returns True

        :param state: the state where the event formulas are evaluated.
        :param event: the event that has the information about the effects to apply.
        :return: A new COWState with some updated values.
        """
        updated_values: Dict["up.model.FNode", "up.model.FNode"] = {}
        assigned_fluent: Set["up.model.FNode"] = set()
        em = self._problem.env.expression_manager
        last_event = state.last_event
        for (
            event
        ) in events:  # TODO Refactor the code inside this for with SequentialSimulator
            for e in event.effects:
                evaluated_args = tuple(
                    self._se.evaluate(a, state) for a in e.fluent.args
                )
                fluent = self._problem.env.expression_manager.FluentExp(
                    e.fluent.fluent(), evaluated_args
                )
                if (not e.is_conditional()) or self._se.evaluate(
                    e.condition, state
                ).is_true():
                    if e.is_assignment():
                        if fluent in updated_values:
                            raise UPConflictingEffectsException(
                                f"The fluent {fluent} is modified by 2 assignments in the same event."
                            )
                        updated_values[fluent] = self._se.evaluate(e.value, state)
                        assigned_fluent.add(fluent)
                    else:
                        if fluent in assigned_fluent:
                            raise UPConflictingEffectsException(
                                f"The fluent {fluent} is modified by an assignment and an increase/decrease in the same event."
                            )
                        # If the fluent is in updated_values, we take his modified value, (which was modified by another increase or deacrease)
                        # otherwisee we take it's evaluation in the state as it's value.
                        f_eval = updated_values.get(
                            fluent, self._se.evaluate(fluent, state)
                        )
                        v_eval = self._se.evaluate(e.value, state)
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
            if event.simulated_effect is not None:
                for f, v in zip(
                    event.simulated_effect.fluents,
                    event.simulated_effect.function(self._problem, state, {}),
                ):
                    if f in updated_values:
                        raise UPConflictingEffectsException(
                            f"The fluent {f} is modified twice in the same event."
                        )
                    updated_values[f] = v

            # TODO UPDATE STN
            # (If AS, put in the STN all the events, set bound from last_event to AS, set bound from AS to AE, set bound for event from AS or AE)
            # Else: bound from Last_event to this one (?) -> problem with duplicate events -> Idea, ID for events?
            # Only after an event is added in the temporal state?
            # TODO UPDATE running events
            # IF AS: add a new list to the running events map with all the events of the action
            # else: Find the event in the running event list and remove it
            # TODO UPDATE Durative conditions
            # IF CS: add the condition in durative_conditions
            # if CE: remove the condition in durative conditions
            # TODO chain events as last_events also in the stn
            last_event = event
        # TODO check that the durative_conditions hold in the new state created.
        return state.make_child(updated_values)

    def _get_applicable_events(self, state: "up.model.ROState") -> Iterator["Event"]:
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
    ) -> List["Event"]:
        """
        Returns a list containing all the events derived from the given action, grounded with the given parameters.

        :param action: The action containing the information to create the event.
        :param parameters: The parameters needed to ground the action
        :return: the List of Events derived from this action with these parameters.
        """
        # sanity checks
        if action not in self._actions:
            raise UPUsageError(
                "The action given as parameter does not belong to the problem given to the SequentialSimulator."
            )
        params_exp = tuple(
            self._problem.env.expression_manager.auto_promote(parameters)
        )
        grounded_action = self._grounder.ground_action(action, params_exp)
        event_list = self._get_or_create_events(action, params_exp, grounded_action)
        return event_list

    def _get_unsatisfied_goals(
        self, state: "up.model.ROState", early_termination: bool = False
    ) -> List["up.model.FNode"]:
        """
        Returns the list of unsatisfied goals evaluated in the given state.
        If the flag "early_termination" is set, the method ends and returns at the first unsatisfied goal.

        :param state: The State in which the problem goals are evaluated.
        :param early_termination: Flag deciding if the method ends and returns at the first unsatisfied goal.
        :return: The list of all the goals that evaluated to False or the list containing the first goal evaluated to False if the flag "early_termination" is set.
        """
        unsatisfied_goals = []
        for g in cast(up.model.Problem, self._problem).goals:
            g_eval = self._se.evaluate(g, state).bool_constant_value()
            if not g_eval:
                unsatisfied_goals.append(g)
                if early_termination:
                    break
        return unsatisfied_goals

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
        Support function that takes the `original Action`, the `parameters` used to ground the `grounded Action` and
        the `grounded Action` itself, and adds the corresponding `List of Events` to this `Simulator`. If the
        corresponding `Events` were already created, the same value is returned and no new `Events` are created.

        :param original_action: The `Action` of the :class:`~unified_planning.model.Problem` grounded with the given `params`.
        :param params: The expressions used to ground the `original_action`.
        :param grounded_action: The grounded action, result of the `original_action` grounded with the given `parameters`.
        :return: The retrieved or created `List of Events` corresponding to the `grounded_action`.
        """
        if isinstance(original_action, up.model.InstantaneousAction):
            assert False, "For now we support only durative actions"
        elif isinstance(original_action, up.model.DurativeAction):
            # check if the event is already cached; if not: create it and cache it
            key = (original_action, params)
            event_list = self._events.get(key, None)
            if event_list is None:
                if (
                    grounded_action is None
                ):  # The grounded action is meaningless, no event associated
                    event_list = []
                else:
                    assert isinstance(grounded_action, DurativeAction)
                    event_list = break_durative_action_in_event_list(
                        grounded_action, original_action, params
                    )
                self._events[key] = event_list
            return event_list  # TODO understand if those events can be returned or they need to be recreated
        else:
            raise NotImplementedError(
                "The TemporalSimulator currently supports only InstantaneousActions and DurativeActions."
            )


def break_durative_action_in_event_list(
    grounded_action: "DurativeAction",
    original_action: "DurativeAction",
    parameters: "Tuple[FNode]",
) -> List[TemporalEvent]:
    point_events_map: Dict[Timing, Set[Union[Effect, FNode]]] = {}
    start_durative_conditions_map: Dict[Tuple[Timing, bool], List[FNode]] = {}
    end_durative_conditions_map: Dict[Tuple[Timing, bool], List[FNode]] = {}

    for t, el in grounded_action.effects.items():
        point_events_map.setdefault(t, set()).update(el)

    for i, cl in grounded_action.conditions.items():
        assert isinstance(i, TimeInterval)
        if i.lower == i.upper:  # point conditions
            if not i.is_left_open() and not i.is_right_open():
                point_events_map.setdefault(i.lower, set()).update(cl)
        else:
            # handle left side
            start_durative_conditions_map.setdefault(
                (i.lower, i.is_left_open()), []
            ).extend(cl)
            # handle right side
            end_durative_conditions_map.setdefault(
                (i.upper, i.is_right_open()), []
            ).extend(cl)

    t_start = StartTiming()
    action_start_created = False
    t_end = EndTiming()
    action_end_created = False
    events = []

    for t, ecs in point_events_map.items():
        effects = [e for e in ecs if isinstance(e, Effect)]
        conditions = [c for c in ecs if isinstance(c, FNode)]
        if t == t_start:
            action_start_created = True
            kind = TemporalEventKind.START_ACTION
        elif t == t_end:
            action_end_created = True
            kind = TemporalEventKind.END_ACTION
        else:
            kind = TemporalEventKind.INTERMEDIATE_CONDITION_EFFECT
        events.append(
            TemporalEvent(
                kind,
                original_action,
                t,
                True,
                parameters,
                conditions,
                effects,
                grounded_action.simulated_effects[t],
            )
        )
    if not action_start_created:
        events.append(
            TemporalEvent(
                TemporalEventKind.START_ACTION,
                original_action,
                t,
                True,
                parameters,
                [],
                [],
                None,
            )
        )
    if not action_end_created:
        events.append(
            TemporalEvent(
                TemporalEventKind.END_ACTION,
                original_action,
                t,
                True,
                parameters,
                [],
                [],
                None,
            )
        )

    for (t, timing_included), cl in start_durative_conditions_map.items():
        events.append(
            TemporalEvent(
                TemporalEventKind.START_CONDITION,
                original_action,
                t,
                timing_included,
                parameters,
                cl,
                [],
                None,
            )
        )

    for (t, timing_included), cl in end_durative_conditions_map.items():
        events.append(
            TemporalEvent(
                TemporalEventKind.END_CONDITION,
                original_action,
                t,
                timing_included,
                parameters,
                cl,
                [],
                None,
            )
        )
