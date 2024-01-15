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


from collections import OrderedDict
from dataclasses import dataclass
from fractions import Fraction
import heapq
from typing import Any, Dict, Generator, List, Optional, Set, Tuple, cast
import warnings
import unified_planning as up
import unified_planning.environment
import unified_planning.engines as engines
import unified_planning.engines.mixins as mixins
from unified_planning.model.action import DurativeAction, InstantaneousAction
from unified_planning.model.effect import Effect, EffectKind, SimulatedEffect
from unified_planning.model.fnode import FNode
from unified_planning.model.parameter import Parameter
from unified_planning.model.state import UPState
from unified_planning.model.timing import TimeInterval, TimepointKind, Timing
import unified_planning.model.walkers as walkers
from unified_planning.model import (
    AbstractProblem,
    Problem,
    ProblemKind,
    State,
)
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.engines.results import (
    ValidationResult,
    ValidationResultStatus,
    LogMessage,
    LogLevel,
    FailedValidationReason,
)
from unified_planning.engines.sequential_simulator import (
    InapplicabilityReasons,
    UPSequentialSimulator,
    evaluate_quality_metric,
    evaluate_quality_metric_in_initial_state,
)
from unified_planning.model.walkers.state_evaluator import StateEvaluator
from unified_planning.plans import SequentialPlan, PlanKind
from unified_planning.exceptions import (
    UPConflictingEffectsException,
    UPUsageError,
    UPProblemDefinitionError,
    UPInvalidActionError,
)
from unified_planning.plans.plan import ActionInstance
from unified_planning.plans.time_triggered_plan import TimeTriggeredPlan


class SequentialPlanValidator(engines.engine.Engine, mixins.PlanValidatorMixin):
    """
    Performs :class:`~unified_planning.plans.Plan` validation.

    If the given :class:`~unified_planning.model.Problem` has any quality metric,
    the metric is simply ignored because it predicates over the Optimality of
    the Plan, but not the Validity!
    """

    def __init__(self, **options):
        engines.engine.Engine.__init__(self)
        mixins.PlanValidatorMixin.__init__(self)
        self._env: "unified_planning.environment.Environment" = (
            unified_planning.environment.get_environment(
                options.get("environment", None)
            )
        )

    @property
    def name(self):
        return "sequential_plan_validator"

    @staticmethod
    def supports_plan(plan_kind: "up.plans.PlanKind") -> bool:
        return plan_kind == PlanKind.SEQUENTIAL_PLAN

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = UPSequentialSimulator.supported_kind()
        supported_kind.set_parameters("UNBOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("REAL_ACTION_PARAMETERS")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= SequentialPlanValidator.supported_kind()

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
        assert isinstance(plan, SequentialPlan)
        assert isinstance(problem, Problem)
        metric = None
        if len(problem.quality_metrics) > 0:
            if len(problem.quality_metrics) == 1:
                metric = problem.quality_metrics[0]
            else:
                raise UPProblemDefinitionError(
                    "The UP does not support more than one quality metric in the problem."
                )
        # To support infinite domain action's parameters the checks on the simulator must be disabled
        # and, if the problem is not supported for different reasons, re-raise the warning/exception
        with warnings.catch_warnings(record=True) as _:
            simulator = UPSequentialSimulator(problem, error_on_failed_checks=False)
        kind = problem.kind
        kind.unset_parameters("UNBOUNDED_INT_ACTION_PARAMETERS")
        kind.unset_parameters("REAL_ACTION_PARAMETERS")
        if not self.skip_checks and not simulator.supports(kind):
            msg: Optional[
                str
            ] = f"We cannot establish whether {self.name} can validate this problem!"
            if self.error_on_failed_checks:
                raise up.exceptions.UPUsageError(msg)
            else:
                warnings.warn(cast(str, msg))
        if metric is not None:
            metric_value = evaluate_quality_metric_in_initial_state(simulator, metric)
        msg = None
        trace: List[State] = [simulator.get_initial_state()]
        for i, ai in zip(range(1, len(plan.actions) + 1), plan.actions):
            try:
                unsat_conds, reason = simulator.get_unsatisfied_conditions(
                    trace[-1], ai
                )
                if unsat_conds:
                    assert reason == InapplicabilityReasons.VIOLATES_CONDITIONS
                    msg = f"Preconditions {unsat_conds} of {str(i)}-th action instance {str(ai)} are not satisfied."
                else:
                    next_state = simulator.apply_unsafe(trace[-1], ai)
            except UPUsageError as e:
                msg = f"{str(i)}-th action instance {str(ai)} creates a UsageError: {str(e)}"
            except UPInvalidActionError as e:
                msg = f"{str(i)}-th action instance {str(ai)} creates an Invalid Action: {str(e)}"
            except UPConflictingEffectsException as e:
                msg = f"{str(i)}-th action instance {str(ai)} creates Conflicting Effects: {str(e)}"
            if msg is not None:
                logs = [LogMessage(LogLevel.INFO, msg)]
                return ValidationResult(
                    status=ValidationResultStatus.INVALID,
                    engine_name=self.name,
                    log_messages=logs,
                    metric_evaluations=None,
                    reason=FailedValidationReason.INAPPLICABLE_ACTION,
                    inapplicable_action=ai,
                    trace=trace,
                )
            assert next_state is not None
            if metric is not None:
                metric_value = evaluate_quality_metric(
                    simulator,
                    metric,
                    metric_value,
                    trace[-1],
                    ai.action,
                    ai.actual_parameters,
                    next_state,
                )
            trace.append(next_state)

        unsatisfied_goals = simulator.get_unsatisfied_goals(trace[-1])
        if not unsatisfied_goals:
            metric_evalutations = None
            if metric is not None:
                metric_evalutations = {metric: metric_value}
            logs = []
            return ValidationResult(
                ValidationResultStatus.VALID,
                self.name,
                logs,
                metric_evalutations,
                trace=trace,
            )
        else:
            msg = f"Goals {unsatisfied_goals} are not satisfied by the plan."
            logs = [LogMessage(LogLevel.INFO, msg)]
            return ValidationResult(
                ValidationResultStatus.INVALID,
                self.name,
                logs,
                None,
                FailedValidationReason.UNSATISFIED_GOALS,
                trace=trace,
            )


class TimeTriggeredPlanValidator(engines.engine.Engine, mixins.PlanValidatorMixin):
    """
    Performs :class:`~unified_planning.plans.Plan` validation.

    If the given :class:`~unified_planning.model.Problem` has any quality metric,
    the metric is simply ignored because it predicates over the Optimality of
    the Plan, but not the Validity!
    """

    def __init__(self, **options):
        engines.engine.Engine.__init__(self)
        mixins.PlanValidatorMixin.__init__(self)
        self._env: "unified_planning.environment.Environment" = (
            unified_planning.environment.get_environment(
                options.get("environment", None)
            )
        )

    @property
    def name(self):
        return "time_triggered_plan_validator"

    @staticmethod
    def supports_plan(plan_kind: "up.plans.PlanKind") -> bool:
        return plan_kind == PlanKind.TIME_TRIGGERED_PLAN

    @staticmethod
    def supported_kind() -> ProblemKind:
        kind = UPSequentialSimulator.supported_kind().clone()
        kind.set_time("CONTINUOUS_TIME")
        kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
        kind.set_time("TIMED_EFFECTS")
        kind.set_time("TIMED_GOALS")
        kind.set_time("DURATION_INEQUALITIES")
        kind.set_time("SELF_OVERLAPPING")
        kind.set_expression_duration("STATIC_FLUENTS_IN_DURATIONS")
        kind.set_expression_duration("FLUENTS_IN_DURATIONS")
        kind.set_expression_duration("INT_TYPE_DURATIONS")
        kind.set_expression_duration("REAL_TYPE_DURATIONS")
        kind.set_parameters("UNBOUNDED_INT_ACTION_PARAMETERS")
        kind.set_parameters("REAL_ACTION_PARAMETERS")
        return kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= TimeTriggeredPlanValidator.supported_kind()

    def _apply_effects(
        self,
        state: UPState,
        se: StateEvaluator,
        effects: List[
            Tuple[List[Effect], Optional[SimulatedEffect], Optional[ActionInstance]]
        ],
        problem: Problem,
    ) -> UPState:
        updates: Dict[FNode, FNode] = {}
        assigned: Dict[FNode, Optional[ActionInstance]] = {}
        for effs, sim_eff, ai in effects:
            for eff in effs:
                changes = self._apply_effect(state, se, ai, eff, updates, problem)
                for f, v in changes.items():
                    if f in assigned or (f in updates and eff.is_assignment()):
                        if f.type.is_bool_type() and assigned[f] == ai:
                            # Handle "delete before add" semantics
                            if v.bool_constant_value():
                                updates[f] = v
                        else:
                            raise UPConflictingEffectsException("Double effect")
                    else:
                        updates[f] = v
                        if eff.is_assignment():
                            assigned[f] = ai
            if sim_eff is not None:
                assert ai is not None
                fluents = [self._ground_expression(f, ai) for f in sim_eff.fluents]
                values = sim_eff.function(
                    problem,
                    state,
                    dict(zip(ai.action.parameters, ai.actual_parameters)),
                )
                for f, v in zip(fluents, values):
                    if f in updates:
                        if f.type.is_bool_type() and assigned[f] == ai:
                            # Handle "delete before add" semantics
                            if v.bool_constant_value():
                                updates[f] = v
                        else:
                            raise UPConflictingEffectsException("Double effect")
                    else:
                        updates[f] = v
                        assigned[f] = ai
        return state.make_child(updated_values=updates)

    def _apply_effect(
        self,
        state: State,
        se: StateEvaluator,
        ai: Optional[ActionInstance],
        effect: Effect,
        updates: Dict[FNode, FNode],
        problem: Problem,
    ) -> Dict[FNode, FNode]:
        result = {}
        for instantiated_effect in effect.expand_effect(problem):
            if self._check_condition(
                state, se, self._ground_expression(instantiated_effect.condition, ai)
            ):
                g_fluent = self._ground_expression(instantiated_effect.fluent, ai)
                g_value = self._ground_expression(instantiated_effect.value, ai)
                f_value = (
                    updates[g_fluent]
                    if g_fluent in updates
                    else state.get_value(g_fluent)
                )
                if instantiated_effect.kind == EffectKind.ASSIGN:
                    result[g_fluent] = se.evaluate(g_value, state=state)
                elif instantiated_effect.kind == EffectKind.DECREASE:
                    result[g_fluent] = f_value - se.evaluate(g_value, state=state)
                elif instantiated_effect.kind == EffectKind.INCREASE:
                    result[g_fluent] = f_value - se.evaluate(g_value, state=state)
        return result

    def _states_in_interval(
        self,
        trace: Dict[Fraction, State],
        start: Fraction,
        end: Fraction,
        open_interval: bool,
    ) -> Generator[Tuple[Fraction, State], None, None]:
        before_time = Fraction(-1)
        equal_time = Fraction(-1)
        inside_indexes = []
        for x in trace:
            if x < start and x > before_time:
                before_time = x
            if x <= start and x > equal_time:
                equal_time = x
            if start < x < end:
                inside_indexes.append(x)

        if not open_interval:
            yield before_time, trace[before_time]
        if equal_time != before_time and equal_time != end:
            yield equal_time, trace[equal_time]
        for x in inside_indexes:
            yield x, trace[x]

    def _check_condition(
        self, state: State, se: StateEvaluator, condition: FNode
    ) -> bool:
        return se.evaluate(condition, state=state).bool_constant_value()

    def _instantiate_timing(
        self,
        timing: Timing,
        action_start: Fraction,
        action_duration: Optional[Fraction],
    ) -> Fraction:
        if timing.is_from_start():
            return action_start + timing.delay
        else:
            assert action_duration is not None
            return action_start + action_duration + timing.delay

    def _instantiate_interval(
        self,
        interval: TimeInterval,
        action_start: Fraction,
        action_duration: Optional[Fraction],
    ) -> Tuple[Fraction, Fraction, bool]:
        return (
            self._instantiate_timing(interval.lower, action_start, action_duration),
            self._instantiate_timing(interval.upper, action_start, action_duration),
            interval.is_left_open(),
        )

    def _ground_expression(self, formula: FNode, ai: Optional[ActionInstance]) -> FNode:
        if ai is None:
            return formula
        else:
            return formula.substitute(
                dict(zip(ai.action.parameters, ai.actual_parameters))
            )

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
        assert isinstance(plan, TimeTriggeredPlan)
        assert isinstance(problem, Problem)

        em = problem.environment.expression_manager
        se = StateEvaluator(problem=problem)

        start_actions: List[Tuple[Fraction, ActionInstance, Optional[Fraction]]] = list(
            plan.timed_actions
        )
        start_actions.sort(key=lambda x: x[0], reverse=True)

        scheduled_effects: List[
            Tuple[
                Fraction,
                int,
                List[Effect],
                Optional[SimulatedEffect],
                Optional[ActionInstance],
            ]
        ] = []
        durative_conditions: List[
            Tuple[Tuple[Fraction, Fraction, bool], int, FNode, Optional[ActionInstance]]
        ] = []

        plan_duration: Fraction = max(
            x[0] + (x[2] if x[2] else 0) for x in start_actions
        )

        next_id = 0
        for timing, effects in problem.timed_effects.items():
            scheduled_effects.append(
                (
                    self._instantiate_timing(
                        timing=timing,
                        action_start=Fraction(0),
                        action_duration=None,
                    ),
                    next_id,
                    effects,
                    None,
                    None,
                )
            )
            plan_duration = max(plan_duration, scheduled_effects[-1][0])
            next_id += 1

        for interval, goals in problem.timed_goals.items():
            iint = self._instantiate_interval(
                interval=interval,
                action_start=Fraction(0),
                action_duration=None,
            )
            plan_duration = max(plan_duration, iint[0], iint[1])
            for g in goals:
                durative_conditions.append(
                    (
                        iint,
                        next_id,
                        g,
                        None,
                    )
                )
                next_id += 1

        for invariant in problem.state_invariants:
            durative_conditions.append(
                (
                    (Fraction(0), plan_duration, False),
                    next_id,
                    invariant,
                    None,
                )
            )
            next_id += 1

        time = Fraction(0)
        last_state = UPState(problem.initial_values)
        trace: Dict[Fraction, State] = {Fraction(-1): last_state}
        scheduled_effects.sort(key=lambda x: x[0])
        while len(start_actions) + len(scheduled_effects) > 0:
            if start_actions and (
                len(scheduled_effects) == 0
                or start_actions[-1][0] <= scheduled_effects[0][0]
            ):
                start_time, ai, duration = start_actions.pop()
                if isinstance(ai.action, DurativeAction):
                    da = cast(DurativeAction, ai.action)
                    assert duration is not None
                    if da.duration.is_left_open():
                        lc = em.GT(duration, da.duration.lower)
                    else:
                        lc = em.GE(duration, da.duration.lower)
                    if da.duration.is_right_open():
                        uc = em.LT(duration, da.duration.upper)
                    else:
                        uc = em.LE(duration, da.duration.upper)
                    durative_conditions.append(
                        (
                            (start_time, start_time, False),
                            next_id,
                            self._ground_expression(formula=em.And(lc, uc), ai=ai),
                            ai,
                        )
                    )
                    next_id += 1
                    for timing, event in da.effects.items():
                        real_timing = self._instantiate_timing(
                            timing=timing,
                            action_start=start_time,
                            action_duration=duration,
                        )
                        heapq.heappush(
                            scheduled_effects, (real_timing, next_id, event, None, ai)
                        )
                        next_id += 1
                    for timing, sim_eff in da.simulated_effects.items():
                        real_timing = self._instantiate_timing(
                            timing=timing,
                            action_start=start_time,
                            action_duration=duration,
                        )
                        eff: List[Effect] = []
                        heapq.heappush(
                            scheduled_effects, (real_timing, next_id, eff, sim_eff, ai)
                        )
                        next_id += 1
                    for interval, conditions in da.conditions.items():
                        real_interval = self._instantiate_interval(
                            interval=interval,
                            action_start=start_time,
                            action_duration=duration,
                        )
                        for c in conditions:
                            durative_conditions.append(
                                (
                                    real_interval,
                                    next_id,
                                    self._ground_expression(formula=c, ai=ai),
                                    ai,
                                )
                            )
                            next_id += 1
                elif isinstance(ai.action, InstantaneousAction):
                    a = cast(InstantaneousAction, ai.action)
                    heapq.heappush(
                        scheduled_effects,
                        (start_time, next_id, a.effects, a.simulated_effect, ai),
                    )
                    next_id += 1
                    for c in a.preconditions:
                        durative_conditions.append(
                            (
                                (start_time, start_time, False),
                                next_id,
                                self._ground_expression(formula=c, ai=ai),
                                ai,
                            )
                        )
                        next_id += 1
                else:
                    raise NotImplementedError
                time = start_time

            elif scheduled_effects:
                time = scheduled_effects[0][0]
                now_effects: List[
                    Tuple[
                        List[Effect],
                        Optional[SimulatedEffect],
                        Optional[ActionInstance],
                    ]
                ] = []
                while scheduled_effects and scheduled_effects[0][0] == time:
                    _, _, add_effs, add_sim_effs, opt_ai = heapq.heappop(
                        scheduled_effects
                    )
                    now_effects.append((add_effs, add_sim_effs, opt_ai))
                try:
                    new_state = self._apply_effects(
                        state=last_state, se=se, effects=now_effects, problem=problem
                    )
                except UPConflictingEffectsException as e:
                    logs = [
                        LogMessage(LogLevel.INFO, f"Conflicting effects at time {time}")
                    ]
                    return ValidationResult(
                        status=ValidationResultStatus.INVALID,
                        engine_name=self.name,
                        log_messages=logs,
                        metric_evaluations=None,
                        reason=FailedValidationReason.INAPPLICABLE_ACTION,
                        inapplicable_action=opt_ai,
                        trace=trace,
                    )
                trace[time] = new_state
                last_state = new_state

        # Check (durative) conditions
        for (start, end, is_open), _, c, opt_ai in durative_conditions:
            for t, state in self._states_in_interval(
                trace=trace, start=start, end=end, open_interval=is_open
            ):
                if not self._check_condition(state=state, se=se, condition=c):
                    if opt_ai is not None:
                        return ValidationResult(
                            status=ValidationResultStatus.INVALID,
                            engine_name=self.name,
                            log_messages=None,
                            metric_evaluations=None,
                            reason=FailedValidationReason.INAPPLICABLE_ACTION,
                            inapplicable_action=opt_ai,
                            trace={k: v for k, v in trace.items() if k <= end},
                        )
                    else:
                        return ValidationResult(
                            status=ValidationResultStatus.INVALID,
                            engine_name=self.name,
                            log_messages=None,
                            metric_evaluations=None,
                            reason=FailedValidationReason.UNSATISFIED_GOALS,
                            inapplicable_action=None,
                            trace={k: v for k, v in trace.items() if k <= end},
                        )

        for g in problem.goals:
            if not self._check_condition(state=last_state, se=se, condition=g):
                return ValidationResult(
                    status=ValidationResultStatus.INVALID,
                    engine_name=self.name,
                    log_messages=None,
                    metric_evaluations=None,
                    reason=FailedValidationReason.UNSATISFIED_GOALS,
                    inapplicable_action=None,
                    trace=trace,
                )

        return ValidationResult(
            status=ValidationResultStatus.VALID,
            engine_name=self.name,
            log_messages=None,
            metric_evaluations=None,
            trace=trace,
        )
