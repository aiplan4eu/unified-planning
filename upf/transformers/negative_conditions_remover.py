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
from upf.fluent import Fluent
from upf.transformers.transformer import Transformer
from upf.problem import Problem
from upf.action import InstantaneousAction, DurativeAction
from upf.fnode import FNode
from upf.walkers.identitydag import IdentityDagWalker
from upf.exceptions import UPFExpressionDefinitionError, UPFProblemDefinitionError
from typing import List, Dict, Union

class NegativeFluentRemover(IdentityDagWalker):
    def __init__(self, env):
        self._env = env
        IdentityDagWalker.__init__(self, self._env)
        self._fluent_mapping: Dict[Fluent, Fluent] = {}

    def remove_negative_fluents(self, expression:FNode) -> FNode:
        return self.walk(expression)

    def walk_not(self, expression: FNode, args: List[FNode], **kwargs) -> FNode:
        assert len(args) == 1
        if not args[0].is_fluent_exp():
            raise UPFExpressionDefinitionError(f"Expression: {expression} is not in NNF.")
        neg_fluent = self._fluent_mapping.get(args[0].fluent(), None)
        if neg_fluent is not None:
            return self._env.expression_manager.FluentExp(neg_fluent, tuple(args[0].args()))
        f = args[0].fluent()
        nf = Fluent(f.name()+"__negated__", f.type(), f.signature(), f._env)
        self._fluent_mapping[f] = nf
        return self._env.expression_manager.FluentExp(nf, tuple(args[0].args()))


class NegativeConditionsRemover(Transformer):
    '''Negative conditions remover class:
    this class requires a problem and offers the capability
    to transform a problem with negative conditions into one
    without negative conditions.

    This is done by substituting every fluent that appears with a Not into the conditions
    with different fluent representing  his negation.'''
    def __init__(self, problem: Problem):
        Transformer.__init__(self, problem)
        self._count = 0
        #NOTE no simplification are made. But it's possible to add them in key points
        self._fluent_remover = NegativeFluentRemover(self._env)

    def get_rewritten_problem(self) -> Problem:
        '''Creates a problem that is a copy of the original problem
        but every ngeative fluent into action preconditions or overall
        goal is replaced by the fluent representing his negative.'''
        if self._new_problem is not None:
            return self._new_problem
        #NOTE that a different environment might be needed when multi-threading
        self._create_problem_copy('no_negative_conditions')
        self._new_problem_add_objects()
        assert self._new_problem is not None
        self._modify_actions_and_goals()
        return self._new_problem

    def _modify_actions_and_goals(self):
        name_action_map: Dict[str, Union[InstantaneousAction, DurativeAction]] = {}
        for name, action in self._problem.actions().items():
            if isinstance(action, InstantaneousAction):
                new_action = self._create_action_copy(action)
                for p in action.preconditions():
                    np = self._fluent_remover.remove_negative_fluents(p)
                    new_action.add_precondition(np)
                name_action_map[name] = new_action
            elif isinstance(action, DurativeAction):
                new_durative_action = self._create_durative_action_copy(action)
                for t, cl in action.conditions().items():
                    for c in cl:
                        nc = self._fluent_remover.remove_negative_fluents(c)
                        new_durative_action.add_condition(t, nc)
                for i, cl in action.durative_conditions().items():
                    for c in cl:
                        nc = self._fluent_remover.remove_negative_fluents(c)
                        new_durative_action.add_durative_condition(i, nc)
                name_action_map[name] = new_durative_action
            else:
                raise NotImplementedError

        for t, gl in self._problem.timed_goals().items():
            for g in gl:
                ng = self._fluent_remover.remove_negative_fluents(g)
                self._new_problem.add_timed_goal(t, ng)
        for i, gl in self._problem.maintain_goals().items():
            for g in gl:
                ng = self._fluent_remover.remove_negative_fluents(g)
                self._new_problem.add_maintain_goal(i, ng)

        for g in self._problem.goals():
            ng = self._fluent_remover.remove_negative_fluents(g)
            self._new_problem.add_goal(ng)

        fluent_mapping = self._fluent_remover._fluent_mapping
        for f in self._problem.fluents().values():
            self._new_problem.add_fluent(f)
            fneg = fluent_mapping.get(f, None)
            if fneg is not None:
                self._new_problem.add_fluent(fneg)

        for fl, v in self._problem.initial_values().items():
            fneg = fluent_mapping.get(fl.fluent(), None)
            if v.is_bool_constant():
                self._new_problem.set_initial_value(fl, v)
                if fneg is not None:
                    if v.bool_constant_value():
                        self._new_problem.set_initial_value(self._env.expression_manager.FluentExp(fneg,
                        tuple(fl.args())), self._env.expression_manager.FALSE())
                    else:
                        self._new_problem.set_initial_value(self._env.expression_manager.FluentExp(fneg,
                        tuple(fl.args())), self._env.expression_manager.TRUE())
            else:
                raise UPFProblemDefinitionError(f"Initial value: {v} of fluent: {fl} is not a boolean constant. An initial value MUST be a Boolean constant.")

        for name, action in self._problem.actions().items():
            if isinstance(action, InstantaneousAction):
                new_action = name_action_map[name]
                for e in action.effects():
                    if e.is_conditional():
                        raise UPFProblemDefinitionError(f"Effect: {e} of action: {action} is conditional. Try using the ConditionalEffectsRemover before the NegativeConditionsRemover.")
                    fl, v = e.fluent(), e.value()
                    fneg = fluent_mapping.get(fl.fluent(), None)
                    if v.is_bool_constant():
                        new_action.add_effect(fl, v)
                        if fneg is not None:
                            if v.bool_constant_value():
                                new_action.add_effect(self._env.expression_manager.FluentExp(fneg, tuple(fl.args())), self._env.expression_manager.FALSE())
                            else:
                                new_action.add_effect(self._env.expression_manager.FluentExp(fneg, tuple(fl.args())), self._env.expression_manager.TRUE())
                    else:
                        raise UPFProblemDefinitionError(f"Effect; {e} assigns value: {v} to fluent: {fl}, but value is not a boolean constant.")
                self._new_problem.add_action(new_action)
            elif isinstance(action, DurativeAction):
                new_durative_action = name_action_map[name]
                new_durative_action.set_duration_constraint(action.duration())
                for t, el in action.effects().items():
                    for e in el:
                        if e.is_conditional():
                            raise UPFProblemDefinitionError(f"Effect: {e} of action: {action} is conditional. Try using the ConditionalEffectsRemover before the NegativeConditionsRemover.")
                        fl, v = e.fluent(), e.value()
                        fneg = fluent_mapping.get(fl.fluent(), None)
                        if v.is_bool_constant():
                            new_durative_action.add_effect(t, fl, v)
                            if fneg is not None:
                                if v.bool_constant_value():
                                    new_durative_action.add_effect(t, self._env.expression_manager.FluentExp(fneg, tuple(fl.args())), self._env.expression_manager.FALSE())
                                else:
                                    new_durative_action.add_effect(t, self._env.expression_manager.FluentExp(fneg, tuple(fl.args())), self._env.expression_manager.TRUE())
                        else:
                            raise UPFProblemDefinitionError(f"Effect; {e} assigns value: {v} to fluent: {fl}, but value is not a boolean constant.")
                self._new_problem.add_action(new_durative_action)
            else:
                raise NotImplementedError

        for t, el in self._problem.timed_effects().items():
            for e in el:
                if e.is_conditional():
                    raise UPFProblemDefinitionError(f"Timed effect: {e} at time {t} is conditional. Try using the ConditionalEffectsRemover before the NegativeConditionsRemover.")
                fl, v = e.fluent(), e.value()
                fneg = fluent_mapping.get(fl.fluent(), None)
                if v.is_bool_constant():
                    self._new_problem.add_timed_effect(t, f, v)
                    if fneg is not None:
                        if v.bool_constant_value():
                            self._new_problem.add_timed_effect(t, self._env.expression_manager.FluentExp(fneg, tuple(fl.args())), self._env.expression_manager.FALSE())
                        else:
                            self._new_problem.add_timed_effect(t, self._env.expression_manager.FluentExp(fneg, tuple(fl.args())), self._env.expression_manager.TRUE())
                else:
                    raise UPFProblemDefinitionError(f"Effect; {e} assigns value: {v} to fluent: {fl}, but value is not a boolean constant.")
