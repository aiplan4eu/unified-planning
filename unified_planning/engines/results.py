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
"""This module defines the PlanGenerationResult class."""


from collections import OrderedDict
from fractions import Fraction
import unified_planning as up
from unified_planning.exceptions import UPUsageError, UPValueError
from unified_planning.model import AbstractProblem, Problem, PlanQualityMetric
from unified_planning.plans import ActionInstance, TimeTriggeredPlan, Plan
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, Optional, List, Union, cast


class ValidationResultStatus(Enum):
    """
    Enum representing the 3 possible values in the `status` field of a :class:`~unified_planning.engines.ValidationResult`:
    VALID, INVALID or UNKNOWN.
    """

    VALID = (
        auto()
    )  # The plan is valid for the problem, it satisfies all the hard constraints
    INVALID = (
        auto()
    )  # The plan is invalid for the problem, it does not satisfy all the hard constraints
    UNKNOWN = (
        auto()
    )  # The planner can't tell if the plan is valid or invalid for the given problem

    def __bool__(self):
        if self == ValidationResultStatus.VALID:
            return True
        else:
            return False


class FailedValidationReason(Enum):
    """Enum representing the possible reasons the plan validation failed."""

    INAPPLICABLE_ACTION = auto()
    UNSATISFIED_GOALS = auto()
    MUTEX_CONFLICT = auto()


class PlanGenerationResultStatus(Enum):
    """
    Enum representing the 9 possible values in the status field of a :class:`~unified_planning.engines.PlanGenerationResult`:
    SOLVED_SATISFICING        -> Valid plan found.
    SOLVED_OPTIMALLY          -> Optimal plan found.
    UNSOLVABLE_PROVEN         -> The problem is impossible, no valid plan exists.
    UNSOLVABLE_INCOMPLETELY   -> The planner could not find a plan, but it's not sure that
    the problem is impossible (The planner is incomplete)
    TIMEOUT                   -> The planner ran out of time
    MEMOUT                    -> The planner ran out of memory
    INTERNAL_ERROR            -> The planner had an internal error
    UNSUPPORTED_PROBLEM       -> The problem given is not supported by the planner
    INTERMEDIATE              -> The report is not a final one but it's given through the callback function
    """

    SOLVED_SATISFICING = auto()  # Valid plan found.
    SOLVED_OPTIMALLY = auto()  # Optimal plan found.
    UNSOLVABLE_PROVEN = auto()  # The problem is impossible, no valid plan exists.
    UNSOLVABLE_INCOMPLETELY = (
        auto()
    )  # The planner could not find a plan, but it's not sure that the problem is impossible (The planner is incomplete)
    TIMEOUT = auto()  # The planner ran out of time
    MEMOUT = auto()  # The planner ran out of memory
    INTERNAL_ERROR = auto()  # The planner had an internal error
    UNSUPPORTED_PROBLEM = auto()  # The problem given is not supported by the planner
    INTERMEDIATE = (
        auto()
    )  # The report is not a final one but it's an intermediate anytime result


POSITIVE_OUTCOMES = frozenset(
    [
        PlanGenerationResultStatus.SOLVED_SATISFICING,
        PlanGenerationResultStatus.SOLVED_OPTIMALLY,
    ]
)

NEGATIVE_OUTCOMES = frozenset(
    [
        PlanGenerationResultStatus.UNSOLVABLE_PROVEN,
        PlanGenerationResultStatus.UNSOLVABLE_INCOMPLETELY,
        PlanGenerationResultStatus.UNSUPPORTED_PROBLEM,
    ]
)


class LogLevel(Enum):
    """
    Enum representing the 4 possible values in the verbosity level of a :class:`~unified_planning.engines.LogMessage`:
    DEBUG, INFO, WARNING and ERROR
    """

    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()


@dataclass
class LogMessage:
    """
    This class is composed by a message and the Enum LogLevel indicating
    this message level, like Debug, Info, Warning or Error.
    """

    level: LogLevel
    message: str

    def __str__(self):
        return f"[{self.level.name}] {self.message}"


@dataclass
class Result:
    """This class represents the base class for results given by the engines to the user."""

    def is_definitive_result(self, *args) -> bool:
        """This predicate should state if the Result is definitive or if it can be improved."""
        raise NotImplementedError


@dataclass
class PlanGenerationResult(Result):
    """Class that represents the result of a plan generation call."""

    status: PlanGenerationResultStatus
    plan: Optional["up.plans.Plan"]
    engine_name: str
    metrics: Optional[Dict[str, str]] = field(default=None)
    log_messages: Optional[List[LogMessage]] = field(default=None)

    def __post__init(self):
        # Checks that plan and status are consistent
        if self.status in POSITIVE_OUTCOMES and self.plan is None:
            raise UPUsageError(
                f"The Result status is {str(self.status)} but no plan is set."
            )
        elif self.status in NEGATIVE_OUTCOMES and self.plan is not None:
            raise UPUsageError(
                f"The Result status is {str(self.status)} but the plan is {str(self.plan)}.\nWith this status the plan must be None."
            )
        return self

    def __str__(self) -> str:
        ret = [
            f"status: {self.status.name}",
            f"engine: {self.engine_name}",
        ]
        if self.plan is not None:
            ret.append(f"plan: {self.plan}")
        else:
            ret.append("plan: None")
        return "\n".join(ret)

    def is_definitive_result(self, *args) -> bool:
        optimality_required = False
        if len(args) > 0:
            optimality_required = (
                len(args[0].quality_metrics) > 0
            )  # Require optimality if the problem has at least one quality metric.
        return (
            self.status == PlanGenerationResultStatus.SOLVED_OPTIMALLY
            or self.status == PlanGenerationResultStatus.UNSOLVABLE_PROVEN
            or (
                optimality_required
                and self.status == PlanGenerationResultStatus.SOLVED_SATISFICING
            )
        )


def correct_plan_generation_result(
    result: PlanGenerationResult,
    problem: Problem,
    engine_epsilon: Optional[Union[int, float, str, Fraction]],
) -> PlanGenerationResult:
    """
    This function takes a PlanGenerationResult of a temporal problem and
    corrects it considering the epsilon requested by the problem.

    This method works only with TimeTriggeredPlans when the result contains a Plan.

    :param result: The PlanGenerationResult that must be checked.
    :param problem: The Problem the given PlanGenerationResult refers to.
    :param engine_epsilon: The epsilon used by the Engine; if None it means that the
        Engine does not guarantee a minimum separation value.
    :return: The new PlanGenerationResult that enforces policy of handling different
        epsilons between the engine and the problem.
    """
    assert result.plan is None or isinstance(
        result.plan, TimeTriggeredPlan
    ), "This method works only for TimeTriggeredPlans"
    if not isinstance(engine_epsilon, Fraction) and engine_epsilon is not None:
        try:
            engine_epsilon = Fraction(engine_epsilon)
        except ValueError as e:
            raise UPValueError(
                f"Given engine_epsilon is not convertible to Fraction: {str(e)}."
            )
    if engine_epsilon == problem.epsilon:
        return result
    elif engine_epsilon is None or (
        problem.epsilon is not None and engine_epsilon < problem.epsilon
    ):
        # if engine_epsilon is not specified or it's smaller than the problem's
        # requested epsilon, if the plan is not found the result is fine.
        # If the plan is found, it must be checked for the plan's epsilon.
        # if the plan epsilon is smaller than the one requested by the problem,
        # the result is not valid.
        assert problem.epsilon is not None
        if result.status in POSITIVE_OUTCOMES:
            # check that the solution fits the problem
            assert isinstance(result.plan, TimeTriggeredPlan)
            plan_epsilon = result.plan.extract_epsilon(problem)
            if plan_epsilon is not None and plan_epsilon < problem.epsilon:
                return PlanGenerationResult(
                    PlanGenerationResultStatus.UNSOLVABLE_INCOMPLETELY,
                    None,
                    result.engine_name,
                    result.metrics,
                    result.log_messages,
                )
    elif problem.epsilon is None or (
        engine_epsilon is not None and problem.epsilon < engine_epsilon
    ):
        # If the problem's epsilon is not specified or it's smaller than the
        # epsilon specified by the Engine, the given solution might not be
        # final, therefore unsatisfiability or optimality can't be proven
        assert engine_epsilon is not None
        if result.status == PlanGenerationResultStatus.UNSOLVABLE_PROVEN:
            return PlanGenerationResult(
                PlanGenerationResultStatus.UNSOLVABLE_INCOMPLETELY,
                None,
                result.engine_name,
                result.metrics,
                result.log_messages,
            )
        elif result.status == PlanGenerationResultStatus.SOLVED_OPTIMALLY:
            return PlanGenerationResult(
                PlanGenerationResultStatus.SOLVED_SATISFICING,
                None,
                result.engine_name,
                result.metrics,
                result.log_messages,
            )
    return result


@dataclass
class ValidationResult(Result):
    """Class that represents the result of a validate call."""

    status: ValidationResultStatus
    engine_name: str
    log_messages: Optional[List[LogMessage]] = field(default=None)
    metric_evaluations: Optional[Dict[PlanQualityMetric, Union[int, Fraction]]] = field(
        default=None
    )
    reason: Optional[FailedValidationReason] = field(default=None)
    inapplicable_action: Optional[up.plans.ActionInstance] = field(default=None)
    metrics: Optional[Dict[str, str]] = field(default=None)
    # The trace is either the sequences of states until the first validation error or a map from time to state for each event up to the first validation error
    trace: Optional[
        Union[List[up.model.State], Dict[Fraction, up.model.State]]
    ] = field(default=None)
    calculated_interpreted_functions: Optional[
        OrderedDict[up.model.FNode, up.model.FNode]
    ] = field(default=None)

    def __post_init__(self):
        assert (
            self.inapplicable_action is None
            or self.reason == FailedValidationReason.INAPPLICABLE_ACTION
        ), "The inapplicable_action can be set only if the reason of the failed plan is an inapplicable action."

    def __str__(self) -> str:
        ret = [
            f"status: {self.status.name}",
            f"engine: {self.engine_name}",
        ]
        if self.metric_evaluations is not None:
            ret.append(f"metrics: ")
            for metric, value in self.metric_evaluations.items():
                ret.append(f"    {metric}: {value}")
        if self.reason is not None:
            ret.append(f"reason: {self.reason.name}")
        if self.inapplicable_action is not None:
            ret.append(f"inapplicable action: {self.inapplicable_action}")
        return "\n".join(ret)

    def is_definitive_result(self, *args) -> bool:
        return True

    def __bool__(self):
        return bool(self.status)


@dataclass
class CompilerResult(Result):
    """Class that represents the result of a compile call."""

    problem: Optional[AbstractProblem]
    map_back_action_instance: Optional[
        Callable[[ActionInstance], Optional[ActionInstance]]
    ]
    engine_name: str
    log_messages: Optional[List[LogMessage]] = field(default=None)
    metrics: Optional[Dict[str, str]] = field(default=None)
    plan_back_conversion: Optional[Callable[[Plan], Plan]] = field(default=None)

    def _post_init(self):
        # Check that compiled problem and map_back_action_instance or plan_back_conversion are consistent with each other
        if self.problem is None:
            if self.map_back_action_instance is not None:
                raise UPUsageError(
                    "The compiled Problem is None but the map_back_action_instance Callable is not None."
                )
            if self.plan_back_conversion is not None:
                raise UPUsageError(
                    "The compiled Problem is None but the plan_back_conversion Callable is not None."
                )
        elif (
            self.map_back_action_instance is None and self.plan_back_conversion is None
        ):
            raise UPUsageError(
                f"The compiled Problem is not None but both map_back_action_instance and plan_back_conversion are None."
            )

        if self.map_back_action_instance is not None:
            if self.plan_back_conversion is not None:
                raise UPUsageError(
                    "Both map_back_action_instance and plan_back_conversion can't be specified"
                )
            self.plan_back_conversion = lambda x: x.replace_action_instances(
                cast(
                    Callable[[ActionInstance], Optional[ActionInstance]],
                    self.map_back_action_instance,
                )
            )

    def __str__(self) -> str:
        ret = [
            f"problem: {self.problem}",
            f"engine: {self.engine_name}",
        ]
        return "\n".join(ret)

    def is_definitive_result(self, *args) -> bool:
        return self.problem is not None
