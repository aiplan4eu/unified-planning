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
from upf.fnode import FNode
from upf.simplifier import Simplifier
from typing import Iterable, List, Dict, Tuple
from itertools import chain, combinations


class ConditionalEffectsRemover():
    '''Conditional effect remover class:
    this class requires a problem and offers the capability
    to transform a conditional problem into an unconditional one.

    This is done by substituting every conditional action with different
    actions representing every possible branch of the original action.'''
    def __init__(self, problem: Problem):
        self._problem = problem
        self._action_mapping: Dict[Action, Action] = {}
        self._env = problem.env
        self._counter: int = 0
        self._unconditional_problem = None
        self._simplifier = Simplifier(self._env)

    def powerset(self, iterable: Iterable) -> Iterable:
        "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
        s = list(iterable)
        return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

    def get_rewritten_problem(self) -> Problem:
        '''Creates a problem that is a copy of the original problem
        but every conditional action is removed and all the possible
        branches of the conditional action are added as non-conditional
        actions.'''
        if self._unconditional_problem is not None:
            return self._unconditional_problem
        #cycle over all the actions
        #NOTE that a different environment might be needed when multy-threading
        new_problem = self._create_problem_copy()

        for action in self._problem.conditional_actions():
            cond_effects = list(action.conditional_effects())
            for p in self.powerset(range(len(cond_effects))):
                na = self._shallow_copy_action_without_conditional_effects(action)
                for i, e in enumerate(cond_effects):
                    if i in p:
                        # positive precondition
                        na.add_precondition(e.condition())
                        ne = Effect(e.fluent(), e.value(), self._env.expression_manager.TRUE(), e.kind())
                        na._add_effect_instance(ne)
                    else:
                        #negative precondition
                        na.add_precondition(self._env.expression_manager.Not(e.condition()))
                #new action is created, then is checked if it has any impact and if it can be simplified
                if len(na.effects()) > 0:
                    if self._check_and_simplify_preconditions(na):
                        self._action_mapping[na] = action
                        new_problem.add_action(na)
        return new_problem

    def _check_and_simplify_preconditions(self, action: Action) -> bool:
        '''Simplifies preconditions and if it False (a contraddiction)
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

    def _shallow_copy_action_without_conditional_effects(self, action: Action) -> Action:
        #emulates a do-while loop: searching for an available name
        is_unavailable_name = True
        while is_unavailable_name:
            new_action_name = action.name()+ "_" +str(self._counter)
            self._counter = self._counter + 1
            is_unavailable_name = self._problem.has_action(new_action_name)
        new_parameters = OrderedDict()
        for ap in action.parameters():
            new_parameters[ap.name()] = ap.type()
        new_action = Action(new_action_name, new_parameters, self._env)
        for p in action.preconditions():
            new_action.add_precondition(p)
        for e in action.unconditional_effects():
            new_action._add_effect_instance(e)
        return new_action

    def _create_problem_copy(self):
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
        for ua in self._problem.unconditional_actions():
                new_problem.add_action(ua)
        return new_problem

    def rewrite_back_plan(self, unconditional_sequential_plan: SequentialPlan) -> SequentialPlan:
        '''Takes the sequential plan of the non-conditional problem (created with
        the method "self.get_rewritten_problem()" and translates the plan back
        to be a plan of the original problem.'''
        uncond_actions = unconditional_sequential_plan.actions()
        cond_actions = []
        for ai in uncond_actions:
            if ai.action() in self._action_mapping:
                cond_actions.append(self._new_action_instance_original_name(ai))
            else:
                cond_actions.append(ai)
        return SequentialPlan(cond_actions)

    def _new_action_instance_original_name(self, ai: ActionInstance) -> ActionInstance:
        #original action
        oa = self._action_mapping[ai.action()]
        return ActionInstance(oa, ai.parameters())
