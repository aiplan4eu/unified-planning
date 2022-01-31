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

import upf
import sys
import copy
from upf.shortcuts import *
import upf.model.operators as op
from upf.model.types import domain_size, domain_item
from upf.exceptions import UPFProblemDefinitionError, UPFTypeError, UPFValueError, UPFExpressionDefinitionError
from upf.walkers import OperatorsExtractor
from fractions import Fraction
from typing import List, Dict, Set, Union, Optional
from upf.model.problem import Problem
from agent import Agent
from environment import Environment
import collections
from typing import List, Union

class MultiAgentProblem(Problem):
    '''Represents a planning MultiAgentProblem.'''
    def __init__(self, *args, **kwargs):
        super(MultiAgentProblem, self).__init__(*args, **kwargs)

    env = None
    agents_list = []
    plan = []
    obj_exp = []
    obj_exp_tot = []

    def add_env(self, Env):
        self.env = Env

    def get_env(self):
        return self.env

    def add_agent(self, Agents):
        self.agents_list.append(Agents)

    def get_agents(self):
        return self.agents_list

    def get_obj_exp(self):
        for ag in self.get_agents():
            self.obj_exp = []
            for obj in ag.get_all_objects():
                obj = copy.deepcopy(obj)
                setattr(obj, '_name', str(getattr(obj, '_name')) + "_" + str(self.get_agents().index(ag)))
                self.obj_exp.append(ObjectExp(obj))
            self.obj_exp_tot.append(tuple(self.obj_exp))
        return tuple(o for o in self.obj_exp_tot)

    def compile(self):
        for flu in self.get_env().get_fluents():
            flu = copy.deepcopy(flu)
            setattr(flu, '_name', str(getattr(flu, '_name')) + "_env")
            self.add_fluent(flu)

        for goal in self.get_env().get_goals():
            goal = copy.deepcopy(goal)
            setattr(goal.fluent(), '_name', str(getattr(goal.fluent(), '_name')) + "_env")
            self.add_goal(goal)

        for flu, value in self.get_env().get_initial_values().items():
            flu = copy.deepcopy(flu)
            value = copy.deepcopy(value)
            setattr(flu.fluent(), '_name', str(getattr(flu.fluent(), '_name')) + "_env")
            self.set_initial_value(flu, value)

        for ag in self.get_agents():
            for flu in ag.get_individual_fluents():
                flu = copy.deepcopy(flu)
                setattr(flu, '_name', str(getattr(flu, '_name')) + "_" + str(self.get_agents().index(ag)))
                self.add_fluent(flu)

            for act in ag.get_actions():
                act = copy.deepcopy(act)
                setattr(act, 'name', str(getattr(act, 'name')) + "_" + str(self.get_agents().index(ag)))
                change_name = True
                for n, t in act._parameters.items():
                    if change_name == True:
                        setattr(t._typename, '_name', str(getattr(t._typename, '_name')) + "_" + (str(self.get_agents().index(ag))))
                    change_name = False
                self.add_action(act)

            for flu, value in ag.get_initial_values().items():
                flu = copy.deepcopy(flu)
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

    def solve_compile(self):
        for ag in self.get_agents():
            for i in range(len(ag.get_actions())):
                self.plan.append(
                    upf.plan.SequentialPlan([upf.plan.ActionInstance(ag.get_actions()[i], self.get_obj_exp()[self.get_agents().index(ag)])]))
        return self.plan

