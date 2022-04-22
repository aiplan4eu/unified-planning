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
'''This module defines the different remover classes.'''


import unified_planning
from unified_planning.model import FNode, TimeInterval, Action, InstantaneousAction, DurativeAction, Problem
from unified_planning.plan import SequentialPlan, TimeTriggeredPlan, ActionInstance, Plan
from typing import Iterable, List, Optional, Tuple


class Transformer:
    '''Represents a generic Transformer with all the needed methods shared among them.'''
    def __init__(self, problem: Problem, name: str):
        self._name = name
        self._problem = problem
        self._env = problem.env
        self._new_problem: Optional[Problem] = None
        self._simplifier = unified_planning.walkers.Simplifier(self._env)

    def get_original_action(self, action: Action) -> Action:
        '''After the method get_rewritten_problem is called, this function should
         map the actions of the transformed problem into the actions of the original problem.'''
        raise NotImplementedError

    def get_transformed_actions(self, action: Action) -> List[Action]:
        '''After the method get_rewritten_problem is called, this function should
         map the actions of the original problem into the actions of the transformed problem.'''
        raise NotImplementedError

    def get_rewritten_problem(self) -> Problem:
        '''This function should rewrite the problem according to the Transformer specifics.
        This should also include the data structure to support the methods get_original_action
        and get_transformed_actions'''
        raise NotImplementedError

    def _replace_action_instance(self, action_instance: ActionInstance) -> ActionInstance:
        return ActionInstance(self.get_original_action(action_instance.action), action_instance.actual_parameters)

    def rewrite_back_plan(self, plan: Plan) -> Plan:
        '''Takes the sequential plan of the problem (created with
        the method "self.get_rewritten_problem()" and translates the plan back
        to be a plan of the original problem.

        NOTE:
        This method uses self._replace_action_instance; which MUST be rewritten if the specific Transformer extension changes
        the action's parameters; for example a Grounder!'''
        return plan.replace_action_instances(self._replace_action_instance)

    def _check_and_simplify_conditions(self, action: DurativeAction, simplify_constants: bool = False) -> Tuple[bool, List[Tuple[TimeInterval, FNode]]]:
        '''Simplifies conditions and if it is False (a contraddiction)
        returns False, otherwise returns True.
        If the simplification is True (a tautology) removes all conditions at the given timing.
        If the simplification is still an AND rewrites back every "arg" of the AND
        in the conditions
        If the simplification is not an AND sets the simplification as the only
        condition at the given timing.
        Then, the new conditions are returned as a List[Tuple[Timing, FNode]] and the user can
        decide how to use the new conditions.'''
        #new action conditions
        nac: List[Tuple[TimeInterval, FNode]] = []
        # t = timing, lc = list condition
        for i, lc in action.conditions.items():
            #conditions (as an And FNode)
            c = self._env.expression_manager.And(lc)
            #conditions simplified
            if simplify_constants:
                cs = self._simplifier.simplify(c, self._problem)
            else:
                cs = self._simplifier.simplify(c)
            if cs.is_bool_constant():
                if not cs.bool_constant_value():
                    return (False, [],)
            else:
                if cs.is_and():
                    for new_cond in cs.args:
                        nac.append((i, new_cond))
                else:
                    nac.append((i, cs))
        return (True, nac)

    def _check_and_simplify_preconditions(self, action: InstantaneousAction, simplify_constants: bool = False) -> Tuple[bool, List[FNode]]:
        '''Simplifies preconditions and if it is False (a contraddiction)
        returns False, otherwise returns True.
        If the simplification is True (a tautology) removes all preconditions.
        If the simplification is still an AND rewrites back every "arg" of the AND
        in the preconditions
        If the simplification is not an AND sets the simplification as the only
        precondition.
        Then, the new preconditions are returned as a List[FNode] and the user can
        decide how to use the new preconditions.'''
        #action preconditions
        ap = action.preconditions
        if len(ap) == 0:
            return (True, [])
        #preconditions (as an And FNode)
        p = self._env.expression_manager.And(ap)
        #preconditions simplified
        if simplify_constants:
            ps = self._simplifier.simplify(p, self._problem)
        else:
            ps = self._simplifier.simplify(p)
        #new action preconditions
        nap: List[FNode] = []
        if ps.is_bool_constant():
            if not ps.bool_constant_value():
                return (False, [])
        else:
            if ps.is_and():
                nap.extend(ps.args)
            else:
                nap.append(ps)
        action._set_preconditions(nap)
        return (True, nap)

    def get_fresh_name(self, original_name: str, parameters_names: Iterable[str] = []) -> str:
        '''To use this method, the new problem returned by the transformer must be stored in the field
        self._new_problem!
        This method returns a fresh name for the problem, given the name of the transformer and a name in input.

        NOTE: The field parameters_names is there just for possible extensions.'''
        assert self._new_problem is not None
        if parameters_names != []:
            raise NotImplementedError
        count = 0
        while(True):
            new_name = f'{self._name}_{original_name}_{str(count)}'
            if self._problem.has_name(new_name) or self._new_problem.has_name(new_name):
                count += 1
            else:
                return new_name
