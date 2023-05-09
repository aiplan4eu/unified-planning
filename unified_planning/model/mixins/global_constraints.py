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


import unified_planning as up
from unified_planning.exceptions import UPProblemDefinitionError
from typing import List


class GlobalConstraintsMixin:
    """
    This class is a mixin that contains the ``global constraints`` with some related methods.
    """

    def __init__(self, environment):
        self._env = environment
        self._global_constraints: List["up.model.fnode.FNode"] = []

    @property
    def environment(self) -> "up.environment.Environment":
        """Returns the `problem` `environment`."""
        return self._env

    @property
    def global_constraints(self) -> List["up.model.fnode.FNode"]:
        """Returns the List of ``global_constraints`` in the problem."""
        return self._global_constraints

    def add_state_invariant(self, constraint: "up.model.expression.BoolExpression"):
        """
        Adds the given ``constraint`` to the problem's global constraints.

        :param constraint: The constraint to add to this problem as a global constraint.
        """
        (constraint_exp,) = self._env.expression_manager.auto_promote(constraint)
        if not constraint_exp.environment == self._env:
            raise UPProblemDefinitionError(
                f"The environment of the problem is different from the environment of the global constraint: {constraint_exp}"
            )
        if not constraint_exp.type.is_bool_type():
            raise UPProblemDefinitionError(
                "The type of a global_constraint must be BOOL but ",
                f"{constraint_exp.type} is the type of the constraint: {constraint_exp}",
            )
        self._global_constraints.append(constraint_exp)

    def clear_global_constraints(self):
        """Removes all the ``global_constraints`` from this problem."""
        self._global_constraints = []

    def __eq__(self, other):
        return isinstance(other, GlobalConstraintsMixin) and set(
            self._global_constraints
        ) == set(other._global_constraints)

    def __hash__(self):
        return sum(map(hash, self._global_constraints))

    def _clone_to(self, other: "GlobalConstraintsMixin"):
        other._global_constraints = self._global_constraints.copy()
