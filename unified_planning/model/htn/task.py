# Copyright 2022 AIPlan4EU project
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
This module defines the Task class.
A Task has a name and a signature that defines the types of its parameters.
"""

import unified_planning as up
from unified_planning.environment import get_env, Environment
from typing import List, OrderedDict, Optional, Union

from unified_planning.exceptions import UPValueError
from unified_planning.model import Timing
from unified_planning.model.action import Action
from unified_planning.model.timing import Timepoint, TimepointKind


class Task:
    """Represents a task."""
    def __init__(self, name: str,
                 _parameters: Optional[Union[OrderedDict[str, 'up.model.types.Type'], List['up.model.parameter.Parameter']]] = None,
                 _env: Environment = None,
                 **kwargs: 'up.model.types.Type'):
        self._env = get_env(_env)
        self._name = name
        self._parameters: List['up.model.parameter.Parameter'] = []
        if _parameters is not None:
            assert len(kwargs) == 0
            if isinstance(_parameters, OrderedDict):
                for param_name, param_type in _parameters.items():
                    self._parameters.append(up.model.parameter.Parameter(param_name, param_type))
            elif isinstance(_parameters, List):
                self._parameters = _parameters[:]
            else:
                raise NotImplementedError
        else:
            for param_name, param_type in kwargs.items():
                self._parameters.append(up.model.parameter.Parameter(param_name, param_type))

    def __repr__(self) -> str:
        sign = ''
        if len(self.parameters) > 0:
            sign_items = [f'{p.name}={str(p.type)}' for p in self.parameters]
            sign = f'[{", ".join(sign_items)}]'
        return f'{self.name}{sign}'

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, Task):
            return self._name == oth._name and self._parameters == oth._parameters and self._env == oth._env
        else:
            return False

    def __hash__(self) -> int:
        res = hash(self._name)
        for p in self._parameters:
            res += hash(p)
        return res

    @property
    def name(self) -> str:
        '''Returns the task's name.'''
        return self._name

    @property
    def parameters(self) -> List['up.model.parameter.Parameter']:
        '''Returns the task's parameters.
        The signature is the List of Parameters.
        '''
        return self._parameters

    def __call__(self, *args: 'up.model.expression.Expression', ident: Optional[str] = None) -> 'Subtask':
        '''Returns a subtask with the given parameters.'''
        return Subtask(self, *self._env.expression_manager.auto_promote(args))


# global counter to enable the creation of unique identifiers.
# TODO: there might be a cleaner way to do this?
_task_id_counter = 0


class Subtask:
    def __init__(self, _task: Union[Action, Task], *args: 'up.model.FNode', ident: Optional[str] = None, _env: Environment = None):
        self._env = get_env(_env)
        self._task = _task
        self._ident = ident
        if self._ident is None:
            # we have to create an unambiguous identifier as there might otherwise identical tasks
            global _task_id_counter
            _task_id_counter += 1
            self._ident = f"_t{_task_id_counter}"
        self._args = self._env.expression_manager.auto_promote(*args)
        assert len(self._args) == len(self._task.parameters)

    def __repr__(self):
        params = ", ".join([str(a) for a in self._args])
        return f"{self.identifier}: {self._task.name}({params})"

    @property
    def identifier(self):
        return self._ident

    @property
    def start(self):
        return Timepoint(TimepointKind.START, container=self)

    @property
    def end(self):
        return Timepoint(TimepointKind.END, container=self)