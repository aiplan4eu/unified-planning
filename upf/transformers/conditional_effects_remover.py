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
from upf.model.timing import Timing
from upf.plan import SequentialPlan, ActionInstance, TimeTriggeredPlan
from upf.model.problem import Problem
from upf.model.action import Action, InstantaneousAction, DurativeAction
from upf.model.effect import Effect
from upf.exceptions import UPFProblemDefinitionError
from upf.model.fnode import FNode
from upf.simplifier import Simplifier
from upf.transformers.transformer import Transformer
from typing import Iterable, List, Dict, Tuple, Union
from itertools import chain, combinations


class ConditionalEffectsRemover(Transformer):
    '''Conditional effect remover class:
    this class requires a problem and offers the capability
    to transform a conditional problem into an unconditional one.

    This is done by substituting every conditional action with different
    actions representing every possible branch of the original action.'''
    def __init__(self, problem: Problem):
        Transformer.__init__(self, problem)
        self._new_to_old = {}
        self._old_to_new = {}
        self._counter: int = 0

    def powerset(self, iterable: Iterable) -> Iterable:
        "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
        s = list(iterable)
        return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

    def get_rewritten_problem(self) -> Problem:
        '''Creates a problem that is a copy of the original problem
        but every conditional action is removed and all the possible
        branches of the conditional action are added as non-conditional
        actions.'''
        if self._new_problem is not None:
            return self._new_problem
        #NOTE that a different environment might be needed when multi-threading
        self._create_problem_copy("unconditional")
        assert self._new_problem is not None
        self._new_problem_add_fluents()
        self._new_problem_add_objects()
        self._new_problem_add_initial_values()
        for t, el in self._problem.timed_effects().items():
            for e in el:
                if e.is_conditional():
                    f, v = e.fluent().fluent(), e.value()
                    if not f.type().is_bool_type():
                        raise UPFProblemDefinitionError(f'The condition of effect: {e}\ncould not be removed without changing the problem.')
                    else:
                        em = self._env.expression_manager
                        c = e.condition()
                        nv = self._simplifier.simplify(em.Or(em.And(c, v), em.And(em.Not(c), f)))
                        self._new_problem.add_timed_effect(t, f, nv)
                else:
                    self._new_problem.add_timed_effect(t, e)
        self._new_problem_add_timed_goals()
        self._new_problem_add_maintain_goals()
        self._new_problem_add_goals()
        for ua in self._problem.unconditional_actions():
            self._new_problem.add_action(ua)
        for action in self._problem.conditional_actions():
            self._counter = 0
            if isinstance(action, InstantaneousAction):
                cond_effects = action.conditional_effects()
                for p in self.powerset(range(len(cond_effects))):
                    na = self._create_action_copy(action, self._counter)
                    self._action_add_preconditions(action, na)
                    for e in action.unconditional_effects():
                        na._add_effect_instance(e)
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
                            self._new_to_old[na] = action
                            self._map_old_to_new_action(action, na)
                            self._new_problem.add_action(na)
                            self._counter += 1
            elif isinstance(action, DurativeAction):
                timing_cond_effects: Dict[Timing, List[Effect]] = action.conditional_effects()
                cond_effects_timing: List[Tuple[Effect, Timing]] = [(e, t) for t, el in timing_cond_effects.items() for e in el]
                for p in self.powerset(range(len(cond_effects_timing))):
                    nda = self._create_durative_action_copy(action, self._counter)
                    self._durative_action_add_conditions(action, nda)
                    self._durative_action_add_durative_conditions(action, nda)
                    for t, e in action.unconditional_effects():
                        nda._add_effect_instance(t, e)
                    for i, (e, t) in enumerate(cond_effects_timing):
                        if i in p:
                            # positive precondition
                            nda.add_condition(t, e.condition())
                            ne = Effect(e.fluent(), e.value(), self._env.expression_manager.TRUE(), e.kind())
                            nda._add_effect_instance(t, ne)
                        else:
                            #negative precondition
                            nda.add_condition(t, self._env.expression_manager.Not(e.condition()))
                    #new action is created, then is checked if it has any impact and if it can be simplified
                    if len(nda.effects()) > 0:
                        if self._check_and_simplify_conditions(nda):
                            self._new_to_old[nda] = action
                            self._map_old_to_new_action(action, nda)
                            self._new_problem.add_action(nda)
                            self._counter += 1
            else:
                raise NotImplementedError
        return self._new_problem
