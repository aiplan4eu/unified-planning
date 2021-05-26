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

from collections import OrderedDict
from upf.environment import get_env


class Action:
    """Represents an instantaneous action."""
    def __init__(self, _name, _parameters=None, _env=None, **kwargs):
        self._env = get_env(_env)
        self._name = _name
        self._preconditions = []
        self._effects = []
        if _parameters is not None:
            assert len(kwargs) == 0
            parameters = _parameters
        else:
            parameters = kwargs
        self._parameters = OrderedDict()
        for n, t in parameters.items():
            self._parameters[n] = ActionParameter(n, t)

    def name(self):
        """Returns the action name."""
        return self._name

    def preconditions(self):
        """Returns the list of the action preconditions."""
        return self._preconditions

    def effects(self):
        """Returns the list of the action effects."""
        return self._effects

    def parameters(self):
        """Returns the list of the action parameters."""
        return self._parameters.values()

    def parameter(self, name):
        """Returns the parameter of the action with the given name."""
        return self._parameters[name]

    def add_precondition(self, precondition):
        """Adds the given action precondition."""
        precondition = self._env.expression_manager.auto_promote(precondition)
        assert self._env.type_checker.get_type(precondition).is_bool_type()
        self._preconditions.append(precondition)

    def add_effect(self, fluent, value):
        """Adds the given action effect."""
        fluent, value = self._env.expression_manager.auto_promote(fluent, value)
        assert self._env.type_checker.get_type(fluent) == self._env.type_checker.get_type(value)
        self._effects.append((fluent, value))


class ActionParameter:
    """Represents an action parameter."""
    def __init__(self, name, typename):
        self._name = name
        self._typename = typename

    def name(self):
        """Returns the parameter name."""
        return self._name

    def type(self):
        """Returns the parameter type."""
        return self._typename
