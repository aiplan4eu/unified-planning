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

import upf
from upf.shortcuts import *
import upf.model.operators as op
from upf.exceptions import UPFProblemDefinitionError, UPFTypeError, UPFValueError, UPFExpressionDefinitionError
from upf.walkers import OperatorsExtractor
from fractions import Fraction
from typing import List, Dict, Set, Union, Optional

class Environment:
    def __init__(
            self,
            obs_fluents = None,
            goals=None,
            env: 'upf.environment.Environment' = None
    ):
        if obs_fluents is None:
            self.obs_fluents = []
        if goals is None:
            self._goals = []

        self._env = upf.environment.get_env(env)
        self._initial_value: Dict['upf.model.fnode.FNode', 'upf.model.fnode.FNode'] = {}

    def add_fluent(self, Fluent):
        if self.has_name(Fluent.name):
            raise UPFProblemDefinitionError('Name ' + Fluent.name + ' already defined!')
        self.obs_fluents.append(Fluent)

    def add_fluents(self, List_fluents: List):
        for flu in List_fluents:
            self.add_fluent(flu)

    def get_fluents(self):
        return self.obs_fluents


    def has_name(self, name: str) -> bool:
        '''Returns true if the name is in the agent.'''
        return self.has_fluent(name)

    def has_fluent(self, name: str) -> bool:
        '''Returns true if the fluent with the given name is in the agent.'''
        for f in self.obs_fluents:
            if f.name() == name:
                return True
        return False

    def set_initial_value(self, fluent: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent'],
                          value: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent', 'upf.model.object.Object', bool,
                                       int, float, Fraction]):
        '''Sets the initial value for the given fluent.'''
        fluent_exp, value_exp = self._env.expression_manager.auto_promote(fluent, value)
        if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPFTypeError('Initial value assignment has not compatible types!')
        if fluent_exp in self._initial_value:
            raise UPFProblemDefinitionError('Initial value already set!')
        self._initial_value[fluent_exp] = value_exp

    def set_initial_values(self, init_values):
        for fluent, value in init_values.items():
            self.set_initial_value(fluent, value)


    def get_initial_values(self) -> Dict['upf.model.fnode.FNode', 'upf.model.fnode.FNode']:
        '''Gets the initial values'''
        return self._initial_value


    def get_initial_value(self, fluent: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent']) -> 'upf.model.fnode.FNode':
        '''Gets the initial value of the given fluent.'''
        fluent_exp, = self._env.expression_manager.auto_promote(fluent)
        for a in fluent_exp.args():
            if not a.is_constant():
                raise UPFExpressionDefinitionError(f'Impossible to return the initial value of a fluent expression with no constant arguments: {fluent_exp}.')
        if fluent_exp in self._initial_value:
            return self._initial_value[fluent_exp]
        else:
            raise UPFProblemDefinitionError('Initial value not set!')


    def add_goal(self, goal: Union['upf.model.fnode.FNode', 'upf.model.fluent.Fluent', bool]):
        '''Adds a goal.'''
        goal_exp, = self._env.expression_manager.auto_promote(goal)
        assert self._env.type_checker.get_type(goal_exp).is_bool_type()
        self._goals.append(goal_exp)

    def add_goals(self, List_goals):
        '''Adds a goals.'''
        for goal in List_goals:
            self.add_goal(goal)

    def get_goals(self) -> Dict['upf.model.fnode.FNode', 'upf.model.fnode.FNode']:
        '''Returns the goals.'''
        return self._goals

    def clear_goals(self):
        '''Removes the goals.'''
        self._goals = []