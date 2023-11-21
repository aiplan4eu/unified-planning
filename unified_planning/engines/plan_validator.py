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
from typing import Dict, List, Optional, Tuple, cast
import warnings
import unified_planning as up
import unified_planning.environment
import unified_planning.engines as engines
import unified_planning.engines.mixins as mixins
from unified_planning.model.action import InstantaneousAction
from unified_planning.model.effect import Effect
from unified_planning.model.fnode import FNode
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
        effects: List[Tuple[List[Effect], ActionInstance]],
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
        trace: Dict[Fraction, UPState],
        start: Fraction,
        end: Fraction,
        open_interval: bool,
    ) -> UPState:
        print("*" * 80)
        print(["%.2f" % float(x) for x in trace.keys()])
        print(("%.2f" % start, "%.2f" % end, open_interval))
        before_time = -1
        equal_time = -1
        inside_indexes = []
        for x in trace:
            if x < start and x > before_time:
                before_time = x
            if x <= start and x > equal_time:
                equal_time = x
            if start < x < end:
                inside_indexes.append(x)

        print(inside_indexes)
        print(before_time)
        print(equal_time)
        print("*" * 80)

        if not open_interval:
            yield before_time, trace[before_time]
        if equal_time != before_time and equal_time != end:
            yield equal_time, trace[equal_time]
        for x in inside_indexes:
            yield x, trace[x]

    def check_condition(
        self, state: UPState, se: StateEvaluator, condition: FNode
    ) -> bool:
        return se.evaluate(condition, state=state).bool_constant_value()

    def _instantiate_timing(
        self, timing: Timing, action_start: Fraction, action_duration: Fraction
    ) -> Fraction:
        if timing.is_from_start():
            return action_start + timing.delay
        else:
            return action_start + action_duration + timing.delay

    def _instantiate_interval(
        self, interval: TimeInterval, action_start: Fraction, action_duration: Fraction
    ) -> Tuple[Fraction, Fraction, bool]:
        return (
            self._instantiate_timing(interval.lower, action_start, action_duration),
            self._instantiate_timing(interval.upper, action_start, action_duration),
            interval.is_left_open(),
        )

    def ground_expression(self, formula: FNode, ai: ActionInstance) -> FNode:
        params = {}
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

        start_actions = list(plan.timed_actions)
        start_actions.sort(key=lambda x: (x[0], x[2]), reverse=True)

        scheduled_effects = []  # TODO: add TILs
        durative_conditions = []  # TODO: add Timed Goals

        time = 0
        last_state = UPState(problem.initial_values)
        trace = {-1: last_state}
        effect_id = 0
        while len(start_actions) + len(scheduled_effects) > 0:
            if start_actions and (
                len(scheduled_effects) == 0
                or start_actions[-1][0] <= scheduled_effects[0][0]
            ):
                start_time, ai, duration = start_actions.pop()
                for timing, event in ai.action.effects.items():
                    real_timing = self._instantiate_timing(timing, start_time, duration)
                    heapq.heappush(
                        scheduled_effects, (real_timing, effect_id, event, ai)
                    )
                    effect_id += 1
                for interval, conditions in ai.action.conditions.items():
                    real_interval = self._instantiate_interval(
                        interval, start_time, duration
                    )
                    for c in conditions:
                        durative_conditions.append(
                            (
                                real_interval,
                                effect_id,
                                self.ground_expression(c, ai),
                                ai,
                            )
                        )
                        effect_id += 1
                time = start_time

            elif scheduled_effects:
                time = scheduled_effects[0][0]
                effects = []
                while scheduled_effects and scheduled_effects[0][0] == time:
                    _, _, add_effs, ai = heapq.heappop(scheduled_effects)
                    effects.append((add_effs, ai))
                print("%s -> %s" % (time, effects))
                new_state = self.apply_effects(last_state, se, effects)
                trace[time] = new_state
                last_state = new_state

        print("*" * 80)
        print(trace)

        print(problem)
        print(plan)

        # Check (durative) conditions
        for (start, end, is_open), _, c, ai in durative_conditions:
            for t, state in self.states_in_interval(trace, start, end, is_open):
                print((t, state))
                if not self.check_condition(state=state, se=se, condition=c):
                    return ValidationResult(
                        status=ValidationResultStatus.INVALID,
                        engine_name=self.name,
                        log_messages="",
                        metric_evaluations=None,
                        reason=FailedValidationReason.INAPPLICABLE_ACTION,
                        inapplicable_action=ai,
                        trace=trace,
                    )

        return ValidationResult(
            ValidationResultStatus.VALID,
            self.name,
            "",
            None,
            trace=trace,
        )
