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

from collections import defaultdict
from fractions import Fraction
from itertools import chain
import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.environment import Environment
from unified_planning.exceptions import UPUsageError, UPValueError
from unified_planning.model import (
    Action,
    Problem,
    ProblemKind,
    Fluent,
    InstantaneousAction,
    DurativeAction,
    Process,
    Event,
    Timing,
    TimeInterval,
    Expression,
    ExpressionManager,
    MinimizeActionCosts,
    Type,
)
from unified_planning.model.expression import (
    ConstantExpression,
    NumericConstant,
    uniform_numeric_constant,
)
from unified_planning.model.fnode import FNode
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.model.fluent import get_all_fluent_exp
from unified_planning.model.type_manager import TypeManager
from unified_planning.model.walkers import Simplifier
from unified_planning.engines.compilers.utils import (
    get_fresh_name,
)
from typing import (
    Dict,
    Iterator,
    Optional,
    OrderedDict,
    Tuple,
    List,
    Union,
    cast,
)
from functools import partial
from unified_planning.model.timing import (
    DurationInterval,
    EndTiming,
)
from unified_planning.plans import ActionInstance, TimeTriggeredPlan


class DurativeActionToProcesses(engines.engine.Engine, CompilerMixin):
    def __init__(self, default_epsilon: NumericConstant = Fraction(1, 100)):
        engines.engine.Engine.__init__(self)
        CompilerMixin.__init__(
            self, CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
        )
        self._default_epsilon = Fraction(uniform_numeric_constant(default_epsilon))
        if self._default_epsilon < 0:
            raise UPUsageError(
                f"Default epsilon must be >= 0. Default epsilon given: {self._default_epsilon}"
            )
        # interesting flags to support:
        # use_counters (instead of a big and at the end to check actions running)
        # a flag to add conditions to end effects
        # it would also be interesting to support fluents in duration
        # (inserting 2 fluents that represent the duration bounds values at the start of the action,
        # the rest of the code should work)

    @property
    def name(self):
        return "datp"

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")

        supported_kind.set_time("CONTINUOUS_TIME")
        supported_kind.set_time("DISCRETE_TIME")
        supported_kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("EXTERNAL_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("TIMED_EFFECTS")
        supported_kind.set_time("TIMED_GOALS")
        supported_kind.set_time("DURATION_INEQUALITIES")
        supported_kind.set_time("PROCESSES")
        supported_kind.set_time("EVENTS")

        supported_kind.set_expression_duration("STATIC_FLUENTS_IN_DURATIONS")
        # supported_kind.set_expression_duration("FLUENTS_IN_DURATIONS") # TODO to support this check comments in the code
        supported_kind.set_expression_duration("INT_TYPE_DURATIONS")
        supported_kind.set_expression_duration("REAL_TYPE_DURATIONS")

        supported_kind.set_numbers("BOUNDED_TYPES")

        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITIES")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")

        supported_kind.set_effects_kind("INCREASE_EFFECTS")
        supported_kind.set_effects_kind("DECREASE_EFFECTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("FORALL_EFFECTS")

        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")

        supported_kind.set_parameters("BOOL_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOOL_ACTION_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("UNBOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("REAL_ACTION_PARAMETERS")

        supported_kind.set_fluents_type("INT_FLUENTS")
        supported_kind.set_fluents_type("REAL_FLUENTS")
        supported_kind.set_fluents_type("OBJECT_FLUENTS")

        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("TEMPORAL_OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("MAKESPAN")
        supported_kind.set_quality_metrics("FINAL_VALUE")

        supported_kind.set_actions_cost_kind("STATIC_FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("INT_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("REAL_NUMBERS_IN_ACTIONS_COST")

        supported_kind.set_oversubscription_kind("INT_NUMBERS_IN_OVERSUBSCRIPTION")
        supported_kind.set_oversubscription_kind("REAL_NUMBERS_IN_OVERSUBSCRIPTION")

        supported_kind.set_constraints_kind("STATE_INVARIANTS")
        supported_kind.set_constraints_kind("TRAJECTORY_CONSTRAINTS")

        supported_kind.set_initial_state("UNDEFINED_INITIAL_NUMERIC")
        supported_kind.set_initial_state("UNDEFINED_INITIAL_SYMBOLIC")
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
        new_kind.unset_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
        if new_kind.has("DURATION_INEQUALITIES"):
            new_kind.unset_time("DURATION_INEQUALITIES")
            new_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        new_kind.unset_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")

        new_kind.unset_expression_duration("STATIC_FLUENTS_IN_DURATIONS")
        new_kind.unset_expression_duration(
            "FLUENTS_IN_DURATIONS"
        )  # TODO keep this if kept in the supported_kind
        new_kind.unset_expression_duration("INT_TYPE_DURATIONS")
        new_kind.unset_expression_duration("REAL_TYPE_DURATIONS")

        new_kind.set_time("PROCESSES")
        new_kind.set_time("EVENTS")
        # new_kind.set_fluents_type("INT_FLUENTS") # TODO should not do that unless we support the counter fluent
        new_kind.set_fluents_type("REAL_FLUENTS")
        return new_kind

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        assert (
            compilation_kind == CompilationKind.DURATIVE_ACTIONS_TO_PROCESSES_CONVERSION
        ), "Not supported compilation kind"
        assert isinstance(problem, Problem)
        env = problem.environment
        mgr: ExpressionManager = env.expression_manager
        tm = env.type_manager
        start_actions: Dict[Action, Action] = {}
        first_end_actions: Dict[Action, Tuple[Action, Timing]] = {}

        new_problem = problem.clone()
        new_problem.name = f"{problem.name}_DurativeActionsToProcesses"
        new_problem.clear_actions()

        epsilon: Fraction = (
            problem.epsilon if problem.epsilon is not None else self._default_epsilon
        )

        simplifier = Simplifier(new_problem.environment, problem)

        alive = Fluent(
            get_fresh_name(new_problem, "alive"), tm.BoolType(), environment=env
        )
        new_problem.add_fluent(alive, default_initial_value=mgr.TRUE())

        for action in problem.actions:
            if isinstance(action, InstantaneousAction):
                start_action = action.clone()
                start_action.name = get_fresh_name(new_problem, start_action.name)
                start_action.add_precondition(alive)
                start_actions[start_action] = action
                new_problem.add_action(start_action)
            elif isinstance(action, DurativeAction):
                (
                    start_action,
                    first_end_action,
                    first_end_timing,
                ) = _compile_durative_action(
                    action, new_problem, alive, simplifier, epsilon
                )
                start_actions[start_action] = action
                if first_end_action is not None:
                    assert first_end_timing is not None
                    first_end_actions[first_end_action] = action, first_end_timing
                else:
                    assert first_end_timing is None

            else:
                raise NotImplementedError

        new_problem.add_goal(alive)

        new_problem.clear_quality_metrics()
        for qm in problem.quality_metrics:
            if isinstance(qm, MinimizeActionCosts):
                new_problem.add_quality_metric(
                    _convert_action_costs(qm, start_actions, first_end_actions)
                )
            else:
                new_problem.add_quality_metric(qm)

        return CompilerResult(
            new_problem,
            None,
            self.name,
            plan_back_conversion=partial(
                _back_plan_to_plan,
                start_actions=start_actions,
                end_actions=first_end_actions,
                simplifier=simplifier,
            ),
            plan_forward_conversion=partial(
                _forward_plan_to_plan,
                start_actions_forward={
                    original_action: compiled_action
                    for compiled_action, original_action in start_actions.items()
                },
                end_actions_forward={
                    original_action: (compiled_action, first_end_timing)
                    for compiled_action, (
                        original_action,
                        first_end_timing,
                    ) in first_end_actions.items()
                },
                environment=env,
            ),
        )


def _compile_durative_action(
    action: DurativeAction,
    new_problem: Problem,
    alive: Fluent,
    simplifier: Simplifier,
    epsilon: Fraction,
) -> Tuple[InstantaneousAction, Optional[InstantaneousAction], Optional[Timing]]:
    env = new_problem.environment
    tm: TypeManager = env.type_manager
    mgr: ExpressionManager = env.expression_manager
    params = OrderedDict(((p.name, p.type) for p in action.parameters))

    add_new_fluent = partial(
        _add_new_fluent, new_problem=new_problem, action=action, params=params
    )

    action_running: FNode = add_new_fluent(
        "running",
        tm.BoolType(),
        mgr.FALSE(),
    )

    action_clock: FNode = add_new_fluent(
        "clock",
        tm.RealType(),
        mgr.Int(0),
    )

    action_running_process = Process(
        get_fresh_name(new_problem, action.name, trailing_info="during"),
        _parameters=params,
        _env=env,
    )
    new_problem.add_process(action_running_process)
    action_running_process.add_precondition(alive)
    action_running_process.add_precondition(action_running)
    action_running_process.add_increase_continuous_effect(action_clock, 1)

    start_action = InstantaneousAction(
        get_fresh_name(new_problem, action.name, trailing_info="start"),
        _parameters=params,
        _env=env,
    )
    new_problem.add_action(start_action)
    start_action.add_precondition(alive)
    start_action.add_effect(action_running, True)
    start_action.add_effect(action_clock, 0)

    has_variable_duration = _action_variable_duration(action)

    first_end_timing: Optional[Timing] = None
    action_duration_exp: Optional[FNode] = None
    first_end_triggered: Optional[FNode] = None
    first_end_action: Optional[InstantaneousAction] = None

    if has_variable_duration:
        first_end_timing = _get_first_end_timing(action)
        if first_end_timing is None:
            first_end_timing = EndTiming()

        action_duration_exp = add_new_fluent(
            "duration",
            tm.RealType(),
            mgr.Int(0),
        )
        start_action.add_effect(cast(FNode, action_duration_exp), 0)

        if not _is_end_timing(first_end_timing):
            first_end_triggered = add_new_fluent(
                "first_end_triggered",
                tm.BoolType(),
                mgr.FALSE(),
            )
            start_action.add_effect(cast(FNode, first_end_triggered), False)

        first_end_action = InstantaneousAction(
            get_fresh_name(new_problem, action.name, trailing_info="first_end"),
            _parameters=params,
            _env=new_problem.environment,
        )
        new_problem.add_action(first_end_action)
        first_end_action.add_precondition(alive)
        first_end_action.add_precondition(action_running)
        first_end_action.add_precondition(
            simplifier.simplify(
                _first_end_action_duration_constraint(
                    action,
                    first_end_timing,
                    action_clock,
                    mgr,
                )
            )
        )
        if not _is_end_timing(first_end_timing):
            first_end_action.add_effect(cast(FNode, first_end_triggered), True)
            first_end_action.add_effect(cast(FNode, action_duration_exp), action_clock)

    # utility function to call add_new_action_or_event without passing the same parameters
    add_new_event = partial(
        _add_new_event,
        new_problem=new_problem,
        params=params,
        action=action,
        alive=alive,
        action_running=action_running,
    )

    end_action: Union[Event, InstantaneousAction]
    if first_end_timing is None or not _is_end_timing(first_end_timing):
        end_action = add_new_event("end")
    else:
        assert has_variable_duration
        assert first_end_action is not None
        end_action = first_end_action

    end_action.add_effect(action_running, False)
    end_action.add_effect(action_clock, 0)
    if has_variable_duration:
        assert action_duration_exp is not None
        assert first_end_timing is not None
        end_action.add_effect(action_duration_exp, 0)
        if not _is_end_timing(first_end_timing):
            assert first_end_triggered is not None
            end_action.add_effect(first_end_triggered, False)
            # add precise time constraint
            clock_exp, timing_exp, additional_constraint = _get_relative_timing(
                EndTiming(),
                first_end_timing,
                first_end_triggered,
                action_clock,
                action_duration_exp,
                action.duration,
                mgr,
            )
            # use GE instead of Equals to avoid equality among floats
            time_constraint = mgr.GE(clock_exp, mgr.Plus(timing_exp, epsilon))
            if additional_constraint is not None:
                time_constraint = mgr.And(additional_constraint, time_constraint)
            end_action.add_precondition(simplifier.simplify(time_constraint))
    else:
        # use GE instead of Equals to avoid equality among floats
        duration_constraint = mgr.GE(
            action_clock, mgr.Plus(action.duration.lower, epsilon)
        )
        end_action.add_precondition(simplifier.simplify(duration_constraint))

    # conditions create an event that sets alive to False when violated
    for i, (interval, conditions) in enumerate(action.conditions.items()):
        assert isinstance(interval, TimeInterval)

        # check start timing
        if _is_start_timing(interval.lower) and not interval.is_left_open():
            start_action.add_precondition(mgr.And(conditions))
            if _is_start_timing(interval.upper) and not interval.is_right_open():
                continue

        # check first end timing
        operand = None
        from_start_timing = None
        if interval.lower == first_end_timing and interval.upper.is_from_start():
            operand = (
                mgr.GT
                if interval.is_right_open() and interval.is_left_open()
                else mgr.GE
            )
            from_start_timing = interval.upper
        elif interval.upper == first_end_timing and interval.lower.is_from_start():
            operand = (
                mgr.LT
                if interval.is_right_open() and interval.is_left_open()
                else mgr.LE
            )
            from_start_timing = interval.upper
        if operand is not None:
            assert from_start_timing is not None
            assert first_end_action is not None
            first_end_action.add_precondition(
                simplifier.simplify(
                    mgr.Or(
                        mgr.Not(operand(from_start_timing.delay, action_clock)),
                        mgr.And(conditions),
                    )
                )
            )
        elif first_end_timing is not None and _is_timepoint_interval(
            interval, first_end_timing
        ):
            assert first_end_action is not None
            first_end_action.add_precondition(simplifier.simplify(mgr.And(conditions)))
            continue

        # default case
        inside_interval = _inside_interval_condition(
            interval,
            first_end_timing,
            first_end_triggered,
            action_clock,
            action_duration_exp,
            action.duration,
            mgr,
        )
        fail_condition = mgr.Or(map(mgr.Not, conditions))
        condition_failed_event = add_new_event(f"condition_{i}_failed")
        condition_failed_event.add_precondition(simplifier.simplify(inside_interval))
        condition_failed_event.add_precondition(simplifier.simplify(fail_condition))
        condition_failed_event.add_effect(alive, False)
        condition_failed_event.add_effect(action_running, False)

    for i, (timing, effects) in enumerate(action.effects.items()):
        if _is_start_timing(timing):
            for eff in effects:
                start_action._add_effect_instance(eff)
            continue

        effect_ev_or_act: Union[Event, InstantaneousAction]
        if timing == first_end_timing:
            assert first_end_action is not None
            effect_ev_or_act = first_end_action
        elif _is_end_timing(timing):
            effect_ev_or_act = end_action
        else:
            # need to add a new event
            effect_ev_or_act = add_new_event(f"effects_{i}")
            clock_exp, timing_exp, additional_constraint = _get_relative_timing(
                timing,
                first_end_timing,
                first_end_triggered,
                action_clock,
                action_duration_exp,
                action.duration,
                mgr,
            )
            time_constraint = mgr.Equals(clock_exp, mgr.Plus(timing_exp, epsilon))
            if additional_constraint is not None:
                time_constraint = mgr.And(additional_constraint, time_constraint)
            effect_ev_or_act.add_precondition(simplifier.simplify(time_constraint))

            # add fluent to avoid infinite trigger of the event
            effect_done = add_new_fluent(
                f"effects_{i}_done",
                tm.BoolType(),
                mgr.FALSE(),
            )
            start_action.add_effect(effect_done, False)
            effect_ev_or_act.add_precondition(mgr.Not(effect_done))
            effect_ev_or_act.add_effect(effect_done, True)

        for eff in effects:
            effect_ev_or_act._add_effect_instance(eff)

    # add an event that sets alive to False if the duration of the action is exceeded
    # and the action is still running
    duration_exceeded_event = add_new_event("duration_exceeded_error")
    duration_exceeded_operand = mgr.GE if action.duration.is_right_open() else mgr.GT
    duration_exceeded_condition = duration_exceeded_operand(
        action_clock, mgr.Plus(action.duration.upper, 2 * epsilon)
    )
    duration_exceeded_event.add_precondition(
        simplifier.simplify(duration_exceeded_condition)
    )
    duration_exceeded_event.add_effect(alive, False)
    duration_exceeded_event.add_effect(action_running, False)

    # add an event that checks that the first_end_action is performed in time
    if has_variable_duration and not _is_end_timing(cast(Timing, first_end_timing)):
        assert first_end_timing is not None
        first_end_late_event = add_new_event("first_end_late_error")
        first_end_late_operand = mgr.GE if action.duration.is_right_open() else mgr.GT
        assert first_end_timing.delay <= 0
        first_end_late_condition = first_end_late_operand(
            action_clock,
            mgr.Plus(action.duration.upper, first_end_timing.delay),
        )
        first_end_late_event.add_precondition(
            simplifier.simplify(first_end_late_condition)
        )
        first_end_late_event.add_effect(alive, False)
        first_end_late_event.add_effect(action_running, False)

    for g in get_all_fluent_exp(new_problem, action_running.fluent()):
        new_problem.add_goal(mgr.Not(g))

    return start_action, first_end_action, first_end_timing


def _add_new_fluent(
    trailing_info: str,
    typename: Type,
    default_initial_value: ConstantExpression,
    new_problem: Problem,
    action: DurativeAction,
    params: OrderedDict[str, Type],
) -> FNode:
    fluent = Fluent(
        get_fresh_name(new_problem, action.name, trailing_info=trailing_info),
        typename,
        params,
        new_problem.environment,
    )
    new_problem.add_fluent(fluent, default_initial_value=default_initial_value)
    fluent_exp: FNode = fluent(*action.parameters)
    return fluent_exp


def _first_end_action_duration_constraint(
    action: DurativeAction,
    first_end_timing: Timing,
    action_clock: FNode,
    mgr: ExpressionManager,
) -> FNode:
    # duration constraint
    lower_operand = mgr.LT if action.duration.is_left_open() else mgr.LE
    upper_operand = mgr.LT if action.duration.is_right_open() else mgr.LE
    lower_bound = mgr.Plus(action.duration.lower, first_end_timing.delay)
    upper_bound = mgr.Plus(action.duration.upper, first_end_timing.delay)
    return mgr.And(
        lower_operand(lower_bound, action_clock),
        upper_operand(action_clock, upper_bound),
    )


def _add_new_event(
    trailing_info: str,
    new_problem: Problem,
    params: OrderedDict[str, Type],
    action: DurativeAction,
    alive: Fluent,
    action_running: FNode,
) -> Event:
    event = Event(
        get_fresh_name(new_problem, action.name, trailing_info=trailing_info),
        _parameters=params,
        _env=new_problem.environment,
    )
    new_problem.add_event(event)

    event.add_precondition(alive)
    event.add_precondition(action_running)
    return event


def _action_variable_duration(action: DurativeAction) -> bool:
    d = action.duration
    return d.is_left_open() or d.is_right_open() or d.lower != d.upper


def _get_first_end_timing(action: DurativeAction) -> Optional[Timing]:

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
            yield timing_or_interval.lower
            yield timing_or_interval.upper

    first_end_timing: Optional[Timing] = None
    for timing_or_interval, conds_or_effs in chain(
        action.conditions.items(), action.effects.items()
    ):
        assert isinstance(timing_or_interval, (Timing, TimeInterval))
        for timing in timing_from_interval(timing_or_interval, conds_or_effs):
            assert isinstance(
                timing, Timing
            ), f"Wrong durative action {action.name} typing associated to {conds_or_effs}"
            if timing.is_from_end():
                assert timing.delay <= 0
                if first_end_timing is None or first_end_timing.delay > timing.delay:
                    first_end_timing = timing

    return first_end_timing


def _get_relative_timing(
    timing: Timing,
    first_end_timing: Optional[Timing],
    first_end_triggered: Optional[FNode],
    action_clock: FNode,
    action_duration_exp: Optional[FNode],
    action_duration: DurationInterval,
    mgr: ExpressionManager,
) -> Tuple[FNode, Union[int, Fraction, FNode], Optional[FNode]]:
    assert not timing.is_global()
    if timing.is_from_start():
        return action_clock, timing.delay, None
    assert timing.delay <= 0
    if action_duration_exp is None:
        assert action_duration.lower == action_duration.upper
        # duration is not variable, so end_timing can be returned as timing from start
        return action_clock, mgr.Plus(action_duration.lower, timing.delay), None
    # complex case where the timing is from end and the action duration is variable
    assert action_duration_exp is not None and first_end_timing is not None
    return (
        mgr.Minus(action_clock, action_duration_exp),
        mgr.Minus(timing.delay, first_end_timing.delay),
        first_end_triggered,
    )


def _inside_interval_condition(
    interval: TimeInterval,
    first_end_timing: Optional[Timing],
    first_end_triggered: Optional[FNode],
    action_clock: FNode,
    action_duration_exp: Optional[FNode],
    action_duration: DurationInterval,
    mgr: ExpressionManager,
) -> FNode:
    # define a utility function to get the relative timing without passing 5 args that are the same
    relative_timing = partial(
        _get_relative_timing,
        first_end_timing=first_end_timing,
        first_end_triggered=first_end_triggered,
        action_clock=action_clock,
        action_duration_exp=action_duration_exp,
        action_duration=action_duration,
        mgr=mgr,
    )

    if interval.lower == interval.upper:
        if interval.is_left_open() or interval.is_right_open():
            return mgr.FALSE()
        (
            clock_expression,
            constant_time_expression,
            additonal_constraint,
        ) = relative_timing(interval.lower)
        exact_timing = mgr.Equals(clock_expression, constant_time_expression)
        if additonal_constraint is not None:
            exact_timing = mgr.And(additonal_constraint, exact_timing)
        return exact_timing

    left_clock_exp, left_timing_exp, left_additional_constraint = relative_timing(
        interval.lower
    )
    left_operand = mgr.GT if interval.is_left_open() else mgr.GE
    left_bound = left_operand(left_clock_exp, left_timing_exp)
    if left_additional_constraint is not None:
        left_bound = mgr.And(left_additional_constraint, left_bound)

    right_clock_exp, right_timing_exp, right_additional_constraint = relative_timing(
        interval.upper
    )
    right_operand = mgr.LT if interval.is_right_open() else mgr.LE
    right_bound = right_operand(right_clock_exp, right_timing_exp)
    if right_additional_constraint is not None:
        # right bound is active if the first_end has not been triggered yet OR
        # the end has been triggered and the constraint is valid
        right_bound = mgr.Or(
            mgr.Not(right_additional_constraint),
            right_bound,
        )

    return mgr.And(
        left_bound,
        right_bound,
    )


def _is_end_timing(timing: Timing) -> bool:
    return timing.is_from_end() and timing.delay == 0 and not timing.is_global()


def _is_start_timing(timing: Timing) -> bool:
    return timing.is_from_start() and timing.delay == 0 and not timing.is_global()


def _is_timepoint_interval(interval: TimeInterval, timing: Timing) -> bool:
    return (
        interval.lower == interval.upper == timing
        and not interval.is_left_open()
        and not interval.is_right_open()
    )


def _convert_action_costs(
    qm: MinimizeActionCosts,
    start_actions: Dict[Action, Action],
    first_end_actions: Dict[Action, Tuple[Action, Timing]],
) -> MinimizeActionCosts:
    new_costs: Dict[Action, Expression] = {}
    for compiled_action, original_action in start_actions.items():
        cost = qm.get_action_cost(original_action)
        if cost is not None:
            new_costs[compiled_action] = cost
    for compiled_action in first_end_actions.keys():
        new_costs[compiled_action] = 0
    return MinimizeActionCosts(new_costs, qm.default, qm.environment)


def _back_plan_to_plan(
    plan: TimeTriggeredPlan,
    start_actions: Dict[Action, Action],
    end_actions: Dict[Action, Tuple[Action, Timing]],
    simplifier: Simplifier,
) -> TimeTriggeredPlan:
    if not isinstance(plan, TimeTriggeredPlan):
        raise NotImplementedError()

    new_actions: Dict[
        Tuple[Action, Tuple[FNode, ...]],
        List[Tuple[Fraction, ActionInstance, Optional[Fraction]]],
    ] = defaultdict(list)
    for trigger_time, old_action_instance, _ in sorted(
        plan.timed_actions, key=lambda x: x[0]
    ):
        assert isinstance(old_action_instance, ActionInstance)
        old_action = old_action_instance.action
        if not isinstance(old_action, InstantaneousAction):
            raise NotImplementedError()
        parameters = old_action_instance.actual_parameters

        original_action = start_actions.get(old_action)
        # represents a start_action
        if original_action is not None:
            duration: Optional[Fraction] = None
            if isinstance(
                original_action, DurativeAction
            ) and not _action_variable_duration(original_action):
                # TODO this fails with fluents in duration
                # this is the hardest part about supporting fluents in duration:
                # to revert a plan you need to simulate it and know the value of the duration in the state where the action is started
                assert len(original_action.parameters) == len(parameters)
                subs: Dict[Expression, Expression] = dict(
                    zip(original_action.parameters, parameters)
                )
                duration_lower = simplifier.simplify(
                    original_action.duration.lower.substitute(subs)
                )
                assert duration_lower.is_constant(), duration_lower
                duration = Fraction(duration_lower.constant_value())
            new_actions[original_action, parameters].append(
                (trigger_time, original_action(*parameters), duration)
            )
            continue
        original_action, timing = end_actions.get(old_action, (None, None))
        if original_action is None:
            raise UPValueError(
                f"The action {old_action.name} in the given plan is neither a start_action or an end_action originated from the {DurativeActionToProcesses.__name__} compiler"
            )
        # represents a first_end action
        assert isinstance(original_action, DurativeAction)
        assert isinstance(timing, Timing)
        new_actions_list = new_actions[original_action, parameters]
        start_trigger_time, new_action_instance, duration = new_actions_list.pop()
        assert duration is None
        assert trigger_time >= start_trigger_time
        assert timing.delay <= 0
        duration = trigger_time - start_trigger_time - timing.delay
        new_actions_list.append((start_trigger_time, new_action_instance, duration))

    timed_actions: List[Tuple[Fraction, ActionInstance, Optional[Fraction]]] = []
    for trigger_time, action_instance, duration in chain(*new_actions.values()):
        if isinstance(action_instance.action, InstantaneousAction):
            assert duration is None
        elif isinstance(action_instance.action, DurativeAction):
            assert duration is not None
        else:
            raise NotImplementedError
        timed_actions.append((trigger_time, action_instance, duration))

    return TimeTriggeredPlan(timed_actions)


def _forward_plan_to_plan(
    plan: TimeTriggeredPlan,
    start_actions_forward: Dict[Action, Action],
    end_actions_forward: Dict[Action, Tuple[Action, Timing]],
    environment: Environment,
) -> TimeTriggeredPlan:
    if not isinstance(plan, TimeTriggeredPlan):
        raise NotImplementedError()

    actions: List[Tuple[Fraction, ActionInstance, Optional[Fraction]]] = []
    original_action_instance: ActionInstance
    for trigger_time, original_action_instance, duration in plan.timed_actions:
        original_action, params = (
            original_action_instance.action,
            original_action_instance.actual_parameters,
        )
        compiled_start_action = start_actions_forward[original_action]
        assert isinstance(compiled_start_action, InstantaneousAction)
        actions.append((trigger_time, compiled_start_action(*params), None))

        compiled_end_action, first_end_timing = end_actions_forward.get(
            original_action, (None, None)
        )
        if compiled_end_action is not None:
            assert first_end_timing is not None and duration is not None
            end_trigger_time_delay = duration + first_end_timing.delay
            assert 0 < end_trigger_time_delay <= duration
            end_trigger_time = trigger_time + end_trigger_time_delay
            actions.append((end_trigger_time, compiled_end_action(*params), None))

    return TimeTriggeredPlan(actions, environment)
