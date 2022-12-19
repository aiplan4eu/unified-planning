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
from typing import List, Tuple, Dict, Set, cast
import unified_planning as up
import unified_planning.environment
import unified_planning.engines as engines
import unified_planning.engines.mixins as mixins
import unified_planning.model.walkers as walkers
from unified_planning.model import (
    AbstractProblem,
    Problem,
    ProblemKind,
    COWState,
    InstantaneousAction,
    DurativeAction,
    TemporalState,
)
from unified_planning.engines.results import (
    ValidationResult,
    ValidationResultStatus,
    LogMessage,
    LogLevel,
)
from unified_planning.engines.temporal_simulator import (
    TemporalSimulator,
    TemporalEvent,
    TemporalEventKind,
)
from unified_planning.plans import PlanKind, TimeTriggeredPlan


def sort_time_events_map(item: Tuple[Tuple[Fraction, bool, bool], Set[TemporalEvent]]):
    """
    This method is used to sort the values of the time_events_map following this logic:
    The first field to order is the time;
    when the time is equivalent the first elements needed are the end_conditions that are
    not included (else branch);
    the second elements needed are the included ones (if branch);
    the last element needed are the start_condition that are not included.
    """
    first_elem = item[0]
    time = first_elem[0]
    is_included = first_elem[1]
    is_start_condition = first_elem[2]

    if is_included:
        second_value = 1
    elif is_start_condition:
        second_value = 2
    else:  # is_end_condition
        second_value = 0

    return (time, second_value)


class TemporalPlanValidator(engines.engine.Engine, mixins.PlanValidatorMixin):
    """Performs :class:`~unified_planning.plans.Plan` validation."""

    def __init__(self, **options):
        engines.engine.Engine.__init__(self)
        self._env: "unified_planning.environment.Environment" = (
            unified_planning.environment.get_env(options.get("env", None))
        )
        self.manager = self._env.expression_manager
        self._substituter = walkers.Substituter(self._env)

    @property
    def name(self):
        return "temporal_plan_validator"

    @staticmethod
    def supports_plan(plan_kind: "up.plans.PlanKind") -> bool:
        return plan_kind == PlanKind.TIME_TRIGGERED_PLAN

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind()
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_time("CONTINUOUS_TIME")
        supported_kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("TIMED_EFFECT")
        supported_kind.set_time("TIMED_GOALS")
        supported_kind.set_time("DURATION_INEQUALITIES")

        # supported_kind.set_expression_duration('STATIC_FLUENTS_IN_DURATION')
        # supported_kind.set_expression_duration('FLUENTS_IN_DURATION')
        # TODO understand how to support those

        supported_kind.set_numbers("CONTINUOUS_NUMBERS")
        supported_kind.set_numbers("DISCRETE_NUMBERS")
        supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITY")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        supported_kind.set_effects_kind("INCREASE_EFFECTS")
        supported_kind.set_effects_kind("DECREASE_EFFECTS")
        supported_kind.set_fluents_type("NUMERIC_FLUENTS")
        supported_kind.set_fluents_type("OBJECT_FLUENTS")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= TemporalPlanValidator.supported_kind()

    def _validate(
        self, problem: "AbstractProblem", plan: "unified_planning.plans.Plan"
    ) -> "up.engines.results.ValidationResult":
        """
        Returns True if and only if the plan given in input is a valid plan for the problem given in input.
        This means that from the initial state of the problem, by following the plan, you can reach the
        problem goal. Otherwise False is returned.

        :param problem: The problem for which the plan to validate was generated.
        :param plan: The plan that must be validated.
        :return: The generated up.engines.results.ValidationResult; a data structure containing the information
            about the plan validity and eventually some additional log messages for the user.
        """
        # TODO document and add epsilon modification possibility
        assert isinstance(plan, TimeTriggeredPlan)
        assert isinstance(problem, Problem)
        simulator = TemporalSimulator(problem)
        current_state: "COWState" = simulator.get_initial_state()
        assert isinstance(current_state, TemporalState)
        end_plan: Fraction = Fraction(0)
        # keys of time_events_map are Fraction (the time), the first bool (that represents if the timing is included),
        # if the timing is not included, then the second bool represents if the events in it are START_CONDITION.
        time_events_map: Dict[Tuple[Fraction, bool, bool], Set[TemporalEvent]] = {}
        for start_time, ai, duration in plan.timed_actions:

            action = ai.action
            assert (
                isinstance(action, InstantaneousAction)
                and duration is None
                or isinstance(action, DurativeAction)
                and duration is not None
            )

            # populate the time_events_map
            events: List[TemporalEvent] = cast(
                List[TemporalEvent],
                simulator.get_events(action, ai.actual_parameters, duration),
            )
            for ev in events:
                assert ev.timing.is_from_start()
                event_time: Fraction = start_time + ev.timing.delay
                end_plan = max(end_plan, event_time)
                specific_time_set_events: Set[
                    TemporalEvent
                ] = time_events_map.setdefault(
                    (
                        event_time,
                        ev.timing_included,
                        ev.kind == TemporalEventKind.START_CONDITION,
                    ),
                    set(),
                )
                specific_time_set_events.add(ev)
        assert len(current_state.running_events) == 1
        only_end_events: bool = False
        for ev in cast(List[TemporalEvent], current_state.running_events[0][:-1]):
            if ev.timing.is_from_start():
                assert (
                    not only_end_events
                ), "Error: end_event in running events before a start_event"
                event_time = Fraction(ev.timing.delay)
                end_plan = max(end_plan, event_time)
                specific_time_set_events = time_events_map.setdefault(
                    (
                        event_time,
                        ev.timing_included,
                        ev.kind == TemporalEventKind.START_CONDITION,
                    ),
                    set(),
                )
                specific_time_set_events.add(ev)
            else:  # EVENT at the end of plan
                only_end_events = True
                assert ev.timing.delay == 0
                specific_time_set_events = time_events_map.setdefault(
                    (
                        end_plan,
                        ev.timing_included,
                        ev.kind == TemporalEventKind.START_CONDITION,
                    ),
                    set(),
                )
                specific_time_set_events.add(ev)

        # TODO add a way to return some logs when plan fails.
        logs: List[LogMessage] = []
        state = simulator.get_initial_state()
        valid_plan = True
        for _, set_events in sorted(time_events_map.items(), key=sort_time_events_map):
            next_state = simulator.apply(set_events, state)
            print(set_events)
            if next_state is None:
                valid_plan = False
                print(set_events)
                print(simulator.is_applicable(set_events, state))

                break
            state = next_state

        if valid_plan:
            print(valid_plan)
            valid_plan = simulator.is_goal(state)
            print(valid_plan)

        status = (
            ValidationResultStatus.VALID
            if valid_plan
            else ValidationResultStatus.INVALID
        )
        return ValidationResult(status, self.name, logs)
