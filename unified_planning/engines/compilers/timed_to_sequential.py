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
    InstantaneousAction,
    DurativeAction,
    Action,
    Effect,
)
from unified_planning.model.timing import StartTiming, EndTiming
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.engines.compilers.utils import replace_action
from typing import Dict, Optional
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
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")  #
        supported_kind.set_effects_kind("INCREASE_EFFECTS")  #
        supported_kind.set_effects_kind("DECREASE_EFFECTS")  #
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
        supported_kind.set_quality_metrics("TEMPORAL_OVERSUBSCRIPTION")  #
        supported_kind.set_actions_cost_kind("INT_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("REAL_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_oversubscription_kind("INT_NUMBERS_IN_OVERSUBSCRIPTION")
        supported_kind.set_oversubscription_kind("REAL_NUMBERS_IN_OVERSUBSCRIPTION")
        # supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
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
        # NOTE: assumes that there are no multiple inc/dec effects on same variables at all, THEY WILL GET OVERWRITTEN AS OF NOW
        assert isinstance(problem, Problem)

        # if problem is already sequential return problem? or raise

        # conditions at start -> preconditions copypaste
        # conditions during and at end -> preconditions but substitute with start_effects_dict
        # effects:
        # > effects_start \ effects_end (remove from start_effects effects on fluents that are also modified at end)
        # > effects_end but substitute with start_effects_dict on values
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
            old_start_effects: Dict = {}
            for timepoint, oel in action.effects.items():
                if timepoint == start:
                    for oe in oel:
                        old_start_effects[oe.fluent] = oe
                elif timepoint == end:
                    for oe in oel:
                        old_end_effects[oe.fluent] = oe
                else:
                    raise BaseException

            subs_dict: Dict = {}
            for osef, ose in old_start_effects.items():
                assert isinstance(ose, Effect)
                if ose.is_assignment():
                    subs_dict[ose.fluent] = ose.value
                elif ose.is_increase():
                    subs_dict[ose.fluent] = em.Plus(ose.fluent, ose.value)
                elif ose.is_decrease():
                    subs_dict[ose.fluent] = em.Minus(ose.fluent, ose.value)
                else:
                    raise BaseException

            for timeinterval, ocl in action.conditions.items():
                if timeinterval.upper == start and timeinterval.lower == start:
                    for oc in ocl:
                        new_action.add_precondition(oc)
                else:
                    for oc in ocl:
                        new_action.add_precondition(oc.substitute(subs_dict))

            # TODO find a way to keep increase/decrease instead of turning everything into assignments
            for oeef, oee in old_end_effects.items():
                assert isinstance(oee, Effect)
                if oee.is_assignment():
                    new_value = oee.value.substitute(subs_dict)
                    new_action.add_effect(oeef, new_value)
                elif oee.is_increase():
                    new_value = em.Plus(oeef, oee.value)
                    new_value = new_value.substitute(subs_dict)
                    new_action.add_effect(oeef, new_value)
                elif oee.is_decrease():
                    new_value = em.Minus(oeef, oee.value)
                    new_value = new_value.substitute(subs_dict)
                    new_action.add_effect(oeef, new_value)
                else:
                    raise BaseException
                new_value = None
            for osef, ose in old_start_effects.items():
                assert isinstance(ose, Effect)
                if osef not in old_end_effects.keys():
                    if ose.is_assignment():
                        new_action.add_effect(osef, ose.value)
                    elif ose.is_increase():
                        new_action.add_increase_effect(osef, ose.value)
                    elif ose.is_decrease():
                        new_action.add_increase_effect(osef, ose.value)
                    else:
                        raise BaseException

            new_problem.add_action(new_action)

        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old), self.name
        )
