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
import upf.model.operators as op
from upf.model.types import domain_size, domain_item
from upf.exceptions import UPFProblemDefinitionError, UPFTypeError, UPFValueError, UPFExpressionDefinitionError
from upf.walkers import OperatorsExtractor
from fractions import Fraction
from typing import List, Dict, Set, Union, Optional
from upf.model.problem import Problem
from agent import agent


class MultiAgentProblem(Problem):
    '''Represents a planning MultiAgentProblem.'''
    def __init__(self, *args, **kwargs):
        super(MultiAgentProblem, self).__init__(*args, **kwargs)

    agents_list = []
    plan = []

    def add_agent(self, Agents):
        self.agents_list.append(Agents)

    def get_agent(self):
        return self.agents_list

    def compile(self, problem ):
        for ag in problem.get_agent():
            for flu in ag.get_individual_fluent():
                problem.add_fluent(flu)
            for flu in ag.get_public_fluent():
                problem.add_fluent(flu)
            for act in ag.get_actions():
                problem.add_action(act)

    def solve_compile(self, problem):
        for ag in problem.get_agent():
            for i in range(len(ag.get_actions())):
                self.plan.append(
                    upf.plan.SequentialPlan([upf.plan.ActionInstance(ag.get_actions()[i], tuple(ag.get_goals()))]))
        return self.plan

