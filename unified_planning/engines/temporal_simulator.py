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
from fractions import Fraction
import unified_planning as up
from unified_planning.model import (
    Action,
    InstantaneousAction,
    DurativeAction,
    FNode,
    Effect,
    Timing,
    TimeInterval,
    StartTiming,
    EndTiming,
    GlobalStartTiming,
    GlobalEndTiming,
    SimulatedEffect,
    TemporalState,
    DeltaSimpleTemporalNetwork,
    COWState,
    ROState,
)
from unified_planning.engines.compilers import Grounder, GrounderHelper
from unified_planning.engines.engine import Engine
from unified_planning.engines.sequential_simulator import (
    InstantaneousEvent,
    SequentialSimulator,
    get_unsatisfied_goals,
    get_unsatisfied_conditions,
)
from unified_planning.engines.mixins.simulator import Event, SimulatorMixin
from unified_planning.exceptions import UPUsageError
from unified_planning.model.walkers import StateEvaluator
from unified_planning.environment import Environment
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple, Union, cast


EPSILON = Fraction(1, 1000)


class TemporalEventKind(Enum):
    START_PLAN = auto()
    END_PLAN = auto()
    INSTANTANEOUS_ACTION = auto()
    START_ACTION = auto()
    END_ACTION = auto()
    START_CONDITION = auto()
    END_CONDITION = auto()
    INTERMEDIATE_CONDITION_EFFECT = auto()


class TemporalEvent(InstantaneousEvent):
    """Implements the Event class for the temporal scenario."""

    _class_id = 0

    def __init__(
        self,
        kind: TemporalEventKind,
        timing: Timing,
        timing_included: bool,
        committed_events: Optional[List["TemporalEvent"]],
        conditions: List["up.model.FNode"],
        effects: List["up.model.Effect"],
        simulated_effect: Optional["up.model.SimulatedEffect"] = None,
    ):
        InstantaneousEvent.__init__(self, conditions, effects, simulated_effect)
        self._kind = kind
        self._timing = timing
        self._timing_included = timing_included
        if committed_events is not None and self._kind not in (
            TemporalEventKind.START_ACTION,
            TemporalEventKind.START_PLAN,
        ):
            raise UPUsageError(
                "Committed events make sense only for start action or start plan events."
            )
        elif committed_events is None and self._kind == TemporalEventKind.START_ACTION:
            raise UPUsageError(
                "Start action events must have a list for committed events."
            )
        elif (
            not timing_included and self._kind == TemporalEventKind.INSTANTANEOUS_ACTION
        ):
            raise UPUsageError(
                "Timing not included for an INSTANTANEOUS_ACTION TemporalEvent is not valid."
            )
        self._committed_events = committed_events
        self._id = type(self)._class_id
        type(self)._class_id += 1

    def __repr__(self) -> str:
        res: List[str] = []
        res.append(str(self._kind))
        res.append(str(self._timing))
        res.append(str(self._timing_included))
        res.append(str(self._committed_events))
        res.append(str(self._conditions))
        res.append(str(self._effects))
        res.append(str(self._simulated_effect))
        return " ".join(res)

    def __hash__(self) -> int:
        return self._id

    @property
    def kind(self) -> TemporalEventKind:
        return self._kind

    @property
    def timing(self) -> Timing:
        return self._timing

    @property
    def timing_included(self) -> bool:
        return self._timing_included

    @property
    def committed_events(self) -> Optional[List["TemporalEvent"]]:
        return self._committed_events

    @property
    def id(self) -> int:
        return self._id


class TemporalSimulator(Engine, SimulatorMixin):
    """
    Implementation of the Temporal Simulator Mixin.
    """

    def __init__(
        self,
        problem: "up.model.Problem",
        error_on_failed_checks: bool = True,
        epsilon: Optional[Union[int, float, Fraction, str]] = None,
    ):
        Engine.__init__(self)
        self.error_on_failed_checks = error_on_failed_checks
        SimulatorMixin.__init__(self, problem)
        pk = problem.kind
        assert Grounder.supports(pk)
        assert isinstance(self._problem, up.model.Problem)
        try:
            self._epsilon = EPSILON if epsilon is None else Fraction(epsilon)
        except ValueError:
            raise UPUsageError(
                "Invalid epsilon value. Must be a numeric value or a parsable string."
            )
        self._grounder = GrounderHelper(problem)
        self._actions = set(self._problem.actions)
        self._se = StateEvaluator(self._problem)
        self._em = problem.env.expression_manager
        initial_values = self._problem.initial_values
        self._all_possible_assignments: Set[FNode] = set(initial_values.keys())
        self._events_to_action: Dict[
            TemporalEvent, Tuple[DurativeAction, Tuple[FNode, ...]]
        ] = {}
        problem_events: List[TemporalEvent] = cast(
            List[TemporalEvent],
            break_action_or_problem_in_event_list(
                problem.timed_effects,
                problem.timed_goals,
                {},
                None,
                problem.env,
                is_global=True,
            ),
        )
        self._start_plan_event = problem_events[0]
        self._end_plan_event = problem_events[-1]
        assert self._start_plan_event.kind == TemporalEventKind.START_PLAN
        assert self._end_plan_event.kind == TemporalEventKind.END_PLAN

    @property
    def epsilon(self) -> Fraction:
        return self._epsilon

    @epsilon.setter
    def epsilon(self, new_value: Union[int, float, Fraction, str]):
        try:
            self._epsilon = Fraction(new_value)
        except ValueError:
            raise UPUsageError(
                "Invalid epsilon value. Must be a numeric value or a parsable string."
            )

    def _is_applicable(
        self, event: Union["Event", Iterable["Event"]], state: "ROState"
    ) -> bool:
        """
        Returns `True` if the given `events` are applicable in the given `state`;
        returns `False` otherwise; a `TemporalEvent` is applicable if it's conditions
        are respected in the state, it's effects don't violate any durative condition,
        the event does not violate any time constraint of events applied before and
        the event is expected in this `state` (it is a `START_ACTION`, an `INSTANTANEOUS_ACTION`
        or it's already in the `state.running_events`).

        :param state: the `state` where the `events` are checked.
        :param event: the `event` or `Iterable[Event]` that are checked.
        :return: Whether or not the `event` is/are applicable in the given `state`.
        """
        if not isinstance(state, TemporalState):
            raise UPUsageError(
                f"Temporal Simulator needs a TemporalState instance, but {type(state)} is given!"
            )
        if isinstance(event, Event):
            events: List[TemporalEvent] = [cast(TemporalEvent, event)]
        else:
            events = [cast(TemporalEvent, e) for e in event]
        for e in events:
            if not isinstance(e, TemporalEvent):
                raise UPUsageError(
                    f"TemporalSimulator only accepts TemporalEvents but {type(e)} is given!"
                )
            if not (
                len(self.get_unsatisfied_conditions(e, state, early_termination=True))
                == 0
            ):
                return False
        # control that the given events are compatible with the given running events
        for oe in correct_order_events_to_apply(
            events,
            cast(List[List[TemporalEvent]], state.running_events),
        ):
            if oe is None:
                return False
        new_state = self.apply_unsafe(events, state)
        assert isinstance(new_state, TemporalState)
        if not new_state.stn.check_stn():
            return False
        assert self._se is not None
        for cl in state.durative_conditions:
            for condition in cl:
                assert isinstance(condition, FNode)
                if not self._se.evaluate(condition, new_state).bool_constant_value():
                    return False
        return True

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
        return get_unsatisfied_conditions(
            cast(SequentialSimulator, self), event, state, early_termination
        )

    def _apply(
        self, event: Union["Event", Iterable["Event"]], state: "up.model.COWState"
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
        self, event: Union["Event", Iterable["Event"]], state: "COWState"
    ) -> "COWState":
        """
        Returns a new COWState, which is a copy of the given state but the applicable effects of the event are applied; therefore
        some fluent values are updated.
        IMPORTANT NOTE: Assumes that self.is_applicable(state, event) returns True

        :param state: the state where the event formulas are evaluated.
        :param event: the event that has the information about the effects to apply.
        :return: A new COWState with some updated values.
        """
        if not isinstance(state, TemporalState):
            raise UPUsageError("Temporal Simulator needs a TemporalState!")
        if isinstance(event, Event):
            events: Set[TemporalEvent] = {cast(TemporalEvent, event)}
        else:
            events = cast(Set[TemporalEvent], set(event))
        updated_values, red_fluents = self._get_updated_values_and_red_fluents(
            events, state, self._se, self._all_possible_assignments
        )
        # New State variables
        stn = state.stn.copy_stn()
        running_events = [rel[:] for rel in state.running_events]
        durative_conditions = [cl[:] for cl in state.durative_conditions]

        if len(events) == 0:
            raise UPUsageError("The given iterator of events is empty")
        last_event = cast(
            TemporalEvent, next(iter(state.last_events))
        )  # TODO check if use list instead of sets
        first = True
        for other_ev in correct_order_events_to_apply(
            events, cast(List[List[TemporalEvent]], running_events)
        ):
            assert (
                other_ev is not None
            ), "Events given to apply_unsafe are supposed to be applicable"
            if not isinstance(other_ev, TemporalEvent):
                raise UPUsageError(
                    f"The timed simulator needs Temporal Events, {type(other_ev)} was given!"
                )
            self._expand_event(
                other_ev, stn, running_events, durative_conditions, last_event, state
            )
            if first:
                first_ev = other_ev
                first = False
            else:
                insert_interval(
                    stn,
                    first_ev,
                    other_ev,
                    left_bound=Fraction(0),
                    right_bound=Fraction(0),
                )
        written_fluents: Set[FNode] = set(updated_values.keys())
        red_fluents.difference_update(written_fluents)
        prev_state = state
        state_father = state._father
        while (red_fluents or written_fluents) and state_father is not None:
            assert isinstance(prev_state, TemporalState)
            assert isinstance(state_father, TemporalState)
            # setup loop variables
            (
                oth_updated_values,
                oth_red_fluents,
            ) = self._get_updated_values_and_red_fluents(
                prev_state.last_events,
                state_father,
                self._se,
                self._all_possible_assignments,
            )
            oth_written_fluents: Set[FNode] = set(oth_updated_values.keys())
            last_event = cast(
                TemporalEvent, next(iter(prev_state.last_events))
            )  # TODO check if use list instead of sets
            assert isinstance(last_event, TemporalEvent)
            # Case where at least 1 Event writes something, that affects the other Event
            if (
                not red_fluents.isdisjoint(oth_written_fluents)
                or not written_fluents.isdisjoint(oth_red_fluents)
                or not written_fluents.isdisjoint(oth_written_fluents)
            ):
                insert_interval(
                    stn,
                    last_event,
                    first_ev,
                    left_bound=Fraction(0) + self._epsilon,
                )
            # Case where both read same fluents
            elif not red_fluents.isdisjoint(oth_red_fluents):
                insert_interval(stn, last_event, first_ev, left_bound=Fraction(0))

            # Update loop variables for sentinel and next loop.
            red_fluents.difference_update(oth_red_fluents)
            red_fluents.difference_update(oth_written_fluents)
            written_fluents.difference_update(oth_red_fluents)
            written_fluents.difference_update(oth_written_fluents)
            prev_state = state_father
            state_father = state_father._father

        new_state = cast(
            TemporalState,
            state.make_child(
                updated_values,
                running_events,
                stn,
                durative_conditions,
                cast(Set[Event], events),
            ),
        )
        return new_state

    def _get_applicable_events(
        self,
        state: "up.model.ROState",
        durations_map: Optional[
            Dict[Tuple[Action, Tuple[FNode]], Union[int, Fraction]]
        ] = None,
    ) -> Iterator["Event"]:
        """
        Returns a view over all the events that are applicable in the given State;
        an Event is considered applicable in a given State, when all the Event condition
        simplify as True when evaluated in the State.

        :param state: The state where the formulas are evaluated.
        :param durations_map: the mapping from the Tuple[Action + grounding_parameters]
            to the duration of said action; if an action with specific parameters is not
            present in this mapping, it will not be proposed in the generated events.
        :return: an Iterator of applicable Events.
        """
        if not isinstance(state, TemporalState):
            raise UPUsageError(
                f"{type(self)}.is_goal expected TemporalState but {type(state)} was given!"
            )
        if durations_map is None:
            raise UPUsageError(
                f"The duration map must bew specified to get all the applicable events of the {type(self)}"
            )
        for rel in state.running_events:
            event = rel[0]
            if self.is_applicable(event, state):
                yield event
        for (action, params), duration in durations_map.items():
            event = self._get_events(action, params, duration)[0]
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
        Returns a list containing all the events derived from the given action, grounded with the given parameters.

        :param action: The action containing the information to create the event.
        :param parameters: The parameters needed to ground the action
        :return: the List of Events derived from this action with these parameters.
        """
        # sanity checks
        if duration is None:
            raise UPUsageError(
                "The TemporalSimulator needs a specified duration to give ordered action events."
            )
        duration = Fraction(duration)
        if action not in self._actions:
            raise UPUsageError(
                "The action given as parameter does not belong to the problem given to the SequentialSimulator."
            )
        params_exp = tuple(
            self._problem.env.expression_manager.auto_promote(parameters)
        )
        grounded_action = self._grounder.ground_action(action, params_exp)
        event_list = self._get_or_create_events(
            action, params_exp, grounded_action, duration
        )
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
        return get_unsatisfied_goals(
            cast(SequentialSimulator, self), state, early_termination
        )

    def _is_goal(self, state: "ROState") -> bool:
        """
        Method called by the up.engines.mixins.simulator.SimulatorMixin.is_goal.
        """
        if not isinstance(state, TemporalState):
            raise UPUsageError(
                f"{type(self)}.is_goal expected TemporalState but {type(state)} was given!"
            )
        if not len(self.get_unsatisfied_goals(state, early_termination=True)) == 0:
            return False
        new_state = cast(TemporalState, self.apply(self._end_plan_event, state))
        if (
            new_state is None
            or len(new_state.running_events) > 0
            or len(new_state.durative_conditions) > 0
            or not new_state.stn.check_stn()
        ):
            return False
        return True

    def _get_initial_state(self) -> "COWState":
        """
        Returns the :class:`~unified_planning.model.TemporalState` instance that represents
        the initial state of the given `problem`.
        """
        initial_stn: DeltaSimpleTemporalNetwork[Fraction] = DeltaSimpleTemporalNetwork()
        assert self._start_plan_event.committed_events is not None
        initial_running_events: List[TemporalEvent] = cast(
            List[TemporalEvent], self._start_plan_event.committed_events[:]
        )
        insert_interval(
            initial_stn,
            self._start_plan_event,
            self._end_plan_event,
            left_bound=Fraction(0),
        )
        for ev in initial_running_events[:-1]:
            if ev.timing.is_from_start():
                distance = Fraction(ev.timing.delay)
                if (
                    not ev.timing_included
                    and ev.kind == TemporalEventKind.START_CONDITION
                ):
                    distance += self._epsilon
                elif (
                    not ev.timing_included
                    and ev.kind == TemporalEventKind.END_CONDITION
                ):
                    distance -= self._epsilon
                insert_interval(
                    initial_stn,
                    self._start_plan_event,
                    ev,
                    left_bound=distance,
                    right_bound=distance,
                )
            else:
                f0 = Fraction(0)
                assert ev.timing.delay == f0
                insert_interval(
                    initial_stn, self._end_plan_event, ev, left_bound=f0, right_bound=f0
                )

        self._initial_state = TemporalState(
            cast(up.model.Problem, self._problem).initial_values,
            cast(List[List[Event]], [initial_running_events]),
            initial_stn,
            [],
            {self._start_plan_event},
        )
        return self._initial_state

    @property
    def name(self) -> str:
        return "temporal_simulator"

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
        supported_kind.set_time("CONTINUOUS_TIME")
        supported_kind.set_time("DISCRETE_TIME")
        supported_kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("TIMED_EFFECT")
        supported_kind.set_time("TIMED_GOALS")
        supported_kind.set_time("DURATION_INEQUALITIES")
        supported_kind.set_expression_duration("STATIC_FLUENTS_IN_DURATION")
        supported_kind.set_expression_duration("FLUENTS_IN_DURATION")
        supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= TemporalSimulator.supported_kind()

    def _get_or_create_events(
        self,
        original_action: "up.model.Action",
        params: Tuple["up.model.FNode", ...],
        grounded_action: Optional["up.model.Action"],
        duration: Fraction,
    ) -> List[Event]:
        """
        Support function that takes the `original Action`, the `parameters` used to ground the `grounded Action` and
        the `grounded Action` itself, and returns the corresponding `List of Events`.

        :param original_action: The `Action` of the :class:`~unified_planning.model.Problem` grounded with the given `params`.
        :param params: The expressions used to ground the `original_action`.
        :param grounded_action: The grounded action, result of the `original_action` grounded with the given `parameters`.
        :return: The retrieved or created `List of Events` corresponding to the `grounded_action`.
        """
        if isinstance(original_action, InstantaneousAction):
            assert isinstance(grounded_action, InstantaneousAction)
            return [
                TemporalEvent(
                    TemporalEventKind.INSTANTANEOUS_ACTION,
                    StartTiming(),
                    True,
                    None,
                    grounded_action.preconditions,
                    grounded_action.effects,
                    grounded_action.simulated_effect,
                )
            ]
        elif isinstance(original_action, DurativeAction):
            if (
                grounded_action is None
            ):  # The grounded action is meaningless, no event associated
                event_list: List["Event"] = []
            else:
                assert isinstance(grounded_action, DurativeAction)
                event_list = break_action_or_problem_in_event_list(
                    grounded_action.effects,
                    grounded_action.conditions,
                    grounded_action.simulated_effects,
                    duration,
                    grounded_action.env,
                    is_global=False,
                )
            self._events_to_action[cast(TemporalEvent, event_list[0])] = (
                original_action,
                params,
            )
            return event_list
        else:
            raise NotImplementedError(
                "The TemporalSimulator currently supports only InstantaneousActions and DurativeActions."
            )

    def _expand_event(
        self,
        event: "TemporalEvent",
        stn: DeltaSimpleTemporalNetwork,
        running_events: List[List[Event]],
        durative_conditions: List[List[FNode]],
        last_event: "TemporalEvent",
        state: TemporalState,
    ):
        """IMPORTANT NOTE: This function modifies the data structures given as parameters."""
        insert_interval(stn, last_event, event, left_bound=Fraction(0))
        if event.kind == TemporalEventKind.START_ACTION:
            # check duration constraints
            assert event.committed_events is not None
            duration = event.committed_events[-1].timing.delay
            em = self._problem.env.expression_manager
            original_action, params = self._events_to_action[event]
            grounded_action = self._grounder.ground_action(original_action, params)
            assert grounded_action is not None
            assert isinstance(grounded_action, DurativeAction)
            action_duration = grounded_action.duration
            left_compare = em.GT if action_duration.is_left_open() else em.GE
            right_compare = em.LT if action_duration.is_right_open() else em.LE
            if not self._se.evaluate(
                left_compare(duration, action_duration.lower), state
            ).bool_constant_value():
                raise UPUsageError(
                    f"The duration: {duration} is lower than the lower bound of the action's {original_action.name} duration constraints."
                )
            if not self._se.evaluate(
                right_compare(duration, action_duration.upper), state
            ).bool_constant_value():
                raise UPUsageError(
                    f"The duration: {duration} is bigger than the upper bound of the action's {original_action.name} duration constraints."
                )

            committed_events: List[Event] = []
            ce = event.committed_events
            assert (
                ce is not None
            ), "Error, start Action event can't have None committed events"
            for committed_event in ce:
                if any(committed_event in el for el in running_events):
                    raise UPUsageError(
                        "START_ACTION event already submitted to ",
                        "the timed_simulator! NOTE that TemporalEvents are unique and only usable once!",
                    )
                committed_events.append(committed_event)
                bound = Fraction(committed_event.timing.delay)
                if (
                    committed_event.kind == TemporalEventKind.START_CONDITION
                    and not committed_event.timing_included
                ):
                    bound += self._epsilon
                elif (
                    committed_event.kind == TemporalEventKind.END_CONDITION
                    and not committed_event.timing_included
                ):
                    bound -= self._epsilon
                insert_interval(
                    stn, event, committed_event, left_bound=bound, right_bound=bound
                )
            running_events.append(committed_events)
        elif not event.kind == TemporalEventKind.INSTANTANEOUS_ACTION:
            found = False
            for el in running_events:
                if el[0] == event:
                    el.pop(0)
                    found = True
                    if len(el) == 0:
                        running_events.remove(el)
                    break
            if not found:
                raise UPUsageError(
                    f"event: {event} not found in this state ",
                    "! NOTE that TemporalEvents are unique, only usable once and ",
                    "must be given to the simulator in the same order as they are given!",
                )
            if event.kind == TemporalEventKind.START_CONDITION:
                durative_conditions.append(event.conditions[:])
            elif event.kind == TemporalEventKind.END_CONDITION:
                conditions_to_remove = event.conditions[:]
                for cl in durative_conditions:
                    cl_indexes_to_remove: List[int] = []
                    for i, cond in enumerate(cl):
                        if cond in conditions_to_remove:
                            conditions_to_remove.remove(cond)
                            cl_indexes_to_remove.append(i)
                    cl_indexes_to_remove.reverse()
                    for itr in cl_indexes_to_remove:
                        cl.pop(itr)
                assert (
                    len(conditions_to_remove) == 0
                ), "All conditions should have been added before being removed"
                # Filter out empty lists
                durative_conditions[:] = [x for x in filter(None, durative_conditions)]


def break_action_or_problem_in_event_list(
    effects: Dict[Timing, List[Effect]],
    conditions: Dict[TimeInterval, List[FNode]],
    simulated_effects: Dict[Timing, SimulatedEffect],
    duration: Optional[Fraction],
    env: Environment,
    is_global: bool,
) -> List[Event]:
    assert is_global != (duration is not None)  # equivalent to xor
    em = env.expression_manager
    point_events_map: Dict[Timing, Set[Union[Effect, FNode]]] = {}
    start_durative_conditions_map: Dict[Tuple[Timing, bool], List[FNode]] = {}
    end_durative_conditions_map: Dict[Tuple[Timing, bool], List[FNode]] = {}

    for t, el in effects.items():
        point_events_map.setdefault(get_timing_from_start(t, duration), set()).update(
            el
        )

    for i, cl in conditions.items():
        assert isinstance(i, TimeInterval)
        lower = get_timing_from_start(i.lower, duration)
        upper = get_timing_from_start(i.upper, duration)
        # valid point condition
        if lower == upper and not i.is_left_open() and not i.is_right_open():
            point_events_map.setdefault(lower, set()).update(cl)
        # Meaningful interval condition (empty interval is True)
        elif lower.delay < upper.delay:
            cond = em.And(cl)
            # handle left side
            start_durative_conditions_map.setdefault(
                (lower, not i.is_left_open()), []
            ).append(cond)
            # handle right side
            end_durative_conditions_map.setdefault(
                (upper, not i.is_right_open()), []
            ).append(cond)

    t_start = GlobalStartTiming() if is_global else StartTiming()
    t_end = (
        GlobalEndTiming() if is_global else get_timing_from_start(EndTiming(), duration)
    )

    # events is a mapping from each timing to the corresponding list of events.
    # after it is populated, it must be ordered for key and it's values returned as a list
    events: Dict[Timing, List[TemporalEvent]] = {}
    start_conditions = None
    start_effects = None
    for t, ecs in point_events_map.items():
        assert t.is_global() == is_global
        tmp_conditions = [c for c in ecs if isinstance(c, FNode)]
        tmp_effects = [e for e in ecs if isinstance(e, Effect)]
        if t == t_start:
            assert (
                start_conditions is None and start_effects is None
            ), "Error, multiple StartTiming found."
            start_conditions = tmp_conditions
            start_effects = tmp_effects
            continue
        elif t == t_end:
            kind = (
                TemporalEventKind.END_PLAN
                if is_global
                else TemporalEventKind.END_ACTION
            )
        else:
            kind = TemporalEventKind.INTERMEDIATE_CONDITION_EFFECT
        event = TemporalEvent(
            kind,
            t,
            True,
            None,
            tmp_conditions,
            tmp_effects,
            simulated_effects.get(t, None),
        )
        events.setdefault(t, []).append(event)

    if start_conditions is None:
        start_conditions = []
        assert start_effects is None
        start_effects = []
    assert start_effects is not None

    if t_end not in events:
        event = TemporalEvent(
            TemporalEventKind.END_PLAN if is_global else TemporalEventKind.END_ACTION,
            t_end,
            True,
            None,
            [],
            [],
            None,
        )
        events[t_end] = [event]

    for (t, timing_included), cl in start_durative_conditions_map.items():
        event = TemporalEvent(
            TemporalEventKind.START_CONDITION,
            t,
            timing_included,
            None,
            cl,
            [],
            None,
        )
        events.setdefault(t, []).append(event)
        if t == t_start and timing_included:
            start_conditions.extend(cl)

    for (t, timing_included), cl in end_durative_conditions_map.items():
        event = TemporalEvent(
            TemporalEventKind.END_CONDITION,
            t,
            timing_included,
            None,
            cl,
            [],
            None,
        )
        events.setdefault(t, []).append(event)
    # reverse t_end so that the END_ACTION/END_PLAN event is the last of the list,
    # if some durative conditions at end were included in the cycle above
    events[t_end].reverse()

    ret_list: List[Event] = []
    for ev_list in (
        events[key] for key in sorted(events.keys(), key=lambda t: t.delay)
    ):
        ret_list.extend(ev_list)

    start_event = TemporalEvent(
        TemporalEventKind.START_PLAN if is_global else TemporalEventKind.START_ACTION,
        t_start,
        True,
        cast(List[TemporalEvent], ret_list)[:],
        start_conditions,
        start_effects,
        simulated_effects.get(t_start, None),
    )
    ret_list.insert(0, start_event)

    assert cast(TemporalEvent, ret_list[0]).kind in (
        TemporalEventKind.START_ACTION,
        TemporalEventKind.START_PLAN,
    )
    assert cast(TemporalEvent, ret_list[-1]).kind in (
        TemporalEventKind.END_ACTION,
        TemporalEventKind.END_PLAN,
    )
    return ret_list


def get_timing_from_start(
    timing: Timing, action_duration: Optional[Fraction]
) -> Timing:
    assert action_duration is not None
    res = timing
    if timing.is_from_end():
        res = StartTiming(action_duration - timing.delay)
    if res.delay > action_duration:
        start_or_end = "end" if timing.is_from_end() else "start"
        raise UPUsageError(
            "Error, the given action duration is smaller than a",
            f" delay from the {start_or_end} of the action.",
        )
    return res


def insert_interval(
    stn: DeltaSimpleTemporalNetwork,
    left_event: TemporalEvent,
    right_event: TemporalEvent,
    *,
    left_bound: Optional[Fraction] = None,
    right_bound: Optional[Fraction] = None,
):
    """Important NOTE: This function modifies the given stn!"""
    if left_bound is not None:
        stn.add(left_event, right_event, -left_bound)
    if right_bound is not None:
        stn.add(right_event, left_event, right_bound)


def correct_order_events_to_apply(
    events: Iterable[TemporalEvent], running_events: List[List[TemporalEvent]]
) -> Iterator[Optional[TemporalEvent]]:
    # TODO find a significative name
    """
    This method yields the events in the correct order they must be applied. If a None element is
    returned, it means the given events are not applicable.
    """
    events = set(events)
    start_action_events = filter(
        lambda ev: ev.kind
        in (TemporalEventKind.START_ACTION, TemporalEventKind.INSTANTANEOUS_ACTION),
        events.copy(),
    )
    # Copy the running events and simulate the events being popped and added from the state as they get applied.
    running_events = [rel[:] for rel in running_events]
    while events:
        # other ev is or an event in the start_action_events (if there are any), if
        # not, it's an event that is also a head of one of the running_events list.
        ret_ev = next(start_action_events, None)
        if ret_ev is None:
            for ev in events:
                found = False
                for rel in running_events:
                    if rel[0] == ev:
                        found = True
                        ret_ev = rel.pop(0)
                        if not rel:
                            running_events.remove(rel)
                        break
                if found:
                    break
        yield ret_ev
        if ret_ev is None:
            break
        assert ret_ev is not None
        events.remove(ret_ev)
        if ret_ev.kind == TemporalEventKind.START_ACTION:
            assert ret_ev.committed_events is not None
            running_events.append(ret_ev.committed_events[:])
