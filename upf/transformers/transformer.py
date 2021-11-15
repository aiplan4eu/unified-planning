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


import upf
from upf.model.fnode import FNode
from upf.model.action import Action, InstantaneousAction, DurativeAction
from upf.exceptions import UPFProblemDefinitionError
from upf.plan import SequentialPlan, TimeTriggeredPlan, ActionInstance
from upf.model.problem import Problem
from upf.model.timing import Timing
from typing import Dict, List, Optional, OrderedDict, Tuple, Union


class Transformer:
    '''Represents a generic remover with all the support methods shared among them.'''
    def __init__(self, problem: Problem, name: str):
        self._name = name
        self._problem = problem
        self._env = problem.env
        self._new_problem: Optional[Problem] = None
        self._simplifier = upf.walkers.Simplifier(self._env)
        self._count = 0

    def get_original_action(self, action: Action) -> Action:
        raise NotImplementedError

    def get_transformed_actions(self, action: Action) -> List[Action]:
        raise NotImplementedError

    def get_rewritten_problem(self) -> Problem:
        raise NotImplementedError

    def rewrite_back_plan(self, plan: Union[SequentialPlan, TimeTriggeredPlan]) -> Union[SequentialPlan, TimeTriggeredPlan]:
        '''Takes the sequential plan of the problem (created with
        the method "self.get_rewritten_problem()" and translates the plan back
        to be a plan of the original problem.'''
        if isinstance(plan, SequentialPlan):
            new_actions: List[ActionInstance] = plan.actions()
            old_actions: List[ActionInstance] = []
            for ai in new_actions:
                old_actions.append(ActionInstance(self.get_original_action(ai.action()), ai.actual_parameters()))
            return SequentialPlan(old_actions)
        elif isinstance(plan, TimeTriggeredPlan):
            s_new_actions_d = plan.actions()
            s_old_actions_d = []
            for s, ai, d in s_new_actions_d:
                s_old_actions_d.append((s, ActionInstance(self.get_original_action(ai.action()), ai.actual_parameters()), d))
            return TimeTriggeredPlan(s_old_actions_d)
        raise NotImplementedError

    def _reset_counter(self):
        self._count = 0

    def _check_and_simplify_conditions(self, action: DurativeAction) -> bool:
        '''Simplifies conditions and if it is False (a contraddiction)
        returns False, otherwise returns True.
        If the simplification is True (a tautology) removes all conditions at the given timing.
        If the simplification is still an AND rewrites back every "arg" of the AND
        in the conditions
        If the simplification is not an AND sets the simplification as the only
        condition at the given timing.'''
        #action conditions
        #tlc = timing list condition
        tlc: Dict[Timing, List[FNode]] = action.conditions()
        if len(tlc) == 0:
            return True
        # t = timing, lc = list condition
        for t, lc in tlc.copy().items():
            #conditions (as an And FNode)
            c = self._env.expression_manager.And(lc)
            #conditions simplified
            cs = self._simplifier.simplify(c)
            #new action conditions
            nac: List[FNode] = []
            if cs.is_bool_constant():
                if not cs.bool_constant_value():
                    return False
            else:
                if cs.is_and():
                    nac.extend(cs.args())
                else:
                    nac.append(cs)
            action._set_conditions(t, nac)
        return True

    def _check_and_simplify_preconditions(self, action: InstantaneousAction) -> bool:
        '''Simplifies preconditions and if it is False (a contraddiction)
        returns False, otherwise returns True.
        If the simplification is True (a tautology) removes all preconditions.
        If the simplification is still an AND rewrites back every "arg" of the AND
        in the preconditions
        If the simplification is not an AND sets the simplification as the only
        precondition.'''
        #action preconditions
        ap = action.preconditions()
        if len(ap) == 0:
            return True
        #preconditions (as an And FNode)
        p = self._env.expression_manager.And(ap)
        #preconditions simplified
        ps = self._simplifier.simplify(p)
        #new action preconditions
        nap: List[FNode] = []
        if ps.is_bool_constant():
            if not ps.bool_constant_value():
                return False
        else:
            if ps.is_and():
                nap.extend(ps.args())
            else:
                nap.append(ps)
        action._set_preconditions(nap)
        return True

    def _get_fresh_action_name(self, original_action: Action) -> str:
        while(True):
            new_action_name = f'{self._name}_{original_action.name}_{str(self._count)}'
            self._count += 1
            if not self._problem.has_action(new_action_name):
                return new_action_name
