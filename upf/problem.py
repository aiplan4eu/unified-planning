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
"""This module defines the problem class."""

from upf.environment import get_env


class Problem:
    """Represents a planning problem."""
    def __init__(self, name=None, env=None):
        self._env = get_env(env)
        self._name = name
        self._fluents = {}
        self._actions = {}
        self._user_types = {}
        self._objects = {}
        self._initial_value = {}
        self._goals = set()

    def name(self):
        """Returns the problem name."""
        return self._name

    def fluents(self):
        """Returns the fluents."""
        return self._fluents

    def fluent(self, name):
        """Returns the fluent with the given name."""
        assert name in self._fluents
        return self._fluents[name]

    def add_fluent(self, fluent):
        """Adds the given fluent."""
        if fluent.name() in self._fluents:
            raise Exception('Fluent ' + fluent.name() + ' already defined!')
        if fluent.type().is_user_type():
            self._user_types[fluent.type().name()] = fluent.type()
        for t in fluent.signature():
            if t.is_user_type():
                self._user_types[t.name()] = t
        self._fluents[fluent.name()] = fluent

    def actions(self):
        """Returns the actions."""
        return self._actions

    def action(self, name):
        """Returns the action with the given name."""
        assert name in self._actions
        return self._actions[name]

    def add_action(self, action):
        """Adds the given action."""
        if action.name() in self._actions:
            raise Exception('Action ' + action.name() + ' already defined!')
        for p in action.parameters():
            if p.type().is_user_type():
                self._user_types[p.type().name()] = p.type()
        self._actions[action.name()] = action

    def user_types(self):
        """Returns the user types."""
        return self._user_types

    def add_object(self, obj):
        """Adds the given object."""
        if obj.type() not in self._objects:
            self._objects[obj.type()] = []
        self._objects[obj.type()].append(obj)

    def objects(self, typename):
        """Returns the user types."""
        return self._objects[typename]

    def set_initial_value(self, fluent, value):
        """Sets the initial value for the given fluent."""
        fluent, value = self._env.expression_manager.auto_promote(fluent, value)
        assert self._env.type_checker.get_type(fluent) == self._env.type_checker.get_type(value)
        if fluent in self._initial_value:
            raise Exception('Initial value already set!')
        self._initial_value[fluent] = value

    def initial_value(self, fluent):
        """Gets the initial value of the given fluent."""
        fluent = self._env.expression_manager.auto_promote(fluent)
        if fluent not in self._initial_value:
            raise Exception('Initial value not set!')
        return self._initial_value[fluent]

    def initial_values(self):
        """Gets the initial value of the fluents."""
        return self._initial_value

    def add_goal(self, goal):
        """Adds a goal."""
        goal = self._env.expression_manager.auto_promote(goal)
        assert self._env.type_checker.get_type(goal).is_bool_type()
        self._goals.add(goal)

    def goals(self):
        """Returns the goals."""
        return self._goals
