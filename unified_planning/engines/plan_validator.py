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


from typing import Optional
import unified_planning as up
import unified_planning.environment
import unified_planning.engines as engines
import unified_planning.engines.mixins as mixins
import unified_planning.model.walkers as walkers
from unified_planning.model import (
    AbstractProblem,
    Problem,
    ProblemKind,
    State,
)
from unified_planning.engines.results import (
    ValidationResult,
    ValidationResultStatus,
    LogMessage,
    LogLevel,
)
from unified_planning.engines.sequential_simulator import (
    UPSequentialSimulator,
    evaluate_quality_metric,
    evaluate_quality_metric_in_initial_state,
)
from unified_planning.plans import SequentialPlan, PlanKind
from unified_planning.exceptions import (
    UPConflictingEffectsException,
    UPUsageError,
    UPProblemDefinitionError,
)


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
        self.manager = self._env.expression_manager
        self._substituter = walkers.Substituter(self._env)

    @property
    def name(self):
        return "sequential_plan_validator"

    @staticmethod
    def supports_plan(plan_kind: "up.plans.PlanKind") -> bool:
        return plan_kind == PlanKind.SEQUENTIAL_PLAN

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind()
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_numbers("CONTINUOUS_NUMBERS")
        supported_kind.set_numbers("DISCRETE_NUMBERS")
        supported_kind.set_numbers("BOUNDED_TYPES")
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
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("TEMPORAL_OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("MAKESPAN")
        supported_kind.set_quality_metrics("FINAL_VALUE")
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
        simulator = UPSequentialSimulator(problem)
        prev_state: Optional[State] = simulator.get_initial_state()
        if metric is not None:
            metric_value = evaluate_quality_metric_in_initial_state(simulator, metric)
        msg = None
        last_executed_action = None
        for i, ai in enumerate(plan.actions):
            assert prev_state is not None
            try:
                unsat_conds = simulator.get_unsatisfied_conditions(prev_state, ai)
            except UPConflictingEffectsException as e:
                msg = f"{str(i)}-th action instance {str(ai)} creates conflicting effects: {str(e)}"
            except UPUsageError as e:
                msg = f"{str(i)}-th action instance {str(ai)} creates a UsageError: {str(e)}"
            if unsat_conds:
                msg = f"Preconditions {unsat_conds} of {str(i)}-th action instance {str(ai)} are not satisfied."
            next_state = simulator.apply_unsafe(prev_state, ai)
            if next_state is None:
                msg = f"{str(i)}-th action instance {str(ai)} creates conflicting effects."
            if msg is not None:
                logs = [LogMessage(LogLevel.INFO, msg)]
                return ValidationResult(
                    ValidationResultStatus.INVALID,
                    self.name,
                    logs,
                    None,
                    last_executed_action,
                )
            assert next_state is not None
            if metric is not None:
                metric_value = evaluate_quality_metric(
                    simulator,
                    metric,
                    metric_value,
                    prev_state,
                    ai.action,
                    ai.actual_parameters,
                    next_state,
                )
            last_executed_action = ai
            prev_state = next_state
        assert next_state is not None
        unsatisfied_goals = simulator.get_unsatisfied_goals(next_state)
        if not unsatisfied_goals:
            metric_evalutations = None
            if metric is not None:
                metric_evalutations = {metric: metric_value}
            logs = []
            return ValidationResult(
                ValidationResultStatus.VALID, self.name, logs, metric_evalutations
            )
        else:
            msg = f"Goals {unsatisfied_goals} are not satisfied by the plan."
            logs = [LogMessage(LogLevel.INFO, msg)]
            return ValidationResult(
                ValidationResultStatus.INVALID,
                self.name,
                logs,
                None,
                last_executed_action,
            )
