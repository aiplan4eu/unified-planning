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
from unified_planning.environment import get_environment, Environment
from typing import List, OrderedDict, Optional, Union
from unified_planning.model.fnode import FNode
from unified_planning.model.action import Action
from unified_planning.model.timing import Timepoint, TimepointKind
from unified_planning.model.types import Type
from unified_planning.model.expression import Expression
from unified_planning.model.parameter import Parameter


class Task:
    """Represents an abstract task."""

    def __init__(
        self,
        name: str,
        _parameters: Optional[Union[OrderedDict[str, Type], List[Parameter]]] = None,
        _env: Optional[Environment] = None,
        **kwargs: Type,
    ):
        self._env = get_environment(_env)
        self._name = name
        self._parameters: List[Parameter] = []
        if _parameters is not None:
            assert len(kwargs) == 0
            if isinstance(_parameters, OrderedDict):
                for param_name, param_type in _parameters.items():
                    self._parameters.append(
                        up.model.parameter.Parameter(param_name, param_type, self._env)
                    )
            elif isinstance(_parameters, List):
                self._parameters = _parameters[:]
            else:
                raise NotImplementedError
        else:
            for param_name, param_type in kwargs.items():
                self._parameters.append(
                    up.model.parameter.Parameter(param_name, param_type, self._env)
                )

    def __repr__(self) -> str:
        sign = ""
        if len(self.parameters) > 0:
            sign_items = [f"{p.name}={str(p.type)}" for p in self.parameters]
            sign = f'[{", ".join(sign_items)}]'
        return f"{self.name}{sign}"

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, Task):
            return (
                self._name == oth._name
                and self._parameters == oth._parameters
                and self._env == oth._env
            )
        else:
            return False

    def __hash__(self) -> int:
        return hash(self._name) + sum(map(hash, self._parameters))

    @property
    def name(self) -> str:
        """Returns the task's name."""
        return self._name

    @property
    def parameters(self) -> List[Parameter]:
        """Returns the task's parameters as a list."""
        return self._parameters

    def __call__(self, *args: Expression, ident: Optional[str] = None) -> "Subtask":
        """Returns a subtask with the given parameters."""
        return Subtask(self, *self._env.expression_manager.auto_promote(args))


# global counter to enable the creation of unique identifiers.
_task_id_counter = 0


class Subtask:
    def __init__(
        self,
        _task: Union[Action, Task],
        *args: Expression,
        ident: Optional[str] = None,
        _env: Optional[Environment] = None,
    ):
        self._env = get_environment(_env)
        self._task = _task
        self._ident: str
        if ident is not None:
            self._ident = ident
        else:
            # we have to create an unambiguous identifier as there might otherwise identical tasks
            global _task_id_counter
            _task_id_counter += 1
            self._ident = f"_t{_task_id_counter}"
        self._args = self._env.expression_manager.auto_promote(*args)

        if len(self._args) != len(self._task.parameters):
            raise ValueError(
                f"Wrong number of arguments. Expected: {self._task.parameters}. Provided: {self._args}"
            )

    def __repr__(self):
        params = ", ".join([str(a) for a in self._args])
        return f"{self.identifier}: {self._task.name}({params})"

    def __eq__(self, other):
        if not isinstance(other, Subtask):
            return False
        return (
            self._env == other._env
            and self._ident == other._ident
            and self._task == other._task
            and self._args == other._args
        )

    def __hash__(self):
        return hash(self._ident) + hash(self._task) + sum(map(hash, self._args))

    @property
    def task(self) -> Union[Task, Action]:
        return self._task

    @property
    def parameters(self) -> List["FNode"]:
        return self._args

    @property
    def identifier(self) -> str:
        """Unique identifier of the subtask in its task network."""
        return self._ident

    @property
    def start(self) -> Timepoint:
        """Timepoint representing the task's end time."""
        return Timepoint(TimepointKind.START, container=self.identifier)

    @property
    def end(self) -> Timepoint:
        """Timepoint representing the task's end time."""
        return Timepoint(TimepointKind.END, container=self.identifier)
