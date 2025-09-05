# Copyright 2025 Unified Planning library and its maintainers
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
"""This module defines the timed to sequential problem converter class."""

import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.model import (
    Problem,
    ProblemKind,
    Fluent,
    InstantaneousAction,
    DurativeAction,
    Action,
)
from unified_planning.model.timing import StartTiming, EndTiming
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.engines.compilers.utils import replace_action
from typing import Dict, Optional, List
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
        # TODO timed? conditional effects? are supported or not?
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
        # supported_kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS") #
        # supported_kind.set_time("EXTERNAL_CONDITIONS_AND_EFFECTS")
        # supported_kind.set_time("TIMED_EFFECTS") #
        # supported_kind.set_time("TIMED_GOALS") #
        supported_kind.set_time("DURATION_INEQUALITIES")
        # supported_kind.set_time("SELF_OVERLAPPING") #
        # supported_kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS") #
        supported_kind.set_expression_duration("INT_TYPE_DURATIONS")
        supported_kind.set_expression_duration("REAL_TYPE_DURATIONS")
        supported_kind.set_expression_duration("STATIC_FLUENTS_IN_DURATIONS")
        supported_kind.set_expression_duration("FLUENTS_IN_DURATIONS")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_actions_cost_kind("STATIC_FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_quality_metrics("FINAL_VALUE")
        supported_kind.set_quality_metrics("MAKESPAN")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("TEMPORAL_OVERSUBSCRIPTION")
        supported_kind.set_actions_cost_kind("INT_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("REAL_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_oversubscription_kind("INT_NUMBERS_IN_OVERSUBSCRIPTION")
        supported_kind.set_oversubscription_kind("REAL_NUMBERS_IN_OVERSUBSCRIPTION")
        supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
        supported_kind.set_constraints_kind("STATE_INVARIANTS")
        supported_kind.set_constraints_kind("TRAJECTORY_CONSTRAINTS")
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
        raise NotImplementedError
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

        # if problem is already sequential return problem? or raise

        # TODO conditions at start -> preconditions copypaste
        # TODO conditions during and at end -> preconditions but substitute with start effects dict
        # TODO effects:
        # > effects_start \ effects_end (remove from start_effects effects on fluents that are also modified at end)
        # > effects_end but substitute with start_effects_dict on values
        # TODO start effects dict -> start effects transition encoded in dict that can be used by substituter walker
        env = problem.environment
        tm = env.type_manager
        em = env.expression_manager

        new_to_old: Dict[Action, Optional[Action]] = {}

        new_problem = problem.clone()
        new_problem.name = f"{self.name}_{problem.name}"

        new_problem.clear_actions()

        for action in problem.actions:
            new_action = InstantaneousAction(action.name)
            assert isinstance(action, DurativeAction)
            start = StartTiming()
            end = EndTiming()
            old_end_effects: Dict = {}
            old_start_effects: Dict = {}  # NOTE also used for substitution
            for i, oel in action.effects.items():
                # TODO FIXME this probably does not work with non assignment effects
                if i == start:
                    for oe in oel:
                        old_start_effects[oe.fluent] = oe.value
                elif i == end:
                    for oe in oel:
                        old_end_effects[oe.fluent] = oe.value
                else:
                    raise BaseException

            for i, ocl in action.conditions.items():
                if i.upper == start and i.lower == start:
                    for oc in ocl:
                        new_action.add_precondition(oc)
                else:
                    for oc in ocl:
                        new_action.add_precondition(oc.substitute(old_start_effects))

            for oeef, oeev in old_end_effects.items():
                new_v = oeev.substitute(old_start_effects)
                new_action.add_effect(oeef, new_v)
            for osef, osev in old_start_effects.items():
                if osef not in old_end_effects.keys():
                    new_action.add_effect(osef, osev)

            # other things like simulated effects ... TODO
            new_problem.add_action(new_action)

        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old), self.name
        )
