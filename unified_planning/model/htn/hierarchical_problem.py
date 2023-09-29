# Copyright 2021-2023 AIPlan4EU project
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
from typing import Optional, List, Union, Dict, Set
from warnings import warn

import unified_planning as up
from unified_planning.model.expression import ConstantExpression
from unified_planning.model.htn.method import Method
from unified_planning.model.htn.task import Task
from unified_planning.model.htn.task_network import TaskNetwork, AbstractTaskNetwork
from unified_planning.exceptions import UPProblemDefinitionError


class HierarchicalProblem(up.model.problem.Problem):
    def __init__(
        self,
        name: Optional[str] = None,
        environment: Optional["up.environment.Environment"] = None,
        *,
        initial_defaults: Dict[
            "up.model.types.Type",
            ConstantExpression,
        ] = {},
    ):
        super().__init__(
            name=name, environment=environment, initial_defaults=initial_defaults
        )
        self._abstract_tasks: OrderedDict[str, Task] = OrderedDict()
        self._methods: OrderedDict[str, Method] = OrderedDict()
        self._initial_task_network = TaskNetwork()

    def __repr__(self):
        s = [super().__repr__()]
        s.append("abstract tasks = [\n")
        for t in self._abstract_tasks.values():
            s.append(f"  {t}\n")
        s.append("]\n\n")
        s.append("methods = [")
        for m in self._methods.values():
            s.append(("\n" + str(m)).replace("\n", "\n  "))
        s.append("\n]\n\n")
        s.append(str(self._initial_task_network))
        return "".join(s)

    def __eq__(self, oth: object) -> bool:
        if not super().__eq__(oth):
            return False
        if not isinstance(oth, HierarchicalProblem):
            return False
        return (
            self._initial_task_network == oth._initial_task_network
            and self._methods == oth._methods
            and self._abstract_tasks == oth._abstract_tasks
        )

    def __hash__(self):
        res = super().__hash__()
        res += sum(map(hash, self._abstract_tasks.values()))
        res += sum(map(hash, self._methods.values()))
        res += hash(self._initial_task_network)
        return res

    def clone(self):
        new_p = HierarchicalProblem(self._name, self._env)
        new_p._fluents = self._fluents[:]
        new_p._actions = [a.clone() for a in self._actions]
        new_p._user_types = self._user_types[:]
        new_p._user_types_hierarchy = self._user_types_hierarchy.copy()
        new_p._objects = self._objects[:]
        new_p._initial_value = self._initial_value.copy()
        new_p._timed_effects = {
            t: [e.clone() for e in el] for t, el in self._timed_effects.items()
        }
        new_p._timed_goals = {i: [g for g in gl] for i, gl in self._timed_goals.items()}
        new_p._goals = self._goals[:]
        new_p._metrics = []
        for m in self._metrics:
            if m.is_minimize_action_costs():
                assert isinstance(m, up.model.metrics.MinimizeActionCosts)
                costs: Dict["up.model.Action", "up.model.Expression"] = {
                    new_p.action(a.name): c for a, c in m.costs.items()
                }
                new_p._metrics.append(up.model.metrics.MinimizeActionCosts(costs))
            else:
                new_p._metrics.append(m)
        new_p._initial_defaults = self._initial_defaults.copy()
        new_p._fluents_defaults = self._fluents_defaults.copy()
        new_p._initial_task_network = self._initial_task_network.clone()
        new_p._methods = self._methods.copy()
        new_p._abstract_tasks = self._abstract_tasks.copy()
        return new_p

    def get_unused_fluents(self):
        """
        Returns the set of `fluents` that are never used in the problem.
        """
        # from our parents unused fluents, remove all those that appear in methods preconditions and constraints
        unused_fluents: Set["up.model.fluent.Fluent"] = super().get_unused_fluents()
        fve = self._env.free_vars_extractor
        # function that takes an FNode and removes all the fluents contained in the given FNode
        # from the unused_fluents  set.
        remove_used_fluents = lambda *exps: unused_fluents.difference_update(
            (f.fluent() for e in exps for f in fve.get(e))
        )
        for m in self.methods:
            remove_used_fluents(*m.preconditions)
            remove_used_fluents(*m.constraints)
        remove_used_fluents(*self.task_network.constraints)

        return unused_fluents

    @property
    def kind(self) -> "up.model.problem_kind.ProblemKind":
        """Returns the problem kind of this planning problem.

        IMPORTANT NOTE: this property does a lot of computation, so it should be called as
        minimum time as possible."""
        factory = self._kind_factory()
        factory.kind.set_problem_class("HIERARCHICAL")
        (TO, PO, TEMPORAL) = (0, 1, 2)

        def lvl(tn: AbstractTaskNetwork):
            """Determines the expressivity level of temporal constraints within a task network"""
            if tn.total_order() is not None:
                return TO
            elif tn.partial_order() is not None:
                return PO
            else:
                return TEMPORAL

        ordering_kind = lvl(self.task_network)
        if len(self.task_network.variables) > 0:
            factory.kind.set_hierarchical("INITIAL_TASK_NETWORK_VARIABLES")
        if len(self.task_network.non_temporal_constraints()) > 0:
            factory.kind.set_hierarchical("TASK_NETWORK_CONSTRAINTS")

        for method in self.methods:
            ordering_kind = max(ordering_kind, lvl(method))
            for method_cond in method.preconditions:
                factory.kind.set_hierarchical("METHOD_PRECONDITIONS")
                factory.update_problem_kind_expression(method_cond)
            if len(method.non_temporal_constraints()) > 0:
                factory.kind.set_hierarchical("TASK_NETWORK_CONSTRAINTS")

        if ordering_kind == TO:
            factory.kind.set_hierarchical("TASK_ORDER_TOTAL")
        elif ordering_kind == PO:
            factory.kind.set_hierarchical("TASK_ORDER_PARTIAL")
        else:
            factory.kind.set_hierarchical("TASK_ORDER_TEMPORAL")
            factory.kind.set_time("CONTINUOUS_TIME")

        return factory.finalize()

    def has_name(self, name: str) -> bool:
        """
        Returns `True` if the given `name` is already in the `HierarchicalProblem`, `False` otherwise.

        :param name: The target name to find in the `HierarchicalProblem`.
        :return: `True` if the given `name` is already in the `HierarchicalProblem`, `False` otherwise."""
        return (
            self.has_action(name)
            or self.has_fluent(name)
            or self.has_object(name)
            or self.has_type(name)
            or self.has_task(name)
            or name in self._methods
        )

    @property
    def tasks(self) -> List[Task]:
        return list(self._abstract_tasks.values())

    def get_task(self, task_name: str) -> Task:
        return self._abstract_tasks[task_name]

    def has_task(self, task_name: str):
        return task_name in self._abstract_tasks

    def add_task(self, task: Union[Task, str], **kwargs: "up.model.types.Type") -> Task:
        if isinstance(task, str):
            task = Task(task, _parameters=OrderedDict(**kwargs))
        else:
            assert len(kwargs) == 0
        if self.has_name(task.name):
            msg = f"Name of task {task.name} already defined! Different elements of a problem can have the same name if the environment flag error_used_name is disabled."
            if self._env.error_used_name or any(
                task.name == t for t in self._abstract_tasks
            ):
                raise UPProblemDefinitionError(msg)
            else:
                warn(msg)
        self._abstract_tasks[task.name] = task
        for param in task.parameters:
            if param.type.is_user_type():
                self._add_user_type(param.type)
        return task

    @property
    def methods(self) -> List[Method]:
        return list(self._methods.values())

    def method(self, method_name) -> Method:
        return self._methods[method_name]

    def add_method(self, method: Method):
        assert (
            method.achieved_task is not None
        ), f"No achieved task was specified for this method."
        if self.has_name(method.name):
            msg = f"Name of method {method.name} already defined! Different elements of a problem can have the same name if the environment flag error_used_name is disabled."
            if self._env.error_used_name or any(
                method.name == m for m in self._methods
            ):
                raise UPProblemDefinitionError(msg)
            else:
                warn(msg)
        assert (
            method.achieved_task.task.name in self._abstract_tasks
        ), f"Method is associated to an unregistered task '{method.achieved_task.task.name}'"
        self._methods[method.name] = method
        for param in method.parameters:
            if param.type.is_user_type():
                self._add_user_type(param.type)

    @property
    def task_network(self):
        return self._initial_task_network
