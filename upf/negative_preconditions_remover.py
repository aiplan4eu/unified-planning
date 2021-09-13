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
"""This module defines the negative preconditions remover class."""

from collections import OrderedDict
from upf.plan import SequentialPlan, ActionInstance
from upf.problem import Problem
from upf.action import Action
from upf.effect import Effect
from upf.fnode import FNode
from upf.simplifier import Simplifier
from typing import Iterable, List, Dict, Tuple
from itertools import chain, combinations


class NegativePreconditionsRemover():
    '''Negative preconditions remover class:
    this class requires a problem and offers the capability
    to transform a problem with negative preconditions into one
    without negative preconditions.

    This is done by substituting every fluent that appears with a Not into the preconditions
    with different fluent representing  his negation.'''
    def __init__(self, problem: Problem):
        self._problem = problem
        self._env = problem.env
        self._positive_problem = None
        self._fluent_mapping: Dict[FNode, FNode] = {}
        self._count = 0
        #NOTE no simplification are made. But it's possible to add them in key points
        self._simplifier = Simplifier(self._env)

    def get_rewritten_problem(self) -> Problem:
        '''Creates a problem that is a copy of the original problem
        but every ngeative fluent into action preconditions or overall
        goal is replaced by the fluent representing his negative.'''
        if self._positive_problem is not None:
            return self._positive_problem
        #NOTE that a different environment might be needed when multy-threading
        new_problem = self._create_problem_copy_without_actions_and_goals()
        for a in self._problem.actions().values():
            na = self._action_without_negative_preconditions(a)
            new_problem.add_action(na)
        for g in self._problem.goals():
            ng = self._expression_quantifier_remover.remove_quantifiers(g, self._problem)
            new_problem.add_goal(ng)
        self._positive_problem = new_problem
        return new_problem

    def _create_problem_copy_without_actions_and_goals(self):
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
        return new_problem

    def _action_without_negative_preconditions(self, action) -> Action:
        new_action = Action(action.name(), OrderedDict((ap.name(), ap.type()) for ap in action.parameters()), self._env)
#HERE
        for p in action.preconditions():
            np = self._expression_quantifier_remover.remove_quantifiers(p, self._problem)
            new_action.add_precondition(np)
        for e in action.effects():
            new_action._add_effect_instance(e)
        return new_action

    def rewrite_back_plan(self, unquantified_sequential_plan: SequentialPlan) -> SequentialPlan:
        '''Takes the sequential plan of the problem (created with
        the method "self.get_rewritten_problem()" and translates the plan back
        to be a plan of the original problem.'''
        quantified_actions = [ActionInstance(self._problem.action(ai.action().name()), ai.actual_parameters()) for ai in unquantified_sequential_plan.actions()]
        return SequentialPlan(quantified_actions)
