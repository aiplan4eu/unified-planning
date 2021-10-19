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


from upf.temporal import DurativeAction
import upf.operators as op
import upf.walkers as walkers
from upf.walkers.identitydag import IdentityDagWalker
from upf.transformers.remover import Remover
from upf.problem import Problem
from upf.action import Action
from upf.object import Object
from upf.effect import Effect
from upf.fnode import FNode
from upf.variable import Variable
from upf.simplifier import Simplifier
from upf.substituter import Substituter
from upf.expression import Expression
from typing import List, Dict, Union
from itertools import product
from collections import OrderedDict


class ExpressionQuantifierRemover(IdentityDagWalker):
    def __init__(self, env):
        self._env = env
        IdentityDagWalker.__init__(self, self._env, True)
        self._substituter = Substituter(self._env)

    def remove_quantifiers(self, expression: FNode, problem: Problem):
        self._problem = problem
        return self.walk(expression)

    def _help_walk_quantifiers(self, expression: FNode, args: List[FNode]) -> List[FNode]:
        vars = expression.variables()
        type_list = [v.type() for v in vars]
        possible_objects: List[List[Object]] = [self._problem.objects(t) for t in type_list]
        #product of n iterables returns a generator of tuples where
        # every tuple has n elements and the tuples make every possible
        # combination of 1 item for each iterable. For example:
        #product([1,2], [3,4], [5,6], [7]) =
        # (1,3,5,7) (1,3,6,7) (1,4,5,7) (1,4,6,7) (2,3,5,7) (2,3,6,7) (2,4,5,7) (2,4,6,7)
        subs_results = []
        for o in product(*possible_objects):
            subs: Dict[Expression, Expression] = dict(zip(vars, list(o)))
            subs_results.append(self._substituter.substitute(args[0], subs))
        return subs_results

    @walkers.handles(op.EXISTS)
    def walk_exists(self, expression: FNode, args: List[FNode], **kwargs) -> FNode:
        subs_results = self._help_walk_quantifiers(expression, args)
        return self._env.expression_manager.Or(subs_results)

    @walkers.handles(op.FORALL)
    def walk_forall(self, expression: FNode, args: List[FNode], **kwargs) -> FNode:
        subs_results = self._help_walk_quantifiers(expression, args)
        return self._env.expression_manager.And(subs_results)


class QuantifiersRemover(Remover):
    '''Quantifiers remover class:
    this class requires a problem and offers the capability
    to transform a problem with quantifiers into a problem without.
    '''
    def __init__(self, problem: Problem):
        Remover.__init__(self, problem)
        #NOTE no simplification are made. But it's possible to add them in key points
        self._expression_quantifier_remover = ExpressionQuantifierRemover(self._env)

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
        #NOTE that a different environment might be needed when multy-threading
        self._create_problem_copy("unquantified")
        self._new_problem_add_fluents()
        self._new_problem_add_objects()
        self._new_problem_add_initial_values()
        assert self._new_problem is not None

        for a in self._problem.actions().values():
            if isinstance(a, Action):
                na = self._action_without_quantifiers(a)
                self._new_problem.add_action(na)
            elif isinstance(a, DurativeAction):
                nda = self._durative_action_without_quantifiers(a)
                self._new_problem.add_action(nda)
            else:
                raise NotImplementedError
        for t, el in self._problem.timed_effects().items():
            for e in el:
                self._new_problem._add_effect_instance(t, self._effect_without_quantifiers(e))
        for t, gl in self._problem.timed_goals().items():
            for g in gl:
                ng = self._expression_quantifier_remover.remove_quantifiers(g, self._problem)
                self._new_problem.add_timed_goal(t, ng)
        for i, gl in self._problem.maintain_goals().items():
            for g in gl:
                ng = self._expression_quantifier_remover.remove_quantifiers(g, self._problem)
                self._new_problem.add_maintain_goal(i, ng)
        for g in self._problem.goals():
            ng = self._expression_quantifier_remover.remove_quantifiers(g, self._problem)
            self._new_problem.add_goal(ng)
        return self._new_problem

    def _durative_action_without_quantifiers(self, action) -> DurativeAction:
        new_action = self._create_durative_action_copy(action)

        for t, cl in action.conditions().items():
            for c in cl:
                nc = self._expression_quantifier_remover.remove_quantifiers(c, self._problem)
                new_action.add_condition(t, nc)
        for i, cl in action.durative_conditions().items():
            for c in cl:
                nc = self._expression_quantifier_remover.remove_quantifiers(c, self._problem)
                new_action.add_durative_condition(i, nc)
        for t, el in action.effects().items():
            for e in el:
                new_action._add_effect_instance(t, self._effect_without_quantifiers(e))
        return new_action

    def _effect_without_quantifiers(self, effect):
        if effect.is_conditional():
            nc = self._expression_quantifier_remover.remove_quantifiers(effect.condition(), self._problem)
        else:
            nc = self._env.expression_manager.TRUE()
        nv = self._expression_quantifier_remover.remove_quantifiers(effect.value(), self._problem)
        return Effect(effect.fluent(), nv, nc, effect.kind())

    def _action_without_quantifiers(self, action) -> Action:
        new_action = self._create_action_copy(action)
        for p in action.preconditions():
            np = self._expression_quantifier_remover.remove_quantifiers(p, self._problem)
            new_action.add_precondition(np)
        for e in action.effects():
            new_action._add_effect_instance(self._effect_without_quantifiers(e))
        return new_action
