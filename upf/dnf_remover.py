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


import upf.operators as op
import upf.walkers as walkers
from upf.walkers.identitydag import IdentityDagWalker
from upf.plan import SequentialPlan, ActionInstance
from upf.problem import Problem
from upf.action import Action
from upf.object import Object
from upf.effect import Effect
from upf.fnode import FNode
from upf.variable import Variable
from upf.simplifier import Simplifier
from upf.substituter import Substituter
from upf.expression import Expression
from typing import List, Dict
from itertools import product
from collections import OrderedDict


class DnfRemover():
    '''Dnf remover class:
    this class requires a problem and offers the capability
    to transform a problem with preconditions not in the DNF form
    into one with all the preconditions in DNF form.
    '''
    def __init__(self, problem: Problem):
        self._problem = problem
        self._env = problem.env
        self._dnf_problem = None
        self._action_mapping: Dict[Action, Action] = {}
        #NOTE no simplification are made. But it's possible to add them in key points
        self._simplifier = Simplifier(self._env)

    def get_rewritten_problem(self) -> Problem:
        '''Creates a problem that is a copy of the original problem
        but every quantifier is removed.'''
        if self._dnf_problem is not None:
            return self._dnf_problem
        #NOTE that a different environment might be needed when multy-threading
        new_problem = self._create_problem_copy_without_actions()
        for a in self._problem.actions().values():
            na = self._action_without_quantifiers(a)
            new_problem.add_action(na)
        for g in self._problem.goals():
            ng = self._expression_quantifier_remover.remove_quantifiers(g, self._problem)
            new_problem.add_goal(ng)
        return new_problem

    def _create_problem_copy_without_actions(self):
        '''Creates the shallow copy of a problem, without adding the actions
        with quantifiers and by pushing them to the stack
        '''
        new_problem: Problem = Problem("noquantifiers_" + str(self._problem.name()), self._env)
        for f in self._problem.fluents().values():
            new_problem.add_fluent(f)
        for o in self._problem.all_objects():
            new_problem.add_object(o)
        for fl, v in self._problem.initial_values().items():
            new_problem.set_initial_value(fl, v)
        for g in self._problem.goals():
            new_problem.add_goal(g)
        return new_problem

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

    def rewrite_back_plan(self, unquantified_sequential_plan: SequentialPlan) -> SequentialPlan:
        '''Takes the sequential plan of the problem (created with
        the method "self.get_rewritten_problem()" and translates the plan back
        to be a plan of the original problem.'''
        quantified_actions = [ActionInstance(self._problem.action(ai.action().name()), ai.actual_parameters()) for ai in unquantified_sequential_plan.actions()]
        return SequentialPlan(quantified_actions)
