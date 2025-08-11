# Copyright 2024 Unified Planning library and its maintainers
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


import time
import unified_planning as up
from unified_planning.engines.compilers.interpreted_functions_remover import (
    InterpretedFunctionsRemover,
)
import unified_planning.engines.mixins as mixins
from unified_planning.engines.mixins.compiler import CompilationKind
from unified_planning.engines.plan_validator import (
    SequentialPlanValidator,
    TimeTriggeredPlanValidator,
)
import unified_planning.engines.results
from unified_planning.environment import get_environment
from unified_planning.exceptions import UPException
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
from unified_planning.plans.sequential_plan import SequentialPlan
from unified_planning.plans.time_triggered_plan import TimeTriggeredPlan
from unified_planning.utils import powerset
from typing import Dict, OrderedDict, Type, IO, Optional, Union, List, Tuple, Callable
from fractions import Fraction


class InterpretedFunctionsPlanner(MetaEngine, mixins.OneshotPlannerMixin):
    """
    This class defines the InterpretedFunctionsPlanner :class:`~unified_planning.engines.MetaEngine`.

    """

    def __init__(self, *args, **kwargs):
        MetaEngine.__init__(self, *args, **kwargs)
        mixins.OneshotPlannerMixin.__init__(self)
        self._knowledge = OrderedDict()

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
        final_supported_kind = supported_kind.intersection(engine.supported_kind())
        additive_supported_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
        additive_supported_kind.set_expression_duration(
            "INTERPRETED_FUNCTIONS_IN_DURATIONS"
        )
        additive_supported_kind.set_conditions_kind(
            "INTERPRETED_FUNCTIONS_IN_CONDITIONS"
        )
        additive_supported_kind.set_effects_kind(
            "INTERPRETED_FUNCTIONS_IN_NUMERIC_ASSIGNMENTS"
        )
        additive_supported_kind.set_effects_kind(
            "INTERPRETED_FUNCTIONS_IN_BOOLEAN_ASSIGNMENTS"
        )
        additive_supported_kind.set_effects_kind(
            "INTERPRETED_FUNCTIONS_IN_OBJECT_ASSIGNMENTS"
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
        # clean memoization values for interpreted functions as we cannot guarantee that the callables are the same as in the last metaengine call
        memoization_keys_to_delete = []
        for key, _ in problem.environment.simplifier.memoization.items():
            if key.is_interpreted_function_exp():
                memoization_keys_to_delete.append(key)
        for key_to_del in memoization_keys_to_delete:
            del problem.environment.simplifier.memoization[key_to_del]
        assert isinstance(self.engine, mixins.OneshotPlannerMixin)
        start = time.time()
        knowledge: Dict[up.model.InterpretedFunction, up.model.FNode] = {}
        if self._skip_checks:
            self.engine._skip_checks = True
        while True:
            if timeout is not None:
                timeout -= time.time() - start
                if timeout <= 0:
                    return PlanGenerationResult(
                        PlanGenerationResultStatus.TIMEOUT, None, self.name
                    )
            with InterpretedFunctionsRemover(knowledge) as if_remover:
                comp_res = if_remover.compile(problem)
            res = self.engine.solve(comp_res.problem, heuristic, timeout, output_stream)
            if res.status in up.engines.results.POSITIVE_OUTCOMES:
                assert res.plan is not None
                if output_stream is not None:
                    output_stream.write(f"\nIFPlanner -> plan found:\n{res.plan}\n\n")
                plan = res.plan.replace_action_instances(
                    comp_res.map_back_action_instance
                )
                validator: Optional[
                    Union[SequentialPlanValidator, TimeTriggeredPlanValidator]
                ] = None
                if plan.kind == up.plans.PlanKind.SEQUENTIAL_PLAN:
                    validator = SequentialPlanValidator()
                elif plan.kind == up.plans.PlanKind.TIME_TRIGGERED_PLAN:
                    validator = TimeTriggeredPlanValidator()
                elif plan.kind == up.plans.PlanKind.STN_PLAN:
                    plan = plan.convert_to(
                        up.plans.plan.PlanKind.TIME_TRIGGERED_PLAN, problem
                    )
                    validator = TimeTriggeredPlanValidator()
                elif plan.kind == up.plans.PlanKind.PARTIAL_ORDER_PLAN:
                    plan = plan.convert_to(
                        up.plans.plan.PlanKind.SEQUENTIAL_PLAN, problem
                    )
                    validator = SequentialPlanValidator()
                else:
                    raise UPException(f"Unexpected plan kind: {plan.kind}")
                validation_result = validator.validate(problem, plan)

                if output_stream is not None:
                    output_stream.write(
                        f"\nIFPlanner -> plan validated as: {validation_result.status}\n\n"
                    )
                if validation_result.status == ValidationResultStatus.VALID:
                    return PlanGenerationResult(
                        res.status, plan, self.name, log_messages=res.log_messages
                    )
                else:
                    assert (
                        validation_result.calculated_interpreted_functions is not None
                    )
                    knowledge.update(validation_result.calculated_interpreted_functions)

                    if output_stream is not None:
                        output_stream.write(
                            f"\nIFPlanner -> dictionary of known interpreted functions values:\n\n"
                        )
                        for log_if, log_val in knowledge.items():
                            output_stream.write(f"{log_if} : {log_val}\n")
                        output_stream.write("\n")

            else:
                return PlanGenerationResult(res.status, None, self.name)
