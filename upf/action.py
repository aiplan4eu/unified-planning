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
import upf.typing
from upf.environment import get_env, Environment
from upf.fnode import FNode
from collections import OrderedDict
from typing import List, Union, Tuple


class ActionParameter:
    """Represents an action parameter."""
    def __init__(self, name: str, typename: upf.typing.Type):
        self._name = name
        self._typename = typename

    def name(self) -> str:
        """Returns the parameter name."""
        return self._name

    def type(self) -> upf.typing.Type:
        """Returns the parameter type."""
        return self._typename


class Action:
    """Represents an instantaneous action."""
    def __init__(self, _name: str, _parameters: 'OrderedDict[str, upf.typing.Type]' = None,
                 _env: Environment = None, **kwargs: upf.typing.Type):
        self._env = get_env(_env)
        self._name = _name
        self._preconditions: List[FNode] = []
        self._effects: List[Tuple[FNode, FNode]] = []
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

    def preconditions(self) -> List[FNode]:
        """Returns the list of the action preconditions."""
        return self._preconditions

    def effects(self) -> List[Tuple[FNode, FNode]]:
        """Returns the list of the action effects."""
        return self._effects

    def parameters(self) -> List[ActionParameter]:
        """Returns the list of the action parameters."""
        return list(self._parameters.values())

    def parameter(self, name: str) -> ActionParameter:
        """Returns the parameter of the action with the given name."""
        return self._parameters[name]

    def add_precondition(self, precondition: Union[FNode, 'upf.Fluent', ActionParameter, bool]):
        """Adds the given action precondition."""
        [precondition_exp] = self._env.expression_manager.auto_promote(precondition)
        assert self._env.type_checker.get_type(precondition_exp).is_bool_type()
        self._preconditions.append(precondition_exp)

    def add_effect(self, fluent: Union[FNode, 'upf.Fluent'],
                   value: Union[FNode, 'upf.Fluent', 'upf.Object', ActionParameter, bool]):
        """Adds the given action effect."""
        [fluent_exp, value_exp] = self._env.expression_manager.auto_promote(fluent, value)
        assert self._env.type_checker.get_type(fluent_exp) == self._env.type_checker.get_type(value_exp)
        self._effects.append((fluent_exp, value_exp))
