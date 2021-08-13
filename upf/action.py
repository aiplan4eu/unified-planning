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
This module defines the Action class and the ActionParameter class.
An Action has a name, a list of ActionParameter, a list of preconditions
and a list of effects.
"""


import upf
import upf.types
from upf.environment import get_env, Environment
from upf.fnode import FNode
from upf.exceptions import UPFTypeError, UPFUnboundedVariablesError
from upf.expression import BoolExpression, Expression
from upf.effect import Effect, INCREASE, DECREASE
from typing import List, Union
from collections import OrderedDict


class ActionParameter:
    """Represents an action parameter."""
    def __init__(self, name: str, typename: upf.types.Type):
        self._name = name
        self._typename = typename

    def __repr__(self) -> str:
        return f'{str(self.type())} {self.name()}'

    def name(self) -> str:
        """Returns the parameter name."""
        return self._name

    def type(self) -> upf.types.Type:
        """Returns the parameter type."""
        return self._typename


class Action:
    """Represents an instantaneous action."""
    def __init__(self, _name: str, _parameters: 'OrderedDict[str, upf.types.Type]' = None,
                 _env: Environment = None, **kwargs: upf.types.Type):
        self._env = get_env(_env)
        self._name = _name
        self._preconditions: List[FNode] = []
        self._effects: List[Effect] = []
        self._parameters: 'OrderedDict[str, ActionParameter]' = OrderedDict()
        if _parameters is not None:
            assert len(kwargs) == 0
            for n, t in _parameters.items():
                self._parameters[n] = ActionParameter(n, t)
        else:
            for n, t in kwargs.items():
                self._parameters[n] = ActionParameter(n, t)

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

    def name(self) -> str:
        """Returns the action name."""
        return self._name

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
        return any(e.is_conditional() for e in self._effects)

    def unconditional_effects(self) -> List[Effect]:
        """Returns the list of the action unconditional effects."""
        return [e for e in self._effects if not e.is_conditional()]

    def parameters(self) -> List[ActionParameter]:
        """Returns the list of the action parameters."""
        return list(self._parameters.values())

    def parameter(self, name: str) -> ActionParameter:
        """Returns the parameter of the action with the given name."""
        return self._parameters[name]

    def add_precondition(self, precondition: Union[FNode, 'upf.Fluent', ActionParameter, bool]):
        """Adds the given action precondition."""
        precondition_exp, = self._env.expression_manager.auto_promote(precondition)
        assert self._env.type_checker.get_type(precondition_exp).is_bool_type()
        free_vars = self._env._free_vars_oracle.get_free_variables(precondition_exp)
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
            raise UPFTypeError('Action effect has not compatible types!')
        self._effects.append(Effect(fluent_exp, value_exp, condition_exp))

    def add_increase_effect(self, fluent: Union[FNode, 'upf.Fluent'],
                   value: Expression, condition: BoolExpression = True):
        """Adds the given action increase effect."""
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('Action effect has not compatible types!')
        self._effects.append(Effect(fluent_exp, value_exp, condition_exp, kind = INCREASE))

    def add_decrease_effect(self, fluent: Union[FNode, 'upf.Fluent'],
                   value: Expression, condition: BoolExpression = True):
        """Adds the given action decrease effect."""
        fluent_exp, value_exp, condition_exp = self._env.expression_manager.auto_promote(fluent, value, condition)
        assert fluent_exp.is_fluent_exp()
        if not self._env.type_checker.get_type(condition_exp).is_bool_type():
            raise UPFTypeError('Effect condition is not a Boolean condition!')
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('Action effect has not compatible types!')
        self._effects.append(Effect(fluent_exp, value_exp, condition_exp, kind = DECREASE))

    def _add_effect_instance(self, effect: Effect):
        self._effects.append(effect)

    def _set_preconditions(self, preconditions: List[FNode]):
        self._preconditions = preconditions
