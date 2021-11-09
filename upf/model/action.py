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
from upf.environment import get_env, Environment
from upf.exceptions import UPFTypeError, UPFUnboundedVariablesError, UPFProblemDefinitionError
from fractions import Fraction
from typing import Dict, List, Union
from collections import OrderedDict


class ActionParameter:
    """Represents an action parameter.
    An action parameter has a name, used to retrieve the parameter
    from the action, and a type, used to represent that the action
    parameter is of the given type."""
    def __init__(self, name: str, typename: 'upf.model.types.Type'):
        self._name = name
        self._typename = typename

    def __repr__(self) -> str:
        return f'{str(self.type())} {self.name()}'

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, ActionParameter):
            return self._name == oth._name and self._typename == oth._typename
        else:
            return False

    def __hash__(self) -> int:
        return hash(self._name) + hash(self._typename)

    def clone(self):
        new_ap = ActionParameter(self._name, self._typename)
        assert self == new_ap
        assert hash(self) == hash(new_ap)
        return new_ap

    def name(self) -> str:
        """Returns the parameter name."""
        return self._name

    def type(self) -> 'upf.model.types.Type':
        """Returns the parameter type."""
        return self._typename

class Action:
    """This is the action interface."""
    def __init__(self, _name: str, _parameters: 'OrderedDict[str, upf.model.types.Type]' = None,
                 _env: Environment = None, **kwargs: 'upf.model.types.Type'):
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

    def __eq__(self, oth: object) -> bool:
        raise NotImplementedError

    def __hash__(self) -> int:
        raise NotImplementedError

    def clone(self):
        raise NotImplementedError

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
                 _env: Environment = None, **kwargs: 'upf.model.types.Type'):
        Action.__init__(self, _name, _parameters, _env, **kwargs)
        self._preconditions: List[upf.model.fnode.FNode] = []
        self._effects: List[upf.model.effect.Effect] = []

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

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, InstantaneousAction):
            cond = self._env == oth._env and self._name == oth._name and self._parameters == oth._parameters
            return cond and set(self._preconditions) == set(oth._preconditions) and set(self._effects) == set(oth._effects)
        else:
            return False

    def __hash__(self) -> int:
        res = hash(self._name)
        for ap in self._parameters.items():
            res += hash(ap)
        for p in self._preconditions:
            res += hash(p)
        for e in self._effects:
            res += hash(e)
        return res

    def clone(self):
        new_params = {}
        for param_name, param in self._parameters.items():
            new_params[param_name] = param.type()
        new_instantaneous_action = InstantaneousAction(self._name, new_params, self._env)
        new_instantaneous_action._preconditions = self._preconditions[:]
        new_instantaneous_action._effects = self._effects[:]
        assert self == new_instantaneous_action
        assert hash(self) == hash(new_instantaneous_action)
        return new_instantaneous_action

    def preconditions(self) -> List['upf.model.fnode.FNode']:
        """Returns the list of the action preconditions."""
        return self._preconditions

    def effects(self) -> List['upf.model.effect.Effect']:
        """Returns the list of the action effects."""
        return self._effects

    def conditional_effects(self) -> List['upf.model.effect.Effect']:
        """Returns the list of the action conditional effects."""
        return [e for e in self._effects if e.is_conditional()]

    def is_conditional(self) -> bool:
        """Returns True if the action has conditional effects."""
        return any(e.is_conditional() for e in self._effects)

    def unconditional_effects(self) -> List['upf.model.effect.Effect']:
        """Returns the list of the action unconditional effects."""
        return [e for e in self._effects if not e.is_conditional()]

    def add_precondition(self, precondition: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent', ActionParameter, bool]):
        """Adds the given action precondition."""
        precondition_exp, = self._env.expression_manager.auto_promote(precondition)
        assert self._env.type_checker.get_type(precondition_exp).is_bool_type()
        free_vars = self._env.free_vars_oracle.get_free_variables(precondition_exp)
        if len(free_vars) != 0:
            raise UPFUnboundedVariablesError(f"The precondition {str(precondition_exp)} has unbounded variables:\n{str(free_vars)}")
        if precondition_exp not in self._preconditions:
            self._preconditions.append(precondition_exp)

    def add_effect(self, fluent: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent'],
                   value: 'upf.model.expression.Expression', condition: 'upf.model.expression.BoolExpression' = True):
        """Adds the given action effect."""
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('InstantaneousAction effect has not compatible types!')
        self._add_effect_instance(upf.model.effect.Effect(fluent_exp, value_exp, condition_exp))

    def add_increase_effect(self, fluent: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent'],
                   value: 'upf.model.expression.Expression', condition: 'upf.model.expression.BoolExpression' = True):
        """Adds the given action increase effect."""
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('InstantaneousAction effect has not compatible types!')
        self._add_effect_instance(upf.model.effect.Effect(fluent_exp, value_exp, condition_exp, kind = upf.model.effect.INCREASE))

    def add_decrease_effect(self, fluent: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent'],
                   value: 'upf.model.expression.Expression', condition: 'upf.model.expression.BoolExpression' = True):
        """Adds the given action decrease effect."""
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('InstantaneousAction effect has not compatible types!')
        self._add_effect_instance(upf.model.effect.Effect(fluent_exp, value_exp, condition_exp, kind = upf.model.effect.DECREASE))

    def _add_effect_instance(self, effect: 'upf.model.effect.Effect'):
        if effect not in self._effects:
            self._effects.append(effect)

    def _set_preconditions(self, preconditions: List['upf.model.fnode.FNode']):
        self._preconditions = preconditions


class DurativeAction(Action):
    '''Represents a durative action.'''
    def __init__(self, _name: str, _parameters: 'OrderedDict[str, upf.model.types.Type]' = None,
                 _env: Environment = None, **kwargs: 'upf.model.types.Type'):
        Action.__init__(self, _name, _parameters, _env, **kwargs)
        self._duration: upf.model.timing.IntervalDuration = upf.model.timing.FixedDuration(self._env.expression_manager.Int(0))
        self._conditions: Dict[upf.model.timing.Timing, List[upf.model.fnode.FNode]] = {}
        self._durative_conditions: Dict[upf.model.timing.Interval, List[upf.model.fnode.FNode]] = {}
        self._effects: Dict[upf.model.timing.Timing, List[upf.model.effect.Effect]] = {}

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
        s.append(f'    duration = {str(self._duration)}\n')
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

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, DurativeAction):
            if self._env != oth._env or self._name != oth._name or self._parameters != oth._parameters or self._duration != oth._duration:
                return False
            if len(self._conditions) != len(oth._conditions):
                return False
            for t, cl in self._conditions.items():
                if (oth_cl := oth._conditions.get(t, None)) is None:
                    return False
                if set(cl) != set(oth_cl):
                    return False
            if len(self._durative_conditions) != len(oth._durative_conditions):
                return False
            for i, dcl in self._durative_conditions.items():
                if (oth_dcl := oth._durative_conditions.get(i, None)) is None:
                    return False
                if set(dcl) != set(oth_dcl):
                    return False
            if len(self._effects) != len(oth._effects):
                return False
            for t, el in self._effects.items():
                if (oth_el := oth._effects.get(t, None)) is None:
                    return False
                if set(el) != set(oth_el):
                    return False
            return True
        else:
            return False

    def __hash__(self) -> int:
        res = hash(self._name) + hash(self._duration)
        for ap in self._parameters.items():
            res += hash(ap)
        for t, cl in self._conditions.items():
            res += hash(t)
            for c in cl:
                res += hash(c)
        for i, dcl in self._durative_conditions.items():
            res += hash(i)
            for dc in dcl:
                res += hash(dc)
        for t, el in self._effects.items():
            res += hash(t)
            for e in el:
                res += hash(e)
        return res

    def clone(self):
        new_params = {}
        for param_name, param in self._parameters.items():
            new_params[param_name] = param.type()
        new_durative_action = DurativeAction(self._name, new_params, self._env)
        new_durative_action._duration = self._duration.clone()
        new_conditions = {}
        for t, cl in self._conditions.items():
            new_conditions[t.clone()] = cl[:]
        new_durative_action._conditions = new_conditions
        new_durative_conditions = {}
        for i, dcl in self._durative_conditions.items():
            new_durative_conditions[i.clone()] = dcl[:]
        new_durative_action._durative_conditions = new_durative_conditions
        new_effects = {}
        for t, el in self._effects.items():
            new_effects[t.clone()] = [e.clone() for e in el]
        new_durative_action._effects = new_effects
        assert self == new_durative_action
        assert hash(self) == hash(new_durative_action)
        return new_durative_action

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
        retval: Dict[upf.model.timing.Timing, List[upf.model.effect.Effect]] = {}
        for timing, effect_list in self._effects.items():
            cond_effect_list = [e for e in effect_list if e.is_conditional()]
            if len(cond_effect_list) > 0:
                retval[timing] = cond_effect_list
        return retval

    def unconditional_effects(self):
        '''Return the action unconditional effects.'''
        retval: Dict[upf.model.timing.Timing, List[upf.model.effect.Effect]] = {}
        for timing, effect_list in self._effects.items():
            uncond_effect_list = [e for e in effect_list if not e.is_conditional()]
            if len(uncond_effect_list) > 0:
                retval[timing] = uncond_effect_list
        return retval

    def is_conditional(self) -> bool:
        '''Returns True if the action has conditional effects.'''
        return any(e.is_conditional() for l in self._effects.values() for e in l)

    def set_duration_constraint(self, duration: 'upf.model.timing.IntervalDuration'):
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

    def set_fixed_duration(self, value: Union['upf.model.fnode.FNode', int, Fraction]):
        value_exp, = self._env.expression_manager.auto_promote(value)
        self.set_duration_constraint(upf.model.timing.FixedDuration(value_exp))

    def set_closed_interval_duration(self, lower: Union['upf.model.fnode.FNode', int, Fraction],
                                     upper: Union['upf.model.fnode.FNode', int, Fraction]):
        lower_exp, upper_exp = self._env.expression_manager.auto_promote(lower, upper)
        self.set_duration_constraint(upf.model.timing.ClosedIntervalDuration(lower_exp, upper_exp))

    def set_open_interval_duration(self, lower: Union['upf.model.fnode.FNode', int, Fraction],
                                   upper: Union['upf.model.fnode.FNode', int, Fraction]):
        lower_exp, upper_exp = self._env.expression_manager.auto_promote(lower, upper)
        self.set_duration_constraint(upf.model.timing.OpenIntervalDuration(lower_exp, upper_exp))

    def set_left_open_interval_duration(self, lower: Union['upf.model.fnode.FNode', int, Fraction],
                                        upper: Union['upf.model.fnode.FNode', int, Fraction]):
        lower_exp, upper_exp = self._env.expression_manager.auto_promote(lower, upper)
        self.set_duration_constraint(upf.model.timing.LeftOpenIntervalDuration(lower_exp, upper_exp))

    def set_right_open_interval_duration(self, lower: Union['upf.model.fnode.FNode', int, Fraction],
                                         upper: Union['upf.model.fnode.FNode', int, Fraction]):
        lower_exp, upper_exp = self._env.expression_manager.auto_promote(lower, upper)
        self.set_duration_constraint(upf.model.timing.RightOpenIntervalDuration(lower_exp, upper_exp))

    def add_condition(self, timing: 'upf.model.timing.Timing',
                      condition: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent', ActionParameter, bool]):
        '''Adds the given condition.'''
        condition_exp, = self._env.expression_manager.auto_promote(condition)
        assert self._env.type_checker.get_type(condition_exp).is_bool_type()
        if timing in self._conditions:
            if condition_exp not in self._conditions[timing]:
                self._conditions[timing].append(condition_exp)
        else:
            self._conditions[timing] = [condition_exp]

    def _set_conditions(self, timing: 'upf.model.timing.Timing', conditions: List['upf.model.fnode.FNode']):
        self._conditions[timing] = conditions

    def add_durative_condition(self, interval: 'upf.model.timing.Interval',
                               condition: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent', ActionParameter, bool]):
        '''Adds the given durative condition.'''
        condition_exp, = self._env.expression_manager.auto_promote(condition)
        assert self._env.type_checker.get_type(condition_exp).is_bool_type()
        if interval in self._durative_conditions:
            if condition_exp not in self._durative_conditions[interval]:
                self._durative_conditions[interval].append(condition_exp)
        else:
            self._durative_conditions[interval] = [condition_exp]

    def add_effect(self, timing: 'upf.model.timing.Timing', fluent: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent'],
                   value: 'upf.model.expression.Expression', condition: 'upf.model.expression.BoolExpression' = True):
        '''Adds the given action effect.'''
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('InstantaneousAction effect has not compatible types!')
        self._add_effect_instance(timing, upf.model.effect.Effect(fluent_exp, value_exp, condition_exp))

    def add_increase_effect(self, timing: 'upf.model.timing.Timing', fluent: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent'],
                            value: 'upf.model.expression.Expression', condition: 'upf.model.expression.BoolExpression' = True):
        '''Adds the given action increase effect.'''
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('InstantaneousAction effect has not compatible types!')
        self._add_effect_instance(timing,
                                  upf.model.effect.Effect(fluent_exp, value_exp,
                                         condition_exp, kind = upf.model.effect.INCREASE))

    def add_decrease_effect(self, timing: 'upf.model.timing.Timing', fluent: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent'],
                            value: 'upf.model.expression.Expression', condition: 'upf.model.expression.BoolExpression' = True):
        '''Adds the given action decrease effect.'''
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('InstantaneousAction effect has not compatible types!')
        self._add_effect_instance(timing,
                                  upf.model.effect.Effect(fluent_exp, value_exp,
                                         condition_exp, kind = upf.model.effect.DECREASE))

    def _add_effect_instance(self, timing: 'upf.model.timing.Timing', effect: 'upf.model.effect.Effect'):
        if timing in self._effects:
            if effect not in self._effects[timing]:
                self._effects[timing].append(effect)
        else:
            self._effects[timing] = [effect]
