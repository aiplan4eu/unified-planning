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
This module defines the Method class.
A Method has a name, a list of Parameters, a list of conditions
and a list of subtasks.
"""
from collections import OrderedDict
from typing import List, Union, Optional

import unified_planning as up
from unified_planning.environment import get_env, Environment
from unified_planning.exceptions import UPUnboundedVariablesError, UPValueError
from unified_planning.model import Timing
from unified_planning.model.action import Action
from unified_planning.model.htn.task import Task, SubTask
from unified_planning.model.timing import Timepoint


class Method:
    """This is the method interface."""
    def __init__(self, _name: str, _task: Task, _parameters: 'OrderedDict[str, up.model.types.Type]' = None,
                 _env: Environment = None, **kwargs: 'up.model.types.Type'):
        self._env = get_env(_env)
        self._task = _task
        self._name = _name
        # Parameters of the method (must include the ones of the task)
        self._parameters: 'OrderedDict[str, up.model.parameter.Parameter]' = OrderedDict()
        self._preconditions: List[up.model.fnode.FNode] = []
        self._subtasks: List[SubTask] = []
        if _parameters is not None:
            assert len(kwargs) == 0
            for n, t in _parameters.items():
                self._parameters[n] = up.model.parameter.Parameter(n, t)
        else:
            for n, t in kwargs.items():
                self._parameters[n] = up.model.parameter.Parameter(n, t)
        for task_param in self._task.parameters:
            assert task_param.name in self._parameters, f"Missing task parameter '{task_param.name}' in method {self._name}"

    def __repr__(self) -> str:
        s = []
        s.append(f'method {self.name}')
        first = True
        for p in self.parameters:
            if first:
                s.append('(')
                first = False
            else:
                s.append(', ')
            s.append(str(p))
        if not first:
            s.append(')')
        s.append(' {\n')
        s.append(f'    task = {self._task}\n')
        s.append('    preconditions = [\n')
        for c in self.preconditions:
            s.append(f'      {str(c)}\n')
        s.append('    ]\n')
        s.append('    subtasks = [\n')
        for st in self.subtasks:
            s.append(f'      {str(st)}\n')
        s.append('    ]\n')
        s.append('  }')
        return ''.join(s)

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, Method):
            cond = self._env == oth._env and self._name == oth._name and self._parameters == oth._parameters
            return cond and self._task == oth._task and set(self._preconditions) == set(oth._preconditions) and set(self._subtasks) == set(oth._subtasks)
        else:
            return False

    def __hash__(self) -> int:
        res = hash(self._name)
        res += hash(self._task)
        for ap in self._parameters.items():
            res += hash(ap)
        for p in self._preconditions:
            res += hash(p)
        for s in self._subtasks:
            res += hash(s)
        return res

    @property
    def name(self) -> str:
        """Returns the action name."""
        return self._name

    @property
    def parameters(self) -> List['up.model.parameter.Parameter']:
        """Returns the list of the action parameters."""
        return list(self._parameters.values())

    def parameter(self, name: str) -> 'up.model.parameter.Parameter':
        """Returns the parameter of the action with the given name."""
        for param in self.parameters:
            if param.name == name:
                return param
        raise UPValueError(f'Unknown parameter name: {name}')

    @property
    def preconditions(self) -> List['up.model.fnode.FNode']:
        """Returns the list of the method's preconditions."""
        return self._preconditions

    def add_precondition(self, precondition: Union['up.model.fnode.FNode', 'up.model.fluent.Fluent', 'up.model.parameter.Parameter', bool]):
        """Adds the given action precondition."""
        precondition_exp, = self._env.expression_manager.auto_promote(precondition)
        assert self._env.type_checker.get_type(precondition_exp).is_bool_type()
        if precondition_exp == self._env.expression_manager.TRUE():
            return
        free_vars = self._env.free_vars_oracle.get_free_variables(precondition_exp)
        if len(free_vars) != 0:
            raise UPUnboundedVariablesError(f"The precondition {str(precondition_exp)} has unbounded variables:\n{str(free_vars)}")
        if precondition_exp not in self._preconditions:
            self._preconditions.append(precondition_exp)

    @property
    def subtasks(self) -> List['SubTask']:
        """Returns the list of the method's subtasks."""
        return self._subtasks

    def add_subtask(self, task: Union[Action, Task], *args, ident: Optional[str] = None) -> SubTask:
        subtask = SubTask(task, *args, ident=ident)
        assert all([subtask.identifier != prev.identifier for prev in self.subtasks])
        self._subtasks.append(subtask)
        return subtask

    def set_ordered(self, *subtasks: SubTask):
        if len(subtasks) < 2:
            return
        prev = subtasks[0]
        for i in range(1, len(subtasks)):
            next = subtasks[i]
            self.set_strictly_before(prev, next)
            prev = next

    def set_strictly_before(self, lhs: Union[SubTask, Timepoint, Timing], rhs: Union[SubTask, Timepoint, Timing]):
        if isinstance(lhs, SubTask):
            lhs = lhs.end
        if isinstance(lhs, Timepoint):
            lhs = Timing(timepoint=lhs, delay=0)
        assert isinstance(lhs, Timing)
        if isinstance(rhs, SubTask):
            rhs = rhs.start
        if isinstance(rhs, Timepoint):
            rhs = Timing(timepoint=rhs, delay=0)
        assert isinstance(rhs, Timing)
        self._preconditions.append(self._env.expression_manager.LT(lhs, rhs))  # TODO



