# Copyright 2026 Unified Planning library and its maintainers
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

from fractions import Fraction
from typing import List, Optional, Union

import unified_planning as up
from unified_planning.engines.engine import Engine
from unified_planning.engines.mixins.heuristic import (
    HeuristicGuarantee,
    HeuristicMixin,
)
from unified_planning.model import FNode, ProblemKind
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.model.walkers import StateEvaluator


class GoalCountingHeuristic(Engine, HeuristicMixin):
    """
    Heuristic returning the number of top-level goal conjuncts that are false in
    the given state. It never detects dead ends and ignores action costs.
    """

    def __init__(
        self, problem: "up.model.Problem", error_on_failed_checks: bool = True, **kwargs
    ):
        Engine.__init__(self)
        HeuristicMixin.__init__(self, problem, error_on_failed_checks)
        assert isinstance(problem, up.model.Problem), "supported_kind not respected"
        self._se = StateEvaluator(problem)
        self._goals: List[FNode] = []
        stack = list(reversed(problem.goals))
        while stack:
            g = stack.pop()
            if g.is_and():
                stack.extend(reversed(g.args))
            else:
                self._goals.append(g)

    @property
    def name(self) -> str:
        return "up_goal_counting"

    @staticmethod
    def satisfies(heuristic_guarantee: HeuristicGuarantee) -> bool:
        return heuristic_guarantee in (
            HeuristicGuarantee.GOAL_AWARE | HeuristicGuarantee.SAFE
        )

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_parameters("BOOL_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOOL_ACTION_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_ACTION_PARAMETERS")
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
        supported_kind.set_conditions_kind("INTERPRETED_FUNCTIONS_IN_CONDITIONS")
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        supported_kind.set_effects_kind("INCREASE_EFFECTS")
        supported_kind.set_effects_kind("DECREASE_EFFECTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("INTERPRETED_FUNCTIONS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("INTERPRETED_FUNCTIONS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("INTERPRETED_FUNCTIONS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("FORALL_EFFECTS")
        supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
        supported_kind.set_constraints_kind("STATE_INVARIANTS")
        # Only metrics under which a goal count is a meaningful cost estimate.
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_actions_cost_kind("STATIC_FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("INT_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("REAL_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        return supported_kind

    @staticmethod
    def supports(problem_kind: ProblemKind) -> bool:
        return problem_kind <= GoalCountingHeuristic.supported_kind()

    def _value(self, state: "up.model.State") -> Optional[Union[int, Fraction]]:
        return sum(
            1
            for g in self._goals
            if not self._se.evaluate(g, state).bool_constant_value()
        )
