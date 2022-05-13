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
"""This module defines the quantifiers remover class."""


from unified_planning.walkers import ExpressionQuantifiersRemover
from unified_planning.transformers.ab_transformer import ABTransformer
from unified_planning.model import Problem, InstantaneousAction, DurativeAction, Action
from typing import List, Dict


class QuantifiersRemover(ABTransformer):
    '''Quantifiers remover class:
    this class requires a problem and offers the capability
    to transform a problem with quantifiers into a problem without.
    '''
    def __init__(self, problem: Problem, name: str = 'qurm'):
        ABTransformer.__init__(self, problem, name)
        #NOTE no simplification are made. But it's possible to add them in key points
        self._expression_quantifier_remover = ExpressionQuantifiersRemover(self._env)
        #Represents the map from the new action to the old action
        self._new_to_old: Dict[Action, Action] = {}
        #represents a mapping from the action of the original problem to action of the new one.
        self._old_to_new: Dict[Action, List[Action]] = {}

    def get_rewritten_problem(self) -> Problem:
        '''Creates a problem that is a copy of the original problem
        but every quantifier is compiled away by it's respective logic formula
        instantiated on object.
        For example the formula:
            Forall (s-sempahore) is_green(s)
        in a problem with 3 objects of type semaphores {s1, s2, s3} is compiled in:
            And(is_green(s1), is_green(s2), is_green(s3)).
        While the respective formula on the same problem:
            Exists (s-semaphore) is_green(s)
        becomes:
            Or(is_green(s1), is_green(s2), is_green(s3)).'''
        if self._new_problem is not None:
            return self._new_problem
        #NOTE that a different environment might be needed when multi-threading
        self._new_problem = self._problem.clone()
        self._new_problem.name = f'{self._name}_{self._problem.name}'
        self._new_problem.clear_timed_goals()
        self._new_problem.clear_goals()
        for action in self._new_problem.actions:
            if isinstance(action, InstantaneousAction):
                original_action = self._problem.action(action.name)
                assert isinstance(original_action, InstantaneousAction)
                action.name = self.get_fresh_name(action.name)
                action.clear_preconditions()
                for p in original_action.preconditions:
                    action.add_precondition(self._expression_quantifier_remover.remove_quantifiers(p, self._problem))
                for e in action.effects:
                    if e.is_conditional():
                        e.set_condition(self._expression_quantifier_remover.remove_quantifiers(e.condition, self._problem))
                    e.set_value(self._expression_quantifier_remover.remove_quantifiers(e.value, self._problem))
                self._old_to_new[original_action] = [action]
                self._new_to_old[action] = original_action
            elif isinstance(action, DurativeAction):
                original_action = self._problem.action(action.name)
                assert isinstance(original_action, DurativeAction)
                action.name = self.get_fresh_name(action.name)
                action.clear_conditions()
                for i, cl in original_action.conditions.items():
                    for c in cl:
                        action.add_condition(i, self._expression_quantifier_remover.remove_quantifiers(c, self._problem))
                for t, el in action.effects.items():
                    for e in el:
                        if e.is_conditional():
                            e.set_condition(self._expression_quantifier_remover.remove_quantifiers(e.condition, self._problem))
                        e.set_value(self._expression_quantifier_remover.remove_quantifiers(e.value, self._problem))
                self._old_to_new[original_action] = [action]
                self._new_to_old[action] = original_action
            else:
                raise NotImplementedError
        for t, el in self._new_problem.timed_effects.items():
            for e in el:
                if e.is_conditional():
                    e.set_condition(self._expression_quantifier_remover.remove_quantifiers(e.condition, self._problem))
                e.set_value(self._expression_quantifier_remover.remove_quantifiers(e.value, self._problem))
        for i, gl in self._problem.timed_goals.items():
            for g in gl:
                ng = self._expression_quantifier_remover.remove_quantifiers(g, self._problem)
                self._new_problem.add_timed_goal(i, ng)
        for g in self._problem.goals:
            ng = self._expression_quantifier_remover.remove_quantifiers(g, self._problem)
            self._new_problem.add_goal(ng)
        return self._new_problem

    def get_original_action(self, action: Action) -> Action:
        '''After the method get_rewritten_problem is called, this function maps
        the actions of the transformed problem into the actions of the original problem.'''
        return self._new_to_old[action]

    def get_transformed_actions(self, action: Action) -> List[Action]:
        '''After the method get_rewritten_problem is called, this function maps
        the actions of the original problem into the actions of the transformed problem.'''
        return self._old_to_new[action]
