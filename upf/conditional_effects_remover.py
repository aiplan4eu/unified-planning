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
from upf.problem import Problem
from upf.action import Action
from upf.effect import Effect
from typing import List, Dict, Tuple


class ConditionalEffectsRemover():
    def __init__(self, problem: Problem):
        self._problem = problem
        self._action_mapping: Dict[str, str] = {}
        self._env = problem.env

    def get_unconditional_problem(self) -> Problem:
        #cycle over all the actions
        #Note that a different environment might be needed when multy-threading
        action_stack: List[Tuple[str, Action, int]] = []
        new_problem = self._create_problem_copy(action_stack)

        while len(action_stack) > 0:
            original_action_name, action, number = action_stack.pop()
            unchanged_effects = action.unconditional_effects()
            cond_effects = action.conditional_effects()
            effect_changed = cond_effects.pop()
            unchanged_effects.extend(cond_effects)
            #TODO parameters coping still missing!!
            #TODO shallow-copy creation in it's own dedicated function!!
            new_action_t = self._create_action_copy(action, original_action_name, number, unchanged_effects)
            number = number + 1
            new_action_f = self._create_action_copy(action, original_action_name, number, unchanged_effects)
            number = number + 1
            new_action_t.add_precondition(effect_changed.condition())
            new_effect = Effect(effect_changed.fluent(), effect_changed.value(),
                    self._env.expression_manager.TRUE(), effect_changed.kind())
            new_action_t.add_effect(new_effect)
            new_action_f.add_precondition(self._env.expression_manager.Not(effect_changed.condition()))
            if new_action_t.has_conditional_effects():
                action_stack.append((original_action_name, new_action_t, number))
                action_stack.append((original_action_name, new_action_f, number+2))
            else:
                new_problem.add_action(new_action_t)
                new_problem.add_action(new_action_f)
                self._action_mapping[new_action_t.name()] = original_action_name
                self._action_mapping[new_action_f.name()] = original_action_name

        return new_problem

    def _create_action_copy(self, action, original_action_name, number, unchanged_effects) -> Action:
        new_action_name = original_action_name+ "_" +str(number)
        new_parameters = OrderedDict()
        for ap in action.parameters():
            new_parameters[ap.name()] = ap.type()
        new_action = Action(new_action_name, new_parameters, self._env)


        for p in action.preconditions():
            new_action.add_precondition(p)
        for e in unchanged_effects:
            new_action.add_effect(e)
        return new_action

    def _create_problem_copy(self, action_stack) -> Problem:
        '''Creates the shallow copy of a problem, without adding the conditional actions
        and by pushing them to the stack
        '''
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
                action_stack.append((n, a, 0))
            else:
                new_problem.add_action(a)
        return new_problem
