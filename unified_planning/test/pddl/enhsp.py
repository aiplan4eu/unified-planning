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
from unified_planning.model.problem_kind import ProblemKind
from unified_planning.environment import get_env
from typing import List, Optional, Union
from unified_planning.solvers import PDDLSolver


FILE_PATH = os.path.dirname(os.path.abspath(__file__))


class ENHSP(PDDLSolver):
    def __init__(self):
        PDDLSolver.__init__(self, False)

    @property
    def name(self) -> str:
        return 'ENHSP'

    def _get_cmd(self, domanin_filename: str, problem_filename: str, plan_filename: str) -> List[str]:
        return ['java', '-jar',
                os.path.join(FILE_PATH, '..', '..', '..', '.planners', 'enhsp-20', 'enhsp.jar'),
                '-o', domanin_filename, '-f', problem_filename, '-sp', plan_filename,
                '-planner', 'opt-hrmax']

    def _result_status(self, problem: 'up.model.Problem', plan: Optional['up.plan.Plan']) -> int:
        if plan is None:
            return up.solvers.results.UNSOLVABLE_PROVEN
        else:
            return up.solvers.results.SOLVED_OPTIMALLY

    @staticmethod
    def satisfies(optimality_guarantee: Union[int, str]) -> bool:
        return True

    @staticmethod
    def supports(problem_kind: 'ProblemKind') -> bool:
        supported_kind = ProblemKind()
        supported_kind.set_numbers('DISCRETE_NUMBERS') # type: ignore
        supported_kind.set_numbers('CONTINUOUS_NUMBERS') # type: ignore
        supported_kind.set_typing('FLAT_TYPING') # type: ignore
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
        return problem_kind <= supported_kind


env = get_env()
if os.path.isfile(os.path.join(FILE_PATH, '..', '..', '..', '.planners', 'enhsp-20', 'enhsp.jar')):
    env.factory.add_solver('enhsp', 'unified_planning.test.pddl.enhsp', 'ENHSP')
