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

from collections import OrderedDict
from upf.plan import SequentialPlan, ActionInstance
from upf.problem import Problem
from upf.action import Action
from upf.effect import Effect
from upf.simplifier import Simplifier
from typing import List, Dict, Tuple


class ConditionalEffectsRemover():
    '''Conditional effect remover class:
    this class requires a problem and offers the capability
    to transform a conditional problem into an unconditional one.

    This is done by substituting every conditional action with different
    actions representing every possible branch of the original action.'''
    def __init__(self, problem: Problem):
        self._problem = problem
        self._action_mapping: Dict[str, str] = {}
        self._env = problem.env
        self._counter: int = 0
        self._unconditional_problem = None
        self._simplifier = Simplifier(self._env)

    def get_rewritten_problem(self) -> Problem:
        '''Creates a problem that is a copy of the original problem
        but every conditional action is removed and all the possible
        branches of the conditional action are added as non-conditional
        actions.'''
        if self._unconditional_problem is not None:
            return self._unconditional_problem
        #cycle over all the actions
        #Note that a different environment might be needed when multy-threading
        action_stack: List[Tuple[str, Action]] = []
        new_problem, action_stack = self._create_problem_copy()

        while len(action_stack) > 0:
            original_action_name, action = action_stack.pop()
            unchanged_effects = [action.unconditional_effects().iter()]
            cond_effects = [action.conditional_effects().iter()]
            effect_changed = cond_effects.pop()
            #boolean that represents if the 2 actions created will be unconditional,
            #therefore inserted into the problem
            uncond_actions = (len(cond_effects) == 0)
            unchanged_effects.extend(cond_effects)
            #set up "new_action_t", that represents the 'then' branch of the conditional effect "effect_changed"
            new_action_t = self._create_action_copy(action, original_action_name, unchanged_effects, uncond_actions)
            new_action_t.add_precondition(effect_changed.condition())
            new_effect = Effect(effect_changed.fluent(), effect_changed.value(),
                    self._env.expression_manager.TRUE(), effect_changed.kind())
            new_action_t._add_effect_instance(new_effect)
            #set up "new_action_f", that represents the 'else' branch of the conditional effect "effect_changed"
            new_action_f = self._create_action_copy(action, original_action_name, unchanged_effects, uncond_actions)
            new_action_f.add_precondition(self._env.expression_manager.Not(effect_changed.condition()))
            #If the action should be added, check if it's preconditions can be simplified and if it's preconditions
            #are in contraddiction with eachother

            #NOTE: This simplification can be also done on the actions before appending them to the stack.
            if uncond_actions:
                if self._check_and_simplify_preconditions(new_action_t):
                    new_problem.add_action(new_action_t)
                    self._action_mapping[new_action_t.name()] = original_action_name
                if self._check_and_simplify_preconditions(new_action_f):
                    if len(new_action_f.effects()) > 0:
                        new_problem.add_action(new_action_f)
                        self._action_mapping[new_action_f.name()] = original_action_name
            else:
                action_stack.append((original_action_name, new_action_t))
                action_stack.append((original_action_name, new_action_f))
        return new_problem

    def _check_and_simplify_preconditions(self, action: Action) -> bool:
        '''Simplifies preconditions and if it False (a contraddiction)
        returns False, otherwise returns True.
        If the simplification is True (a tautology) removes all preconditions.
        If the simplification is still an AND rewrites back every "arg" of the AND
        in the preconditions
        If the simplification is not an AND sets the simplification as the only
        precondition.'''
        action_preconditions = action.preconditions()
        if len(action_preconditions) == 0:
            return True
        precondition = self._env.expression_manager.And(action_preconditions)
        precondition_simplified = self._simplifier.simplify(precondition)
        if precondition_simplified.is_bool_constant():
            if precondition_simplified.bool_constant_value():
                action_preconditions.clear()
            else:
                return False
        else:
            action_preconditions.clear()
            if precondition_simplified.is_and():
                action_preconditions.extend(precondition_simplified.args())
            else:
                action_preconditions.append(precondition_simplified)
        return True

    def _create_action_copy(self, action, original_action_name, unchanged_effects, uncond_action) -> Action:
        if uncond_action: #search for a free name
            #emulates a do-while loop
            is_unavailable_name = True
            while is_unavailable_name:
                new_action_name = original_action_name+ "_" +str(self._counter)
                self._counter = self._counter + 1
                is_unavailable_name = self._problem.has_action(new_action_name)
        else: #otherwise the name does not matter.
            new_action_name = original_action_name

        new_parameters = OrderedDict()
        for ap in action.parameters():
            new_parameters[ap.name()] = ap.type()
        new_action = Action(new_action_name, new_parameters, self._env)
        for p in action.preconditions():
            new_action.add_precondition(p)
        for e in unchanged_effects:
            new_action._add_effect_instance(e)
        return new_action

    def _create_problem_copy(self):
        '''Creates the shallow copy of a problem, without adding the conditional actions
        and by pushing them to the stack
        '''
        action_stack = []
        new_problem: Problem = Problem("unconditional_" + str(self._problem.name()), self._env)
        for f in self._problem.fluents().values():
            new_problem.add_fluent(f)
        for o in self._problem.all_objects():
            new_problem.add_object(o)
        for fl, v in self._problem.initial_values().items():
            new_problem.set_initial_value(fl, v)
        for g in self._problem.goals():
            new_problem.add_goal(g)
        for n, a in self._problem.actions().items():
            if a.has_conditional_effects():
                action_stack.append((n, a))
            else:
                new_problem.add_action(a)
        return (new_problem, action_stack)

    def rewrite_back_plan(self, unconditional_sequential_plan: SequentialPlan) -> SequentialPlan:
        '''Takes the sequential plan of the non-conditional problem (created with
        the method "self.get_rewritten_problem()" and translates the plan back
        to be a plan of the original problem.'''
        uncond_actions = unconditional_sequential_plan.actions()
        cond_actions = []
        for ai in uncond_actions:
            if ai.action().name() in self._action_mapping:
                cond_actions.append(self._new_action_instance_original_name(ai))
            else:
                cond_actions.append(ai)
        return SequentialPlan(cond_actions)

    def _new_action_instance_original_name(self, action_instance: ActionInstance) -> ActionInstance:
        action_name = self._action_mapping[action_instance.action().name()]
        action = self._problem.action(action_name)
        return ActionInstance(action, action_instance.parameters())
