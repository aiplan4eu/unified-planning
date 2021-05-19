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
"""This module defines the problem class. """

from upf.expression import EXPR_MANAGER


class Problem:
    """Represents a planning problem."""
    def __init__(self, name=None):
        self._name = name
        self._fluents = {}
        self._actions = {}
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
        """Adds the given fluent"""
        if fluent.name() in self._fluents:
            raise Exception('Fluent ' + fluent.name() + 'already defined!')
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
            raise Exception('Action ' + action.name() + 'already defined!')
        self._actions[action.name()] = action

    def set_initial_value(self, fluent, value):
        """Sets the initial value for the given fluent."""
        fluent, value = EXPR_MANAGER.auto_promote(fluent, value)
        if fluent in self._initial_value:
            raise Exception('Initial value already set!')
        self._initial_value[fluent] = value

    def initial_value(self, fluent):
        """Gets the initial value of the given fluent."""
        fluent = EXPR_MANAGER.auto_promote(fluent)
        if fluent not in self._initial_value:
            raise Exception('Initial value not set!')
        return self._initial_value[fluent]

    def initial_values(self):
        """Gets the initial value of the fluents."""
        return self._initial_value

    def add_goal(self, goal):
        """Adds a goal."""
        goal = EXPR_MANAGER.auto_promote(goal)
        self._goals.add(goal)

    def goals(self):
        """Returns the goals."""
        return self._goals
