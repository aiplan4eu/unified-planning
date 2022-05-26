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
from typing import Dict, List, Optional,Tuple
import unified_planning.environment
import unified_planning.solvers as solvers
import unified_planning.transformers
from unified_planning.plan import ActionInstance
from unified_planning.solvers.results import GroundingResult
from unified_planning.model import Problem, ProblemKind


class Grounder(solvers.solver.Solver):
    """Performs grounding."""
    def __init__(self, **options):
        pass

    def ground(self, problem: 'unified_planning.model.AbstractProblem') -> GroundingResult:
        '''This method takes an "unified_planning.model.Problem" and returns the generated
        "up.solvers.results.GroundingResult".'''
        assert isinstance(problem, Problem)
        grounder = unified_planning.transformers.Grounder(problem)
        grounded_problem = grounder.get_rewritten_problem()
        trace_back_map = grounder.get_rewrite_back_map()
        return GroundingResult(
            grounded_problem,
            partial(lift_action_instance, map=trace_back_map),
            self.name,
            [])

    @property
    def name(self):
        return 'grounder'

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind()
        supported_kind.set_problem_class('ACTION_BASED') # type: ignore
        supported_kind.set_typing('FLAT_TYPING') # type:ignore
        supported_kind.set_typing('HIERARCHICAL_TYPING') # type:ignore
        supported_kind.set_numbers('CONTINUOUS_NUMBERS') # type:ignore
        supported_kind.set_numbers('DISCRETE_NUMBERS') # type:ignore
        supported_kind.set_fluents_type('NUMERIC_FLUENTS') # type:ignore
        supported_kind.set_fluents_type('OBJECT_FLUENTS') # type:ignore
        supported_kind.set_conditions_kind('NEGATIVE_CONDITIONS') # type:ignore
        supported_kind.set_conditions_kind('DISJUNCTIVE_CONDITIONS') # type:ignore
        supported_kind.set_conditions_kind('EQUALITY') # type:ignore
        supported_kind.set_conditions_kind('EXISTENTIAL_CONDITIONS') # type:ignore
        supported_kind.set_conditions_kind('UNIVERSAL_CONDITIONS') # type:ignore
        supported_kind.set_effects_kind('CONDITIONAL_EFFECTS') # type:ignore
        supported_kind.set_effects_kind('INCREASE_EFFECTS') # type:ignore
        supported_kind.set_effects_kind('DECREASE_EFFECTS') # type:ignore
        supported_kind.set_time('CONTINUOUS_TIME') # type:ignore
        supported_kind.set_time('DISCRETE_TIME') # type:ignore
        supported_kind.set_time('INTERMEDIATE_CONDITIONS_AND_EFFECTS') # type:ignore
        supported_kind.set_time('TIMED_EFFECT') # type:ignore
        supported_kind.set_time('TIMED_GOALS') # type:ignore
        supported_kind.set_time('DURATION_INEQUALITIES') # type:ignore
        supported_kind.set_simulated_entities('SIMULATED_EFFECTS') # type:ignore
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= Grounder.supported_kind()

    @staticmethod
    def is_grounder():
        return True

    @staticmethod
    def get_credits(**kwargs) -> Optional[solvers.solver.Credits]:
        return None

    def destroy(self):
        pass

def lift_action_instance(action_instance: ActionInstance, map: Dict['unified_planning.model.Action', Tuple['unified_planning.model.Action', List['unified_planning.model.FNode']]]) -> ActionInstance:
    '''"map" is a map from every action in the "grounded_problem" to the tuple
        (original_action, parameters).

        Where the grounded actions is obtained by grounding
        the "original_action" with the specific "parameters".'''
    lifted_action, parameters = map[action_instance.action]
    return ActionInstance(lifted_action, tuple(parameters))
