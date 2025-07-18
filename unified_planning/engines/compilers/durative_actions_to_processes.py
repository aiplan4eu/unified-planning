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

from itertools import chain
import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.model import (
    Problem,
    ProblemKind,
    Fluent,
    Action,
    InstantaneousAction,
    DurativeAction,
    Process,
    Event,
    Timing,
    TimeInterval,
    ExpressionManager,
)
from unified_planning.model.effect import Effect
from unified_planning.model.fnode import FNode
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.model.fluent import get_all_fluent_exp
from unified_planning.engines.compilers.utils import (
    get_fresh_name,
    replace_action,
)
from typing import Dict, Iterator, Optional, OrderedDict, Tuple, List, Union
from functools import partial
from unified_planning.model.timing import (
    DurationInterval,
    Timepoint,
    TimepointKind,
    TimePointInterval,
)
import unified_planning.plans as plans
from unified_planning.plans import ActionInstance, TimeTriggeredPlan
from fractions import Fraction
from unified_planning.exceptions import UPUsageError


class DurativeActionToProcesses(engines.engine.Engine, CompilerMixin):
    def __init__(self):
        engines.engine.Engine.__init__(self)
        CompilerMixin.__init__(
            self, CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
        )
        # interesting flags to support:
        # use_counters (instead of a big and at the end to check actions running)
        # a flag to add conditions to end effects

    @property
    def name(self):
        return "datp"

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_parameters("BOOL_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOOL_ACTION_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("UNBOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("REAL_ACTION_PARAMETERS")
        supported_kind.set_numbers("BOUNDED_TYPES")
        supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
        supported_kind.set_fluents_type("INT_FLUENTS")
        supported_kind.set_fluents_type("REAL_FLUENTS")
        supported_kind.set_fluents_type("OBJECT_FLUENTS")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITIES")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        supported_kind.set_effects_kind("INCREASE_EFFECTS")
        supported_kind.set_effects_kind("DECREASE_EFFECTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("FORALL_EFFECTS")
        supported_kind.set_time("CONTINUOUS_TIME")
        supported_kind.set_time("DISCRETE_TIME")
        supported_kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("EXTERNAL_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("TIMED_EFFECTS")
        supported_kind.set_time("TIMED_GOALS")
        supported_kind.set_time("DURATION_INEQUALITIES")
        supported_kind.set_time("SELF_OVERLAPPING")
        supported_kind.set_expression_duration("STATIC_FLUENTS_IN_DURATIONS")
        supported_kind.set_expression_duration("FLUENTS_IN_DURATIONS")
        supported_kind.set_expression_duration("INT_TYPE_DURATIONS")
        supported_kind.set_expression_duration("REAL_TYPE_DURATIONS")
        supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
        supported_kind.set_constraints_kind("STATE_INVARIANTS")
        supported_kind.set_constraints_kind("TRAJECTORY_CONSTRAINTS")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_actions_cost_kind("STATIC_FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("TEMPORAL_OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("MAKESPAN")
        supported_kind.set_quality_metrics("FINAL_VALUE")
        supported_kind.set_actions_cost_kind("INT_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("REAL_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_oversubscription_kind("INT_NUMBERS_IN_OVERSUBSCRIPTION")
        supported_kind.set_oversubscription_kind("REAL_NUMBERS_IN_OVERSUBSCRIPTION")
        supported_kind.set_initial_state("UNDEFINED_INITIAL_NUMERIC")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= DurativeActionToProcesses.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return (
            compilation_kind == CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
        )

    @staticmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: Optional[CompilationKind] = None
    ) -> ProblemKind:
        new_kind = problem_kind.clone()
        # TODO this removed durative actions, adds processes and events. and increasing_cont_effects
        return new_kind

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        assert isinstance(problem, Problem)
        env = problem.environment
        mgr: ExpressionManager = env.expression_manager
        tm = env.type_manager
        new_to_old: Dict[Action, Optional[Action]] = {}  # TODO should not be needed

        new_problem = problem.clone()
        new_problem.name = f"{problem.name}_DurativeActionsToProcesses"
        new_problem.clear_actions()

        alive = Fluent(
            get_fresh_name(new_problem, "alive"), tm.BoolType(), environment=env
        )
        new_problem.add_fluent(alive, default_initial_value=mgr.TRUE())

        # TODO old code
        # if self._use_counter:
        #     new_fluent = Fluent("process_active", tm.IntType(), environment=env)
        #     new_problem.add_fluent(new_fluent, default_initial_value=0)

        # timing to end the action
        start_timing = Timepoint(TimepointKind.START)
        start_interval = TimePointInterval(start_timing)
        end_timing = Timing(0, Timepoint(TimepointKind.END))
        action_running_fluents: List[FNode] = []

        for action in problem.actions:
            if isinstance(action, InstantaneousAction):
                start_action = action.clone()
                start_action.name = get_fresh_name(new_problem, start_action.name)
                start_action.add_precondition(alive)
                new_to_old[start_action] = action
                new_problem.add_action(start_action)
            elif isinstance(action, DurativeAction):
                params = OrderedDict(((p.name, p.type) for p in action.parameters))

                start_action = InstantaneousAction(
                    get_fresh_name(new_problem, action.name, trailing_info="start"),
                    _parameters=params,
                    _env=env,
                )
                new_problem.add_action(start_action)

                action_running_fluent = Fluent(
                    get_fresh_name(new_problem, action.name, trailing_info="running"),
                    tm.BoolType(),
                    params,
                    env,
                )
                new_problem.add_fluent(
                    action_running_fluent, default_initial_value=mgr.FALSE()
                )
                action_running_fluents.append(action_running_fluent)
                action_running = action_running_fluent(start_action.parameters)

                new_clock_fluent = Fluent(
                    get_fresh_name(new_problem, action.name, trailing_info="clock"),
                    tm.RealType(),
                    params,
                    env,
                )
                new_problem.add_fluent(new_clock_fluent, default_initial_value=0)
                action_clock = new_clock_fluent(start_action.parameters)

                action_running_process = Process(
                    get_fresh_name(new_problem, action.name, trailing_info="during"),
                    _parameters=params,
                    _env=env,
                )
                action_running_process.add_precondition(action_running)
                action_running_process.add_increase_continuous_effect(action_clock, 1)

                # TODO stop event has to be added
                has_variable_duration = action_variable_duration(action)
                first_end_timing: Optional[Timing] = None
                action_duration_exp: Optional[FNode] = None

                if has_variable_duration:
                    first_end_timing = get_first_end_timing(action)
                    action_duration_fluent = Fluent(
                        get_fresh_name(
                            new_problem, action.name, trailing_info="duration"
                        ),
                        tm.RealType(),
                        params,
                        env,
                    )
                    new_problem.add_fluent(
                        action_duration_fluent, default_initial_value=0
                    )  # TODO which should be the default here? Could zero be a problem? The initial action should set this to a non-problematic number
                    action_duration_exp = action_duration_fluent(
                        start_action.parameters
                    )

                first_end_timing_conditions: List[
                    FNode
                ] = []  # TODO check if this is needed. It should not be
                # TODO maybe we need to save conditions at the end?
                for i, (interval, conditions) in enumerate(action.conditions.items()):
                    if interval == start_interval:
                        start_action.add_precondition(mgr.And(conditions))
                        continue
                        # TODO consider here if duration intervals that contains start should be added as
                        # precond to start_actions (in case, we have to ensure that it's not an empty interval
                        # which might not be too easy, expecially if we support fluents in duration)
                    if (
                        interval.lower == first_end_timing
                        or interval.upper == first_end_timing
                    ):
                        first_end_timing_conditions.append(mgr.And(conditions))
                    fail_condition = mgr.Or(map(mgr.Not, conditions))
                    inside_interval = inside_interval_condition(
                        interval,
                        first_end_timing,
                        action_clock,
                        action_duration_exp,
                        action.duration,
                        mgr,
                    )
                    # TODO we are missing the booleans that ensure previous end_event happened. Is it actually needed?
                    # I think if we put a correct default for the duration fluent it could be avoided but I am not sure
                    condition_failed_event = Event(
                        get_fresh_name(
                            new_problem,
                            action.name,
                            trailing_info=f"condition_{i}_failed",
                        ),
                        _parameters=params,
                        _env=env,
                    )
                    new_problem.add_event(condition_failed_event)
                    condition_failed_event.add_precondition(alive)
                    condition_failed_event.add_precondition(action_running)
                    condition_failed_event.add_precondition(inside_interval)
                    condition_failed_event.add_precondition(fail_condition)
                    condition_failed_event.add_effect(alive, False)
                    condition_failed_event.add_effect(
                        action_running, False
                    )  # TODO this might be not needed but might help?

                # flag that decides if we need to create the first_end instantaneous action
                first_end_action_created = not has_variable_duration
                end_action_event_created = False

                for i, (timing, effects) in action.effects.items():
                    if timing == start_timing:
                        for eff in effects:
                            start_action._add_effect_instance(eff)
                        continue
                    effect_ev_or_act: Union[Event, InstantaneousAction]
                    if timing == first_end_timing:
                        effect_ev_or_act = InstantaneousAction(
                            get_fresh_name(
                                new_problem, action.name, trailing_info="first_end"
                            ),
                            _parameters=params,
                            _env=env,
                        )
                        new_problem.add_action(effect_ev_or_act)
                        effect_ev_or_act.add_effect(
                            mgr.Equals(action_duration_exp, action_clock)
                        )
                        assert first_end_action_created == False
                        first_end_action_created = True
                    else:
                        effect_ev_or_act = Event(
                            get_fresh_name(
                                new_problem, action.name, trailing_info=f"effects_{i}"
                            ),
                            _parameters=params,
                            _env=env,
                        )
                        new_problem.add_event(effect_ev_or_act)

                    event_moment = mgr.Equals(
                        *get_relative_timing(
                            timing,
                            first_end_timing,
                            action_clock,
                            action_duration_exp,
                            action.duration,
                            mgr,
                        )
                    )
                    effect_ev_or_act.add_precondition(alive)
                    effect_ev_or_act.add_precondition(action_running)
                    effect_ev_or_act.add_precondition(event_moment)

                    for eff in effects:
                        effect_ev_or_act._add_effect_instance(eff)

                    if timing == end_timing:
                        # TODO this also has to reset the duration fluent to the safe value, whenever we decide what it is
                        # the safe value should be returned by a method, to refactor.
                        effect_ev_or_act.add_effect(action_running, False)
                        end_action_event_created = True
                    else:
                        # fluent to avoid infinite trigger fo the event
                        effect_done_fluent = Fluent(
                            get_fresh_name(
                                new_problem,
                                action.name,
                                trailing_info=f"effects_{i}_done",
                            ),
                            tm.BoolType(),
                            environment=env,
                        )
                        new_problem.add_fluent(
                            effect_done_fluent, default_initial_value=False
                        )
                        start_action.add_effect(effect_done_fluent, False)
                        effect_ev_or_act.add_precondition(mgr.Not(effect_done_fluent))
                        effect_ev_or_act.add_effect(effect_done_fluent, True)

                if not end_action_event_created:
                    if has_variable_duration and not first_end_action_created:
                        end_action_ev_or_act = InstantaneousAction(
                            get_fresh_name(
                                new_problem, action.name, trailing_info="end"
                            ),
                            _parameters=params,
                            _env=env,
                        )
                        new_problem.add_action(end_action_ev_or_act)
                        end_action_ev_or_act.add_effect(
                            mgr.Equals(action_duration_exp, action_clock)
                        )
                    else:
                        end_action_ev_or_act = Event(
                            get_fresh_name(
                                new_problem, action.name, trailing_info="end"
                            ),
                            _parameters=params,
                            _env=env,
                        )
                        new_problem.add_event(end_action_ev_or_act)
                    end_action_ev_or_act.add_precondition(alive)
                    end_action_ev_or_act.add_precondition(action_running)
                    end_action_ev_or_act.add_effect(action_running, False)

                duration_exceeded_event = Event(
                    get_fresh_name(
                        new_problem,
                        action.name,
                        trailing_info="duration_exceeded_error",
                    ),
                    _parameters=params,
                    _env=env,
                )
                new_problem.add_event(duration_exceeded_event)

                duration_exceeded_condition = (
                    mgr.GE if action.duration.is_right_open() else mgr.GT
                )  # TODO check this I am not 200% positive

                duration_exceeded_event.add_precondition(alive)
                duration_exceeded_event.add_precondition(action_running)
                duration_exceeded_event.add_precondition(duration_exceeded_condition)
                duration_exceeded_event.add_effect(alive, False)
                duration_exceeded_event.add_effect(action_running, False)

                for g in get_all_fluent_exp(new_problem, action_running_fluent):
                    new_problem.add_goal(mgr.Not(g))

            else:
                raise NotImplementedError

        new_problem.add_goal(alive)
        # if self._use_counter:
        #     new_problem.add_goal(em.Equals(new_fluent, 0))

        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old), self.name
        )

    def plantoplan(
        self,
        plan_result: "up.plans.TimeTriggeredPlan",
        map: Dict["up.model.Action", Optional["up.model.Action"]],
    ) -> Optional["up.plans.TimeTriggeredPlan"]:
        translatePlan: List[
            Tuple[Fraction, "plans.plan.ActionInstance", Optional[Fraction]]
        ] = []
        if isinstance(plan_result, TimeTriggeredPlan):
            for index, action_plans in enumerate(plan_result.timed_actions):
                fraction = action_plans[0]
                try:
                    action_durative = map[action_plans[1].action]
                except:
                    action_durative = None
                if isinstance(action_durative, DurativeAction):
                    if action_durative is not None:
                        if not (
                            action_durative.duration.lower
                            == action_durative.duration.upper
                        ):
                            target_name = action_durative.name + "_stop"
                            (found_action, _) = next(
                                (
                                    (i, action_start)
                                    for i, (_, action_start, _) in enumerate(
                                        plan_result.timed_actions[index:]
                                    )
                                    if action_start.action.name == target_name
                                    and action_plans[1].actual_parameters
                                    == action_start.actual_parameters
                                ),
                                (None, None),
                            )
                            if found_action == None:
                                (delay_variable_duration_effect, te_delay) = min(
                                    (
                                        (eff_control, te_control.delay)
                                        for te_control, eff_control in action_durative.effects.items()
                                        if te_control.delay < 0
                                    ),
                                    key=lambda x: x[1],
                                    default=(None, None),
                                )
                                if (
                                    delay_variable_duration_effect is not None
                                    and te_delay is not None
                                ):
                                    delay_found = []
                                    for i, (_, action_start, _) in enumerate(
                                        plan_result.timed_actions[index:]
                                    ):
                                        for (
                                            delay_effect
                                        ) in delay_variable_duration_effect:
                                            if (
                                                delay_effect.fluent.fluent().name
                                                in action_start.action.name
                                                and "_end_delay"
                                                in action_start.action.name
                                                and action_durative.name
                                                in action_start.action.name
                                                and action_plans[1].actual_parameters
                                                == action_start.actual_parameters
                                            ):
                                                delay_found.append(i)
                                    found_action = next(
                                        ((i) for i in delay_found if i is not None),
                                        None,
                                    )
                                    if found_action is not None:
                                        found_action = index + found_action
                                        action_time = (
                                            plan_result.timed_actions[found_action][0]
                                            + (te_delay * (-1))
                                            - fraction
                                        )
                                    else:
                                        raise UPUsageError(
                                            "The Action of the given ActionInstance does not have a valid replacement."
                                        )
                                else:
                                    raise UPUsageError(
                                        "The Action of the given ActionInstance does not have a valid replacement."
                                    )
                            else:
                                found_action = index + found_action
                                action_time = (
                                    plan_result.timed_actions[found_action][0]
                                    - fraction
                                )

                        else:
                            if action_durative.duration.lower.is_int_constant():
                                action_time = Fraction(
                                    action_durative.duration.lower.int_constant_value()
                                )
                            else:
                                action_time = None
                        translateAction = ActionInstance(
                            action_durative, action_plans[1].actual_parameters
                        )
                        translatePlan.append((fraction, translateAction, action_time))
                elif isinstance(action_durative, InstantaneousAction):
                    translateAction = ActionInstance(
                        action_durative, action_plans[1].actual_parameters
                    )
                    translatePlan.append((fraction, translateAction, Fraction(0)))
                elif action_durative is not None:
                    raise NotImplementedError

        return TimeTriggeredPlan(translatePlan)


def action_variable_duration(action: DurativeAction) -> bool:
    return action.duration.lower == action.duration.upper
    # TODO could we add an assert that if they are the same is_{right/left}_open have to be False?


def get_first_end_timing(action: DurativeAction) -> Optional[Timing]:

    # utility function to take timing or intervals and return the respective timing or timings
    def timing_from_interval(
        timing_or_interval: Union[Timing, TimeInterval], conds_or_effs
    ) -> Iterator[Timing]:
        if isinstance(timing_or_interval, Timing):
            yield timing_or_interval
        else:
            assert isinstance(
                timing_or_interval, TimeInterval
            ), f"Wrong durative action {action.name} typing associated to {conds_or_effs}"
            yield timing_or_interval.lower, timing_or_interval.upper

    first_end_timing: Optional[Timing] = None
    for timing_or_interval, conds_or_effs in chain(
        action.conditions.items(), action.effects.items()
    ):
        for timing in timing_from_interval(timing_or_interval, conds_or_effs):
            assert isinstance(
                timing, Timing
            ), f"Wrong durative action {action.name} typing associated to {conds_or_effs}"
            if timing.is_from_end():
                assert timing.delay <= 0
                if first_end_timing is None or first_end_timing.delay > timing.delay:
                    first_end_timing = timing

    return first_end_timing


def get_relative_timing(
    timing: Timing,
    first_end_timing: Optional[Timing],
    action_clock: FNode,
    action_duration_exp: Optional[FNode],
    action_duration: DurationInterval,
    mgr: ExpressionManager,
) -> Tuple[FNode, Union[int, Fraction, FNode]]:
    assert not timing.is_global()
    if timing.is_from_start():
        return action_clock, timing.delay
    assert timing.delay <= 0
    if action_duration_exp is None:
        assert action_duration.lower == action_duration.upper
        # duration is not variable, so end_timing can be returned as timing from start
        return action_clock, mgr.Plus(action_duration.lower, timing.delay)
    # complex case where the timing is from end and the action duration is variable
    assert action_duration_exp is not None and first_end_timing is not None
    return mgr.Minus(action_clock, action_duration_exp), mgr.Minus(
        timing.delay, first_end_timing.delay
    )


def inside_interval_condition(
    interval: TimeInterval,
    first_end_timing: Optional[Timing],
    action_clock: FNode,
    action_duration_exp: Optional[FNode],
    action_duration: DurationInterval,
    mgr: ExpressionManager,
) -> FNode:
    # define a utility function to get the relative timing without passing 5 args that are the same
    relative_timing = partial(
        get_relative_timing,
        first_end_timing=first_end_timing,
        action_clock=action_clock,
        action_duration_exp=action_duration_exp,
        action_duration=action_duration,
        mgr=mgr,
    )

    if interval.lower == interval.upper:
        if interval.is_left_open() or interval.is_right_open():
            return mgr.FALSE()
        return mgr.Equals(*relative_timing(interval.lower))
    left_operand = mgr.GT if interval.is_left_open() else mgr.GE
    right_operand = mgr.LT if interval.is_right_open() else mgr.LE
    return mgr.And(
        left_operand(*relative_timing(interval.lower)),
        right_operand(*relative_timing(interval.upper)),
    )
