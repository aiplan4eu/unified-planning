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

import upf.typing
from upf.environment import get_env, Environment
from upf.fnode import FNode
from upf.exceptions import UPFProblemDefinitionError, UPFTypeError
from upf.problem_kind import ProblemKind
from typing import List, Dict, Set, Union, Optional


class Problem:
    """Represents a planning problem."""
    def __init__(self, name: str = None, env: Environment = None):
        self._env = get_env(env)
        self._kind = ProblemKind()
        self._name = name
        self._fluents: Dict[str, upf.Fluent] = {}
        self._actions: Dict[str, upf.Action] = {}
        self._user_types: Dict[str, upf.typing.Type] = {}
        self._objects: Dict[upf.typing.Type, List[upf.Object]] = {}
        self._initial_value: Dict[FNode, FNode] = {}
        self._goals: Set[FNode] = set()

    def __repr__(self) -> str:
        s = []
        if not self.name() is None:
            s.append(f'problem name = {str(self.name())}\n\n')
        s.append(f'types = {str(list(self.user_types().values()))}\n\n')
        s.append('fluents = [\n')
        for f in self.fluents().values():
            s.append(f'  {str(f)}\n')
        s.append(']\n\n')
        s.append('actions = [\n')
        for a in self.actions().values():
            s.append(f'  {str(a)}\n')
        s.append(']\n\n')
        s.append('objects = [\n')
        for t in self.user_types().values():
            s.append(f'  {str(t)}: {str(self.objects(t))}\n')
        s.append(']\n\n')
        s.append('initial values = [\n')
        for k, v in self.initial_values().items():
            s.append(f'  {str(k)} := {str(v)}\n')
        s.append(']\n\n')
        s.append('goals = [\n')
        for g in self.goals():
            s.append(f'  {str(g)}\n')
        s.append(']\n\n')
        return ''.join(s)

    @property
    def env(self) -> Environment:
        """Returns the problem environment."""
        return self._env

    def name(self) -> Optional[str]:
        """Returns the problem name."""
        return self._name

    def fluents(self) -> Dict[str, upf.Fluent]:
        """Returns the fluents."""
        return self._fluents

    def fluent(self, name: str) -> upf.Fluent:
        """Returns the fluent with the given name."""
        assert name in self._fluents
        return self._fluents[name]

    def add_fluent(self, fluent: upf.Fluent):
        """Adds the given fluent."""
        if fluent.name() in self._fluents:
            raise UPFProblemDefinitionError('Fluent ' + fluent.name() + ' already defined!')
        if fluent.type().is_user_type():
            self._user_types[fluent.type().name()] = fluent.type() # type: ignore
        elif fluent.type().is_int_type():
            self._kind.set_numbers('DISCRETE_NUMBERS') # type: ignore
        elif fluent.type().is_real_type():
            self._kind.set_numbers('CONTINUOUS_NUMBERS') # type: ignore
        for t in fluent.signature():
            if t.is_user_type():
                self._user_types[t.name()] = t # type: ignore
            elif t.is_int_type():
                self._kind.set_numbers('DISCRETE_NUMBERS') # type: ignore
            elif t.is_real_type():
                self._kind.set_numbers('CONTINUOUS_NUMBERS') # type: ignore
        self._fluents[fluent.name()] = fluent

    def actions(self) -> Dict[str, upf.Action]:
        """Returns the actions."""
        return self._actions

    def action(self, name: str) -> upf.Action:
        """Returns the action with the given name."""
        assert name in self._actions
        return self._actions[name]

    def add_action(self, action: upf.Action):
        """Adds the given action."""
        if action.name() in self._actions:
            raise UPFProblemDefinitionError('Action ' + action.name() + ' already defined!')
        for p in action.parameters():
            if p.type().is_user_type():
                self._user_types[p.type().name()] = p.type() # type: ignore
            elif p.type().is_int_type():
                self._kind.set_numbers('DISCRETE_NUMBERS') # type: ignore
            elif p.type().is_real_type():
                self._kind.set_numbers('CONTINUOUS_NUMBERS') # type: ignore
        self._actions[action.name()] = action

    def user_types(self) -> Dict[str, upf.typing.Type]:
        """Returns the user types."""
        return self._user_types

    def add_object(self, obj: upf.Object):
        """Adds the given object."""
        if obj.type() not in self._objects:
            self._objects[obj.type()] = []
        self._objects[obj.type()].append(obj)

    def objects(self, typename: upf.typing.Type) -> List[upf.Object]:
        """Returns the user types."""
        return self._objects[typename]

    def set_initial_value(self, fluent: Union[FNode, upf.Fluent],
                          value: Union[FNode, upf.Fluent, upf.Object, bool]):
        """Sets the initial value for the given fluent."""
        fluent_exp, value_exp = self._env.expression_manager.auto_promote(fluent, value)
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('Initial value assignment has not compatible types!')
        if fluent_exp in self._initial_value:
            raise UPFProblemDefinitionError('Initial value already set!')
        self._initial_value[fluent_exp] = value_exp

    def initial_value(self, fluent: Union[FNode, upf.Fluent]) -> FNode:
        """Gets the initial value of the given fluent."""
        fluent_exp, = self._env.expression_manager.auto_promote(fluent)
        if fluent_exp not in self._initial_value:
            raise UPFProblemDefinitionError('Initial value not set!')
        return self._initial_value[fluent_exp]

    def initial_values(self) -> Dict[FNode, FNode]:
        """Gets the initial value of the fluents."""
        return self._initial_value

    def add_goal(self, goal: Union[FNode, upf.Fluent, bool]):
        """Adds a goal."""
        goal_exp, = self._env.expression_manager.auto_promote(goal)
        assert self._env.type_checker.get_type(goal_exp).is_bool_type()
        self._goals.add(goal_exp)

    def goals(self) -> Set[FNode]:
        """Returns the goals."""
        return self._goals

    def kind(self) -> ProblemKind:
        """Returns the problem kind of this planning problem."""
        return self._kind
