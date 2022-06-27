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
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.model import Fluent, Problem, InstantaneousAction, DurativeAction, FNode, Action, Effect, Timing, ProblemKind
from unified_planning.model.walkers import Simplifier
from unified_planning.model.walkers.identitydag import IdentityDagWalker
from unified_planning.engines.compilers.utils import get_fresh_name, replace_action
from unified_planning.exceptions import UPExpressionDefinitionError, UPProblemDefinitionError
from typing import List, Dict, Union
from functools import partial


class NegativeFluentRemover(IdentityDagWalker):
    def __init__(self, problem, env):
        self._env = env
        IdentityDagWalker.__init__(self, self._env)
        self._fluent_mapping: Dict[Fluent, Fluent] = {}
        self._problem = problem

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
        nf = Fluent(get_fresh_name(self._problem, f.name), f.type, f.signature, f._env)
        self._fluent_mapping[f] = nf
        return self._env.expression_manager.FluentExp(nf, tuple(args[0].args))

    @property
    def fluent_mapping(self) -> Dict[Fluent, Fluent]:
        return self._fluent_mapping


class NegativeConditionsRemover(engines.engine.Engine, CompilerMixin):
    '''Negative conditions remover class: this class offers the capability
    to transform a problem with negative conditions into one
    without negative conditions.

    This is done by substituting every fluent that appears with a Not into the conditions
    with different fluent representing  his negation.'''

    @property
    def name(self):
        return 'ncrm'

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind()
        supported_kind.set_problem_class('ACTION_BASED')
        supported_kind.set_typing('FLAT_TYPING')
        supported_kind.set_typing('HIERARCHICAL_TYPING')
        supported_kind.set_numbers('CONTINUOUS_NUMBERS')
        supported_kind.set_numbers('DISCRETE_NUMBERS')
        supported_kind.set_fluents_type('NUMERIC_FLUENTS')
        supported_kind.set_fluents_type('OBJECT_FLUENTS')
        supported_kind.set_conditions_kind('NEGATIVE_CONDITIONS')
        supported_kind.set_conditions_kind('DISJUNCTIVE_CONDITIONS')
        supported_kind.set_conditions_kind('EQUALITY')
        supported_kind.set_conditions_kind('EXISTENTIAL_CONDITIONS')
        supported_kind.set_conditions_kind('UNIVERSAL_CONDITIONS')
        supported_kind.set_effects_kind('CONDITIONAL_EFFECTS')
        supported_kind.set_effects_kind('INCREASE_EFFECTS')
        supported_kind.set_effects_kind('DECREASE_EFFECTS')
        supported_kind.set_time('CONTINUOUS_TIME')
        supported_kind.set_time('DISCRETE_TIME')
        supported_kind.set_time('INTERMEDIATE_CONDITIONS_AND_EFFECTS')
        supported_kind.set_time('TIMED_EFFECT')
        supported_kind.set_time('TIMED_GOALS')
        supported_kind.set_time('DURATION_INEQUALITIES')
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= NegativeConditionsRemover.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == CompilationKind.NEGATIVE_CONDITIONS_REMOVING

    def _compile(self, problem: 'up.model.AbstractProblem',
                 compilation_kind: 'up.engines.CompilationKind') -> CompilerResult:
        assert isinstance(problem, Problem)

        env = problem.env
        simplifier = Simplifier(env)

        fluent_remover = NegativeFluentRemover(problem, env)

        new_to_old: Dict[Action, Action] = {}

        new_problem = Problem(f'{self.name}_{problem.name}', env)
        for o in problem.all_objects:
            new_problem.add_object(o)

        name_action_map: Dict[str, Union[InstantaneousAction, DurativeAction]] = {}
        for action in problem.actions:
            if isinstance(action, InstantaneousAction):
                new_action = action.clone()
                new_action.name = get_fresh_name(new_problem, action.name)
                new_action.clear_preconditions()
                for p in action.preconditions:
                    np = fluent_remover.remove_negative_fluents(p)
                    new_action.add_precondition(np)
                for ce in new_action.conditional_effects:
                    ce.set_condition(fluent_remover.remove_negative_fluents(ce.condition))
                name_action_map[action.name] = new_action
            elif isinstance(action, DurativeAction):
                new_durative_action = action.clone()
                new_durative_action.name = get_fresh_name(new_problem, action.name)
                new_durative_action.clear_conditions()
                for i, cl in action.conditions.items():
                    for c in cl:
                        nc = fluent_remover.remove_negative_fluents(c)
                        new_durative_action.add_condition(i, nc)
                for t, cel in new_durative_action.conditional_effects.items():
                    for ce in cel:
                        ce.set_condition(fluent_remover.remove_negative_fluents(ce.condition))
                name_action_map[action.name] = new_durative_action
            else:
                raise NotImplementedError

        for t, el in problem.timed_effects.items():
            for e in el:
                new_problem._add_effect_instance(t, e.clone())

        for t, el in new_problem.timed_effects.items():
            for e in el:
                if e.is_conditional():
                    e.set_condition(fluent_remover.remove_negative_fluents(e.condition))

        for i, gl in problem.timed_goals.items():
            for g in gl:
                ng = fluent_remover.remove_negative_fluents(g)
                new_problem.add_timed_goal(i, ng)

        for g in problem.goals:
            ng = fluent_remover.remove_negative_fluents(g)
            new_problem.add_goal(ng)

        #fluent_mapping is the map between a fluent and it's negation, when the
        # negation is None it means the fluent is never found in a negation into
        # every condititon analized before; therefore it does not need to exist.
        fluent_mapping = fluent_remover.fluent_mapping
        for f in problem.fluents:
            new_problem.add_fluent(f)
            fneg = fluent_mapping.get(f, None)
            if fneg is not None:
                new_problem.add_fluent(fneg)

        for fl, v in problem.initial_values.items():
            fneg = fluent_mapping.get(fl.fluent(), None)
            new_problem.set_initial_value(fl, v)
            if fneg is not None:
                if v.bool_constant_value():
                    new_problem.set_initial_value(env.expression_manager.FluentExp(fneg,
                    tuple(fl.args)), env.expression_manager.FALSE())
                else:
                    new_problem.set_initial_value(env.expression_manager.FluentExp(fneg,
                    tuple(fl.args)), env.expression_manager.TRUE())

        for action in problem.actions:
            if isinstance(action, InstantaneousAction):
                new_action = name_action_map[action.name]
                new_effects: List[Effect] = []
                for e in new_action.effects:
                    fl, v = e.fluent, e.value
                    fneg = fluent_mapping.get(fl.fluent(), None)
                    if fneg is not None:
                        simplified_not_v = simplifier.simplify(env.expression_manager.Not(v))
                        new_effects.append(Effect(env.expression_manager.FluentExp(fneg, tuple(fl.args)),
                                                  simplified_not_v, e.condition, e.kind))
                for ne in new_effects:
                    new_action._add_effect_instance(ne)
                new_problem.add_action(new_action)
                new_to_old[new_action] = action
            elif isinstance(action, DurativeAction):
                new_durative_action = name_action_map[action.name]
                new_durative_action.set_duration_constraint(action.duration)

                for t, el in new_durative_action.effects.items():
                    for e in el:
                        fl, v = e.fluent, e.value
                        fneg = fluent_mapping.get(fl.fluent(), None)
                        if fneg is not None:
                            simplified_not_v = simplifier.simplify(env.expression_manager.Not(v))
                            new_durative_action._add_effect_instance(t, Effect(env.expression_manager.FluentExp(fneg, tuple(fl.args)),
                                                                               simplified_not_v, e.condition, e.kind))
                new_problem.add_action(new_durative_action)
                new_to_old[new_durative_action] = action
            else:
                raise NotImplementedError

        for t, el in new_problem.timed_effects.items():
            for e in el:
                fl, v = e.fluent, e.value
                fneg = fluent_mapping.get(fl.fluent(), None)
                if fneg is not None:
                    simplified_not_v = simplifier.simplify(env.expression_manager.Not(v))
                    new_problem._add_effect_instance(t, Effect(env.expression_manager.FluentExp(fneg, tuple(fl.args)),
                                                               simplified_not_v, e.condition, e.kind))

        return CompilerResult(new_problem, partial(replace_action, map=new_to_old), self.name)
