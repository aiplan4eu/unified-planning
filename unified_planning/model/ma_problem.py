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
'''This module defines the MultiAgentProblem class.'''

import unified_planning
import sys
import copy
from unified_planning.shortcuts import *
import unified_planning.model.operators as op
from unified_planning.model.types import domain_size, domain_item
from unified_planning.environment import get_env, Environment
from unified_planning.walkers import OperatorsExtractor
from fractions import Fraction
from typing import List, Dict, Set, Union, Optional
from unified_planning.model.problem import Problem
from unified_planning.exceptions import UPProblemDefinitionError, UPTypeError, UPValueError, UPExpressionDefinitionError
from unified_planning.model.agent import Agent
from unified_planning.environment import Environment
import collections
from typing import List, Union



class MultiAgentProblem(Problem):
    '''Represents a planning MultiAgentProblem.'''
    def __init__(self, *args, **kwargs):
        super(MultiAgentProblem, self).__init__(*args, **kwargs)

    env = None
    agents_list = []
    plan = []
    #obj_exp = []
    #obj_exp_tot = []
    #plan_solve = []

    def set_initial_value(self, fluent: Union['unified_planning.model.fnode.FNode', 'unified_planning.model.fluent.Fluent'],
                          value: Union['unified_planning.model.fnode.FNode', 'unified_planning.model.fluent.Fluent', 'unified_planning.model.object.Object', bool,
                                       int, float, Fraction]):
        '''Sets the initial value for the given fluent.'''
        fluent_exp, value_exp = self._env.expression_manager.auto_promote(fluent, value)
        '''if not self._env.type_checker.is_compatible_exp(fluent_exp, value_exp):
            raise UPTypeError('Initial value assignment has not compatible types!')'''
        if fluent_exp in self._initial_value:
            raise UPProblemDefinitionError('Initial value already set!')
        self._initial_value[fluent_exp] = value_exp


    def initial_values(self) -> Dict['unified_planning.model.fnode.FNode', 'unified_planning.model.fnode.FNode']:
        '''Gets the initial value of the fluents.'''
        res = self._initial_value
        return res

    def add_fluent(self, fluent: 'unified_planning.model.fluent.Fluent', *,
                   default_initial_value: Union['unified_planning.model.fnode.FNode', 'unified_planning.model.object.Object', bool,
                                                int, float, Fraction] = None):
        '''Adds the given fluent.'''
        if self.has_name(fluent.name()):
            raise UPProblemDefinitionError('Name ' + fluent.name() + ' already defined!')
        self._fluents.append(fluent)
        if not default_initial_value is None:
            v_exp, = self._env.expression_manager.auto_promote(default_initial_value)
            self._fluents_defaults[fluent] = v_exp


    def add_objects(self, objs: List['unified_planning.model.object.Object']):
        '''Adds the given objects.'''
        for obj in objs:
            self.add_object(obj)

    def get_all_objects(self) -> List['unified_planning.model.object.Object']:
        '''Returns all the objects.'''
        return [o for o in self._objects]



    def add_environment(self, Env):
        self.env = Env

    def get_environment(self):
        return self.env

    def add_agent(self, Agents):
        self.agents_list.append(Agents)

    def get_agents(self):
        return self.agents_list

    '''def get_obj_exp(self):
        for ag in self.get_agents():
            self.obj_exp = []
            for obj in ag.get_all_objects():
                obj = copy.deepcopy(obj)
                setattr(obj, '_name', str(getattr(obj, '_name')) + "_" + str(self.get_agents().index(ag)))
                self.obj_exp.append(ObjectExp(obj))
            self.obj_exp_tot.append(tuple(self.obj_exp))
        return tuple(o for o in self.obj_exp_tot)'''

    def compile(self):
        for flu in self.get_environment().get_fluents():
            flu = copy.deepcopy(flu)
            setattr(flu, '_name', str(getattr(flu, '_name')) + "_env")
            self.add_fluent(flu)

        for flu, value in self.get_environment().get_initial_values().items():
            flu = copy.deepcopy(flu)
            value = copy.deepcopy(value)
            setattr(flu.fluent(), '_name', str(getattr(flu.fluent(), '_name')) + "_env")
            self.set_initial_value(flu, value)


        for ag in self.get_agents():
            for flu in ag.get_fluents():

                flu = copy.deepcopy(flu)
                setattr(flu, '_name', str(getattr(flu, '_name')) + "_" + str(self.get_agents().index(ag)))
                self.add_fluent(flu)


            for act in ag.get_actions():
                act = copy.deepcopy(act)
                setattr(act, 'name', str(getattr(act, 'name')) + "_" + str(self.get_agents().index(ag)))
                change_name = True
                for n, t in act._parameters.items(): #n è str:l_fro e l_to. t è Location
                    if change_name == True:
                        setattr(t._typename, '_name', str(getattr(t._typename, '_name')) + "_" + (str(self.get_agents().index(ag))))
                    change_name = False
                for i in act._preconditions:
                    if i._content.args != None:
                        for flu in i._content.args:
                            if flu.is_fluent_exp():
                                setattr(flu.fluent(), '_name', str(getattr(flu.fluent(), '_name')) + "_" + str(self.get_agents().index(ag)))
                    '''if i.is_fluent_exp():
                        setattr(i._content.payload, '_name', str(getattr(i._content.payload, '_name')) + "_" + str(self.get_agents().index(ag)))'''
                self.add_action(act)
            for flu, value in ag.get_initial_values().items():
                flu = copy.deepcopy(flu)        #hash commentato in fnode
                value = copy.deepcopy(value)
                setattr(flu.fluent(), '_name', str(getattr(flu.fluent(), '_name')) + "_" + str(self.get_agents().index(ag)))
                self.set_initial_value(flu, value)
            for goal in ag.get_goals():
                goal = copy.deepcopy(goal)
                setattr(goal.fluent(), '_name', str(getattr(goal.fluent(), '_name')) + "_" + str(self.get_agents().index(ag)))
                self.add_goal(goal)
            for obj in ag.get_all_objects():
                obj = copy.deepcopy(obj)
                setattr(obj, '_name', str(getattr(obj, '_name')) + "_" + str(self.get_agents().index(ag)))
                self.add_object(obj)
        return self


    '''def solve_compile(self):
        for ag in self.get_agents():
            for i in range(len(ag.get_actions())):
                self.plan.append(
                    unified_planning.plan.SequentialPlan([unified_planning.plan.ActionInstance(ag.get_actions()[i], self.get_obj_exp()[self.get_agents().index(ag)])]))
        return self.plan'''

    def solve_OneshotPlanner(self):
        with OneshotPlanner(name='pyperplan') as planner:
            solve_plan = planner.solve(self)
            print("Pyperplan returned: %s" % solve_plan)
        return

    def extract_plans(self, plan_problem):
        for ag in self.get_agents():
            for act in plan_problem._actions:
                act = copy.deepcopy(act)
                setattr(act._action, 'name', str(getattr(act._action, 'name')) + "_" + str(self.get_agents().index(ag)))
                for par in act._params: #l1, l2 , ...
                    setattr(par._content.payload, '_name', str(getattr(par._content.payload, '_name')) + "_" + str(self.get_agents().index(ag)))
                self.plan.append(act)
        return self.plan

