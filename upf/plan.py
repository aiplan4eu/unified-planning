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
"""This module defines the different plan classes."""


class Plan:
    """Represents a generic plan."""
    pass


class ActionInstance:
    """Represents an action instance with the actual parameters."""
    def __init__(self, action, params=tuple()):
        assert len(action.parameters()) == len(params)
        self._action = action
        self._params = params

    def __repr__(self):
        s = ''
        if len(self._params) > 0:
            s = '('
            first = True
            for p in self._params:
                if not first:
                    s += ', '
                s += str(p)
                first = False
            s += ')'
        return self._action.name() + s

    def action(self):
        """Returns the action."""
        return self._action

    def parameters(self):
        """Returns the actual parameters."""
        return self._params


class SequentialPlan(Plan):
    """Represents a sequential plan."""
    def __init__(self, actions):
        self._actions = actions

    def __repr__(self):
        return str(self._actions)

    def actions(self):
        """Returns the sequence of action instances."""
        return self._actions
