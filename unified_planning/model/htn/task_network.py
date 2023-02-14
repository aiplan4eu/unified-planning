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
from typing import List, Union, Optional, Tuple

import unified_planning.model.walkers
from unified_planning.environment import get_environment, Environment
from unified_planning.exceptions import UPUnboundedVariablesError
from unified_planning.model.htn.ordering import (
    TemporalConstraints,
    ordering,
    PartialOrder,
    TotalOrder,
)
from unified_planning.model.timing import Timing
from unified_planning.model.parameter import Parameter
from unified_planning.model.fnode import FNode
from unified_planning.model.types import Type
from unified_planning.model.expression import Expression
from unified_planning.model.operators import OperatorKind
from unified_planning.model.action import Action
from unified_planning.model.htn.task import Task, Subtask
from unified_planning.model.timing import Timepoint
from unified_planning.model.walkers import OperatorsExtractor


class AbstractTaskNetwork:
    """Core functionalities to represent task networks,
    either in a method o in an initial task network."""

    def __init__(self, _env: Optional[Environment] = None):
        self._env = get_environment(_env)
        self._subtasks: List[Subtask] = []
        self._constraints: List[FNode] = []
        self._operators_extractor = OperatorsExtractor()  # maybe add to Environment?
        self._time_checker = unified_planning.model.walkers.AnyChecker(
            lambda e: e.is_timing_exp()
        )

    @property
    def subtasks(self) -> List["Subtask"]:
        """Returns the list of the subtasks."""
        return self._subtasks

    def add_subtask(
        self,
        task: Union[Subtask, Action, Task],
        *args: Expression,
        ident: Optional[str] = None,
    ) -> Subtask:
        """Adds a subtask, with no particular ordering relative to the existing ones."""
        if isinstance(task, Subtask):
            assert len(args) == 0 and ident is None
            subtask = task
        else:
            subtask = Subtask(task, *args, ident=ident)
        assert all([subtask.identifier != prev.identifier for prev in self.subtasks])
        self._subtasks.append(subtask)
        return subtask

    def get_subtask(self, ident: str) -> Subtask:
        """Returns the subtask with the given identifier."""
        for st in self._subtasks:
            if st.identifier == ident:
                return st
        raise ValueError(f"No subtask with identifier {ident}")

    @property
    def constraints(self) -> List[FNode]:
        """Returns the list of the method's constraints.
        Note that these may contain both ordering and non-ordering constraints."""
        return self._constraints

    def temporal_constraints(self) -> List[FNode]:
        """All constraints that impose an order between tasks or explicitly refer to a timepoint."""
        return [c for c in self.constraints if self._time_checker.any(c)]

    def non_temporal_constraints(self) -> List[FNode]:
        """All constraints that do not involve any temporal aspect"""
        return [c for c in self.constraints if not self._time_checker.any(c)]

    def _ordering(self) -> TemporalConstraints:
        """Analyses the temporal constraints and classifies them into TO, PO or Temporal"""
        return ordering(
            list(t.identifier for t in self.subtasks), self.temporal_constraints()
        )

    def partial_order(self) -> Optional[List[Tuple[str, str]]]:
        """If the temporal constraints define a partial order, returns a list of precedences between the network' subtasks.
        Returns None, if the temporal constraints cannot be fully expressed by a set of precedence constraints.
        This can be the case if, e.g., the constraint contains simple temporal constraints, implying a given delay between
        two subtasks.
        """
        order = self._ordering()
        if isinstance(order, PartialOrder):
            return order.precedences
        else:
            return None

    def total_order(self) -> Optional[List[str]]:
        """If the temporal constraints define a total order, returns the ordered list of task identifiers.
        Returns None, if the temporal constraints cannot be exactly expressed by a total order.
        """
        order = self._ordering()
        if isinstance(order, TotalOrder):
            return order.order
        else:
            return None

    def add_constraint(self, constraint: Expression):
        (constraint,) = self._env.expression_manager.auto_promote(constraint)
        assert isinstance(constraint, FNode)
        assert self._env.type_checker.get_type(constraint).is_bool_type()
        assert OperatorKind.FLUENT_EXP not in self._operators_extractor.get(
            constraint
        ), f"The expression is not static (references a fluent): {constraint}"
        free_vars = self._env.free_vars_oracle.get_free_variables(constraint)
        if len(free_vars) != 0:
            raise UPUnboundedVariablesError(
                f"The constraint {str(constraint)} has unbounded variables:\n{str(free_vars)}"
            )
        if (
            constraint != self._env.expression_manager.TRUE()
            and constraint not in self._constraints
        ):
            self._constraints.append(constraint)

    def set_ordered(self, *subtasks: Subtask):
        """Imposes a sequential order between the given subtasks."""
        if len(subtasks) < 2:
            return
        prev = subtasks[0]
        for next in subtasks[1:]:
            self.set_strictly_before(prev, next)
            prev = next

    def set_strictly_before(
        self,
        lhs: Union[Subtask, Timepoint, Timing],
        rhs: Union[Subtask, Timepoint, Timing],
    ):
        if isinstance(lhs, Subtask):
            lhs = lhs.end
        if isinstance(lhs, Timepoint):
            lhs = Timing(timepoint=lhs, delay=0)
        assert isinstance(lhs, Timing)
        if isinstance(rhs, Subtask):
            rhs = rhs.start
        if isinstance(rhs, Timepoint):
            rhs = Timing(timepoint=rhs, delay=0)
        assert isinstance(rhs, Timing)
        self.add_constraint(self._env.expression_manager.LT(lhs, rhs))


class TaskNetwork(AbstractTaskNetwork):
    def __init__(self, _env: Optional[Environment] = None):
        super().__init__(_env)
        self._variables: OrderedDict[str, Parameter] = OrderedDict()

    def __repr__(self):
        s = ["task network {\n"]
        if len(self._variables) > 0:
            s.append("  variables = [\n")
            for v in self.variables:
                s.append(f"    {v}\n")
            s.append("  ]\n")
        s.append("  subtasks = [\n")
        for t in self.subtasks:
            s.append(f"    {t}\n")
        s.append("  ]\n")
        if len(self._constraints) > 0:
            s.append("  constraints = [\n")
            for c in self.constraints:
                s.append(f"    {c}\n")
            s.append("  ]\n")
        s.append("}")
        return "".join(s)

    def __eq__(self, oth):
        if not isinstance(oth, TaskNetwork):
            return False
        return (
            set(self.variables) == set(oth.variables)
            and set(self.subtasks) == set(oth.subtasks)
            and set(self.constraints) == set(oth.constraints)
        )

    def __hash__(self):
        return (
            sum(map(hash, self.variables))
            + sum(map(hash, self.subtasks))
            + sum(map(hash, self.constraints))
        )

    def clone(self):
        new = TaskNetwork(self._env)
        new._variables = self._variables.copy()
        new._subtasks = self._subtasks[:]
        new._constraints = self._constraints[:]
        return new

    @property
    def variables(self) -> List[Parameter]:
        return list(self._variables.values())

    def add_variable(self, name: str, typename: Type) -> Parameter:
        if name in self._variables:
            raise ValueError(f"A variable with name {name} already exists.")
        param = Parameter(name, typename, self._env)
        self._variables[name] = param
        return param

    def parameter(self, name: str) -> Parameter:
        """Returns the variable with the given name."""
        return self._variables[name]
