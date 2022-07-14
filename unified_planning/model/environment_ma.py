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

import unified_planning
from unified_planning.shortcuts import *
import unified_planning.model.operators as op
from unified_planning.exceptions import (
    UPProblemDefinitionError,
    UPTypeError,
    UPValueError,
    UPExpressionDefinitionError,
)
from unified_planning.model.walkers import OperatorsExtractor
from fractions import Fraction
from typing import List, Dict, Set, Union, Optional
from unified_planning.model.mixins import (
    FluentsSetMixin,
)


class Environment_ma(
    FluentsSetMixin,
):

    """Represents a Environment_ma."""

    def __init__(
        self,
        env: "unified_planning.environment.Environment" = None,
        *,
        initial_defaults: Dict["up.model.types.Type", "ConstantExpression"] = {},
    ):
        self._env = unified_planning.environment.get_env(env)
        FluentsSetMixin.__init__(self, self.env, self.has_name, initial_defaults)
        self._goals: List["up.model.fnode.FNode"] = []
        self._initial_value: Dict[
            "unified_planning.model.fnode.FNode", "unified_planning.model.fnode.FNode"
        ] = {}

    def has_name(self, name: str) -> bool:
        """Returns true if the name is in the problem."""
        return self.has_fluent(name)

    def set_initial_value(
        self,
        fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"],
        value: Union[
            "up.model.fnode.FNode",
            "up.model.fluent.Fluent",
            "up.model.object.Object",
            bool,
            int,
            float,
            Fraction,
        ],
    ):
        """Sets the initial value for the given fluent."""
        fluent_exp, value_exp = self._env.expression_manager.auto_promote(fluent, value)
        if not self._env.type_checker.is_compatible_exp(fluent_exp, value_exp):
            raise UPTypeError("Initial value assignment has not compatible types!")
        self._initial_value[fluent_exp] = value_exp

    def set_initial_values(self, init_values):
        """Sets the initial values for the specified fluent list."""
        for fluent, value in init_values.items():
            self.set_initial_value(fluent, value)

    def get_initial_values(
        self,
    ) -> Dict[
        "unified_planning.model.fnode.FNode", "unified_planning.model.fnode.FNode"
    ]:
        """Gets the initial values"""
        return self._initial_value

    def get_initial_value(self) -> Dict["up.model.fnode.FNode", "up.model.fnode.FNode"]:
        """Gets the initial value of the fluents.

        IMPORTANT NOTE: this property does a lot of computation, so it should be called as
        seldom as possible."""
        res = self._initial_value
        for f in self._fluents:
            if f.arity == 0:
                f_exp = self._env.expression_manager.FluentExp(f)
                res[f_exp] = self.initial_value(f_exp)
            else:
                ground_size = 1
                domain_sizes = []
                for p in f.signature:
                    ds = domain_size(self, p.type)
                    domain_sizes.append(ds)
                    ground_size *= ds
                for i in range(ground_size):
                    f_exp = self._get_ith_fluent_exp(f, domain_sizes, i)
                    res[f_exp] = self.initial_value(f_exp)
        return res

    def add_goal(
        self,
        goal: Union[
            "unified_planning.model.fnode.FNode",
            "unified_planning.model.fluent.Fluent",
            bool,
        ],
    ):
        """Adds a goal."""
        (goal_exp,) = self._env.expression_manager.auto_promote(goal)
        assert self._env.type_checker.get_type(goal_exp).is_bool_type()
        self._goals.append(goal_exp)

    def add_goals(self, List_goals):
        """Adds a goals."""
        for goal in List_goals:
            self.add_goal(goal)

    @property
    def goals(self) -> List["up.model.fnode.FNode"]:
        """Returns the goals."""
        return self._goals
