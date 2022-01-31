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


import upf
from upf.shortcuts import *
import upf.model.operators as op
from upf.exceptions import UPFProblemDefinitionError, UPFTypeError, UPFValueError, UPFExpressionDefinitionError
from upf.walkers import OperatorsExtractor
from fractions import Fraction
from typing import List, Dict, Set, Union, Optional

class Agent:
    def __init__(
            self,
            ID =  None,
            obs_individual_fluents = None,
            obs_public_fluents = None,
            actions = None,
            goals = None,
            env: 'upf.environment.Environment' = None,
    ):
        self.ID =  ID
        if obs_individual_fluents is None:
            self.obs_individual_fluents = []
        if obs_public_fluents is None:
            self.obs_public_fluents = []
        if actions is None:
            self.actions = []
        if goals is None:
            self._goals = []

        self._env = upf.environment.get_env(env)
        self._initial_value: Dict['upf.model.fnode.FNode', 'upf.model.fnode.FNode'] = {}
        self._objects: List['upf.model.object.Object'] = []
        self._user_types: List['upf.model.types.Type'] = []

    def add_individual_fluent(self, Fluent):
        if self.has_name(Fluent.name):
            raise UPFProblemDefinitionError('Name ' + Fluent.name + ' already defined!')
        self.obs_individual_fluents.append(Fluent)

    def add_individual_fluents(self, List_fluents: List):
        for flu in List_fluents:
            self.add_individual_fluent(flu)

    def get_individual_fluents(self):
        '''Returns the individual fluents'''
        return self.obs_individual_fluents

    def get_individual_fluent(self, name: str) -> 'upf.model.fluent.Fluent':
        '''Returns the fluent with the given name.'''
        for f in self.obs_individual_fluents:
            if f.name() == name:
                return f
        raise UPFValueError(f'Fluent of name: {name} is not defined!')


    def add_public_fluent(self, Fluent):
        if self.has_name(Fluent.name):
            raise UPFProblemDefinitionError('Name ' + Fluent.name + ' already defined!')
        self.obs_public_fluents.append(Fluent)

    def add_public_fluents(self, List_fluents: List):
        for flu in List_fluents:
            self.add_public_fluent(flu)

    def get_public_fluents(self):
        '''Returns the public fluents'''
        return self.obs_public_fluents

    def get_public_fluent(self, name: str) -> 'upf.model.fluent.Fluent':
        '''Returns the fluent with the given name.'''
        for f in self.obs_public_fluents:
            if f.name() == name:
                return f
        raise UPFValueError(f'Fluent of name: {name} is not defined!')


    def add_action(self, Action):
        '''Adds the given action.'''
        if self.has_name(Action.name):
            raise UPFProblemDefinitionError('Name ' + Action.name + ' already defined!')
        self.actions.append(Action)

    def add_actions(self, List_actions: List):
        for act in List_actions:
            self.add_action(act)

    def get_actions(self):
        '''Returns the actions'''
        return self.actions


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


    def has_name(self, name: str) -> bool:
        '''Returns true if the name is in the agent.'''
        return self.has_action(name) or self.has_fluent(name)

    def has_fluent(self, name: str) -> bool:
        '''Returns true if the fluent with the given name is in the agent.'''
        for f in self.obs_individual_fluents:
            if f.name() == name:
                return True
        return False

    def has_action(self, name: str) -> bool:
        '''Returns True if the agent has the action with the given name .'''
        for a in self.actions:
            if a.name == name:
                return True
        return False

    def has_object(self, name: str) -> bool:
        '''Returns true if the object with the given name is in the problem.'''
        for o in self._objects:
            if o.name() == name:
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


    def add_object(self, obj: 'upf.model.object.Object'):
        '''Adds the given object.'''
        if self.has_name(obj.name()):
            raise UPFProblemDefinitionError('Name ' + obj.name() + ' already defined!')
        self._objects.append(obj)
        if obj.type().is_user_type() and obj.type() not in self._user_types:
            self._user_types.append(obj.type())

    def add_objects(self, objs: List['upf.model.object.Object']):
        '''Adds the given objects.'''
        for obj in objs:
            self.add_object(obj)

    def get_all_objects(self) -> List['upf.model.object.Object']:
        '''Returns all the objects.'''
        return [o for o in self._objects]


