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


import unified_planning
from unified_planning.shortcuts import *
import unified_planning.model.operators as op
from unified_planning.exceptions import UPProblemDefinitionError, UPTypeError, UPValueError, UPExpressionDefinitionError
from unified_planning.model.walkers import OperatorsExtractor
from fractions import Fraction
from typing import List, Dict, Set, Union, Optional

from unified_planning.model.abstract_problem import AbstractProblem
from unified_planning.model.mixins import (
    ActionsSetMixin,
    FluentsSetMixin,
    UserTypesSetMixin,
    AgentsSetMixin,
)

class Agent(
    ActionsSetMixin,
    FluentsSetMixin,
    UserTypesSetMixin,
    AgentsSetMixin,

):

    '''Represents an Agent.'''

    def __init__(
            self,
            ID,
            env: 'unified_planning.environment.Environment' = None,
    ):
        self._env = unified_planning.environment.get_env(env)
        UserTypesSetMixin.__init__(self, self.has_name)
        FluentsSetMixin.__init__(
            self, self.env, self._add_user_type, self.has_name
        )
        ActionsSetMixin.__init__(self, self.env, self._add_user_type_method, self.has_name)
        AgentsSetMixin.__init__(self, self.env, self._has_name_method)
        self._ID: str =  ID
        self._goals: List['up.model.fnode.FNode'] = []
        self._initial_value: Dict['unified_planning.model.fnode.FNode', 'unified_planning.model.fnode.FNode'] = {}


    def has_name(self, name: str) -> bool:
        """Returns true if the name is in the problem."""
        return (
            self.has_action(name)
            or self.has_fluent(name)
        )

    def add_goal(self, goal: Union['unified_planning.model.fnode.FNode', 'unified_planning.model.fluent.Fluent', bool]):
        '''Adds a goal.'''
        goal_exp, = self._env.expression_manager.auto_promote(goal)
        assert self._env.type_checker.get_type(goal_exp).is_bool_type()
        self._goals.append(goal_exp)

    def add_goals(self, List_goals):
        '''Adds a goals.'''
        for goal in List_goals:
            self.add_goal(goal)

    def get_goals(self) -> List["up.model.fnode.FNode"]:
        '''Returns the goals.'''
        return self._goals

    def clear_goals(self):
        '''Removes the goals.'''
        self._goals = []

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

    def get_initial_values(self) -> Dict['unified_planning.model.fnode.FNode', 'unified_planning.model.fnode.FNode']:
        '''Gets the initial values'''
        return self._initial_value

    def initial_value(
        self, fluent: Union["up.model.fnode.FNode", "up.model.fluent.Fluent"]
    ) -> "up.model.fnode.FNode":
        """Gets the initial value of the given fluent."""
        (fluent_exp,) = self._env.expression_manager.auto_promote(fluent)
        for a in fluent_exp.args:
            if not a.is_constant():
                raise UPExpressionDefinitionError(
                    f"Impossible to return the initial value of a fluent expression with no constant arguments: {fluent_exp}."
                )
        if fluent_exp in self._initial_value:
            return self._initial_value[fluent_exp]
        elif fluent_exp.fluent() in self._fluents_defaults:
            return self._fluents_defaults[fluent_exp.fluent()]
        else:
            raise UPProblemDefinitionError("Initial value not set!")


