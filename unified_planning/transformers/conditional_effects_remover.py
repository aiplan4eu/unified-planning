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
"""This module defines the conditional effects remover class."""


import unified_planning
from unified_planning.exceptions import UPProblemDefinitionError
from unified_planning.transformers.ab_transformer import ActionBasedTransformer
from typing import Iterable, List, Dict, Tuple, Union, Optional
from itertools import chain, combinations


class ConditionalEffectsRemover(ActionBasedTransformer):
    '''Conditional effect remover class:
    this class requires a problem and offers the capability
    to transform a conditional problem into an unconditional one.

    This is done by substituting every conditional action with different
    actions representing every possible branch of the original action.

    Also the conditional timed_effects are removed maintaining the same
    semanthics. When this is not possible, an exception is raised.'''
    def __init__(self, problem: 'unified_planning.model.Problem', name: str = 'cerm'):
        ActionBasedTransformer.__init__(self, problem, name)
        #Represents the map from the new action to the old action
        self._new_to_old: Dict['unified_planning.model.Action', 'unified_planning.model.Action'] = {}
        #represents a mapping from the action of the original problem to action of the new one.
        self._old_to_new: Dict['unified_planning.model.Action', List['unified_planning.model.Action']] = {}

    def powerset(self, iterable: Iterable) -> Iterable:
        "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
        s = list(iterable)
        return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

    def get_rewritten_problem(self) -> 'unified_planning.model.Problem':
        '''Creates a problem that is a copy of the original problem
        but every conditional action or effect are removed.'''
        if self._new_problem is not None:
            return self._new_problem
        #NOTE that a different environment might be needed when multi-threading
        self._new_problem = self._problem.clone()
        self._new_problem.name = f'{self._name}_{self._problem.name}'
        self._new_problem.clear_timed_effects()
        for t, el in self._problem.timed_effects.items():
            for e in el:
                if e.is_conditional():
                    f, v = e.fluent.fluent(), e.value
                    if not f.type.is_bool_type():
                        raise UPProblemDefinitionError(f'The condition of effect: {e}\ncould not be removed without changing the problem.')
                    else:
                        em = self._env.expression_manager
                        c = e.condition
                        nv = self._simplifier.simplify(em.Or(em.And(c, v), em.And(em.Not(c), f)))
                        self._new_problem.add_timed_effect(t, e.fluent, nv)
                else:
                    self._new_problem._add_effect_instance(t, e.clone())
        self._new_problem.clear_actions()
        for ua in self._problem.unconditional_actions:
            new_uncond_action = ua.clone()
            self._new_problem.add_action(new_uncond_action)
            self._new_to_old[new_uncond_action] = ua
            self._map_old_to_new_action(ua, new_uncond_action)
        for action in self._problem.conditional_actions:
            if isinstance(action, unified_planning.model.InstantaneousAction):
                cond_effects = action.conditional_effects
                for p in self.powerset(range(len(cond_effects))):
                    new_action = action.clone()
                    new_action.name = self.get_fresh_name(action.name)
                    new_action.clear_effects()
                    for e in action.unconditional_effects:
                        new_action._add_effect_instance(e.clone())
                    for i, e in enumerate(cond_effects):
                        if i in p:
                            # positive precondition
                            new_action.add_precondition(e.condition)
                            ne = unified_planning.model.Effect(e.fluent, e.value, self._env.expression_manager.TRUE(), e.kind)
                            new_action._add_effect_instance(ne)
                        else:
                            #negative precondition
                            new_action.add_precondition(self._env.expression_manager.Not(e.condition))
                    #new action is created, then is checked if it has any impact and if it can be simplified
                    if len(new_action.effects) > 0:
                        action_is_feasible, simplified_preconditions = self._check_and_simplify_preconditions(new_action)
                        if action_is_feasible:
                            new_action._set_preconditions(simplified_preconditions)
                            self._new_to_old[new_action] = action
                            self._map_old_to_new_action(action, new_action)
                            self._new_problem.add_action(new_action)
            elif isinstance(action, unified_planning.model.DurativeAction):
                timing_cond_effects: Dict['unified_planning.model.Timing', List['unified_planning.model.Effect']] = action.conditional_effects
                cond_effects_timing: List[Tuple['unified_planning.model.Effect', 'unified_planning.model.Timing']] = [(e, t) for t, el in timing_cond_effects.items() for e in el]
                for p in self.powerset(range(len(cond_effects_timing))):
                    new_action = action.clone()
                    new_action.name = self.get_fresh_name(action.name)
                    new_action.clear_effects()
                    for t, el in action.unconditional_effects.items():
                        for e in el:
                            new_action._add_effect_instance(t, e.clone())
                    for i, (e, t) in enumerate(cond_effects_timing):
                        if i in p:
                            # positive precondition
                            new_action.add_condition(t, e.condition)
                            ne = unified_planning.model.Effect(e.fluent, e.value, self._env.expression_manager.TRUE(), e.kind)
                            new_action._add_effect_instance(t, ne)
                        else:
                            #negative precondition
                            new_action.add_condition(t, self._env.expression_manager.Not(e.condition))
                    #new action is created, then is checked if it has any impact and if it can be simplified
                    if len(new_action.effects) > 0:
                        action_is_feasible, simplified_conditions = self._check_and_simplify_conditions(new_action)
                        if action_is_feasible:
                            new_action.clear_conditions()
                            for interval, c in simplified_conditions:
                                new_action.add_condition(interval, c)
                            self._new_to_old[new_action] = action
                            self._map_old_to_new_action(action, new_action)
                            self._new_problem.add_action(new_action)
            else:
                raise NotImplementedError
        return self._new_problem

    def _map_old_to_new_action(self, old_action, new_action):
        if old_action in self._old_to_new:
            self._old_to_new[old_action].append(new_action)
        else:
            self._old_to_new[old_action] = [new_action]

    def get_original_action(self, action: 'unified_planning.model.Action') -> 'unified_planning.model.Action':
        '''After the method get_rewritten_problem is called, this function maps
        the actions of the transformed problem into the actions of the original problem.'''
        return self._new_to_old[action]

    def get_transformed_actions(self, action: 'unified_planning.model.Action') -> List['unified_planning.model.Action']:
        '''After the method get_rewritten_problem is called, this function maps
        the actions of the original problem into the actions of the transformed problem.'''
        return self._old_to_new[action]
