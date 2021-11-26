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
"""This module defines the dnf remover class."""

import upf
from itertools import product
from upf.model import FNode, Problem, InstantaneousAction, DurativeAction, Interval, Timing, Action
from upf.walkers import Dnf
from upf.transformers.transformer import Transformer
from typing import List, Tuple, Dict


class DisjunctiveConditionsRemover(Transformer):
    '''DisjunctiveConditions remover class:
    this class requires a problem and offers the capability
    to transform a problem with preconditions not in the DNF form
    into one with all the preconditions in DNF form (an OR of AND);
    Then this OR is decomposed into subactions, therefore after this
    remover is called, every action condition or precondition will be
    an AND of leaf nodes.
    '''
    def __init__(self, problem: Problem, name: str = 'djrm'):
        Transformer.__init__(self, problem, name)
        #Represents the map from the new action to the old action
        self._new_to_old: Dict[Action, Action] = {}
        #represents a mapping from the action of the original problem to action of the new one.
        self._old_to_new: Dict[Action, List[Action]] = {}

    def get_rewritten_problem(self) -> Problem:
        '''Creates a problem that is a copy of the original problem
        but every precondition is compiled into one with preconditions in DNF.'''
        if self._new_problem is not None:
            return self._new_problem
        #NOTE that a different environment might be needed when multi-threading
        self._new_problem = self._problem.clone()
        self._new_problem.name = f'{self._name}_{self._problem.name}'
        self._new_problem.clear_actions()
        self._handle_actions()

        return self._new_problem

    def _handle_actions(self):
        dnf = Dnf(self._env)
        for a in self._problem.actions():
            if isinstance(a, InstantaneousAction):
                new_precond = dnf.get_dnf_expression(self._env.expression_manager.And(a.preconditions()))
                if new_precond.is_or():
                    for and_exp in new_precond.args():
                        na = self._create_new_action_with_given_precond(and_exp, a)
                        self._new_problem.add_action(na)
                else:
                    na = self._create_new_action_with_given_precond(new_precond, a)
                    self._new_problem.add_action(na)
            elif isinstance(a, DurativeAction):
                timing_list: List[Timing] = []
                interval_list: List[Interval] = []
                conditions: List[List[FNode]] = []
                # save the timing, calculate the dnf of the and of all the conditions at the same time
                # and then save it in conditions.
                # conditions contains lists of Fnodes, where [a,b,c] means a or b or c
                for t, cl in a.conditions().items():
                    timing_list.append(t)
                    new_cond = dnf.get_dnf_expression(self._env.expression_manager.And(cl))
                    if new_cond.is_or():
                        conditions.append(new_cond.args())
                    else:
                        conditions.append([new_cond])
                for i, cl in a.durative_conditions().items():
                    interval_list.append(i)
                    new_cond = dnf.get_dnf_expression(self._env.expression_manager.And(cl))
                    if new_cond.is_or():
                        conditions.append(new_cond.args())
                    else:
                        conditions.append([new_cond])
                conditions_tuple: Tuple[List[FNode], ...] = product(*conditions)
                for cond_list in conditions_tuple:
                    nda = self._create_new_durative_action_with_given_conds_at_given_times(timing_list, interval_list, cond_list, a)
                    self._new_problem.add_action(nda)
            else:
                raise NotImplementedError

    def _create_new_durative_action_with_given_conds_at_given_times(self, timing_list: List[Timing], interval_list: List[Interval], cond_list: List[FNode], original_action: DurativeAction) -> DurativeAction:
        new_action = original_action.clone()
        new_action.name = self.get_fresh_name(original_action.name)
        new_action.clear_conditions()
        new_action.clear_durative_conditions()
        for t, c in zip(timing_list, cond_list[:len(timing_list)]):
            if c.is_and():
                for co in c.args():
                    new_action.add_condition(t, co)
            else:
                new_action.add_condition(t, c)
        for i, c in zip(interval_list, cond_list[len(interval_list):]):
            if c.is_and():
                for co in c.args():
                    new_action.add_durative_condition(i, co)
            else:
                new_action.add_durative_condition(i, c)
        assert self._new_to_old is not None
        self._new_to_old[new_action] = original_action
        self._map_old_to_new_action(original_action, new_action)
        return new_action

    def _create_new_action_with_given_precond(self, precond: FNode, original_action: InstantaneousAction) -> InstantaneousAction:
        new_action = original_action.clone()
        new_action.name = self.get_fresh_name(original_action.name)
        new_action.clear_preconditions()
        if precond.is_and():
            for leaf in precond.args():
                new_action.add_precondition(leaf)
        else:
            new_action.add_precondition(precond)
        assert self._new_to_old is not None
        self._new_to_old[new_action] = original_action
        self._map_old_to_new_action(original_action, new_action)
        return new_action

    def _map_old_to_new_action(self, old_action, new_action):
        if old_action in self._old_to_new:
            self._old_to_new[old_action].append(new_action)
        else:
            self._old_to_new[old_action] = [new_action]

    def get_original_action(self, action: Action) -> Action:
        '''After the method get_rewritten_problem is called, this function maps
        the actions of the transformed problem into the actions of the original problem.'''
        return self._new_to_old[action]

    def get_transformed_actions(self, action: Action) -> List[Action]:
        '''After the method get_rewritten_problem is called, this function maps
        the actions of the original problem into the actions of the transformed problem.'''
        return self._old_to_new[action]
