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


import unified_planning as up
from unified_planning.transformers.transformer import Transformer
from unified_planning.model import Fluent, Problem, InstantaneousAction, DurativeAction, FNode, Action, Effect, Timing
from unified_planning.walkers.identitydag import IdentityDagWalker
from unified_planning.exceptions import UPExpressionDefinitionError, UPProblemDefinitionError
from typing import List, Dict, Union

class NegativeFluentRemover(IdentityDagWalker):
    def __init__(self, negative_conditions_remover, env):
        self._env = env
        IdentityDagWalker.__init__(self, self._env)
        self._fluent_mapping: Dict[Fluent, Fluent] = {}
        self._negative_conditions_remover = negative_conditions_remover

    def remove_negative_fluents(self, expression:FNode) -> FNode:
        return self.walk(expression)

    def walk_not(self, expression: FNode, args: List[FNode], **kwargs) -> FNode:
        assert len(args) == 1
        if not args[0].is_fluent_exp():
            raise UPExpressionDefinitionError(f"Expression: {expression} is not in NNF.")
        neg_fluent = self._fluent_mapping.get(args[0].fluent(), None)
        if neg_fluent is not None:
            return self._env.expression_manager.FluentExp(neg_fluent, tuple(args[0].args))
        f = args[0].fluent()
        nf = Fluent(self._negative_conditions_remover.get_fresh_name(f.name), f.type, f.signature, f._env)
        self._fluent_mapping[f] = nf
        return self._env.expression_manager.FluentExp(nf, tuple(args[0].args))

    @property
    def fluent_mapping(self) -> Dict[Fluent, Fluent]:
        return self._fluent_mapping


class NegativeConditionsRemover(Transformer):
    '''Negative conditions remover class:
    this class requires a problem and offers the capability
    to transform a problem with negative conditions into one
    without negative conditions.

    This is done by substituting every fluent that appears with a Not into the conditions
    with different fluent representing  his negation.'''
    def __init__(self, problem: Problem, name: str = 'ncrm'):
        Transformer.__init__(self, problem, name)
        #NOTE no simplification are made. But it's possible to add them in key points
        self._fluent_remover = NegativeFluentRemover(self, self._env)
        #Represents the map from the new action to the old action
        self._new_to_old: Dict[Action, Action] = {}
        #represents a mapping from the action of the original problem to action of the new one.
        self._old_to_new: Dict[Action, List[Action]] = {}

    def get_rewritten_problem(self) -> Problem:
        '''Creates a problem that is a copy of the original problem
        but every ngeative fluent into action preconditions or overall
        goal is replaced by the fluent representing his negative.'''
        if self._new_problem is not None:
            return self._new_problem
        #NOTE that a different environment might be needed when multi-threading

        self._new_problem = Problem(f'{self._name}_{self._problem.name}', self._env)
        for o in self._problem.all_objects:
            self._new_problem.add_object(o)
        assert self._new_problem is not None

        name_action_map: Dict[str, Union[InstantaneousAction, DurativeAction]] = {}
        for action in self._problem.actions:
            if isinstance(action, InstantaneousAction):
                new_action = action.clone()
                new_action.name = self.get_fresh_name(action.name)
                new_action.clear_preconditions()
                for p in action.preconditions:
                    np = self._fluent_remover.remove_negative_fluents(p)
                    new_action.add_precondition(np)
                for ce in new_action.conditional_effects:
                    ce.set_condition(self._fluent_remover.remove_negative_fluents(ce.condition))
                name_action_map[action.name] = new_action
            elif isinstance(action, DurativeAction):
                new_durative_action = action.clone()
                new_durative_action.name = self.get_fresh_name(action.name)
                new_durative_action.clear_conditions()
                for i, cl in action.conditions.items():
                    for c in cl:
                        nc = self._fluent_remover.remove_negative_fluents(c)
                        new_durative_action.add_condition(i, nc)
                for t, cel in new_durative_action.conditional_effects.items():
                    for ce in cel:
                        ce.set_condition(self._fluent_remover.remove_negative_fluents(ce.condition))
                name_action_map[action.name] = new_durative_action
            else:
                raise NotImplementedError

        for t, el in self._problem.timed_effects.items():
            for e in el:
                self._new_problem._add_effect_instance(t, e.clone())

        for t, el in self._new_problem.timed_effects.items():
            for e in el:
                if e.is_conditional():
                    e.set_condition(self._fluent_remover.remove_negative_fluents(e.condition))

        for i, gl in self._problem.timed_goals.items():
            for g in gl:
                ng = self._fluent_remover.remove_negative_fluents(g)
                self._new_problem.add_timed_goal(i, ng)

        for g in self._problem.goals:
            ng = self._fluent_remover.remove_negative_fluents(g)
            self._new_problem.add_goal(ng)

        #fluent_mapping is the map between a fluent and it's negation, when the
        # negation is None it means the fluent is never found in a negation into
        # every condititon analized before; therefore it does not need to exist.
        fluent_mapping = self._fluent_remover.fluent_mapping
        for f in self._problem.fluents:
            self._new_problem.add_fluent(f)
            fneg = fluent_mapping.get(f, None)
            if fneg is not None:
                self._new_problem.add_fluent(fneg)

        for fl, v in self._problem.initial_values.items():
            fneg = fluent_mapping.get(fl.fluent(), None)
            self._new_problem.set_initial_value(fl, v)
            if fneg is not None:
                if v.bool_constant_value():
                    self._new_problem.set_initial_value(self._env.expression_manager.FluentExp(fneg,
                    tuple(fl.args)), self._env.expression_manager.FALSE())
                else:
                    self._new_problem.set_initial_value(self._env.expression_manager.FluentExp(fneg,
                    tuple(fl.args)), self._env.expression_manager.TRUE())

        for action in self._problem.actions:
            if isinstance(action, InstantaneousAction):
                if action.simulated_effects() is not None:
                    raise up.exceptions.UPUsageError('NegativeConditionsRemover does not work with simulated effects')
                new_action = name_action_map[action.name]
                new_effects: List[Effect] = []
                for e in new_action.effects:
                    fl, v = e.fluent, e.value
                    fneg = fluent_mapping.get(fl.fluent(), None)
                    if fneg is not None:
                        simplified_not_v = self._simplifier.simplify(self._env.expression_manager.Not(v))
                        new_effects.append(Effect(self._env.expression_manager.FluentExp(fneg, tuple(fl.args)),
                                                simplified_not_v, e.condition, e.kind))
                for ne in new_effects:
                    new_action._add_effect_instance(ne)
                self._new_problem.add_action(new_action)
                self._old_to_new[action] = [new_action]
                self._new_to_old[new_action] = action
            elif isinstance(action, DurativeAction):
                if len(action.simulated_effects()) > 0:
                    raise up.exceptions.UPUsageError('NegativeConditionsRemover does not work with simulated effects')
                new_durative_action = name_action_map[action.name]
                new_durative_action.set_duration_constraint(action.duration)

                for t, el in new_durative_action.effects.items():
                    for e in el:
                        fl, v = e.fluent, e.value
                        fneg = fluent_mapping.get(fl.fluent(), None)
                        if fneg is not None:
                            simplified_not_v = self._simplifier.simplify(self._env.expression_manager.Not(v))
                            new_durative_action._add_effect_instance(t, Effect(self._env.expression_manager.FluentExp(fneg, tuple(fl.args)),
                                                            simplified_not_v, e.condition, e.kind))
                self._new_problem.add_action(new_durative_action)
                self._old_to_new[action] = [new_durative_action]
                self._new_to_old[new_durative_action] = action
            else:
                raise NotImplementedError

        for t, el in self._new_problem.timed_effects.items():
            for e in el:
                fl, v = e.fluent, e.value
                fneg = fluent_mapping.get(fl.fluent(), None)
                if fneg is not None:
                    simplified_not_v = self._simplifier.simplify(self._env.expression_manager.Not(v))
                    self._new_problem._add_effect_instance(t, Effect(self._env.expression_manager.FluentExp(fneg, tuple(fl.args)),
                                                    simplified_not_v, e.condition, e.kind))

        return self._new_problem

    def get_original_action(self, action: Action) -> Action:
        '''After the method get_rewritten_problem is called, this function maps
        the actions of the transformed problem into the actions of the original problem.'''
        return self._new_to_old[action]

    def get_transformed_actions(self, action: Action) -> List[Action]:
        '''After the method get_rewritten_problem is called, this function maps
        the actions of the original problem into the actions of the transformed problem.'''
        return self._old_to_new[action]
