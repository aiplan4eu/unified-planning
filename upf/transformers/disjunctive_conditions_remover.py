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
from upf.exceptions import UPFProblemDefinitionError
from upf.model import FNode, Problem, InstantaneousAction, DurativeAction, Interval, Timing, Action
from upf.walkers import Dnf
from upf.transformers.transformer import Transformer
from typing import List, Tuple, Union, Dict


class DisjunctiveConditionsRemover(Transformer):
    '''DisjunctiveConditions remover class:
    this class requires a problem and offers the capability
    to transform a problem with preconditions not in the DNF form
    into one with all the preconditions in DNF form (an OR of AND);
    Then this OR is decomposed into subactions, therefore after this
    remover is called, every action condition or precondition will be
    an AND of leaf nodes.
    '''
    def __init__(self, problem: Problem, name: str = 'dnf_remover'):
        Transformer.__init__(self, problem)
        self._name = name
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
        self._create_problem_copy(self._name)
        assert self._new_problem is not None
        self._new_problem_add_fluents()
        self._new_problem_add_objects()
        self._new_problem_add_initial_values()
        self._new_problem_add_timed_effects()
        self._new_problem_add_timed_goals()
        self._new_problem_add_maintain_goals()
        self._new_problem_add_goals()
        self._handle_actions()

        return self._new_problem

    def _handle_actions(self):
        dnf = Dnf(self._env)
        for a in self._problem.actions().values():
            self._count = 0
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
                temporal_list: List[Union[Timing, Interval]] = []
                conditions: List[List[FNode]] = []
                # save the timing, calculate the dnf of the and of all the conditions at the same time
                # and then save it in conditions.
                # conditions contains lists of Fnodes, where [a,b,c] means a or b or c
                for t, cl in a.conditions().items():
                    temporal_list.append(t)
                    new_cond = dnf.get_dnf_expression(self._env.expression_manager.And(cl))
                    if new_cond.is_or():
                        conditions.append(new_cond.args())
                    else:
                        conditions.append([new_cond])
                for i, cl in a.durative_conditions().items():
                    temporal_list.append(i)
                    new_cond = dnf.get_dnf_expression(self._env.expression_manager.And(cl))
                    if new_cond.is_or():
                        conditions.append(new_cond.args())
                    else:
                        conditions.append([new_cond])
                conditions_tuple: Tuple[List[FNode], ...] = product(*conditions)
                for cond_list in conditions_tuple:
                    nda = self._create_new_durative_action_with_given_conds_at_given_times(temporal_list, cond_list, a)
                    self._new_problem.add_action(nda)
            else:
                raise NotImplementedError

    def _create_new_durative_action_with_given_conds_at_given_times(self, temporal_list: List[Union[Timing, Interval]], cond_list: List[FNode], original_action: DurativeAction) -> DurativeAction:
        new_action = original_action.clone()
        new_action.name = f'{self._name}_{original_action.name}_{str(self._count)}'
        if self._problem.has_action(new_action.name):
            raise UPFProblemDefinitionError(f"Action: {new_action.name} of problem: {self._problem.name} has invalid name. Double underscore '__' is reserved by the naming convention.")
        self._count += 1
        new_action.clear_conditions()
        new_action.clear_durative_conditions()
        for t, c in zip(temporal_list, cond_list):
            if c.is_and():
                for co in c.args():
                    self._add_condition(new_action, t, co)
            else:
                self._add_condition(new_action, t, c)
        for timing, effects in original_action.effects().items():
            for effect in effects:
                new_action._add_effect_instance(timing, effect)
        assert self._new_to_old is not None
        self._new_to_old[new_action] = original_action
        self._map_old_to_new_action(original_action, new_action)
        return new_action

    def _add_condition(self, new_action: DurativeAction, time: Union[Timing, Interval], condition: FNode):
        if isinstance(time, Timing):
            new_action.add_condition(time, condition)
        elif isinstance(time, Interval):
            new_action.add_durative_condition(time, condition)
        else:
            raise NotImplementedError

    def _create_new_action_with_given_precond(self, precond: FNode, original_action: InstantaneousAction) -> InstantaneousAction:
        new_action = original_action.clone()
        new_action.name = f'{self._name}_{original_action.name}_{str(self._count)}'
        if self._problem.has_action(new_action.name):
            raise UPFProblemDefinitionError(f"Action: {new_action.name} of problem: {self._problem.name} has invalid name. Double underscore '__' is reserved by the naming convention.")
        self._count += 1
        new_action.clear_preconditions()
        if precond.is_and():
            for leaf in precond.args():
                new_action.add_precondition(leaf)
        else:
            new_action.add_precondition(precond)
        for effect in original_action.effects():
            new_action._add_effect_instance(effect)
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
        return self._new_to_old[action]

    def get_transformed_actions(self, action: Action) -> List[Action]:
        return self._old_to_new[action]
