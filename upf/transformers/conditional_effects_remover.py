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
from upf.temporal import DurativeAction, Timing
from upf.plan import SequentialPlan, ActionInstance, TimeTriggeredPlan
from upf.problem import Problem
from upf.action import ActionInterface, Action
from upf.effect import Effect
from upf.fnode import FNode
from upf.simplifier import Simplifier
from upf.transformers.remover import Remover
from typing import Iterable, List, Dict, Tuple, Union
from itertools import chain, combinations


class ConditionalEffectsRemover(Remover):
    '''Conditional effect remover class:
    this class requires a problem and offers the capability
    to transform a conditional problem into an unconditional one.

    This is done by substituting every conditional action with different
    actions representing every possible branch of the original action.'''
    def __init__(self, problem: Problem):
        Remover.__init__(self, problem)
        self._action_mapping = {}
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
        #NOTE that a different environment might be needed when multy-threading
        self._create_problem_copy("unconditional")
        assert self._new_problem is not None
        self._new_problem_add_fluents()
        self._new_problem_add_objects()
        self._new_problem_add_initial_values()
        for t, el in self._problem.timed_effects():
            for e in el:
                if e.is_conditional():
                    raise # NOTE is it a problem if a timed_effect is conditional? It should be if this class is used!
                self._new_problem.add_timed_effect(t, e)
        self._new_problem_add_timed_goals()
        self._new_problem_add_mantain_goals()
        self._new_problem_add_goals()
        for ua in self._problem.unconditional_actions():
            self._new_problem.add_action(ua)
        for action in self._problem.conditional_actions():
            self._counter = 0
            if isinstance(action, Action):
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
                            self._action_mapping[na] = action
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
                            self._action_mapping[nda] = action
                            self._new_problem.add_action(nda)
                            self._counter += 1
            else:
                raise NotImplementedError
        return self._new_problem

    def _check_and_simplify_conditions(self, action: DurativeAction) -> bool:
        '''Simplifies conditions and if it is False (a contraddiction)
        returns False, otherwise returns True.
        If the simplification is True (a tautology) removes all conditions at the given timing.
        If the simplification is still an AND rewrites back every "arg" of the AND
        in the conditions
        If the simplification is not an AND sets the simplification as the only
        condition at the given timing.'''
        #action conditions
        #tlc = timing list condition
        tlc: Dict[Timing, List[FNode]] = action.conditions()
        if len(tlc) == 0:
            return True
        # t = timing, lc = list condition
        for t, lc in tlc.copy().items():
            #conditions (as an And FNode)
            c = self._env.expression_manager.And(lc)
            #conditions simplified
            cs = self._simplifier.simplify(c)
            #new action conditions
            nac: List[FNode] = []
            if cs.is_bool_constant():
                if not cs.bool_constant_value():
                    return False
            else:
                if cs.is_and():
                    nac.extend(cs.args())
                else:
                    nac.append(cs)
            action._set_conditions(t, nac)
        return True

    def _check_and_simplify_preconditions(self, action: Action) -> bool:
        '''Simplifies preconditions and if it is False (a contraddiction)
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
