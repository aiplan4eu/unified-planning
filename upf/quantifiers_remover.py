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


class ExpressionQuantifierRemover(IdentityDagWalker):
    def __init__(self, problem: Problem, env):
        self._env = env
        IdentityDagWalker.__init__(self, self._env, True)
        self._problem = problem
        self._substituter = Substituter(self._env)

    def remove_quantifiers(self, expression: FNode):
        return self.walk(expression)

    @walkers.handles(op.EXISTS)
    def walk_exists(self, expression: FNode, args: List[FNode], **kwargs) -> FNode:
        vars: List[Variable] = expression.variables()
        type_list = [v.type() for v in vars]
        possible_objects: List[List[Object]] = []
        for t in type_list:
            possible_objects.append(self._problem.objects(t))
        #product([1,2], [3,4]) = (1,3) (1,4) (2,3) (2,4)
        possible_combinations = list(product(*possible_objects))
        subs_results = []
        for o in possible_combinations:
            ol: List[Object] = list(o)
            subs: Dict[Expression, Expression] = dict(zip(vars, ol))
            subs_results.append(self._substituter.substitute(args[0], subs))
        return self._env.expression_manager.Or(subs_results)

    @walkers.handles(op.FORALL)
    def walk_forall(self, expression: FNode, args: List[FNode], **kwargs) -> FNode:
        vars = expression.variables()
        type_list = [v.type() for v in vars]
        possible_objects: List[List[Object]] = []
        for t in type_list:
            possible_objects.append(self._problem.objects(t))
        #product([1,2], [3,4]) = (1,3) (1,4) (2,3) (2,4)
        possible_combinations = list(product(*possible_objects))
        subs_results = []
        for o in possible_combinations:
            ol: List[Object] = list(o)
            subs: Dict[Expression, Expression] = dict(zip(vars, ol))
            subs_results.append(self._substituter.substitute(args[0], subs))
        return self._env.expression_manager.And(subs_results)


class QuantifiersRemover():
    '''Conditional effect remover class:
    this class requires a problem and offers the capability
    to transform a problem with quantifiers into a problem without.
    '''
    def __init__(self, problem: Problem):
        self._problem = problem
        self._action_mapping: Dict[Action, Action] = {}
        self._env = problem.env
        self._counter: int = 0
        self._noquantifier_problem = None
        #NOTE no simplification are made. But it's possible to add them in key points
        self._simplifier = Simplifier(self._env)
        self._expression_quantifier_remover = ExpressionQuantifierRemover(self._problem, self._env)

    def get_rewritten_problem(self) -> Problem:
        '''Creates a problem that is a copy of the original problem
        but every quantifier is removed.'''
        if self._noquantifier_problem is not None:
            return self._noquantifier_problem
        #NOTE that a different environment might be needed when multy-threading
        new_problem = self._create_problem_copy_without_actions_and_goals()
        for a in self._problem.actions().values():
            na = self._action_without_quantifiers(a)
            new_problem.add_action(na)
            self._action_mapping[na] = a
        for g in self._problem.goals():
            ng = self._expression_quantifier_remover.remove_quantifiers(g)
            new_problem.add_goal(ng)
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

    def _action_without_quantifiers(self, action) -> Action:
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
            np = self._expression_quantifier_remover.remove_quantifiers(p)
            new_action.add_precondition(np)
        for e in action.effects():
            if e.is_conditional():
                nc = self._expression_quantifier_remover.remove_quantifiers(e.condition())
            else:
                nc = self._env.expression_manager.TRUE()
            nv = self._expression_quantifier_remover.remove_quantifiers(e.value())
            ne = Effect(e.fluent(), nv, nc, e.kind())
            new_action._add_effect_instance(ne)
        return new_action

    def rewrite_back_plan(self, unconditional_sequential_plan: SequentialPlan) -> SequentialPlan:
        '''Takes the sequential plan of the problem (created with
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
