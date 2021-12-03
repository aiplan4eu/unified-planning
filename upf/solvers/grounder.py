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


from typing import Dict, List,Tuple, Callable

import upf.environment
import upf.solvers as solvers
import upf.transformers
from upf.plan import Plan
from upf.model import FNode, Problem, ProblemKind, Action



class Grounder(solvers.solver.Solver):
    """Performs grounding."""
    def __init__(self, **options):
        pass

    def ground(self, problem: 'upf.model.Problem') -> Tuple[Problem, Callable[[Plan], Plan]]:
        grounder = upf.transformers.Grounder(problem)
        grounded_problem = grounder.get_rewritten_problem()
        return (grounded_problem, grounder.rewrite_back_plan)

    @staticmethod
    def name():
        return 'grounder'

    @staticmethod
    def supports(problem_kind):
        supported_kind = ProblemKind()
        supported_kind.set_typing('FLAT_TYPING')
        supported_kind.set_numbers('CONTINUOUS_NUMBERS')
        supported_kind.set_numbers('DISCRETE_NUMBERS')
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
        supported_kind.set_time('MAINTAIN_GOALS')
        supported_kind.set_time('DURATION_INEQUALITIES')
        return problem_kind <= supported_kind

    @staticmethod
    def is_grounder():
        return True

    def destroy(self):
        pass
