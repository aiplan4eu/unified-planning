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
'''This module defines the problem class.'''

from functools import partial
import unified_planning as up
from unified_planning.model.abstract_problem import AbstractProblem
from unified_planning.model.actions_set import ActionsSetMixin
from unified_planning.model.fluents_set import FluentsSetMixin
from unified_planning.model.objects_set import ObjectsSetMixin
from unified_planning.model.user_types_set import UserTypesSetMixin
from unified_planning.model.expression import ConstantExpression
from unified_planning.model.operators import OperatorKind
from unified_planning.model.types import domain_size, domain_item
from unified_planning.exceptions import UPProblemDefinitionError, UPTypeError, UPValueError, UPExpressionDefinitionError, UPUsageError
from unified_planning.plans import ActionInstance
from unified_planning.walkers import OperatorsExtractor
from fractions import Fraction
from typing import Iterator, List, Dict, Set, Union, Optional, cast


class Problem(AbstractProblem, UserTypesSetMixin, FluentsSetMixin, ActionsSetMixin, ObjectsSetMixin):
    '''Represents a, action based planning problem.'''
    def __init__(self, name: str = None, env: 'up.environment.Environment' = None, *,
                 initial_defaults: Dict['up.model.types.Type', 'ConstantExpression'] = {}):
        AbstractProblem.__init__(self, name, env)
        UserTypesSetMixin.__init__(self, self.has_name)
        FluentsSetMixin.__init__(self, self.env, self._add_user_type, self.has_name, initial_defaults)
        ActionsSetMixin.__init__(self, self.env, self._add_user_type, self.has_name)
        ObjectsSetMixin.__init__(self, self.env, self._add_user_type, self.has_name)
        self._operators_extractor = OperatorsExtractor()
        self._initial_value: Dict['up.model.fnode.FNode', 'up.model.fnode.FNode'] = {}
        self._timed_effects: Dict['up.model.timing.Timing', List['up.model.effect.Effect']] = {}
        self._timed_goals: Dict['up.model.timing.TimeInterval', List['up.model.fnode.FNode']] = {}
        self._goals: List['up.model.fnode.FNode'] = list()
        self._metrics: List['up.model.metrics.PlanQualityMetric'] = []

    def __repr__(self) -> str:
        s = []
        if not self.name is None:
            s.append(f'problem name = {str(self.name)}\n\n')
        if len(self.user_types) > 0:
            s.append(f'types = {str(list(self.user_types))}\n\n')
        s.append('fluents = [\n')
        for f in self.fluents:
            s.append(f'  {str(f)}\n')
        s.append(']\n\n')
        s.append('actions = [\n')
        for a in self.actions:
            s.append(f'  {str(a)}\n')
        s.append(']\n\n')
        if len(self.user_types) > 0:
            s.append('objects = [\n')
            for ty in self.user_types:
                s.append(f'  {str(ty)}: {str(list(self.objects(ty)))}\n')
            s.append(']\n\n')
        s.append('initial fluents default = [\n')
        for f in self._fluents:
            if f in self._fluents_defaults:
                v = self._fluents_defaults[f]
                s.append(f'  {str(f)} := {str(v)}\n')
        s.append(']\n\n')
        s.append('initial values = [\n')
        for k, v in self._initial_value.items():
            s.append(f'  {str(k)} := {str(v)}\n')
        s.append(']\n\n')
        if len(self.timed_effects) > 0:
            s.append('timed effects = [\n')
            for t, el in self.timed_effects.items():
                s.append(f'  {str(t)} :\n')
                for e in el:
                    s.append(f'    {str(e)}\n')
            s.append(']\n\n')
        if len(self.timed_goals) > 0:
            s.append('timed goals = [\n')
            for i, gl in self.timed_goals.items():
                s.append(f'  {str(i)} :\n')
                for g in gl:
                    s.append(f'    {str(g)}\n')
            s.append(']\n\n')
        s.append('goals = [\n')
        for g in self.goals:
            s.append(f'  {str(g)}\n')
        s.append(']\n\n')
        if len(self.quality_metrics) > 0:
            s.append('quality metrics = [\n')
            for qm in self.quality_metrics:
                s.append(f'  {str(qm)}\n')
            s.append(']\n\n')
        return ''.join(s)

    def __eq__(self, oth: object) -> bool:
        if not (isinstance(oth, Problem)) or self._env != oth._env:
            return False
        if self.kind != oth.kind or self._name != oth._name:
            return False
        if set(self._fluents) != set(oth._fluents) or set(self._goals) != set(oth._goals):
            return False
        if set(self._user_types) != set(oth._user_types) or set(self._objects) != set(oth._objects):
            return False
        if set(self._actions) != set(oth._actions):
            return False
        oth_initial_values = oth.initial_values
        if len(self.initial_values) != len(oth_initial_values):
            return False
        for fluent, value in self.initial_values.items():
            oth_value = oth_initial_values.get(fluent, None)
            if oth_value is None:
                return False
            elif value != oth_value:
                return False
        if len(self._timed_effects) != len(oth._timed_effects):
                return False
        for t, tel in self._timed_effects.items():
            oth_tel = oth._timed_effects.get(t, None)
            if oth_tel is None:
                return False
            elif set(tel) != set(oth_tel):
                return False
        if len(self._timed_goals) != len(oth._timed_goals):
            return False
        for i, tgl in self._timed_goals.items():
            oth_tgl = oth._timed_goals.get(i, None)
            if oth_tgl is None:
                return False
            elif set(tgl) != set(oth_tgl):
                return False
        return True

    def __hash__(self) -> int:
        res = hash(self._kind) + hash(self._name)
        for f in self._fluents:
            res += hash(f)
        for a in self._actions:
            res += hash(a)
        for ut in self._user_types:
            res += hash(ut)
        for o in self._objects:
            res += hash(o)
        for iv in self.initial_values.items():
            res += hash(iv)
        for t, el in self._timed_effects.items():
            res += hash(t)
            for e in set(el):
                res += hash(e)
        for i, gl in self._timed_goals.items():
            res += hash(i)
            for g in set(gl):
                res += hash(g)
        for g in self._goals:
            res += hash(g)
        return res

    def clone(self):
        new_p = Problem(self._name, self._env)
        new_p._fluents = self._fluents[:]
        new_p._actions = [a.clone() for a in self._actions]
        new_p._user_types = self._user_types[:]
        new_p._user_types_hierarchy = self._user_types_hierarchy.copy()
        new_p._objects = self._objects[:]
        new_p._initial_value = self._initial_value.copy()
        new_p._timed_effects = {t: [e.clone() for e in el] for t, el in self._timed_effects.items()}
        new_p._timed_goals = {i: [g for g in gl] for i, gl in self._timed_goals.items()}
        new_p._goals = self._goals[:]
        new_p._metrics = []
        for m in self._metrics:
            if isinstance(m, up.model.metrics.MinimizeActionCosts):
                costs = {new_p.action(a.name) : c for a, c in m.costs.items()}
                new_p._metrics.append(up.model.metrics.MinimizeActionCosts(costs))
            else:
                new_p._metrics.append(m)
        new_p._initial_defaults = self._initial_defaults.copy()
        new_p._fluents_defaults = self._fluents_defaults.copy()
        return new_p

    def has_name(self, name: str) -> bool:
        '''Returns true if the name is in the problem.'''
        return self.has_action(name) or self.has_fluent(name) or self.has_object(name) or self.has_type(name)

    def normalize_plan(self, plan: 'up.plans.Plan')-> 'up.plans.Plan':
        '''Normalizes the given plan updating the action and object instances.'''
        objects = {}
        for obj in self.all_objects:
            objects[obj.name] = obj
        replace_action_instance = partial(self._replace_action_instance, objects=objects)
        return plan.replace_action_instances(replace_action_instance)

    def _replace_action_instance(self,
                                action_instance: ActionInstance,
                                objects: Dict[str, 'up.model.object.Object']
                                ) -> ActionInstance:
        em = self.env.expression_manager
        new_a = self.action(action_instance.action.name)
        params = []
        for p in action_instance.actual_parameters:
            if p.is_object_exp():
                obj = objects[p.object().name]
                params.append(em.ObjectExp(obj))
            elif p.is_bool_constant():
                params.append(em.Bool(p.is_true()))
            elif p.is_int_constant():
                params.append(em.Int(cast(int, p.constant_value())))
            elif p.is_real_constant():
                params.append(em.Real(cast(Fraction, p.constant_value())))
            else:
                raise
        return ActionInstance(new_a, tuple(params))

    def get_static_fluents(self) -> Set['up.model.fluent.Fluent']:
        '''Returns the set of the static fluents.

        Static fluents are those who can't change their values because they never
        appear in the "fluent" field of an effect, therefore there are no Actions
        in the Problem that can change their value.'''
        static_fluents: Set['up.model.fluent.Fluent'] = set(self._fluents)
        for a in self._actions:
            if isinstance(a, up.model.action.InstantaneousAction):
                for e in a.effects:
                    if e.fluent.fluent() in static_fluents:
                        static_fluents.remove(e.fluent.fluent())
            elif isinstance(a, up.model.action.DurativeAction):
                for el in a.effects.values():
                    for e in el:
                        if e.fluent.fluent() in static_fluents:
                            static_fluents.remove(e.fluent.fluent())
            else:
                raise NotImplementedError
        for el in self._timed_effects.values():
            for e in el:
                if e.fluent.fluent() in static_fluents:
                    static_fluents.remove(e.fluent.fluent())
        return static_fluents

    def set_initial_value(self, fluent: Union['up.model.fnode.FNode', 'up.model.fluent.Fluent'],
                          value: Union['up.model.fnode.FNode', 'up.model.fluent.Fluent', 'up.model.object.Object', bool,
                                       int, float, Fraction]):
        '''Sets the initial value for the given fluent.'''
        fluent_exp, value_exp = self._env.expression_manager.auto_promote(fluent, value)
        if not self._env.type_checker.is_compatible_exp(fluent_exp, value_exp):
            raise UPTypeError('Initial value assignment has not compatible types!')
        self._initial_value[fluent_exp] = value_exp

    def initial_value(self, fluent: Union['up.model.fnode.FNode', 'up.model.fluent.Fluent']) -> 'up.model.fnode.FNode':
        '''Gets the initial value of the given fluent.'''
        fluent_exp, = self._env.expression_manager.auto_promote(fluent)
        for a in fluent_exp.args:
            if not a.is_constant():
                raise UPExpressionDefinitionError(f'Impossible to return the initial value of a fluent expression with no constant arguments: {fluent_exp}.')
        if fluent_exp in self._initial_value:
            return self._initial_value[fluent_exp]
        elif fluent_exp.fluent() in self._fluents_defaults:
            return self._fluents_defaults[fluent_exp.fluent()]
        else:
            print(fluent)
            raise UPProblemDefinitionError('Initial value not set!')

    def _get_ith_fluent_exp(self, fluent: 'up.model.fluent.Fluent', domain_sizes: List[int], idx: int) -> 'up.model.fnode.FNode':
        '''Returns the ith ground fluent expression.'''
        quot = idx
        rem = 0
        actual_parameters = []
        for i, p in enumerate(fluent.signature):
            ds = domain_sizes[i];
            rem = quot % ds
            quot //= ds
            v = domain_item(self, p.type, rem)
            actual_parameters.append(v)
        return fluent(*actual_parameters)

    @property
    def initial_values(self) -> Dict['up.model.fnode.FNode', 'up.model.fnode.FNode']:
        '''Gets the initial value of the fluents.

        IMPORTANT NOTE: this property does a lot of computation, so it should be called as
        seldom as possible.'''
        res = self._initial_value
        for f in self._fluents:
            if f.arity == 0:
                f_exp = self._env.expression_manager.FluentExp(f)
                res[f_exp] = self.initial_value(f_exp)
            else:
                ground_size = 1
                domain_sizes = []
                for p in f.signature:
                    ds = domain_size(self, p.type)
                    domain_sizes.append(ds)
                    ground_size *= ds
                for i in range(ground_size):
                    f_exp = self._get_ith_fluent_exp(f, domain_sizes, i)
                    res[f_exp] = self.initial_value(f_exp)
        return res

    @property
    def explicit_initial_values(self) -> Dict['up.model.fnode.FNode', 'up.model.fnode.FNode']:
        '''Returns the problem's defined initial values.
        IMPORTANT NOTE: For all the initial values of hte problem use Problem.initial_values.'''
        return self._initial_value

    def add_timed_goal(self, interval: Union['up.model.timing.Timing', 'up.model.timing.TimeInterval'],
                       goal: Union['up.model.fnode.FNode', 'up.model.fluent.Fluent', bool]):
        '''Adds a timed goal.'''
        if isinstance(interval, up.model.Timing):
            interval = up.model.TimePointInterval(interval)
        if ((interval.lower.is_from_end() and interval.lower.delay > 0) or
            (interval.upper.is_from_end() and interval.upper.delay > 0)):
            raise UPProblemDefinitionError('Problem timing can not be `end - k` with k > 0.')
        goal_exp, = self._env.expression_manager.auto_promote(goal)
        assert self._env.type_checker.get_type(goal_exp).is_bool_type()
        if interval in self._timed_goals:
            if goal_exp not in self._timed_goals[interval]:
                self._timed_goals[interval].append(goal_exp)
        else:
            self._timed_goals[interval] = [goal_exp]

    @property
    def timed_goals(self) -> Dict['up.model.timing.TimeInterval', List['up.model.fnode.FNode']]:
        '''Returns the timed goals.'''
        return self._timed_goals

    def clear_timed_goals(self):
        '''Removes the timed goals.'''
        self._timed_goals = {}

    def add_timed_effect(self, timing: 'up.model.timing.Timing', fluent: Union['up.model.fnode.FNode', 'up.model.fluent.Fluent'],
                         value: 'up.model.expression.Expression', condition: 'up.model.expression.BoolExpression' = True):
        '''Adds the given timed effect.'''
        if timing.is_from_end():
            raise UPProblemDefinitionError(f'Timing used in timed effect cannot be EndTiming.')
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value,
                                                                                         condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_exp(fluent_exp, value_exp):
            raise UPTypeError('Timed effect has not compatible types!')
        self._add_effect_instance(timing, up.model.effect.Effect(fluent_exp, value_exp, condition_exp))

    def add_increase_effect(self, timing: 'up.model.timing.Timing', fluent: Union['up.model.fnode.FNode', 'up.model.fluent.Fluent'],
                            value: 'up.model.expression.Expression', condition: 'up.model.expression.BoolExpression' = True):
        '''Adds the given timed increase effect.'''
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value,
                                                                                         condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_exp(fluent_exp, value_exp):
            raise UPTypeError('Timed effect has not compatible types!')
        self._add_effect_instance(timing,
                                  up.model.effect.Effect(fluent_exp, value_exp,
                                         condition_exp, kind = up.model.effect.EffectKind.INCREASE))

    def add_decrease_effect(self, timing: 'up.model.timing.Timing', fluent: Union['up.model.fnode.FNode', 'up.model.fluent.Fluent'],
                            value: 'up.model.expression.Expression', condition: 'up.model.expression.BoolExpression' = True):
        '''Adds the given timed decrease effect.'''
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value,
                                                                                         condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_exp(fluent_exp, value_exp):
            raise UPTypeError('Timed effect has not compatible types!')
        self._add_effect_instance(timing,
                                  up.model.effect.Effect(fluent_exp, value_exp,
                                         condition_exp, kind = up.model.effect.EffectKind.DECREASE))

    def _add_effect_instance(self, timing: 'up.model.timing.Timing', effect: 'up.model.effect.Effect'):
        if timing in self._timed_effects:
            if effect not in self._timed_effects[timing]:
                self._timed_effects[timing].append(effect)
        else:
            self._timed_effects[timing] = [effect]

    @property
    def timed_effects(self) -> Dict['up.model.timing.Timing', List['up.model.effect.Effect']]:
        '''Returns the timed effects.'''
        return self._timed_effects

    def clear_timed_effects(self):
        '''Removes the timed effects.'''
        self._timed_effects = {}

    def add_goal(self, goal: Union['up.model.fnode.FNode', 'up.model.fluent.Fluent', bool]):
        '''Adds a goal.'''
        goal_exp, = self._env.expression_manager.auto_promote(goal)
        assert self._env.type_checker.get_type(goal_exp).is_bool_type()
        if goal_exp != self._env.expression_manager.TRUE():
            self._goals.append(goal_exp)

    @property
    def goals(self) -> List['up.model.fnode.FNode']:
        '''Returns the goals.'''
        return self._goals

    def clear_goals(self):
        '''Removes the goals.'''
        self._goals = []

    def add_quality_metric(self, metric: 'up.model.metrics.PlanQualityMetric'):
        '''Adds a quality metric'''
        self._metrics.append(metric)

    @property
    def quality_metrics(self) -> List['up.model.metrics.PlanQualityMetric']:
        '''Returns the quality metrics'''
        return self._metrics

    @property
    def kind(self) -> 'up.model.problem_kind.ProblemKind':
        '''Returns the problem kind of this planning problem.

        IMPORTANT NOTE: this property does a lot of computation, so it should be called as
        seldom as possible.'''
        self._kind = up.model.problem_kind.ProblemKind()
        self._kind.set_problem_class('ACTION_BASED') # type: ignore
        for fluent in self._fluents:
            self._update_problem_kind_fluent(fluent)
        for action in self._actions:
            self._update_problem_kind_action(action)
        if len(self._timed_effects) > 0:
            self._kind.set_time('CONTINUOUS_TIME') # type: ignore
            self._kind.set_time('TIMED_EFFECT') # type: ignore
        for effect_list in self._timed_effects.values():
                for effect in effect_list:
                    self._update_problem_kind_effect(effect)
        if len(self._timed_goals) > 0:
            self._kind.set_time('TIMED_GOALS') # type: ignore
            self._kind.set_time('CONTINUOUS_TIME') # type: ignore
        for goal_list in self._timed_goals.values():
            for goal in goal_list:
                self._update_problem_kind_condition(goal)
        for goal in self._goals:
            self._update_problem_kind_condition(goal)
        for metric in self._metrics:
            if isinstance(metric, up.model.metrics.MinimizeExpressionOnFinalState) or \
               isinstance(metric, up.model.metrics.MaximizeExpressionOnFinalState):
                self._kind.set_quality_metrics('FINAL_VALUE') # type: ignore
            elif isinstance(metric, up.model.metrics.MinimizeActionCosts):
                self._kind.set_quality_metrics('ACTIONS_COST') # type: ignore
            elif isinstance(metric, up.model.metrics.MinimizeMakespan):
                self._kind.set_quality_metrics('MAKESPAN') # type: ignore
            elif isinstance(metric, up.model.metrics.MinimizeSequentialPlanLength):
                self._kind.set_quality_metrics('PLAN_LENGTH') # type: ignore
            else:
                assert False, 'Unknown quality metric'
        return self._kind

    def _update_problem_kind_effect(self, e: 'up.model.effect.Effect'):
        if e.is_conditional():
            self._update_problem_kind_condition(e.condition)
            self._kind.set_effects_kind('CONDITIONAL_EFFECTS') # type: ignore
        if e.is_increase():
            self._kind.set_effects_kind('INCREASE_EFFECTS') # type: ignore
        elif e.is_decrease():
            self._kind.set_effects_kind('DECREASE_EFFECTS') # type: ignore

    def _update_problem_kind_condition(self, exp: 'up.model.fnode.FNode'):
        ops = self._operators_extractor.get(exp)
        if OperatorKind.EQUALS in ops:
            self._kind.set_conditions_kind('EQUALITY') # type: ignore
        if OperatorKind.NOT in ops:
            self._kind.set_conditions_kind('NEGATIVE_CONDITIONS') # type: ignore
        if OperatorKind.OR in ops:
            self._kind.set_conditions_kind('DISJUNCTIVE_CONDITIONS') # type: ignore
        if OperatorKind.EXISTS in ops:
            self._kind.set_conditions_kind('EXISTENTIAL_CONDITIONS') # type: ignore
        if OperatorKind.FORALL in ops:
            self._kind.set_conditions_kind('UNIVERSAL_CONDITIONS') # type: ignore

    def _update_problem_kind_type(self, type: 'up.model.types.Type'):
        if type.is_user_type():
            self._kind.set_typing('FLAT_TYPING') # type: ignore
            if type.father is not None: # type: ignore
               self._kind.set_typing('HIERARCHICAL_TYPING') # type: ignore
        elif type.is_int_type():
            self._kind.set_numbers('DISCRETE_NUMBERS') # type: ignore
        elif type.is_real_type():
            self._kind.set_numbers('CONTINUOUS_NUMBERS') # type: ignore

    def _update_problem_kind_fluent(self, fluent: 'up.model.fluent.Fluent'):
        self._update_problem_kind_type(fluent.type)
        if fluent.type.is_int_type() or fluent.type.is_real_type():
            self._kind.set_fluents_type('NUMERIC_FLUENTS') # type: ignore
        elif fluent.type.is_user_type():
            self._kind.set_fluents_type('OBJECT_FLUENTS') # type: ignore
        for p in fluent.signature:
            self._update_problem_kind_type(p.type)

    def _update_problem_kind_action(self, action: 'up.model.action.Action'):
        for p in action.parameters:
            self._update_problem_kind_type(p.type)
        if isinstance(action, up.model.action.InstantaneousAction):
            for c in action.preconditions:
                self._update_problem_kind_condition(c)
            for e in action.effects:
                self._update_problem_kind_effect(e)
            if action.simulated_effect is not None:
                self._kind.set_simulated_entities('SIMULATED_EFFECTS') # type: ignore
        elif isinstance(action, up.model.action.DurativeAction):
            lower, upper = action.duration.lower, action.duration.upper
            if lower.constant_value() != upper.constant_value():
                self._kind.set_time('DURATION_INEQUALITIES') # type: ignore
            for i, lc in action.conditions.items():
                if i.lower.delay != 0 or i.upper.delay != 0:
                    self._kind.set_time('INTERMEDIATE_CONDITIONS_AND_EFFECTS') # type: ignore
                for c in lc:
                    self._update_problem_kind_condition(c)
            for t, le in action.effects.items():
                if t.delay != 0:
                    self._kind.set_time('INTERMEDIATE_CONDITIONS_AND_EFFECTS') # type: ignore
                for e in le:
                    self._update_problem_kind_effect(e)
            if len(action.simulated_effects) > 0:
                self._kind.set_simulated_entities('SIMULATED_EFFECTS') # type: ignore
            self._kind.set_time('CONTINUOUS_TIME') # type: ignore
        else:
            raise NotImplementedError
