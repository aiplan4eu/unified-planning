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

import upf
import upf.model.operators as op
from upf.exceptions import UPFProblemDefinitionError, UPFTypeError
from upf.walkers import OperatorsExtractor
from fractions import Fraction
from typing import List, Dict, Union, Optional


class Problem:
    '''Represents a planning problem.'''
    def __init__(self, name: str = None, env: 'upf.environment.Environment' = None, *,
                 initial_defaults: Dict['upf.model.types.Type', Union['upf.model.fnode.FNode', 'upf.model.object.Object', bool,
                                                              int, float, Fraction]] = {}):
        self._env = upf.environment.get_env(env)
        self._operators_extractor = OperatorsExtractor()
        self._kind = upf.model.problem_kind.ProblemKind()
        self._name = name
        self._fluents: Dict[str, 'upf.model.fluent.Fluent'] = {}
        self._actions: Dict[str, 'upf.model.action.Action'] = {}
        self._user_types: Dict[str, 'upf.model.types.Type'] = {}
        self._objects: Dict[str, 'upf.model.object.Object'] = {}
        self._initial_value: Dict['upf.model.fnode.FNode', 'upf.model.fnode.FNode'] = {}
        self._timed_effects: Dict['upf.model.timing.Timing', List['upf.model.effect.Effect']] = {}
        self._timed_goals: Dict['upf.model.timing.Timing', List['upf.model.fnode.FNode']] = {}
        self._maintain_goals: Dict['upf.model.timing.Interval', List['upf.model.fnode.FNode']] = {}
        self._goals: List['upf.model.fnode.FNode'] = list()
        self._initial_defaults: Dict['upf.model.types.Type', 'upf.model.fnode.FNode'] = {}
        for k, v in initial_defaults.items():
            v_exp, = self._env.expression_manager.auto_promote(v)
            self._initial_defaults[k] = v_exp
        self._fluents_defaults: Dict['upf.model.fluent.Fluent', 'upf.model.fnode.FNode'] = {}

    def __repr__(self) -> str:
        s = []
        if not self.name() is None:
            s.append(f'problem name = {str(self.name())}\n\n')
        if len(self.user_types()) > 0:
            s.append(f'types = {str(list(self.user_types().values()))}\n\n')
        s.append('fluents = [\n')
        for f in self.fluents().values():
            s.append(f'  {str(f)}\n')
        s.append(']\n\n')
        s.append('actions = [\n')
        for a in self.actions().values():
            s.append(f'  {str(a)}\n')
        s.append(']\n\n')
        if len(self.user_types()) > 0:
            s.append('objects = [\n')
            for ty in self.user_types().values():
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
        if self._kind != oth._kind or self._name != oth._name:
            return False
        if self._fluents != oth._fluents or set(self._goals) != set(oth._goals):
            return False
        if self._user_types != oth._user_types or self._objects != oth._objects:
            return False
        if len(self._actions) != len(oth._actions):
                return False
        for action_name, action in self._actions.items():
            if (oth_action := oth._actions.get(action_name, None)) is None:
                return False
            if action != oth_action:
                return False
        oth_initial_values = oth.initial_values()
        if len(self.initial_values()) != len(oth_initial_values):
                return False
        for fluent, value in self.initial_values().items():
            if (oth_value := oth_initial_values.get(fluent, None)) is None:
                return False
            if value != oth_value:
                return False
        if len(self._timed_effects) != len(oth._timed_effects):
                return False
        for t, tel in self._timed_effects.items():
            if (oth_tel := oth._timed_effects.get(t, None)) is None:
                return False
            if set(tel) != set(oth_tel):
                return False
        if len(self._timed_goals) != len(oth._timed_goals):
                return False
        for t, tgl in self._timed_goals.items():
            if (oth_tgl := oth._timed_goals.get(t, None)) is None:
                return False
            if set(tgl) != set(oth_tgl):
                return False
        if len(self._maintain_goals) != len(oth._maintain_goals):
                return False
        for i, mgl in self._maintain_goals.items():
            if (oth_mgl := oth._maintain_goals.get(i, None)) is None:
                return False
            if set(mgl) != set(oth_mgl):
                return False
        return True

    def __hash__(self) -> int:
        res = hash(self._kind) + hash(self._name)
        for f in self._fluents.items():
            res += hash(f)
        for a in self._actions.items():
            res += hash(a)
        for ut in self._user_types.items():
            res += hash(ut)
        for o in self._objects.items():
            res += hash(o)
        for iv in self.initial_values().items():
            res += hash(iv)
        for te in self._timed_effects.items():
            res += hash(te)
        for tg in self._timed_goals.items():
            res += hash(tg)
        for mg in self._maintain_goals.items():
            res += hash(mg)
        for g in self._goals:
            res += hash(g)
        return res

    def clone(self):
        new_p = Problem(self._name, self._env)
        new_p._kind = self._kind.clone()
        new_p._fluents = {fn: f.clone() for fn, f in self._fluents.items()}
        new_p._actions = {an: a.clone() for an, a in self._actions.items()}
        new_p._user_types = self._user_types.copy()
        new_p._objects = {on: o.clone() for on, o in self._objects.items()}
        new_p._initial_value = self._initial_value.copy()
        new_p._timed_effects = {t.clone(): [e.clone() for e in el] for t, el in self._timed_effects.items()}
        new_p._timed_goals = {t.clone(): [g for g in gl] for t, gl in self._timed_goals.items()}
        new_p._maintain_goals = {i.clone(): [g for g in gl] for i, gl in self._maintain_goals.items()}
        new_p._goals = self._goals[:]
        new_p._initial_defaults = self._initial_defaults.copy()
        new_p._fluents_defaults = {new_p._fluents[fluent.name()]: exp for fluent, exp in self._fluents_defaults.items()}
        assert self == new_p
        assert hash(self) == hash(new_p)
        return new_p

    @property
    def env(self) -> 'upf.environment.Environment':
        '''Returns the problem environment.'''
        return self._env

    def name(self) -> Optional[str]:
        '''Returns the problem name.'''
        return self._name

    def fluents(self) -> Dict[str, 'upf.model.fluent.Fluent']:
        '''Returns the fluents.'''
        return self._fluents

    def fluent(self, name: str) -> 'upf.model.fluent.Fluent':
        '''Returns the fluent with the given name.'''
        assert name in self._fluents
        return self._fluents[name]

    def add_fluent(self, fluent: 'upf.model.fluent.Fluent', *,
                   default_initial_value: Union['upf.model.fnode.FNode', 'upf.model.object.Object', bool,
                                                int, float, Fraction] = None):
        '''Adds the given fluent.'''
        if fluent.name() in self._fluents:
            raise UPFProblemDefinitionError('Fluent ' + fluent.name() + ' already defined!')
        self._update_problem_kind_type(fluent.type())
        for t in fluent.signature():
            self._update_problem_kind_type(t)
        self._fluents[fluent.name()] = fluent
        if not default_initial_value is None:
            v_exp, = self._env.expression_manager.auto_promote(default_initial_value)
            self._fluents_defaults[fluent] = v_exp

    def actions(self) -> Dict[str, 'upf.model.action.Action']:
        '''Returns the actions.'''
        return self._actions

    def instantaneous_actions(self):
        for a in self._actions:
            if isinstance(a, upf.model.action.InstantaneousAction):
                yield a

    def durative_actions(self):
        for a in self._actions:
            if isinstance(a, upf.model.action.DurativeAction):
                yield a

    def conditional_actions(self) -> List['upf.model.action.Action']:
        '''Returns the conditional actions.'''
        return [a for a in self._actions.values() if a.is_conditional()]

    def unconditional_actions(self) -> List['upf.model.action.Action']:
        '''Returns the conditional actions.'''
        return [a for a in self._actions.values() if not a.is_conditional()]

    def action(self, name: str) -> 'upf.model.action.Action':
        '''Returns the action with the given name.'''
        assert name in self._actions
        return self._actions[name]

    def has_action(self, name: str) -> bool:
        '''Returns True if the problem has the action with the given name .'''
        return name in self._actions

    def add_action(self, action: 'upf.model.action.Action'):
        '''Adds the given action.'''
        if action.name() in self._actions:
            raise UPFProblemDefinitionError('InstantaneousAction ' + action.name() + ' already defined!')
        for p in action.parameters():
            self._update_problem_kind_type(p.type())
        if isinstance(action, upf.model.action.InstantaneousAction):
            for c in action.preconditions():
                self._update_problem_kind_condition(c)
            for e in action.effects():
                self._update_problem_kind_effect(e)
        elif isinstance(action, upf.model.action.DurativeAction):
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
        self._actions[action.name()] = action

    def user_types(self) -> Dict[str, 'upf.model.types.Type']:
        '''Returns the user types.'''
        return self._user_types

    def user_type(self, name: str) -> 'upf.model.types.Type':
        '''Returns the user type with the given name.'''
        return self._user_types[name]

    def has_type(self, name: str) -> bool:
        '''Returns True iff the type 'name' is defined.'''
        return name in self._user_types

    def add_object(self, obj: 'upf.model.object.Object'):
        '''Adds the given object.'''
        if obj.name() in self._objects:
            raise UPFProblemDefinitionError('Object ' + obj.name() + ' already defined!')
        self._objects[obj.name()] = obj

    def add_objects(self, objs: List['upf.model.object.Object']):
        '''Adds the given objects.'''
        for obj in objs:
            if obj.name() in self._objects:
                raise UPFProblemDefinitionError('Object ' + obj.name() + ' already defined!')
            self._objects[obj.name()] = obj

    def object(self, name: str) -> 'upf.model.object.Object':
        '''Returns the object with the given name.'''
        return self._objects[name]

    def objects(self, typename: 'upf.model.types.Type') -> List['upf.model.object.Object']:
        '''Returns the objects of the given user types.'''
        res = []
        for obj in self._objects.values():
            if obj.type() == typename:
                res.append(obj)
        return res

    def all_objects(self) -> List['upf.model.object.Object']:
        '''Returns all the objects.'''
        return [o for o in self._objects.values()]

    def set_initial_value(self, fluent: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent'],
                          value: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent', 'upf.model.object.Object', bool,
                                       int, float, Fraction]):
        '''Sets the initial value for the given fluent.'''
        fluent_exp, value_exp = self._env.expression_manager.auto_promote(fluent, value)
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('Initial value assignment has not compatible types!')
        if fluent_exp in self._initial_value:
            raise UPFProblemDefinitionError('Initial value already set!')
        self._initial_value[fluent_exp] = value_exp

    def initial_value(self, fluent: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent']) -> 'upf.model.fnode.FNode':
        '''Gets the initial value of the given fluent.'''
        fluent_exp, = self._env.expression_manager.auto_promote(fluent)
        if fluent_exp in self._initial_value:
            return self._initial_value[fluent_exp]
        elif fluent_exp.fluent() in self._fluents_defaults:
            return self._fluents_defaults[fluent_exp.fluent()]
        elif fluent_exp.fluent().type() in self._initial_defaults:
            return self._initial_defaults[fluent_exp.fluent().type()]
        else:
            raise UPFProblemDefinitionError('Initial value not set!')

    def _domain_size(self, typename: 'upf.model.types.Type') -> int:
        '''Returns the domain size of the given type.'''
        if typename.is_bool_type():
            return 2
        elif typename.is_user_type():
            return len(self.objects(typename))
        elif typename.is_int_type():
            lb = typename.lower_bound() # type: ignore
            ub = typename.upper_bound() # type: ignore
            if lb is None or ub is None:
                raise UPFProblemDefinitionError('Fluent parameters must be groundable!')
            return ub - lb
        else:
            raise UPFProblemDefinitionError('Fluent parameters must be groundable!')

    def _domain_item(self, typename: 'upf.model.types.Type', idx: int) -> 'upf.model.fnode.FNode':
        '''Returns the ith domain item of the given type.'''
        if typename.is_bool_type():
            return self._env.expression_manager.Bool(idx == 0)
        elif typename.is_user_type():
            return self._env.expression_manager.ObjectExp(self.objects(typename)[idx])
        elif typename.is_int_type():
            lb = typename.lower_bound() # type: ignore
            ub = typename.upper_bound() # type: ignore
            if lb is None or ub is None:
                raise UPFProblemDefinitionError('Fluent parameters must be groundable!')
            return self._env.expression_manager.Int(lb + idx)
        else:
            raise UPFProblemDefinitionError('Fluent parameters must be groundable!')

    def _get_ith_fluent_exp(self, fluent: 'upf.model.fluent.Fluent', domain_sizes: List[int], idx: int) -> 'upf.model.fnode.FNode':
        '''Returns the ith ground fluent expression.'''
        quot = idx
        rem = 0
        actual_parameters = []
        for i in range(fluent.arity()):
            ds = domain_sizes[i];
            rem = quot % ds
            quot //= ds
            v = self._domain_item(fluent.signature()[i], rem)
            actual_parameters.append(v)
        return fluent(*actual_parameters)

    def initial_values(self) -> Dict['upf.model.fnode.FNode', 'upf.model.fnode.FNode']:
        '''Gets the initial value of the fluents.'''
        res = self._initial_value
        for f in self._fluents.values():
            if f.arity() == 0:
                f_exp = self._env.expression_manager.FluentExp(f)
                res[f_exp] = self.initial_value(f_exp)
            else:
                ground_size = 1
                domain_sizes = []
                is_groundable = True
                for p in f.signature():
                    ds = self._domain_size(p)
                    domain_sizes.append(ds)
                    ground_size *= ds
                if is_groundable:
                    for i in range(ground_size):
                        f_exp = self._get_ith_fluent_exp(f, domain_sizes, i)
                        res[f_exp] = self.initial_value(f_exp)
        return res

    def add_timed_goal(self, timing: 'upf.model.timing.Timing', goal: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent', bool]):
        '''Adds a timed goal.'''
        if timing.is_from_end() and timing.bound() > 0:
            raise UPFProblemDefinitionError('Timing used in timed goal cannot be `end - k` with k > 0.')
        self._kind.set_time('TIMED_GOALS') # type: ignore
        goal_exp, = self._env.expression_manager.auto_promote(goal)
        assert self._env.type_checker.get_type(goal_exp).is_bool_type()
        self._update_problem_kind_condition(goal_exp)
        if timing in self._timed_goals:
            self._timed_goals[timing].append(goal_exp)
        else:
            self._timed_goals[timing] = [goal_exp]
        self._kind.set_time('CONTINUOUS_TIME') # type: ignore

    def timed_goals(self) -> Dict['upf.model.timing.Timing', List['upf.model.fnode.FNode']]:
        '''Returns the timed goals.'''
        return self._timed_goals

    def add_timed_effect(self, timing: 'upf.model.timing.Timing', fluent: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent'],
                         value: 'upf.model.expression.Expression', condition: 'upf.model.expression.BoolExpression' = True):
        '''Adds the given timed effect.'''
        if timing.is_from_end():
            raise UPFProblemDefinitionError(f'Timing used in timed effect cannot be EndTiming.')
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value,
                                                                                         condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('Timed effect has not compatible types!')
        self._add_effect_instance(timing, upf.model.effect.Effect(fluent_exp, value_exp, condition_exp))

    def add_increase_effect(self, timing: 'upf.model.timing.Timing', fluent: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent'],
                            value: 'upf.model.expression.Expression', condition: 'upf.model.expression.BoolExpression' = True):
        '''Adds the given timed increase effect.'''
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value,
                                                                                         condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('Timed effect has not compatible types!')
        self._add_effect_instance(timing,
                                  upf.model.effect.Effect(fluent_exp, value_exp,
                                         condition_exp, kind = upf.model.effect.INCREASE))

    def add_decrease_effect(self, timing: 'upf.model.timing.Timing', fluent: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent'],
                            value: 'upf.model.expression.Expression', condition: 'upf.model.expression.BoolExpression' = True):
        '''Adds the given timed decrease effect.'''
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value,
                                                                                         condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('Timed effect has not compatible types!')
        self._add_effect_instance(timing,
                                  upf.model.effect.Effect(fluent_exp, value_exp,
                                         condition_exp, kind = upf.model.effect.DECREASE))

    def _add_effect_instance(self, timing: 'upf.model.timing.Timing', effect: 'upf.model.effect.Effect'):
        self._update_problem_kind_effect(effect)
        self._kind.set_time('CONTINUOUS_TIME') # type: ignore
        self._kind.set_time('TIMED_EFFECT') # type: ignore
        if timing in self._timed_effects:
            self._timed_effects[timing].append(effect)
        else:
            self._timed_effects[timing] = [effect]

    def timed_effects(self) -> Dict['upf.model.timing.Timing', List['upf.model.effect.Effect']]:
        '''Returns the timed effects.'''
        return self._timed_effects

    def add_maintain_goal(self, interval: 'upf.model.timing.Interval', goal: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent', bool]):
        '''Adds a maintain goal.'''
        if ((interval.lower().is_from_end() and interval.lower().bound() > 0) or
            (interval.upper().is_from_end() and interval.upper().bound() > 0)):
            raise UPFProblemDefinitionError('Problem timing can not be `end - k` with k > 0.')
        self._kind.set_time('MAINTAIN_GOALS') # type: ignore
        goal_exp, = self._env.expression_manager.auto_promote(goal)
        assert self._env.type_checker.get_type(goal_exp).is_bool_type()
        self._update_problem_kind_condition(goal_exp)
        if interval in self._maintain_goals:
            self._maintain_goals[interval].append(goal_exp)
        else:
            self._maintain_goals[interval] = [goal_exp]
        self._kind.set_time('CONTINUOUS_TIME') # type: ignore

    def maintain_goals(self) -> Dict['upf.model.timing.Interval', List['upf.model.fnode.FNode']]:
        '''Returns the maintain goals.'''
        return self._maintain_goals

    def add_goal(self, goal: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent', bool]):
        '''Adds a goal.'''
        goal_exp, = self._env.expression_manager.auto_promote(goal)
        assert self._env.type_checker.get_type(goal_exp).is_bool_type()
        self._update_problem_kind_condition(goal_exp)
        self._goals.append(goal_exp)

    def goals(self) -> List['upf.model.fnode.FNode']:
        '''Returns the goals.'''
        return self._goals

    def kind(self) -> 'upf.model.problem_kind.ProblemKind':
        '''Returns the problem kind of this planning problem.'''
        return self._kind

    def has_quantifiers(self) -> bool:
        '''Returns True only if the problem has quantifiers'''
        return self._kind.has_existential_conditions() or self._kind.has_universal_conditions() # type: ignore

    def _update_problem_kind_effect(self, e: 'upf.model.effect.Effect'):
        if e.is_conditional():
            self._kind.set_effects_kind('CONDITIONAL_EFFECTS') # type: ignore
        elif e.is_increase():
            self._kind.set_effects_kind('INCREASE_EFFECTS') # type: ignore
        elif e.is_decrease():
            self._kind.set_effects_kind('DECREASE_EFFECTS') # type: ignore

    def _update_problem_kind_condition(self, exp: 'upf.model.fnode.FNode'):
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

    def _update_problem_kind_type(self, type: 'upf.model.types.Type'):
        if type.is_user_type():
            self._kind.set_typing('FLAT_TYPING') # type: ignore
            self._user_types[type.name()] = type # type: ignore
        elif type.is_int_type():
            self._kind.set_numbers('DISCRETE_NUMBERS') # type: ignore
        elif type.is_real_type():
            self._kind.set_numbers('CONTINUOUS_NUMBERS') # type: ignore
