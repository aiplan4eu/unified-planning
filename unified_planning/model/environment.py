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
from unified_planning.exceptions import UPProblemDefinitionError, UPTypeError, UPValueError, UPExpressionDefinitionError
from unified_planning.walkers import OperatorsExtractor
from fractions import Fraction
from typing import List, Dict, Set, Union, Optional

class Environment:
    def __init__(
            self,
            obs_fluents = None,
            env: 'unified_planning.environment.Environment' = None
    ):
        if obs_fluents is None:
            self.obs_fluents = []

        self._env = unified_planning.environment.get_env(env)
        self._initial_value: Dict['unified_planning.model.fnode.FNode', 'upf.model.fnode.FNode'] = {}

    def add_fluent(self, Fluent):
        if self.has_name(Fluent.name):
            raise UPProblemDefinitionError('Name ' + Fluent.name + ' already defined!')
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

    def set_initial_value(self, fluent: Union['unified_planning.model.fnode.FNode', 'unified_planning.model.fluent.Fluent'],
                          value: Union['unified_planning.model.fnode.FNode', 'unified_planning.model.fluent.Fluent', 'unified_planning.model.object.Object', bool,
                                       int, float, Fraction]):
        '''Sets the initial value for the given fluent.'''
        fluent_exp, value_exp = self._env.expression_manager.auto_promote(fluent, value)
        '''if not self._env.type_checker.is_compatible_type(fluent_exp, value_exp):
            raise UPTypeError('Initial value assignment has not compatible types!')'''
        if fluent_exp in self._initial_value:
            raise UPProblemDefinitionError('Initial value already set!')
        self._initial_value[fluent_exp] = value_exp

    def set_initial_values(self, init_values):
        for fluent, value in init_values.items():
            self.set_initial_value(fluent, value)

    def get_initial_values(self) -> Dict['unified_planning.model.fnode.FNode', 'unified_planning.model.fnode.FNode']:
        '''Gets the initial values'''
        return self._initial_value

    def get_initial_value(self, fluent: Union['unified_planning.model.fnode.FNode', 'unified_planning.model.fluent.Fluent']) -> 'unified_planning.model.fnode.FNode':
        '''Gets the initial value of the given fluent.'''
        fluent_exp, = self._env.expression_manager.auto_promote(fluent)
        for a in fluent_exp.args():
            if not a.is_constant():
                raise UPExpressionDefinitionError(f'Impossible to return the initial value of a fluent expression with no constant arguments: {fluent_exp}.')
        if fluent_exp in self._initial_value:
            return self._initial_value[fluent_exp]
        else:
            raise UPProblemDefinitionError('Initial value not set!')
