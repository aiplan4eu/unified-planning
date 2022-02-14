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

import unified_planning
import unified_planning.model.operators as op
from unified_planning.model.types import domain_size, domain_item
from unified_planning.exceptions import UPProblemDefinitionError, UPTypeError, UPValueError, UPExpressionDefinitionError
from unified_planning.walkers import OperatorsExtractor
from fractions import Fraction
from typing import List, Dict, Set, Union, Optional


class Problem:
    '''Represents a planning problem.'''
    def __init__(self, name: str = None, env: 'unified_planning.environment.Environment' = None, *,
                 initial_defaults: Dict['unified_planning.model.types.Type', Union['unified_planning.model.fnode.FNode', 'unified_planning.model.object.Object', bool,
                                                              int, float, Fraction]] = {}):
        self._env = unified_planning.environment.get_env(env)
        self._operators_extractor = OperatorsExtractor()
        self._name = name
        self._fluents: List['unified_planning.model.fluent.Fluent'] = []
        self._actions: List['unified_planning.model.action.Action'] = []
        self._user_types: List['unified_planning.model.types.Type'] = []
        self._objects: List['unified_planning.model.object.Object'] = []
        self._initial_value: Dict['unified_planning.model.fnode.FNode', 'unified_planning.model.fnode.FNode'] = {}
        self._timed_effects: Dict['unified_planning.model.timing.Timing', List['unified_planning.model.effect.Effect']] = {}
        self._timed_goals: Dict['unified_planning.model.timing.Timing', List['unified_planning.model.fnode.FNode']] = {}
        self._maintain_goals: Dict['unified_planning.model.timing.Interval', List['unified_planning.model.fnode.FNode']] = {}
        self._goals: List['unified_planning.model.fnode.FNode'] = list()
        self._initial_defaults: Dict['unified_planning.model.types.Type', 'unified_planning.model.fnode.FNode'] = {}
        for k, v in initial_defaults.items():
            v_exp, = self._env.expression_manager.auto_promote(v)
            self._initial_defaults[k] = v_exp
        self._fluents_defaults: Dict['unified_planning.model.fluent.Fluent', 'unified_planning.model.fnode.FNode'] = {}

    def __repr__(self) -> str:
        s = []
        if not self.name is None:
            s.append(f'problem name = {str(self.name)}\n\n')
        if len(self.user_types()) > 0:
            s.append(f'types = {str(list(self.user_types()))}\n\n')
        s.append('fluents = [\n')
        for f in self.fluents():
            s.append(f'  {str(f)}\n')
        s.append(']\n\n')
        s.append('actions = [\n')
        for a in self.actions():
            s.append(f'  {str(a)}\n')
        s.append(']\n\n')
        if len(self.user_types()) > 0:
            s.append('objects = [\n')
            for ty in self.user_types():
                s.append(f'  {str(ty)}: {str(self.objects(ty))}\n')
            s.append(']\n\n')
        s.append('initial values = [\n')
        for k, v in self.initial_values().items():
            s.append(f'  {str(k)} := {str(v)}\n')
        s.append(']\n\n')
        if len(self.timed_effects()) > 0:
            s.append('timed effects = [\n')
            for t, el in self.timed_effects().items():
                s.append(f'  {str(t)} :\n')
                for e in el:
                    s.append(f'    {str(e)}\n')
            s.append(']\n\n')
        if len(self.timed_goals()) > 0:
            s.append('timed goals = [\n')
            for t, gl in self.timed_goals().items():
                s.append(f'  {str(t)} :\n')
                for g in gl:
                    s.append(f'    {str(g)}\n')
            s.append(']\n\n')
        if len(self.maintain_goals()) > 0:
            s.append('maintain goals = [\n')
            for i, gl in self.timed_goals().items():
                s.append(f'  {str(i)} :\n')
                for g in gl:
                    s.append(f'    {str(g)}\n')
            s.append(']\n\n')
        s.append('goals = [\n')
        for g in self.goals():
            s.append(f'  {str(g)}\n')
        s.append(']\n\n')
        return ''.join(s)

    def __eq__(self, oth: object) -> bool:
        if not (isinstance(oth, Problem)) or self._env != oth._env:
            return False
        if self.kind() != oth.kind() or self._name != oth._name:
            return False
        if set(self._fluents) != set(oth._fluents) or set(self._goals) != set(oth._goals):
            return False
        if set(self._user_types) != set(oth._user_types) or set(self._objects) != set(oth._objects):
            return False
        if set(self._actions) != set(oth._actions):
            return False
        oth_initial_values = oth.initial_values()
        if len(self.initial_values()) != len(oth_initial_values):
            return False
        for fluent, value in self.initial_values().items():
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
        for t, tgl in self._timed_goals.items():
            oth_tgl = oth._timed_goals.get(t, None)
            if oth_tgl is None:
                return False
            elif set(tgl) != set(oth_tgl):
                return False
        if len(self._maintain_goals) != len(oth._maintain_goals):
            return False
        for i, mgl in self._maintain_goals.items():
            oth_mgl = oth._maintain_goals.get(i, None)
            if oth_mgl is None:
                return False
            elif set(mgl) != set(oth_mgl):
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
        for iv in self.initial_values().items():
            res += hash(iv)
        for t, el in self._timed_effects.items():
            res += hash(t)
            for e in set(el):
                res += hash(e)
        for t, gl in self._timed_goals.items():
            res += hash(t)
            for g in set(gl):
                res += hash(g)
        for i, gl in self._maintain_goals.items():
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
        new_p._objects = self._objects[:]
        new_p._initial_value = self._initial_value.copy()
        new_p._timed_effects = {t: [e.clone() for e in el] for t, el in self._timed_effects.items()}
        new_p._timed_goals = {t: [g for g in gl] for t, gl in self._timed_goals.items()}
        new_p._maintain_goals = {i: [g for g in gl] for i, gl in self._maintain_goals.items()}
        new_p._goals = self._goals[:]
        new_p._initial_defaults = self._initial_defaults.copy()
        new_p._fluents_defaults = self._fluents_defaults.copy()
        return new_p

    @property
    def env(self) -> 'unified_planning.environment.Environment':
        '''Returns the problem environment.'''
        return self._env

    @property
    def name(self) -> Optional[str]:
        '''Returns the problem name.'''
        return self._name

    @name.setter
    def name(self, new_name: str):
        '''Sets the problem name.'''
        self._name = new_name

    def has_name(self, name: str) -> bool:
        '''Returns true if the name is in the problem.'''
        return self.has_action(name) or self.has_fluent(name) or self.has_object(name) or self.has_type(name)

    def fluents(self) -> List['unified_planning.model.fluent.Fluent']:
        '''Returns the fluents.'''
        return self._fluents

    def fluent(self, name: str) -> 'unified_planning.model.fluent.Fluent':
        '''Returns the fluent with the given name.'''
        for f in self._fluents:
            if f.name() == name:
                return f
        raise UPValueError(f'Fluent of name: {name} is not defined!')

    def has_fluent(self, name: str) -> bool:
        '''Returns true if the fluent with the given name is in the problem.'''
        for f in self._fluents:
            if f.name() == name:
                return True
        return False

    def add_fluent(self, fluent: 'unified_planning.model.fluent.Fluent', *,
                   default_initial_value: Union['unified_planning.model.fnode.FNode', 'unified_planning.model.object.Object', bool,
                                                int, float, Fraction] = None):
        '''Adds the given fluent.'''
        if self.has_name(fluent.name()):
            raise UPProblemDefinitionError('Name ' + fluent.name() + ' already defined!')
        self._fluents.append(fluent)
        if not default_initial_value is None:
            v_exp, = self._env.expression_manager.auto_promote(default_initial_value)
            self._fluents_defaults[fluent] = v_exp
        if fluent.type().is_user_type() and fluent.type() not in self._user_types:
            self._user_types.append(fluent.type()) # type: ignore
        for type in fluent.signature():
            if type.is_user_type() and type not in self._user_types:
                self._user_types.append(type) # type: ignore

    def get_static_fluents(self) -> Set['unified_planning.model.fluent.Fluent']:
        '''Returns the set of the static fluents.

        Static fluents are those who can't change their values because they never
        appear in the "fluent" field of an effect, therefore there are no Actions
        in the Problem that can change their value.'''
        static_fluents: Set['unified_planning.model.fluent.Fluent'] = set(self._fluents)
        for a in self._actions:
            if isinstance(a, unified_planning.model.action.InstantaneousAction):
                for e in a.effects():
                    if e.fluent().fluent() in static_fluents:
                        static_fluents.remove(e.fluent().fluent())
            elif isinstance(a, unified_planning.model.action.DurativeAction):
                for el in a.effects().values():
                    for e in el:
                        if e.fluent().fluent() in static_fluents:
                            static_fluents.remove(e.fluent().fluent())
            else:
                raise NotImplementedError
        for el in self._timed_effects.values():
            for e in el:
                if e.fluent().fluent() in static_fluents:
                    static_fluents.remove(e.fluent().fluent())
        return static_fluents

    def actions(self) -> List['unified_planning.model.action.Action']:
        '''Returns the list of the actions in the problem.'''
        return self._actions

    def clear_actions(self):
        '''Removes all the problem actions.'''
        self._actions = []

    def instantaneous_actions(self):
        for a in self._actions:
            if isinstance(a, unified_planning.model.action.InstantaneousAction):
                yield a

    def durative_actions(self):
        for a in self._actions:
            if isinstance(a, unified_planning.model.action.DurativeAction):
                yield a

    def conditional_actions(self) -> List['unified_planning.model.action.Action']:
        '''Returns the conditional actions.'''
        return [a for a in self._actions if a.is_conditional()]

    def unconditional_actions(self) -> List['unified_planning.model.action.Action']:
        '''Returns the conditional actions.'''
        return [a for a in self._actions if not a.is_conditional()]

    def action(self, name: str) -> 'unified_planning.model.action.Action':
        '''Returns the action with the given name.'''
        for a in self._actions:
            if a.name == name:
                return a
        raise UPValueError(f'Action of name: {name} is not defined!')

    def has_action(self, name: str) -> bool:
        '''Returns True if the problem has the action with the given name .'''
        for a in self._actions:
            if a.name == name:
                return True
        return False

    def add_action(self, action: 'unified_planning.model.action.Action'):
        '''Adds the given action.'''
        if self.has_name(action.name):
            raise UPProblemDefinitionError('Name ' + action.name + ' already defined!')
        self._actions.append(action)

    def user_types(self) -> List['unified_planning.model.types.Type']:
        '''Returns the user types.'''
        return self._user_types

    def user_type(self, name: str) -> 'unified_planning.model.types.Type':
        '''Returns the user type with the given name.'''
        for ut in self._user_types:
            assert ut.is_user_type()
            if ut.name() == name: # type: ignore
                return ut
        raise UPValueError(f'UserType {name} is not defined!')

    def has_type(self, name: str) -> bool:
        '''Returns True iff the type 'name' is defined.'''
        for ut in self._user_types:
            assert ut.is_user_type()
            if ut.name() == name: # type: ignore
                return True
        return False

    def add_object(self, obj: 'unified_planning.model.object.Object'):
        '''Adds the given object.'''
        if self.has_name(obj.name()):
            raise UPProblemDefinitionError('Name ' + obj.name() + ' already defined!')
        self._objects.append(obj)
        if obj.type().is_user_type() and obj.type() not in self._user_types:
            self._user_types.append(obj.type())

    def add_objects(self, objs: List['unified_planning.model.object.Object']):
        '''Adds the given objects.'''
        for obj in objs:
            if self.has_name(obj.name()):
                raise UPProblemDefinitionError('Name ' + obj.name() + ' already defined!')
            self._objects.append(obj)
            if obj.type().is_user_type() and obj.type() not in self._user_types:
                self._user_types.append(obj.type())

    def object(self, name: str) -> 'unified_planning.model.object.Object':
        '''Returns the object with the given name.'''
        for o in self._objects:
            if o.name() == name:
                return o
        raise UPValueError(f'Object of name: {name} is not defined!')

    def has_object(self, name: str) -> bool:
        '''Returns true if the object with the given name is in the problem.'''
        for o in self._objects:
            if o.name() == name:
                return True
        return False

    def objects(self, typename: 'unified_planning.model.types.Type') -> List['unified_planning.model.object.Object']:
        '''Returns the objects of the given user types.'''
        res = []
        for obj in self._objects:
            if obj.type() == typename:
                res.append(obj)
        return res

    def all_objects(self) -> List['unified_planning.model.object.Object']:
        '''Returns all the objects.'''
        return [o for o in self._objects]

    def set_initial_value(self, fluent: Union['unified_planning.model.fnode.FNode', 'unified_planning.model.fluent.Fluent'],
                          value: Union['unified_planning.model.fnode.FNode', 'unified_planning.model.fluent.Fluent', 'unified_planning.model.object.Object', bool,
                                       int, float, Fraction]):
        '''Sets the initial value for the given fluent.'''
        fluent_exp, value_exp = self._env.expression_manager.auto_promote(fluent, value)
        if not self._env.type_checker.is_compatible_exp(fluent_exp, value_exp):
            raise UPTypeError('Initial value assignment has not compatible types!')
        self._initial_value[fluent_exp] = value_exp

    def initial_value(self, fluent: Union['unified_planning.model.fnode.FNode', 'unified_planning.model.fluent.Fluent']) -> 'unified_planning.model.fnode.FNode':
        '''Gets the initial value of the given fluent.'''
        fluent_exp, = self._env.expression_manager.auto_promote(fluent)
        for a in fluent_exp.args():
            if not a.is_constant():
                raise UPExpressionDefinitionError(f'Impossible to return the initial value of a fluent expression with no constant arguments: {fluent_exp}.')
        if fluent_exp in self._initial_value:
            return self._initial_value[fluent_exp]
        elif fluent_exp.fluent() in self._fluents_defaults:
            return self._fluents_defaults[fluent_exp.fluent()]
        elif fluent_exp.fluent().type() in self._initial_defaults:
            return self._initial_defaults[fluent_exp.fluent().type()]
        else:
            raise UPProblemDefinitionError('Initial value not set!')

    def _get_ith_fluent_exp(self, fluent: 'unified_planning.model.fluent.Fluent', domain_sizes: List[int], idx: int) -> 'unified_planning.model.fnode.FNode':
        '''Returns the ith ground fluent expression.'''
        quot = idx
        rem = 0
        actual_parameters = []
        for i in range(fluent.arity()):
            ds = domain_sizes[i];
            rem = quot % ds
            quot //= ds
            v = domain_item(self, fluent.signature()[i], rem)
            actual_parameters.append(v)
        return fluent(*actual_parameters)

    def initial_values(self) -> Dict['unified_planning.model.fnode.FNode', 'unified_planning.model.fnode.FNode']:
        '''Gets the initial value of the fluents.'''
        res = self._initial_value
        for f in self._fluents:
            if f.arity() == 0:
                f_exp = self._env.expression_manager.FluentExp(f)
                res[f_exp] = self.initial_value(f_exp)
            else:
                ground_size = 1
                domain_sizes = []
                for p in f.signature():
                    ds = domain_size(self, p)
                    domain_sizes.append(ds)
                    ground_size *= ds
                for i in range(ground_size):
                    f_exp = self._get_ith_fluent_exp(f, domain_sizes, i)
                    res[f_exp] = self.initial_value(f_exp)
        return res

    def add_timed_goal(self, timing: 'unified_planning.model.timing.Timing', goal: Union['unified_planning.model.fnode.FNode', 'unified_planning.model.fluent.Fluent', bool]):
        '''Adds a timed goal.'''
        if timing.is_from_end() and timing.bound() > 0:
            raise UPProblemDefinitionError('Timing used in timed goal cannot be `end - k` with k > 0.')
        goal_exp, = self._env.expression_manager.auto_promote(goal)
        assert self._env.type_checker.get_type(goal_exp).is_bool_type()
        if timing in self._timed_goals:
            if goal_exp not in self._timed_goals[timing]:
                self._timed_goals[timing].append(goal_exp)
        else:
            self._timed_goals[timing] = [goal_exp]

    def timed_goals(self) -> Dict['unified_planning.model.timing.Timing', List['unified_planning.model.fnode.FNode']]:
        '''Returns the timed goals.'''
        return self._timed_goals

    def clear_timed_goals(self):
        '''Removes the timed goals.'''
        self._timed_goals = {}

    def add_timed_effect(self, timing: 'unified_planning.model.timing.Timing', fluent: Union['unified_planning.model.fnode.FNode', 'unified_planning.model.fluent.Fluent'],
                         value: 'unified_planning.model.expression.Expression', condition: 'unified_planning.model.expression.BoolExpression' = True):
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
        self._add_effect_instance(timing, unified_planning.model.effect.Effect(fluent_exp, value_exp, condition_exp))

    def add_increase_effect(self, timing: 'unified_planning.model.timing.Timing', fluent: Union['unified_planning.model.fnode.FNode', 'unified_planning.model.fluent.Fluent'],
                            value: 'unified_planning.model.expression.Expression', condition: 'unified_planning.model.expression.BoolExpression' = True):
        '''Adds the given timed increase effect.'''
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value,
                                                                                         condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_exp(fluent_exp, value_exp):
            raise UPTypeError('Timed effect has not compatible types!')
        self._add_effect_instance(timing,
                                  unified_planning.model.effect.Effect(fluent_exp, value_exp,
                                         condition_exp, kind = unified_planning.model.effect.INCREASE))

    def add_decrease_effect(self, timing: 'unified_planning.model.timing.Timing', fluent: Union['unified_planning.model.fnode.FNode', 'unified_planning.model.fluent.Fluent'],
                            value: 'unified_planning.model.expression.Expression', condition: 'unified_planning.model.expression.BoolExpression' = True):
        '''Adds the given timed decrease effect.'''
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value,
                                                                                         condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_exp(fluent_exp, value_exp):
            raise UPTypeError('Timed effect has not compatible types!')
        self._add_effect_instance(timing,
                                  unified_planning.model.effect.Effect(fluent_exp, value_exp,
                                         condition_exp, kind = unified_planning.model.effect.DECREASE))

    def _add_effect_instance(self, timing: 'unified_planning.model.timing.Timing', effect: 'unified_planning.model.effect.Effect'):
        if timing in self._timed_effects:
            if effect not in self._timed_effects[timing]:
                self._timed_effects[timing].append(effect)
        else:
            self._timed_effects[timing] = [effect]

    def timed_effects(self) -> Dict['unified_planning.model.timing.Timing', List['unified_planning.model.effect.Effect']]:
        '''Returns the timed effects.'''
        return self._timed_effects

    def clear_timed_effects(self):
        '''Removes the timed effects.'''
        self._timed_effects = {}

    def add_maintain_goal(self, interval: 'unified_planning.model.timing.Interval', goal: Union['unified_planning.model.fnode.FNode', 'unified_planning.model.fluent.Fluent', bool]):
        '''Adds a maintain goal.'''
        if ((interval.lower().is_from_end() and interval.lower().bound() > 0) or
            (interval.upper().is_from_end() and interval.upper().bound() > 0)):
            raise UPProblemDefinitionError('Problem timing can not be `end - k` with k > 0.')
        goal_exp, = self._env.expression_manager.auto_promote(goal)
        assert self._env.type_checker.get_type(goal_exp).is_bool_type()
        if interval in self._maintain_goals:
            if goal_exp not in self._maintain_goals[interval]:
                self._maintain_goals[interval].append(goal_exp)
        else:
            self._maintain_goals[interval] = [goal_exp]

    def maintain_goals(self) -> Dict['unified_planning.model.timing.Interval', List['unified_planning.model.fnode.FNode']]:
        '''Returns the maintain goals.'''
        return self._maintain_goals

    def clear_maintain_goals(self):
        '''Removes the maintain goals.'''
        self._maintain_goals = {}

    def add_goal(self, goal: Union['unified_planning.model.fnode.FNode', 'unified_planning.model.fluent.Fluent', bool]):
        '''Adds a goal.'''
        goal_exp, = self._env.expression_manager.auto_promote(goal)
        assert self._env.type_checker.get_type(goal_exp).is_bool_type()
        if goal_exp != self._env.expression_manager.TRUE():
            self._goals.append(goal_exp)

    def goals(self) -> List['unified_planning.model.fnode.FNode']:
        '''Returns the goals.'''
        return self._goals

    def clear_goals(self):
        '''Removes the goals.'''
        self._goals = []

    def kind(self) -> 'unified_planning.model.problem_kind.ProblemKind':
        '''Returns the problem kind of this planning problem.'''
        self._kind = unified_planning.model.problem_kind.ProblemKind()
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
        if len(self._maintain_goals) > 0:
            self._kind.set_time('MAINTAIN_GOALS') # type: ignore
            self._kind.set_time('CONTINUOUS_TIME') # type: ignore
        for goal_list in self._maintain_goals.values():
            for goal in goal_list:
                self._update_problem_kind_condition(goal)
        for goal in self._goals:
            self._update_problem_kind_condition(goal)
        return self._kind

    def has_quantifiers(self) -> bool:
        '''Returns True only if the problem has quantifiers'''
        kind = self.kind()
        return kind.has_existential_conditions() or kind.has_universal_conditions() # type: ignore

    def _update_problem_kind_effect(self, e: 'unified_planning.model.effect.Effect'):
        if e.is_conditional():
            self._update_problem_kind_condition(e.condition())
            self._kind.set_effects_kind('CONDITIONAL_EFFECTS') # type: ignore
        elif e.is_increase():
            self._kind.set_effects_kind('INCREASE_EFFECTS') # type: ignore
        elif e.is_decrease():
            self._kind.set_effects_kind('DECREASE_EFFECTS') # type: ignore

    def _update_problem_kind_condition(self, exp: 'unified_planning.model.fnode.FNode'):
        ops = self._operators_extractor.get(exp)
        if op.EQUALS in ops:
            self._kind.set_conditions_kind('EQUALITY') # type: ignore
        if op.NOT in ops:
            self._kind.set_conditions_kind('NEGATIVE_CONDITIONS') # type: ignore
        if op.OR in ops:
            self._kind.set_conditions_kind('DISJUNCTIVE_CONDITIONS') # type: ignore
        if op.EXISTS in ops:
            self._kind.set_conditions_kind('EXISTENTIAL_CONDITIONS') # type: ignore
        if op.FORALL in ops:
            self._kind.set_conditions_kind('UNIVERSAL_CONDITIONS') # type: ignore

    def _update_problem_kind_type(self, type: 'unified_planning.model.types.Type'):
        if type.is_user_type():
            self._kind.set_typing('FLAT_TYPING') # type: ignore
        elif type.is_int_type():
            self._kind.set_numbers('DISCRETE_NUMBERS') # type: ignore
        elif type.is_real_type():
            self._kind.set_numbers('CONTINUOUS_NUMBERS') # type: ignore

    def _update_problem_kind_fluent(self, fluent: 'unified_planning.model.fluent.Fluent'):
        self._update_problem_kind_type(fluent.type())
        if fluent.type().is_int_type() or fluent.type().is_real_type():
            self._kind.set_fluents_type('NUMERIC_FLUENTS') # type: ignore
        elif fluent.type().is_user_type():
            self._kind.set_fluents_type('OBJECT_FLUENTS') # type: ignore
        for t in fluent.signature():
            self._update_problem_kind_type(t)

    def _update_problem_kind_action(self, action: 'unified_planning.model.action.Action'):
        for p in action.parameters():
            self._update_problem_kind_type(p.type())
        if isinstance(action, unified_planning.model.action.InstantaneousAction):
            for c in action.preconditions():
                self._update_problem_kind_condition(c)
            for e in action.effects():
                self._update_problem_kind_effect(e)
        elif isinstance(action, unified_planning.model.action.DurativeAction):
            lower, upper = action.duration().lower(), action.duration().upper()
            if lower.constant_value() != upper.constant_value():
                self._kind.set_time('DURATION_INEQUALITIES') # type: ignore
            for i, l in action.durative_conditions().items():
                if i.lower().bound() != 0 or i.upper().bound() != 0:
                    self._kind.set_time('INTERMEDIATE_CONDITIONS_AND_EFFECTS') # type: ignore
                for c in l:
                    self._update_problem_kind_condition(c)
            for t, l in action.conditions().items():
                if t.bound() != 0:
                    self._kind.set_time('INTERMEDIATE_CONDITIONS_AND_EFFECTS') # type: ignore
                for c in l:
                    self._update_problem_kind_condition(c)
            for t, l in action.effects().items():
                if t.bound() != 0:
                    self._kind.set_time('INTERMEDIATE_CONDITIONS_AND_EFFECTS') # type: ignore
                for e in l:
                    self._update_problem_kind_effect(e)
            self._kind.set_time('CONTINUOUS_TIME') # type: ignore
        else:
            raise NotImplementedError
