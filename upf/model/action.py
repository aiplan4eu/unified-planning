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
"""
This module defines the InstantaneousAction class and the ActionParameter class.
An InstantaneousAction has a name, a list of ActionParameter, a list of preconditions
and a list of effects.
"""


import upf
import upf.model.types
from upf.environment import get_env, Environment
from upf.model.fnode import FNode
from upf.exceptions import UPFTypeError, UPFUnboundedVariablesError, UPFProblemDefinitionError
from upf.model.expression import BoolExpression, Expression
from upf.model.effect import Effect, INCREASE, DECREASE
from upf.model.timing import ClosedIntervalDuration, FixedDuration, Interval, IntervalDuration, LeftOpenIntervalDuration, OpenIntervalDuration, RightOpenIntervalDuration
from upf.model.timing import EndTiming, StartTiming, Timing
from fractions import Fraction
from typing import Dict, List, Union
from collections import OrderedDict


class ActionParameter:
    """Represents an action parameter.
    An action parameter has a name, used to retrieve the parameter
    from the action, and a type, used to represent that the action
    parameter is of the given type."""
    def __init__(self, name: str, typename: upf.model.types.Type):
        self._name = name
        self._typename = typename

    def __repr__(self) -> str:
        return f'{str(self.type())} {self.name()}'

    def name(self) -> str:
        """Returns the parameter name."""
        return self._name

    def type(self) -> upf.model.types.Type:
        """Returns the parameter type."""
        return self._typename

    def __eq__(self, oth: object) -> bool:
        return self.name() == oth.name() and self.type() == oth.type() # type: ignore

    def __hash__(self) -> int:
        return hash(self.name()) + hash(self.type())


class Action:
    """This is the action interface."""
    def __init__(self, _name: str, _parameters: 'OrderedDict[str, upf.model.types.Type]' = None,
                 _env: Environment = None, **kwargs: upf.model.types.Type):
        self._env = get_env(_env)
        self._name = _name
        self._parameters: 'OrderedDict[str, ActionParameter]' = OrderedDict()
        if _parameters is not None:
            assert len(kwargs) == 0
            for n, t in _parameters.items():
                self._parameters[n] = ActionParameter(n, t)
        else:
            for n, t in kwargs.items():
                self._parameters[n] = ActionParameter(n, t)

    def name(self) -> str:
        """Returns the action name."""
        return self._name

    def parameters(self) -> List[ActionParameter]:
        """Returns the list of the action parameters."""
        return list(self._parameters.values())

    def parameter(self, name: str) -> ActionParameter:
        """Returns the parameter of the action with the given name."""
        return self._parameters[name]

    def is_conditional(self) -> bool:
        """Returns True if the action has conditional effects."""
        raise NotImplementedError


class InstantaneousAction(Action):
    """Represents an instantaneous action."""
    def __init__(self, _name: str, _parameters: 'OrderedDict[str, upf.model.types.Type]' = None,
                 _env: Environment = None, **kwargs: upf.model.types.Type):
        Action.__init__(self, _name, _parameters, _env, **kwargs)
        self._preconditions: List[FNode] = []
        self._effects: List[Effect] = []

    def __repr__(self) -> str:
        s = []
        s.append(f'action {self.name()}')
        first = True
        for p in self.parameters():
            if first:
                s.append('(')
                first = False
            else:
                s.append(', ')
            s.append(str(p))
        if not first:
            s.append(')')
        s.append(' {\n')
        s.append('    preconditions = [\n')
        for c in self.preconditions():
            s.append(f'      {str(c)}\n')
        s.append('    ]\n')
        s.append('    effects = [\n')
        for e in self.effects():
            s.append(f'      {str(e)}\n')
        s.append('    ]\n')
        s.append('  }')
        return ''.join(s)

    def preconditions(self) -> List[FNode]:
        """Returns the list of the action preconditions."""
        return self._preconditions

    def effects(self) -> List[Effect]:
        """Returns the list of the action effects."""
        return self._effects

    def conditional_effects(self) -> List[Effect]:
        """Returns the list of the action conditional effects."""
        return [e for e in self._effects if e.is_conditional()]

    def is_conditional(self) -> bool:
        """Returns True if the action has conditional effects."""
        return any(e.is_conditional() for e in self._effects)

    def unconditional_effects(self) -> List[Effect]:
        """Returns the list of the action unconditional effects."""
        return [e for e in self._effects if not e.is_conditional()]

    def add_precondition(self, precondition: Union[FNode, 'upf.Fluent', ActionParameter, bool]):
        """Adds the given action precondition."""
        precondition_exp, = self._env.expression_manager.auto_promote(precondition)
        assert self._env.type_checker.get_type(precondition_exp).is_bool_type()
        free_vars = self._env.free_vars_oracle.get_free_variables(precondition_exp)
        if len(free_vars) != 0:
            raise UPFUnboundedVariablesError(f"The precondition {str(precondition_exp)} has unbounded variables:\n{str(free_vars)}")
        self._preconditions.append(precondition_exp)

    def add_effect(self, fluent: Union[FNode, 'upf.Fluent'],
                   value: Expression, condition: BoolExpression = True):
        """Adds the given action effect."""
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('InstantaneousAction effect has not compatible types!')
        self._effects.append(Effect(fluent_exp, value_exp, condition_exp))

    def add_increase_effect(self, fluent: Union[FNode, 'upf.Fluent'],
                   value: Expression, condition: BoolExpression = True):
        """Adds the given action increase effect."""
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('InstantaneousAction effect has not compatible types!')
        self._effects.append(Effect(fluent_exp, value_exp, condition_exp, kind = INCREASE))

    def add_decrease_effect(self, fluent: Union[FNode, 'upf.Fluent'],
                   value: Expression, condition: BoolExpression = True):
        """Adds the given action decrease effect."""
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('InstantaneousAction effect has not compatible types!')
        self._effects.append(Effect(fluent_exp, value_exp, condition_exp, kind = DECREASE))

    def _add_effect_instance(self, effect: Effect):
        self._effects.append(effect)

    def _set_preconditions(self, preconditions: List[FNode]):
        self._preconditions = preconditions


class DurativeAction(Action):
    '''Represents a durative action.'''
    def __init__(self, _name: str, _parameters: 'OrderedDict[str, upf.model.types.Type]' = None,
                 _env: Environment = None, **kwargs: upf.model.types.Type):
        Action.__init__(self, _name, _parameters, _env, **kwargs)
        self._duration: IntervalDuration = FixedDuration(self._env.expression_manager.Int(0))
        self._conditions: Dict[Timing, List[FNode]] = {}
        self._durative_conditions: Dict[Interval, List[FNode]] = {}
        self._effects: Dict[Timing, List[Effect]] = {}

    def __repr__(self) -> str:
        s = []
        s.append(f'durative action {self.name()}')
        first = True
        for p in self.parameters():
            if first:
                s.append('(')
                first = False
            else:
                s.append(', ')
            s.append(str(p))
        if not first:
            s.append(')')
        s.append(' {\n')
        s.append(f'    duration = {str(self._duration)}')
        s.append('    conditions = [\n')
        for t, cl in self.conditions().items():
            s.append(f'      {str(t)}:\n')
            for c in cl:
                s.append(f'        {str(c)}\n')
        s.append('    ]\n')
        s.append('    durative conditions = [\n')
        for i, cl in self.durative_conditions().items():
            s.append(f'      {str(i)}:\n')
            for c in cl:
                s.append(f'        {str(c)}\n')
        s.append('    ]\n')
        s.append('    effects = [\n')
        for t, el in self.effects().items():
            s.append(f'      {str(t)}:\n')
            for e in el:
                s.append(f'        {str(e)}:\n')
        s.append('    ]\n')
        s.append('  }')
        return ''.join(s)

    def duration(self):
        '''Returns the action duration interval.'''
        return self._duration

    def conditions(self):
        '''Returns the action conditions.'''
        return self._conditions

    def durative_conditions(self):
        '''Returns the action durative conditions.'''
        return self._durative_conditions

    def effects(self):
        '''Returns the action effects.'''
        return self._effects

    def conditional_effects(self):
        '''Return the action conditional effects.'''
        retval: Dict[Timing, List[Effect]] = {}
        for timing, effect_list in self._effects.items():
            cond_effect_list = [e for e in effect_list if e.is_conditional()]
            if len(cond_effect_list) > 0:
                retval[timing] = cond_effect_list
        return retval

    def unconditional_effects(self):
        '''Return the action unconditional effects.'''
        retval: Dict[Timing, List[Effect]] = {}
        for timing, effect_list in self._effects.items():
            uncond_effect_list = [e for e in effect_list if not e.is_conditional()]
            if len(uncond_effect_list) > 0:
                retval[timing] = uncond_effect_list
        return retval

    def is_conditional(self) -> bool:
        '''Returns True if the action has conditional effects.'''
        return any(e.is_conditional() for l in self._effects.values() for e in l)

    def set_duration_constraint(self, duration: IntervalDuration):
        '''Sets the duration interval.'''
        lower, upper = duration.lower(), duration.upper()
        if not (lower.is_int_constant() or lower.is_real_constant()):
            raise UPFProblemDefinitionError('Duration bound must be constant.')
        elif not (upper.is_int_constant() or upper.is_real_constant()):
            raise UPFProblemDefinitionError('Duration bound must be constant.')
        elif (upper.constant_value() < lower.constant_value() or
              (upper.constant_value() == lower.constant_value() and
               (duration.is_left_open() or duration.is_right_open()))):
            raise UPFProblemDefinitionError(f'{duration} is an empty interval duration of action: {self.name()}.')
        self._duration = duration

    def set_fixed_duration(self, value: Union[FNode, int, Fraction]):
        value_exp, = self._env.expression_manager.auto_promote(value)
        self.set_duration_constraint(FixedDuration(value_exp))

    def set_closed_interval_duration(self, lower: Union[FNode, int, Fraction],
                                     upper: Union[FNode, int, Fraction]):
        lower_exp, upper_exp = self._env.expression_manager.auto_promote(lower, upper)
        self.set_duration_constraint(ClosedIntervalDuration(lower_exp, upper_exp))

    def set_open_interval_duration(self, lower: Union[FNode, int, Fraction],
                                   upper: Union[FNode, int, Fraction]):
        lower_exp, upper_exp = self._env.expression_manager.auto_promote(lower, upper)
        self.set_duration_constraint(OpenIntervalDuration(lower_exp, upper_exp))

    def set_left_open_interval_duration(self, lower: Union[FNode, int, Fraction],
                                        upper: Union[FNode, int, Fraction]):
        lower_exp, upper_exp = self._env.expression_manager.auto_promote(lower, upper)
        self.set_duration_constraint(LeftOpenIntervalDuration(lower_exp, upper_exp))

    def set_right_open_interval_duration(self, lower: Union[FNode, int, Fraction],
                                         upper: Union[FNode, int, Fraction]):
        lower_exp, upper_exp = self._env.expression_manager.auto_promote(lower, upper)
        self.set_duration_constraint(RightOpenIntervalDuration(lower_exp, upper_exp))

    def add_condition(self, timing: Timing,
                      condition: Union[FNode, 'upf.Fluent', ActionParameter, bool]):
        '''Adds the given condition.'''
        condition_exp, = self._env.expression_manager.auto_promote(condition)
        assert self._env.type_checker.get_type(condition_exp).is_bool_type()
        if timing in self._conditions:
            self._conditions[timing].append(condition_exp)
        else:
            self._conditions[timing] = [condition_exp]

    def _set_conditions(self, timing: Timing, conditions: List[FNode]):
        self._conditions[timing] = conditions

    def add_durative_condition(self, interval: Interval,
                               condition: Union[FNode, 'upf.Fluent', ActionParameter, bool]):
        '''Adds the given durative condition.'''
        if not ((isinstance(interval.lower(), StartTiming) or isinstance(interval.lower(), EndTiming)) and
                (isinstance(interval.upper(), StartTiming) or isinstance(interval.upper(), EndTiming))):
            raise UPFProblemDefinitionError(f'The interval bounds of a durative condition in an action must be a StartTiming or an EndTiming.\n Interval {interval} does not respect this.')
        condition_exp, = self._env.expression_manager.auto_promote(condition)
        assert self._env.type_checker.get_type(condition_exp).is_bool_type()
        if interval in self._durative_conditions:
            self._durative_conditions[interval].append(condition_exp)
        else:
            self._durative_conditions[interval] = [condition_exp]

    def add_effect(self, timing: Timing, fluent: Union[FNode, 'upf.Fluent'],
                   value: Expression, condition: BoolExpression = True):
        '''Adds the given action effect.'''
        if not (isinstance(timing, StartTiming) or isinstance(timing, EndTiming)):
            raise UPFProblemDefinitionError(f'The timing of an effect into an action must be a StartTiming or an EndTiming.\n Timing {timing} is none of those.')
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('InstantaneousAction effect has not compatible types!')
        self._add_effect_instance(timing, Effect(fluent_exp, value_exp, condition_exp))

    def add_increase_effect(self, timing: Timing, fluent: Union[FNode, 'upf.Fluent'],
                            value: Expression, condition: BoolExpression = True):
        '''Adds the given action increase effect.'''
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('InstantaneousAction effect has not compatible types!')
        self._add_effect_instance(timing,
                                  Effect(fluent_exp, value_exp,
                                         condition_exp, kind = INCREASE))

    def add_decrease_effect(self, timing: Timing, fluent: Union[FNode, 'upf.Fluent'],
                            value: Expression, condition: BoolExpression = True):
        '''Adds the given action decrease effect.'''
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('InstantaneousAction effect has not compatible types!')
        self._add_effect_instance(timing,
                                  Effect(fluent_exp, value_exp,
                                         condition_exp, kind = DECREASE))

    def _add_effect_instance(self, timing: Timing, effect: Effect):
        if timing in self._effects:
            self._effects[timing].append(effect)
        else:
            self._effects[timing] = [effect]
