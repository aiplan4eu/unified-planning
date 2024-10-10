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
# copyright info is not up to date as of september 27th 2024


import time
import unified_planning as up
from unified_planning.engines.compilers.interpreted_functions_remover import (
    InterpretedFunctionsRemover,
)
import unified_planning.engines.mixins as mixins
from unified_planning.engines.mixins.compiler import CompilationKind
from unified_planning.engines.plan_validator import SequentialPlanValidator
import unified_planning.engines.results
from unified_planning.environment import get_environment
from unified_planning.model import ProblemKind
from unified_planning.model.action import InstantaneousAction
from unified_planning.model.interpreted_function import InterpretedFunction
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.engines.engine import Engine
from unified_planning.engines.meta_engine import MetaEngine
from unified_planning.engines.results import (
    FailedValidationReason,
    PlanGenerationResultStatus,
    PlanGenerationResult,
    ValidationResultStatus,
)
from unified_planning.engines.mixins.oneshot_planner import OptimalityGuarantee
from unified_planning.plans.time_triggered_plan import TimeTriggeredPlan
from unified_planning.utils import powerset
from typing import OrderedDict, Type, IO, Optional, Union, List, Tuple, Callable
from fractions import Fraction


class InterpretedFunctionsPlanner(MetaEngine, mixins.OneshotPlannerMixin):
    """
    This class defines the InterpretedFunctionsPlanner :class:`~unified_planning.engines.MetaEngine`.

    """

    def __init__(self, *args, **kwargs):
        MetaEngine.__init__(self, *args, **kwargs)
        mixins.OneshotPlannerMixin.__init__(self)
        self._knowledge = OrderedDict()
        self._debug_print_final_problem = False

    @property
    def knowledge(self):
        return self._knowledge

    def add_knowledge(self, key, value):
        self._knowledge[key] = value

    @property
    def name(self) -> str:
        return f"InterpretedFunctionsPlanner[{self.engine.name}]"

    @staticmethod
    def satisfies(optimality_guarantee: OptimalityGuarantee) -> bool:
        if optimality_guarantee == OptimalityGuarantee.SATISFICING:
            return True
        return False

    @staticmethod
    def is_compatible_engine(engine: Type[Engine]) -> bool:
        return engine.is_oneshot_planner() and engine.supports(ProblemKind({"ACTION_BASED", "NEGATIVE_CONDITIONS"}, version=LATEST_PROBLEM_KIND_VERSION))  # type: ignore

    @staticmethod
    def _supported_kind(engine: Type[Engine]) -> "ProblemKind":
        supported_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_numbers("BOUNDED_TYPES")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
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
        final_supported_kind = supported_kind.intersection(engine.supported_kind())  #
        additive_supported_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
        # additive_supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        # additive_supported_kind.set_quality_metrics("TEMPORAL_OVERSUBSCRIPTION")
        # additive_supported_kind.set_oversubscription_kind(
        #    "INT_NUMBERS_IN_OVERSUBSCRIPTION"
        # )
        # additive_supported_kind.set_oversubscription_kind(
        #    "REAL_NUMBERS_IN_OVERSUBSCRIPTION"
        # )
        additive_supported_kind.set_expression_duration(
            "INTERPRETED_FUNCTIONS_IN_DURATIONS"
        )
        additive_supported_kind.set_conditions_kind(
            "INTERPRETED_FUNCTIONS_IN_CONDITIONS"
        )
        return final_supported_kind.union(additive_supported_kind)

    @staticmethod
    def _supports(problem_kind: "ProblemKind", engine: Type[Engine]) -> bool:
        return problem_kind <= InterpretedFunctionsPlanner._supported_kind(engine)

    def _solve(
        self,
        problem: "up.model.AbstractProblem",
        heuristic: Optional[Callable[["up.model.state.State"], Optional[float]]] = None,
        timeout: Optional[float] = None,
        output_stream: Optional[IO[str]] = None,
    ) -> "PlanGenerationResult":

        assert isinstance(problem, up.model.Problem)
        assert isinstance(self.engine, mixins.OneshotPlannerMixin)
        em = problem.environment.expression_manager
        f = problem.environment.factory

        with f.Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.INTERPRETED_FUNCTIONS_REMOVING,
        ) as if_remover:
            ifr = if_remover.compile(
                problem, CompilationKind.INTERPRETED_FUNCTIONS_REMOVING
            )

        retval = _attempt_to_solve(
            self, problem, ifr, heuristic, timeout, output_stream
        )
        return retval


def _attempt_to_solve(
    self,
    problem: "up.model.AbstractProblem",
    compilerresult,
    heuristic: Optional[Callable[["up.model.state.State"], Optional[float]]] = None,
    timeout: Optional[float] = None,
    output_stream: Optional[IO[str]] = None,
) -> "PlanGenerationResult":
    f = problem.environment.factory
    new_problem = compilerresult.problem
    start = time.time()
    if self._skip_checks:
        self.engine._skip_checks = True
    res = self.engine.solve(new_problem, heuristic, timeout, output_stream)

    if timeout is not None:
        timeout -= min(timeout, time.time() - start)
    if res.status in up.engines.results.POSITIVE_OUTCOMES:
        status = res.status
        mapback = compilerresult.map_back_action_instance
        mappedbackplan = res.plan.replace_action_instances(mapback)
        with f.PlanValidator(
            problem_kind=problem.kind, plan_kind=mappedbackplan.kind
        ) as validator:
            validation_result = validator.validate(problem, mappedbackplan)
        if validation_result.status == ValidationResultStatus.VALID:

            if self._debug_print_final_problem:
                print(new_problem)

            retval = PlanGenerationResult(
                status,
                mappedbackplan,
                self.name,
                log_messages=res.log_messages,
            )
            return retval
        else:
            # temporary skip for ttp
            if isinstance(mappedbackplan, TimeTriggeredPlan):
                return PlanGenerationResult(
                    validation_result.status,
                    mappedbackplan,
                    self.name,
                    log_messages=res.log_messages,
                )

            refined_problem = _refine(self, problem, validation_result)
            if refined_problem is None:
                retval = PlanGenerationResult(
                    PlanGenerationResultStatus.UNSOLVABLE_PROVEN,  # validation_result.status,
                    mappedbackplan,
                    self.name,
                    log_messages=res.log_messages,
                )
            else:
                retval = _attempt_to_solve(
                    self, problem, refined_problem, heuristic, timeout, output_stream
                )
        return retval
    elif res.status == PlanGenerationResultStatus.TIMEOUT:
        return PlanGenerationResult(PlanGenerationResultStatus.TIMEOUT, None, self.name)
    elif res.status in [
        PlanGenerationResultStatus.MEMOUT,
        PlanGenerationResultStatus.INTERNAL_ERROR,
        PlanGenerationResultStatus.UNSUPPORTED_PROBLEM,
        PlanGenerationResultStatus.UNSOLVABLE_INCOMPLETELY,
    ]:
        incomplete = True
        if incomplete:
            status = res.status
    else:
        status = PlanGenerationResultStatus.UNSOLVABLE_PROVEN
    return PlanGenerationResult(status, None, self.name)


def _refine(self, problem, validation_result):
    newProb = None
    if validation_result.calculated_interpreted_functions is None:
        print("no updates available, the problem has no solution")
    elif len(validation_result.calculated_interpreted_functions) == 0:
        print("no updates available, the problem has no solution")
    else:
        for k in validation_result.calculated_interpreted_functions:
            self.add_knowledge(k, validation_result.calculated_interpreted_functions[k])
        with InterpretedFunctionsRemover(self.knowledge) as if_remover:
            newProb = if_remover.compile(
                problem,
                CompilationKind.INTERPRETED_FUNCTIONS_REMOVING,
            )
    return newProb
