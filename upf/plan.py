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

import upf
from upf.fnode import FNode
from typing import Tuple, List


class Plan:
    """Represents a generic plan."""
    pass


class ActionInstance:
    """Represents an action instance with the actual parameters."""
    def __init__(self, action: 'upf.ActionInterface', params: Tuple[FNode, ...] = tuple()):
        assert len(action.parameters()) == len(params)
        self._action = action
        self._params = params

    def __repr__(self) -> str:
        s = []
        if len(self._params) > 0:
            s.append('(')
            first = True
            for p in self._params:
                if not first:
                    s.append(', ')
                s.append(str(p))
                first = False
            s.append(')')
        return self._action.name() + ''.join(s)

    def action(self) -> 'upf.ActionInterface':
        """Returns the action."""
        return self._action

    def actual_parameters(self) -> Tuple[FNode, ...]:
        """Returns the actual parameters."""
        return self._params


class SequentialPlan(Plan):
    """Represents a sequential plan."""
    def __init__(self, actions: List[ActionInstance]):
        self._actions = actions

    def __repr__(self) -> str:
        return str(self._actions)

    def actions(self) -> List[ActionInstance]:
        """Returns the sequence of action instances."""
        return self._actions


class TimeTriggeredPlan(Plan):
    """Represents a time triggered plan."""
    def __init__(self, actions: List[Tuple[float, ActionInstance, float]]):
        self._actions = actions

    def __repr__(self) -> str:
        return str(self._actions)

    def actions(self) -> List[Tuple[float, ActionInstance, float]]:
        """Returns the sequence of action instances."""
        return self._actions
