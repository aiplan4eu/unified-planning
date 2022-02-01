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

"""This module implements the grounder that uses tarski."""



from functools import partial
import shutil
from typing import Callable, Tuple, Dict, List
import tarski # type: ignore
import unified_planning
import unified_planning.interop
from unified_planning.interop.from_tarski import convert_tarski_formula
from unified_planning.model.problem_kind import full_classical_kind, full_numeric_kind
from unified_planning.model import Action, FNode
from unified_planning.solvers.grounder import lift_plan
from unified_planning.solvers.solver import Solver
from unified_planning.transformers import Grounder


from tarski.grounding import LPGroundingStrategy, NaiveGroundingStrategy # type: ignore


class TarskiGrounder(Solver):
    """Implements the gounder that uses tarski."""
    def __init__(self, **kwargs):
        if len(kwargs) > 0:
            raise

    @staticmethod
    def name() -> str:
        return 'tarski_grounder'

    @staticmethod
    def is_grounder() -> bool:
        return True

    @staticmethod
    def supports(problem_kind: 'unified_planning.model.ProblemKind') -> bool:
        supported_kind = unified_planning.model.ProblemKind()
        supported_kind.set_typing('FLAT_TYPING') # type: ignore
        supported_kind.set_conditions_kind('NEGATIVE_CONDITIONS') # type: ignore
        supported_kind.set_conditions_kind('DISJUNCTIVE_CONDITIONS') # type: ignore
        supported_kind.set_conditions_kind('EQUALITY') # type: ignore
        supported_kind.set_conditions_kind('EXISTENTIAL_CONDITIONS') # type: ignore
        supported_kind.set_conditions_kind('UNIVERSAL_CONDITIONS') # type: ignore
        supported_kind.set_effects_kind('CONDITIONAL_EFFECTS') # type: ignore
        return problem_kind <= supported_kind

    def ground(self, problem: 'unified_planning.model.Problem') -> Tuple['unified_planning.model.Problem', Callable[[unified_planning.plan.Plan], unified_planning.plan.Plan]]:
        tarski_problem = unified_planning.interop.convert_problem_to_tarski(problem)
        actions = None
        gringo = shutil.which('gringo')
        if gringo is None:
            raise tarski.errors.CommandNotFoundError('gringo')
        try:
            lpgs = LPGroundingStrategy(tarski_problem)
            actions = lpgs.ground_actions()
        except tarski.grounding.errors.ReachabilityLPUnsolvable:
            raise unified_planning.exceptions.UPUsageError('tarski grounder can not find a solvable grounding.')
        grounded_actions_map: Dict[Action, List[Tuple[FNode, ...]]] = {}
        fluents = {fluent.name(): fluent for fluent in problem.fluents()}
        objects = {object.name(): object for object in problem.all_objects()}
        for action_name, list_of_tuple_of_parameters in actions.items():
            action = problem.action(action_name)
            parameters = {parameter.name(): parameter for parameter in action.parameters()}
            grounded_actions_map[action] = []
            for tuple_of_parameters in list_of_tuple_of_parameters:
                temp_list_of_converted_parameters = []
                for p in tuple_of_parameters:
                    if isinstance(p, str):
                        temp_list_of_converted_parameters.append(problem.env.expression_manager.ObjectExp(problem.object(p)))
                    else:
                        temp_list_of_converted_parameters.append(convert_tarski_formula(problem.env, fluents, \
                            objects, parameters, p))
                grounded_actions_map[action].append(tuple(temp_list_of_converted_parameters))
        unified_planning_grounder = Grounder(problem, grounding_actions_map=grounded_actions_map)
        grounded_problem = unified_planning_grounder.get_rewritten_problem()
        trace_back_map = unified_planning_grounder.get_rewrite_back_map()
        return (grounded_problem, partial(lift_plan, map=trace_back_map)) 
            
    def destroy(self):
        pass
