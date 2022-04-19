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


from functools import partial
from typing import Dict, List, Tuple

import unified_planning.environment
import unified_planning.solvers as solvers
import unified_planning.transformers
from unified_planning.plan import Plan, SequentialPlan, TimeTriggeredPlan, ActionInstance
from unified_planning.model import ProblemKind
from unified_planning.solvers.results import GroundingResult


class Grounder(solvers.solver.Solver):
    """Performs grounding."""
    def __init__(self, **options):
        pass

    def ground(self, problem: 'unified_planning.model.Problem') -> GroundingResult:
        '''This method takes an "unified_planning.model.Problem" and returns the grounded version of the problem
        and a function, that called on an "unified_planning.plan.Plan" of grounded problem returns the Plan
        version to apply to the original problem.'''
        grounder = unified_planning.transformers.Grounder(problem)
        grounded_problem = grounder.get_rewritten_problem()
        trace_back_map = grounder.get_rewrite_back_map()
        return GroundingResult(grounded_problem, partial(lift_plan, map=trace_back_map))

    @property
    def name(self):
        return 'grounder'

    @staticmethod
    def supports(problem_kind):
        supported_kind = ProblemKind()
        supported_kind.set_typing('FLAT_TYPING')
        supported_kind.set_typing('HIERARCHICAL_TYPING')
        supported_kind.set_numbers('CONTINUOUS_NUMBERS')
        supported_kind.set_numbers('DISCRETE_NUMBERS')
        supported_kind.set_fluents_type('NUMERIC_FLUENTS')
        supported_kind.set_fluents_type('OBJECT_FLUENTS')
        supported_kind.set_conditions_kind('NEGATIVE_CONDITIONS')
        supported_kind.set_conditions_kind('DISJUNCTIVE_CONDITIONS')
        supported_kind.set_conditions_kind('EQUALITY')
        supported_kind.set_conditions_kind('EXISTENTIAL_CONDITIONS')
        supported_kind.set_conditions_kind('UNIVERSAL_CONDITIONS')
        supported_kind.set_effects_kind('CONDITIONAL_EFFECTS')
        supported_kind.set_effects_kind('INCREASE_EFFECTS')
        supported_kind.set_effects_kind('DECREASE_EFFECTS')
        supported_kind.set_time('CONTINUOUS_TIME')
        supported_kind.set_time('DISCRETE_TIME')
        supported_kind.set_time('INTERMEDIATE_CONDITIONS_AND_EFFECTS')
        supported_kind.set_time('TIMED_EFFECT')
        supported_kind.set_time('TIMED_GOALS')
        supported_kind.set_time('DURATION_INEQUALITIES')
        supported_kind.set_simulated_entities('SIMULATED_EFFECTS')
        return problem_kind <= supported_kind

    @staticmethod
    def is_grounder():
        return True

    def destroy(self):
        pass


def lift_plan(plan: Plan, map: Dict['unified_planning.model.Action', Tuple['unified_planning.model.Action', List['unified_planning.model.FNode']]]) -> Plan:
    '''"map" is a map from every action in the "grounded_problem" to the tuple
        (original_action, parameters).

        Where the grounded actions is obtained by grounding
        the "original_action" with the specific "parameters".'''
    if isinstance(plan, SequentialPlan):
        original_actions: List[ActionInstance] = []
        for ai in plan.actions:
            original_action, parameters = map[ai.action]
            original_actions.append(ActionInstance(original_action, tuple(parameters)))
        return SequentialPlan(original_actions)
    elif isinstance(plan, TimeTriggeredPlan):
        s_original_actions_d = []
        for s, ai, d in plan.actions:
            original_action, parameters = map[ai.action]
            s_original_actions_d.append((s, ActionInstance(original_action, tuple(parameters)), d))
        return TimeTriggeredPlan(s_original_actions_d)
    raise NotImplementedError
