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
from collections import OrderedDict
from fractions import Fraction
from typing import List, Union, Dict

import unified_planning as up
from unified_planning.model.htn.method import Method
from unified_planning.model.htn.task import Task
from unified_planning.model.htn.task_network import TaskNetwork


class HierarchicalProblem(up.model.problem.Problem):
    def __init__(self, name: str = None, env: 'up.environment.Environment' = None, *,
                 initial_defaults: Dict['up.model.types.Type', Union[
                     'up.model.fnode.FNode', 'up.model.object.Object', bool, int, float, Fraction]] = {}):
        super().__init__(name=name, env=env, initial_defaults=initial_defaults)
        self._abstract_tasks: OrderedDict[str, Task] = OrderedDict()
        self._methods: OrderedDict[str, Method] = OrderedDict()
        self._initial_task_network = TaskNetwork()

    def __repr__(self):
        s = [super().__repr__()]
        s.append('abstract tasks = [\n')
        for t in self._abstract_tasks.values():
            s.append(f"  {t}\n")
        s.append(']\n\n')
        s.append('methods = [')
        for m in self._methods.values():
            s.append(('\n' + str(m)).replace('\n', '\n  '))
        s.append('\n]\n\n')
        s.append(str(self._initial_task_network))
        return ''.join(s)

    def __eq__(self, oth: object) -> bool:
        if not super().__eq__(oth):
            return False
        if not isinstance(oth, HierarchicalProblem):
            return False
        return (self._initial_task_network == oth._initial_task_network and
                self._methods == oth._methods and
                self._abstract_tasks == oth._abstract_tasks)

    def __hash__(self):
        res = super().__hash__()
        res += sum(map(hash, self._abstract_tasks.values()))
        res += sum(map(hash, self._methods.values()))
        res += hash(self._initial_task_network)
        return res

    @property
    def kind(self) -> 'up.model.problem_kind.ProblemKind':
        '''Returns the problem kind of this planning problem.

        IMPORTANT NOTE: this property does a lot of computation, so it should be called as
        minimum time as possible.'''
        self._kind = super().kind
        self._kind.set_problem_class('HIERARCHICAL')
        return self._kind

    @property
    def tasks(self) -> List[Task]:
        return list(self._abstract_tasks.values())

    def get_task(self, task_name: str) -> Task:
        return self._abstract_tasks[task_name]

    def has_task(self, task_name: str):
        return task_name in self._abstract_tasks

    def add_task(self, task: Union[Task, str], **kwargs: 'up.model.types.Type') -> Task:
        if isinstance(task, str):
            task = Task(task, _parameters=OrderedDict(**kwargs))
        else:
            assert len(kwargs) == 0
        assert task.name not in self._abstract_tasks, f"A task with name '{task.name}' already exists."
        self._abstract_tasks[task.name] = task
        return task

    @property
    def methods(self) -> List[Method]:
        return list(self._methods.values())

    def method(self, method_name) -> Method:
        return self._methods[method_name]

    def add_method(self, method: Method):
        assert method.achieved_task is not None, f"No achieved task was specified for this method."
        assert method.name not in self._methods, f"A method with name '{method.name}' already exists."
        assert method.achieved_task.task.name in self._abstract_tasks, f"Method is associated to an unregistered task '{method.achieved_task.task.name}'"
        self._methods[method.name] = method

    @property
    def task_network(self):
        return self._initial_task_network
