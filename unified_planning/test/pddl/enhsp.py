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

import os
import unified_planning as up
import unified_planning.solvers
from unified_planning.model.problem_kind import ProblemKind
from unified_planning.environment import get_env
from typing import List, Optional, Union


FILE_PATH = os.path.dirname(os.path.abspath(__file__))

credits = up.solvers.Credits('ENHSP',
                             'Enrico Scala',
                             'enricos83@gmail.com',
                             'https://sites.google.com/view/enhsp/home',
                             'GNU General Public license, version 3 or later',
                             'Expressive Numeric Heuristic Search Planner',
                             'ENHSP is a forward heuristic search planner, but it is expressive in that it can handle:\n - Classical Planning\n - Numeric Planning with linear and non-linear (!!) expressions\n - Planning with discretised autonomous processes and events\n - Global constraints, which are the analogous of always constraints of PDDL.'
                            )

class ENHSP(up.solvers.PDDLSolver):
    def __init__(self):
        up.solvers.PDDLSolver.__init__(self, False)

    @property
    def name(self) -> str:
        return 'ENHSP'

    def _get_cmd(self, domanin_filename: str, problem_filename: str, plan_filename: str) -> List[str]:
        return ['java', '-jar',
                os.path.join(FILE_PATH, '..', '..', '..', '.planners', 'enhsp-20', 'enhsp.jar'),
                '-o', domanin_filename, '-f', problem_filename, '-sp', plan_filename,
                '-planner', 'opt-hrmax']

    def _result_status(self, problem: 'up.model.Problem', plan: Optional['up.plan.Plan']) -> 'up.solvers.results.PlanGenerationResultStatus':
        if plan is None:
            return up.solvers.results.PlanGenerationResultStatus.UNSOLVABLE_PROVEN
        else:
            return up.solvers.results.PlanGenerationResultStatus.SOLVED_OPTIMALLY

    @staticmethod
    def satisfies(optimality_guarantee: Union[up.solvers.solver.OptimalityGuarantee, str]) -> bool:
        return True

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind()
        supported_kind.set_problem_class('ACTION_BASED') # type: ignore
        supported_kind.set_numbers('DISCRETE_NUMBERS') # type: ignore
        supported_kind.set_numbers('CONTINUOUS_NUMBERS') # type: ignore
        supported_kind.set_typing('FLAT_TYPING') # type: ignore
        supported_kind.set_typing('HIERARCHICAL_TYPING') # type: ignore
        supported_kind.set_conditions_kind('NEGATIVE_CONDITIONS') # type: ignore
        supported_kind.set_conditions_kind('DISJUNCTIVE_CONDITIONS') # type: ignore
        supported_kind.set_conditions_kind('EQUALITY') # type: ignore
        supported_kind.set_conditions_kind('EXISTENTIAL_CONDITIONS') # type: ignore
        supported_kind.set_conditions_kind('UNIVERSAL_CONDITIONS') # type: ignore
        supported_kind.set_effects_kind('CONDITIONAL_EFFECTS') # type: ignore
        supported_kind.set_effects_kind('INCREASE_EFFECTS') # type: ignore
        supported_kind.set_effects_kind('DECREASE_EFFECTS') # type: ignore
        supported_kind.set_fluents_type('NUMERIC_FLUENTS') # type: ignore
        supported_kind.set_quality_metrics('ACTIONS_COST') # type: ignore
        supported_kind.set_quality_metrics('FINAL_VALUE') # type: ignore
        return supported_kind

    @staticmethod
    def supports(problem_kind: 'ProblemKind') -> bool:
        return problem_kind <= ENHSP.supported_kind()

    @staticmethod
    def get_credits(**kwargs) -> Optional[up.solvers.Credits]:
        return credits


env = get_env()
if os.path.isfile(os.path.join(FILE_PATH, '..', '..', '..', '.planners', 'enhsp-20', 'enhsp.jar')):
    env.factory.add_solver('opt-pddl-solver', 'unified_planning.test.pddl.enhsp', 'ENHSP')
