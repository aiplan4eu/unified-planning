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
import upf.model.operators as op
from upf.model.types import domain_size, domain_item
from upf.exceptions import UPFProblemDefinitionError, UPFTypeError, UPFValueError, UPFExpressionDefinitionError
from upf.walkers import OperatorsExtractor
from fractions import Fraction
from typing import List, Dict, Set, Union, Optional
from upf.model.problem import Problem
from agent import Agent
from environment import Environment


class MultiAgentProblem(Problem):
    '''Represents a planning MultiAgentProblem.'''
    def __init__(self, *args, **kwargs):
        super(MultiAgentProblem, self).__init__(*args, **kwargs)

    agents_list = []
    plan = []

    def add_agent(self, Agents):
        self.agents_list.append(Agents)

    def get_agents(self):
        return self.agents_list




    def compile(self):
        '''for flu in Environment.get_fluents(self):
            problem.add_fluent(flu)'''

        for ag in self.get_agents():
            for flu in ag.get_individual_fluents():

                new_flu = copy.copy(flu)
                setattr(new_flu, '_name', str(getattr(new_flu, '_name')) + str(self.get_agents().index(ag)))
                self.add_fluent(new_flu)

            for act in ag.get_actions():
                new_act = copy.deepcopy(act)
                setattr(new_act, 'name', str(getattr(new_act, 'name')) + str(self.get_agents().index(ag)))
                #new_act._name = str(getattr(new_act, '_name')) + str(self.get_agents().index(ag))
                #print("new_act._parameters", new_act._parameters, id(new_act._parameters))
                change_name = True
                for n, t in new_act._parameters.items(): #n è str:l_fro e l_to. t è Location
                    if change_name == True:
                        setattr(t._typename, '_name', str(getattr(t._typename, '_name')) + (str(self.get_agents().index(ag))))
                    change_name = False

                #print("_preconditions", dir(new_act._preconditions[0]), "\n")
                #print("new_act._preconditions", new_act._preconditions)
                #print("_preconditions", type(new_act._preconditions[0]._content.args[1]))
                #print("_preconditions", type(new_act._preconditions[0]._content.payload))
                #print("_preconditions", new_act._preconditions[0]._content.payload)
                #t._typename._name = t._typename._name + (str(self.get_agents().index(ag)))
                #setattr(t._typename, '_name', (str(self.get_agents().index(ag))))

                #new_act._parameters.__setitem__('l_to', 'Location' + str(self.get_agents().index(ag)) + ' l_to')
                #new_act._parameters.__setitem__('l_from', 'Location' + str(self.get_agents().index(ag)) + ' l_from')
                #print("quaaaa", new_act._parameters)
                #print("quaaaa", new_act._parameters.__setitem__('l_to', 'aoooa'))

                #act._parameters.update()
                #breakpoint()

                #print("parameterparameter", act._parameters)
                self.add_action(new_act)
        return self


    def solve_compile(self):
        for ag in self.get_agents():
            for i in range(len(ag.get_actions())):
                self.plan.append(
                    upf.plan.SequentialPlan([upf.plan.ActionInstance(ag.get_actions()[i], tuple(ag.get_goals()))]))
        return self.plan

