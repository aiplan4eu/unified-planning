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


import upf.types
import upf.operators as op
from upf.environment import get_env, Environment
from upf.expression import Expression, BoolExpression
from upf.temporal import Interval, Timing
from upf.effect import Effect, INCREASE, DECREASE
from upf.fnode import FNode
from upf.exceptions import UPFProblemDefinitionError, UPFTypeError
from upf.problem_kind import ProblemKind
from upf.operators_extractor import OperatorsExtractor
from fractions import Fraction
from typing import List, Dict, Set, Union, Optional


class Problem:
    '''Represents a planning problem.'''
    def __init__(self, name: str = None, env: Environment = None, *,
                 initial_defaults: Dict[upf.types.Type, Union[FNode, 'upf.Object', bool,
                                                              int, float, Fraction]] = {}):
        self._env = get_env(env)
        self._operators_extractor = OperatorsExtractor()
        self._kind = ProblemKind()
        self._name = name
        self._fluents: Dict[str, upf.Fluent] = {}
        self._actions: Dict[str, upf.ActionInterface] = {}
        self._user_types: Dict[str, upf.types.Type] = {}
        self._objects: Dict[str, upf.Object] = {}
        self._initial_value: Dict[FNode, FNode] = {}
        self._timed_effects: Dict[Timing, List[Effect]] = {}
        self._timed_goals: Dict[Timing, List[FNode]] = {}
        self._maintain_goals: Dict[Interval, List[FNode]] = {}
        self._goals: List[FNode] = list()
        self._initial_defaults: Dict[upf.types.Type, FNode] = {}
        for k, v in initial_defaults.items():
            v_exp, = self._env.expression_manager.auto_promote(v)
            self._initial_defaults[k] = v_exp
        self._fluents_defaults: Dict[upf.Fluent, FNode] = {}

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

    @property
    def env(self) -> Environment:
        '''Returns the problem environment.'''
        return self._env

    def name(self) -> Optional[str]:
        '''Returns the problem name.'''
        return self._name

    def fluents(self) -> Dict[str, upf.Fluent]:
        '''Returns the fluents.'''
        return self._fluents

    def fluent(self, name: str) -> upf.Fluent:
        '''Returns the fluent with the given name.'''
        assert name in self._fluents
        return self._fluents[name]

    def add_fluent(self, fluent: upf.Fluent, *,
                   default_initial_value: Union[FNode, 'upf.Object', bool,
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

    def actions(self) -> Dict[str, upf.ActionInterface]:
        '''Returns the actions.'''
        return self._actions

    def conditional_actions(self) -> List[upf.ActionInterface]:
        '''Returns the conditional actions.'''
        return [a for a in self._actions.values() if a.is_conditional()]

    def unconditional_actions(self) -> List[upf.ActionInterface]:
        '''Returns the conditional actions.'''
        return [a for a in self._actions.values() if not a.is_conditional()]

    def action(self, name: str) -> upf.ActionInterface:
        '''Returns the action with the given name.'''
        assert name in self._actions
        return self._actions[name]

    def has_action(self, name: str) -> bool:
        '''Returns True if the problem has the action with the given name .'''
        return name in self._actions

    def add_action(self, action: upf.ActionInterface):
        '''Adds the given action.'''
        if action.name() in self._actions:
            raise UPFProblemDefinitionError('Action ' + action.name() + ' already defined!')
        for p in action.parameters():
            self._update_problem_kind_type(p.type())
        if isinstance(action, upf.Action):
            for c in action.preconditions():
                self._update_problem_kind_condition(c)
            for e in action.effects():
                self._update_problem_kind_effect(e)
        elif isinstance(action, upf.DurativeAction):
            lower, upper = action.duration().lower(), action.duration().upper()
            if lower.constant_value() != upper.constant_value():
                self._kind.set_time('DURATION_INEQUALITIES') # type: ignore
            for i, l in action.durative_conditions().items():
                if i.lower().bound() != 0 or i.upper().bound() != 0:
                    self._kind.set_time('ICE') # type: ignore
                for c in l:
                    self._update_problem_kind_condition(c)
            for t, l in action.conditions().items():
                if t.bound() != 0:
                    self._kind.set_time('ICE') # type: ignore
                for c in l:
                    self._update_problem_kind_condition(c)
            for t, l in action.effects().items():
                if t.bound() != 0:
                    self._kind.set_time('ICE') # type: ignore
                for e in l:
                    self._update_problem_kind_effect(e)
            self._kind.set_time('CONTINUOUS_TIME') # type: ignore
        self._actions[action.name()] = action

    def user_types(self) -> Dict[str, upf.types.Type]:
        '''Returns the user types.'''
        return self._user_types

    def user_type(self, name: str) -> upf.types.Type:
        '''Returns the user type with the given name.'''
        return self._user_types[name]

    def has_type(self, name: str) -> bool:
        '''Returns True iff the type 'name' is defined.'''
        return name in self._user_types

    def add_object(self, obj: upf.Object):
        '''Adds the given object.'''
        if obj.name() in self._objects:
            raise UPFProblemDefinitionError('Object ' + obj.name() + ' already defined!')
        self._objects[obj.name()] = obj

    def add_objects(self, objs: List[upf.Object]):
        '''Adds the given objects.'''
        for obj in objs:
            if obj.name() in self._objects:
                raise UPFProblemDefinitionError('Object ' + obj.name() + ' already defined!')
            self._objects[obj.name()] = obj

    def object(self, name: str) -> upf.Object:
        '''Returns the object with the given name.'''
        return self._objects[name]

    def objects(self, typename: upf.types.Type) -> List[upf.Object]:
        '''Returns the objects of the given user types.'''
        res = []
        for obj in self._objects.values():
            if obj.type() == typename:
                res.append(obj)
        return res

    def all_objects(self) -> List[upf.Object]:
        '''Returns all the objects.'''
        return [o for o in self._objects.values()]

    def set_initial_value(self, fluent: Union[FNode, upf.Fluent],
                          value: Union[FNode, upf.Fluent, upf.Object, bool,
                                       int, float, Fraction]):
        '''Sets the initial value for the given fluent.'''
        fluent_exp, value_exp = self._env.expression_manager.auto_promote(fluent, value)
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('Initial value assignment has not compatible types!')
        if fluent_exp in self._initial_value:
            raise UPFProblemDefinitionError('Initial value already set!')
        self._initial_value[fluent_exp] = value_exp

    def initial_value(self, fluent: Union[FNode, upf.Fluent]) -> FNode:
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

    def _domain_size(self, typename: upf.types.Type) -> int:
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

    def _domain_item(self, typename: upf.types.Type, idx: int) -> FNode:
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

    def _get_ith_fluent_exp(self, fluent: upf.Fluent, domain_sizes: List[int], idx: int) -> FNode:
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

    def initial_values(self) -> Dict[FNode, FNode]:
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

    def add_timed_goal(self, timing: Timing, goal: Union[FNode, upf.Fluent, bool]):
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

    def timed_goals(self) -> Dict[Timing, List[FNode]]:
        '''Returns the timed goals.'''
        return self._timed_goals

    def add_timed_effect(self, timing: Timing, fluent: Union[FNode, 'upf.Fluent'],
                         value: Expression, condition: BoolExpression = True):
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
        self._add_effect_instance(timing, Effect(fluent_exp, value_exp, condition_exp))

    def add_increase_effect(self, timing: Timing, fluent: Union[FNode, 'upf.Fluent'],
                            value: Expression, condition: BoolExpression = True):
        '''Adds the given timed increase effect.'''
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value,
                                                                                         condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('Timed effect has not compatible types!')
        self._add_effect_instance(timing,
                                  Effect(fluent_exp, value_exp,
                                         condition_exp, kind = INCREASE))

    def add_decrease_effect(self, timing: Timing, fluent: Union[FNode, 'upf.Fluent'],
                            value: Expression, condition: BoolExpression = True):
        '''Adds the given timed decrease effect.'''
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value,
                                                                                         condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('Timed effect has not compatible types!')
        self._add_effect_instance(timing,
                                  Effect(fluent_exp, value_exp,
                                         condition_exp, kind = DECREASE))

    def _add_effect_instance(self, timing: Timing, effect: Effect):
        self._update_problem_kind_effect(effect)
        self._kind.set_time('CONTINUOUS_TIME') # type: ignore
        self._kind.set_time('TIMED_EFFECT') # type: ignore
        if timing in self._timed_effects:
            self._timed_effects[timing].append(effect)
        else:
            self._timed_effects[timing] = [effect]

    def timed_effects(self) -> Dict[Timing, List[Effect]]:
        '''Returns the timed effects.'''
        return self._timed_effects

    def add_maintain_goal(self, interval: Interval, goal: Union[FNode, 'upf.Fluent', bool]):
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

    def maintain_goals(self) -> Dict[Interval, List[FNode]]:
        '''Returns the maintain goals.'''
        return self._maintain_goals

    def add_goal(self, goal: Union[FNode, upf.Fluent, bool]):
        '''Adds a goal.'''
        goal_exp, = self._env.expression_manager.auto_promote(goal)
        assert self._env.type_checker.get_type(goal_exp).is_bool_type()
        self._update_problem_kind_condition(goal_exp)
        self._goals.append(goal_exp)

    def goals(self) -> List[FNode]:
        '''Returns the goals.'''
        return self._goals

    def kind(self) -> ProblemKind:
        '''Returns the problem kind of this planning problem.'''
        return self._kind

    def has_quantifiers(self) -> bool:
        '''Returns True only if the problem has quantifiers'''
        return self._kind.has_existential_conditions() or self._kind.has_universal_conditions() # type: ignore

    def _update_problem_kind_effect(self, e: Effect):
        if e.is_conditional():
            self._kind.set_effects_kind('CONDITIONAL_EFFECTS') # type: ignore
        elif e.is_increase():
            self._kind.set_effects_kind('INCREASE_EFFECTS') # type: ignore
        elif e.is_decrease():
            self._kind.set_effects_kind('DECREASE_EFFECTS') # type: ignore

    def _update_problem_kind_condition(self, exp: FNode):
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

    def _update_problem_kind_type(self, type: upf.types.Type):
        if type.is_user_type():
            self._kind.set_typing('FLAT_TYPING') # type: ignore
            self._user_types[type.name()] = type # type: ignore
        elif type.is_int_type():
            self._kind.set_numbers('DISCRETE_NUMBERS') # type: ignore
        elif type.is_real_type():
            self._kind.set_numbers('CONTINUOUS_NUMBERS') # type: ignore
