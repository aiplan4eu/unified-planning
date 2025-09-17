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
"""This module defines the conditional effects remover class."""


from itertools import product
import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.model import (
    Problem,
    ProblemKind,
    Fluent,
    Parameter,
    BoolExpression,
    NumericConstant,
    Action,
    InstantaneousAction,
    DurativeAction,
    Effect,
    SimulatedEffect,
    FNode,
    ExpressionManager,
    MinimizeActionCosts,
    MinimizeExpressionOnFinalState,
    MaximizeExpressionOnFinalState,
    Oversubscription,
    TemporalOversubscription,
    Object,
    Expression,
    DurationInterval,
    UPState,
)
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.model.walkers import UsertypeFluentsWalker
from unified_planning.model.types import _UserType
from unified_planning.engines.compilers.utils import replace_action
from unified_planning.model.fluent import get_all_fluent_exp
from typing import Iterator, Dict, List, OrderedDict, Set, Tuple, Optional, Union, cast
from functools import partial


class TimedToSequential(engines.engine.Engine, CompilerMixin):
    """
    TODO
    """

    def __init__(self):
        engines.engine.Engine.__init__(self)
        CompilerMixin.__init__(self, CompilationKind.TIMED_TO_SEQUENTIAL)

    @property
    def name(self):
        return "t2s"

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
        # supported_kind.set_problem_class("ACTION_BASED")
        # supported_kind.set_typing("FLAT_TYPING")
        # supported_kind.set_typing("HIERARCHICAL_TYPING")
        # supported_kind.set_parameters("BOOL_FLUENT_PARAMETERS")
        # supported_kind.set_parameters("BOUNDED_INT_FLUENT_PARAMETERS")
        # supported_kind.set_parameters("BOOL_ACTION_PARAMETERS")
        # supported_kind.set_parameters("BOUNDED_INT_ACTION_PARAMETERS")
        # supported_kind.set_parameters("UNBOUNDED_INT_ACTION_PARAMETERS")
        # supported_kind.set_parameters("REAL_ACTION_PARAMETERS")
        # supported_kind.set_numbers("BOUNDED_TYPES")
        # supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        # supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
        # supported_kind.set_fluents_type("INT_FLUENTS")
        # supported_kind.set_fluents_type("REAL_FLUENTS")
        # supported_kind.set_fluents_type("OBJECT_FLUENTS")
        # supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        # supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        # supported_kind.set_conditions_kind("EQUALITIES")
        # supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        # supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        # supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        # supported_kind.set_effects_kind("INCREASE_EFFECTS")
        # supported_kind.set_effects_kind("DECREASE_EFFECTS")
        # supported_kind.set_effects_kind("STATIC_FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        # supported_kind.set_effects_kind("STATIC_FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        # supported_kind.set_effects_kind("STATIC_FLUENTS_IN_OBJECT_ASSIGNMENTS")
        # supported_kind.set_effects_kind("FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        # supported_kind.set_effects_kind("FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        # supported_kind.set_effects_kind("FLUENTS_IN_OBJECT_ASSIGNMENTS")
        # supported_kind.set_effects_kind("FORALL_EFFECTS")
        # supported_kind.set_time("CONTINUOUS_TIME")
        # supported_kind.set_time("DISCRETE_TIME")
        # supported_kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS") #
        # supported_kind.set_time("EXTERNAL_CONDITIONS_AND_EFFECTS")
        # supported_kind.set_time("TIMED_EFFECTS") #
        # supported_kind.set_time("TIMED_GOALS") #
        # supported_kind.set_time("DURATION_INEQUALITIES")
        # supported_kind.set_time("SELF_OVERLAPPING") #
        # supported_kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS") #
        # supported_kind.set_expression_duration("INT_TYPE_DURATIONS")
        # supported_kind.set_expression_duration("REAL_TYPE_DURATIONS")
        # supported_kind.set_expression_duration("STATIC_FLUENTS_IN_DURATIONS")
        # supported_kind.set_expression_duration("FLUENTS_IN_DURATIONS")
        # supported_kind.set_quality_metrics("ACTIONS_COST")
        # supported_kind.set_actions_cost_kind("STATIC_FLUENTS_IN_ACTIONS_COST")
        # supported_kind.set_actions_cost_kind("FLUENTS_IN_ACTIONS_COST")
        # supported_kind.set_quality_metrics("FINAL_VALUE")
        # supported_kind.set_quality_metrics("MAKESPAN")
        # supported_kind.set_quality_metrics("PLAN_LENGTH")
        # supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        # supported_kind.set_quality_metrics("TEMPORAL_OVERSUBSCRIPTION")
        # supported_kind.set_actions_cost_kind("INT_NUMBERS_IN_ACTIONS_COST")
        # supported_kind.set_actions_cost_kind("REAL_NUMBERS_IN_ACTIONS_COST")
        # supported_kind.set_oversubscription_kind("INT_NUMBERS_IN_OVERSUBSCRIPTION")
        # supported_kind.set_oversubscription_kind("REAL_NUMBERS_IN_OVERSUBSCRIPTION")
        # supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
        # supported_kind.set_constraints_kind("STATE_INVARIANTS")
        # supported_kind.set_constraints_kind("TRAJECTORY_CONSTRAINTS")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= TimedToSequential.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == CompilationKind.TIMED_TO_SEQUENTIAL

    @staticmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: Optional[CompilationKind] = None
    ) -> ProblemKind:
        new_kind = problem_kind.clone()
        if new_kind.has_object_fluents():
            new_kind.unset_fluents_type("OBJECT_FLUENTS")
            new_kind.set_effects_kind("CONDITIONAL_EFFECTS")
            new_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
            new_kind.set_conditions_kind("EQUALITIES")
            new_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        return new_kind

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        """
        TODO
        """
        assert isinstance(problem, Problem)
        raise NotImplementedError
        env = problem.environment
        tm = env.type_manager
        em = env.expression_manager

        new_to_old: Dict[Action, Optional[Action]] = {}

        new_problem = Problem(f"{self.name}_{problem.name}", env)
        new_problem.add_objects(problem.all_objects)

        fluents_map: Dict[Fluent, Fluent] = {}

        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old), self.name
        )
