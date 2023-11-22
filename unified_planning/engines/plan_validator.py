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
from typing import Any, Dict, Generator, List, Optional, Tuple, cast
import warnings
import unified_planning as up
import unified_planning.environment
import unified_planning.engines as engines
import unified_planning.engines.mixins as mixins
from unified_planning.model.action import DurativeAction, InstantaneousAction
from unified_planning.model.effect import Effect
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
        return UPSequentialSimulator.supported_kind()

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
            except UPUsageError as e:
                msg = f"{str(i)}-th action instance {str(ai)} creates a UsageError: {str(e)}"
            except UPInvalidActionError as e:
                msg = f"{str(i)}-th action instance {str(ai)} creates an Invalid Action: {str(e)}"
            try:
                next_state = simulator.apply_unsafe(trace[-1], ai)
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
        kind.set_expression_duration("STATIC_FLUENTS_IN_DURATIONS")
        return kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= SequentialPlanValidator.supported_kind()

    # TODO: support simulated effects, action parameters and quantifiers
    def apply_effects(
        self,
        state: UPState,
        se: StateEvaluator,
        effects: List[Tuple[List[Effect], Optional[ActionInstance]]],
    ) -> UPState:
        updates: Dict[FNode, FNode] = {}
        for effs, ai in effects:
            for eff in effs:
                if self.check_condition(
                    state, se, self.ground_expression(eff.condition, ai)
                ):
                    g_fluent = self.ground_expression(eff.fluent, ai)
                    g_value = self.ground_expression(eff.value, ai)
                    if g_fluent in updates:
                        raise RuntimeError("Double effect")
                    updates[g_fluent] = se.evaluate(g_value, state=state)
        return state.make_child(updated_values=updates)

    def states_in_interval(
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

    def check_condition(
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

    def ground_expression(self, formula: FNode, ai: Optional[ActionInstance]) -> FNode:
        if ai is None:
            return formula
        else:
            params: Any = {}
            for p, ap in zip(ai.action.parameters, ai.actual_parameters):
                params[p] = ap
            return formula.substitute(params)

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

        se = StateEvaluator(problem=problem)

        start_actions: List[Tuple[Fraction, ActionInstance, Optional[Fraction]]] = list(
            plan.timed_actions
        )
        start_actions.sort(key=lambda x: (x[0], x[2]), reverse=True)

        scheduled_effects: List[
            Tuple[Fraction, int, List[Effect], Optional[ActionInstance]]
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
                        action_duration=plan_duration,
                    ),
                    next_id,
                    effects,
                    None,
                )
            )
            next_id += 1

        for interval, goals in problem.timed_goals.items():
            for g in goals:
                durative_conditions.append(
                    (
                        self._instantiate_interval(
                            interval=interval,
                            action_start=Fraction(0),
                            action_duration=plan_duration,
                        ),
                        next_id,
                        g,
                        None,
                    )
                )
                next_id += 1

        time = Fraction(0)
        last_state = UPState(problem.initial_values)
        trace: Dict[Fraction, State] = {Fraction(-1): last_state}
        while len(start_actions) + len(scheduled_effects) > 0:
            if start_actions and (
                len(scheduled_effects) == 0
                or start_actions[-1][0] <= scheduled_effects[0][0]
            ):
                start_time, ai, duration = start_actions.pop()
                da = cast(DurativeAction, ai.action)
                for timing, event in da.effects.items():
                    real_timing = self._instantiate_timing(
                        timing=timing, action_start=start_time, action_duration=duration
                    )
                    heapq.heappush(scheduled_effects, (real_timing, next_id, event, ai))
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
                                self.ground_expression(formula=c, ai=ai),
                                ai,
                            )
                        )
                        next_id += 1
                time = start_time

            elif scheduled_effects:
                time = scheduled_effects[0][0]
                now_effects: List[Tuple[List[Effect], Optional[ActionInstance]]] = []
                while scheduled_effects and scheduled_effects[0][0] == time:
                    _, _, add_effs, opt_ai = heapq.heappop(scheduled_effects)
                    now_effects.append((add_effs, opt_ai))
                new_state = self.apply_effects(
                    state=last_state, se=se, effects=now_effects
                )
                trace[time] = new_state
                last_state = new_state

        # Check (durative) conditions
        for (start, end, is_open), _, c, opt_ai in durative_conditions:
            for t, state in self.states_in_interval(
                trace=trace, start=start, end=end, open_interval=is_open
            ):
                if not self.check_condition(state=state, se=se, condition=c):
                    if opt_ai is not None:
                        return ValidationResult(
                            status=ValidationResultStatus.INVALID,
                            engine_name=self.name,
                            log_messages=None,
                            metric_evaluations=None,
                            reason=FailedValidationReason.INAPPLICABLE_ACTION,
                            inapplicable_action=opt_ai,
                            trace=trace,
                        )
                    else:
                        return ValidationResult(
                            status=ValidationResultStatus.INVALID,
                            engine_name=self.name,
                            log_messages=None,
                            metric_evaluations=None,
                            reason=FailedValidationReason.UNSATISFIED_GOALS,
                            inapplicable_action=None,
                            trace=trace,
                        )

        for g in problem.goals:
            if not self.check_condition(state=last_state, se=se, condition=g):
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
