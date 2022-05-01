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

#import unified_planning
import sys
import copy
from unified_planning.shortcuts import *
import unified_planning.model.operators as op
from unified_planning.model.types import domain_size, domain_item
from unified_planning.environment import get_env, Environment
from unified_planning.walkers import OperatorsExtractor
from .fluent import Fluent
from .action import *

from fractions import Fraction
from typing import List, Dict, Set, Union, Optional
from unified_planning.model.problem import Problem
from unified_planning.exceptions import UPProblemDefinitionError, UPTypeError, UPValueError, UPExpressionDefinitionError
from unified_planning.model.agent import Agent
from unified_planning.io.pddl_writer import PDDLWriter
from unified_planning.environment import Environment
from unified_planning.model.environment_ma import Environment_ma
import collections
from typing import List, Union
from unified_planning.transformers.transformer import Transformer
from unified_planning.io.pddl_writer_ma import PDDLWriter_MA

from unified_planning.walkers.substituter import Substituter
import re
import os
from typing import IO
from io import StringIO


class MultiAgentProblem(Problem):
    '''Represents a planning MultiAgentProblem.'''
    def __init__(self, *args, **kwargs):
        super(MultiAgentProblem, self).__init__(
            *args, **kwargs
        )
        self.env_ = None
        self.agents_list = []
        self.plan = []
        self._shared_data_list: List['up.model.fluent.Fluent'] = []
        self._new_fluents: Dict['up.model.fluent.Fluent'] = {}
        self._new_objects: Dict['up.model.object.Object']  = {}
        self._shared_data: List['up.model.fluent.Fluent'] = []
        self._flu_fuctions: List['up.model.fluent.Fluent'] = []
        self._agent_list_problems = {}

    ######################################################################################


    def add_shared_data(self, Fluent):
        if self.has_name(Fluent.name):
            raise UPProblemDefinitionError('Name ' + Fluent.name + ' already defined!')
        self._shared_data.append(Fluent)


    def get_shared_data(self) -> List['up.model.fluent.Fluent']:
        '''Returns the shared_data fluents.'''
        return self._shared_data


    def add_shared_data_list(self, List_fluents):
        for shared_data in List_fluents:
            self._shared_data.append(shared_data)


    def add_flu_function(self, Fluent):
        if self.has_name(Fluent.name):
            raise UPProblemDefinitionError('Name ' + Fluent.name + ' already defined!')
        self._flu_fuctions.append(Fluent)

    def get_flu_functions(self) -> List['up.model.fluent.Fluent']:
        '''Returns the shared_data fluents.'''
        return self._flu_fuctions


    def add_flu_functions_list(self, List_fluents):
        for fluent in List_fluents:
            self._flu_fuctions.append(fluent)

    ######################################################################################

    def add_user_types(self, user_types):
        for user_type in user_types:
            if user_type.is_user_type() and user_type not in self._user_types:
                self._user_types.append(user_type)

    def add_environment_(self, Env):
        self.env_ = Env

    def get_environment_(self):
        return self.env_

    def add_agent(self, Agents):
        self.agents_list.append(Agents)

    def get_agents(self):
        return self.agents_list

    def remove_user_type(self, user_type):
        del (self._user_types_hierarchy[user_type])
        self._user_types.remove(user_type)
        key = None
        if user_type in self._user_types_hierarchy[key]:
            self._user_types_hierarchy[key].remove(user_type)

    def chose_agent(self, name_agent :str):

        for user_type in self.user_types():
            if user_type._name == name_agent:
                #from ..shortcuts import UserType
                #agent = UserType('agent', None)
                #self._add_user_type(agent)
                #self._add_user_type(new_user_type)
                #self._add_user_type(agent)
                #new_user_type = UserType(name_agent, agent)
                #self._add_user_type(new_user_type)

                agent = copy.copy(user_type)
                self.remove_user_type(user_type)
                agent._name = 'agent'
                agent._father = None
                user_type._father = agent
                self._add_user_type(agent)


            else:
                pass


    def new_agent_fluent(self, key):
        if key in self._new_fluents.keys():
            new_fluent = self._new_fluents[key]
            return new_fluent

    def sub_exp(self, fluent_to_replace: Fluent, expresion, params = None):
        key = fluent_to_replace.name()
        if key in self._new_fluents.keys():
            new_fluent = self._new_fluents[key]
            if params is None:
                new_exp = self.env.expression_manager.FluentExp(new_fluent)
                old_exp = self.env.expression_manager.FluentExp(fluent_to_replace)
            else:
                new_exp = self.env.expression_manager.FluentExp(new_fluent, params)
                old_exp = self.env.expression_manager.FluentExp(fluent_to_replace, params)
            sub = Substituter(self.env)
            subs_map = {}
            subs_map[old_exp] = new_exp
            print("subs_map", subs_map)
            new_expresion = sub.substitute(expresion, subs_map)

            print("new_cnew_cnew_c", new_expresion)
        else:
            assert False, (key, "This fluent is not in the problem!")
        return new_expresion


    def compile(self):
        for flu in self.get_environment_().get_fluents():
            flu = copy.copy(flu)
            new_flu = Fluent((flu.name() + "_env"), flu._typename, flu._signature)
            self._new_fluents[flu.name()] = new_flu
            self.add_fluent(new_flu)

        for flu, value in self.get_environment_().get_initial_values().items():
            if flu.is_fluent_exp():
                fluent_to_replace = flu.fluent()
                args = flu._content.args
                new_exp_init = self.sub_exp(fluent_to_replace, flu, args)
            else:  # example (not clear_s(pallet0)) "depot"
                fluent_to_replace = flu._content.args[0].fluent()
                args = flu._content.args[0]._content.args
                new_exp_init = self.sub_exp(fluent_to_replace, flu, args)
            self.set_initial_value(new_exp_init, value)


        for ag in self.get_agents():
            for flu in ag.get_fluents():
                flu = copy.copy(flu) #qui anche copy va bene
                new_flu = Fluent((flu.name() + "_" + str(self.get_agents().index(ag))), flu._typename, flu._signature)
                self._new_fluents[flu.name()] = new_flu
                self.add_fluent(new_flu)

            for obj in self.all_objects():
                self._new_objects[obj.name()] = obj

            #Actions
            for act in ag.get_actions():
                new_act = InstantaneousAction((str(getattr(act, 'name')) + "_" + str(self.get_agents().index(ag))))

                # Preconditions
                for p in act._preconditions:
                    is_fluent = False

                    for arg in p._content.args:
                        if arg.is_fluent_exp():
                            is_fluent = True
                    if is_fluent:
                        if p.args()[0].is_fluent_exp(): #example: (not robot_at_0(l_to))
                            params = p._content.args[0]._content.args
                            fluent_to_replace = p.args()[0].fluent()
                            new_exp_p = self.sub_exp(fluent_to_replace, p, params)
                            new_act.add_precondition(new_exp_p)

                        else: # example: (10 <= battery_charge_0) "robot"
                            fluent_to_replace = p.args()[1].fluent()
                            new_exp_p = self.sub_exp(fluent_to_replace, p)
                            new_act.add_precondition(new_exp_p)

                    elif p.is_fluent_exp(): #example: robot_at_0(l_from) "robot"
                        params = p.args()
                        fluent_to_replace = p.fluent()
                        new_exp_p = self.sub_exp(fluent_to_replace, p, params)
                        new_act.add_precondition(new_exp_p)

                    elif p.is_not() and p._content.args[0]._content.args[0].is_fluent_exp(): #example: (not (is_at_0(robot) == l_to)) "robot_fluent_of_user_type"
                        fluent_to_replace = p._content.args[0]._content.args[0].fluent()
                        args = p._content.args[0]._content.args[0]._content.args
                        new_exp_p = self.sub_exp(fluent_to_replace, p, args)
                        new_act.add_precondition(new_exp_p)
                    else: #example:  (not (l_from == l_to)) "robot"
                        new_act.add_precondition(p)
                        print(new_act)

                # Effects
                for e in act._effects: # example robot_at_0(l_from) "robot"
                    if e.fluent().is_fluent_exp():
                        key = e.fluent().fluent().name()
                        if e.fluent()._content.args != ():
                            args = e.fluent()._content.args
                            new_fluent = self.new_agent_fluent(key)
                            new_fluent = new_fluent(args)
                            new_act.add_effect(new_fluent, e._value, e._condition)
                        else: #example (battery_charge_0 - 10) "robot"
                            new_fluent = self.new_agent_fluent(key)
                            fluent_to_replace = e.fluent().fluent()  # effect (battery_charge_0 - 10)
                            new_exp_e = self.sub_exp(fluent_to_replace, e._value)
                            new_act.add_effect(new_fluent, new_exp_e, e._condition)
                self.add_action(new_act)

            # Initial Value
            for flu, value in ag.get_initial_values().items():
                if flu.is_fluent_exp():
                    fluent_to_replace = flu.fluent()
                    args = flu._content.args
                    new_exp_init = self.sub_exp(fluent_to_replace, flu, args)
                else: #example (not clear_s(pallet0)) "depot"
                    fluent_to_replace = flu._content.args[0].fluent()
                    args = flu._content.args[0]._content.args
                    new_exp_init = self.sub_exp(fluent_to_replace, flu, args)
                self.set_initial_value(new_exp_init, value)

            # Goals
            for goal in ag.get_goals():
                if goal.is_fluent_exp(): #example:  robot_at(l2) "robot"
                    fluent_to_replace = goal.fluent()
                    args = goal._content.args
                    new_exp_goal = self.sub_exp(fluent_to_replace, goal, args)
                else: #example:  (is_at(r1) == l1) "robot_fluent_of_user_type"
                    fluent_to_replace = goal._content.args[0].fluent()
                    args = goal._content.args[0]._content.args
                    new_exp_goal = self.sub_exp(fluent_to_replace, goal, args)
                self.add_goal(new_exp_goal)
        return self

    #Se il tipo non ha un padre, creo agent e setto come pare agent
    def get_obj_type_father(self, name_obj):
        for object in self.all_objects():
            if object._name == name_obj:
                obj_type_father = object.type()._father
            else:
                pass

        return obj_type_father


    def set_agents_type(self):
        for ag in self.get_agents():
            name_agent = ag._ID
            for object in self.all_objects():

                if object._name == name_agent:
                    obj_type = object.type()
                    if object.type()._father == None:
                        agent = copy.copy(obj_type)
                        self.remove_user_type(obj_type)
                        agent._name = 'agent'
                        agent._father = None
                        obj_type._father = agent
                        if agent not in self.user_types():
                            self._add_user_type(agent)
                    else:
                        pass




                    # from ..shortcuts import UserType
                    # agent = UserType('agent', None)
                    # self._add_user_type(agent)
                    # self._add_user_type(new_user_type)
                    # self._add_user_type(agent)
                    # new_user_type = UserType(name_agent, agent)
                    # self._add_user_type(new_user_type)



    def compile_ma(self, my_agent:str = None):
        self.set_agents_type()
        #self.chose_agent(my_agent)
        #user_type = self.user_type(my_agent)
        #myAgent = Fluent('myAgent', None, [user_type])

        for flu in self.get_environment_().get_fluents():
            flu = copy.copy(flu)
            new_flu = Fluent((flu.name() + "_env"), flu._typename, flu._signature)
            self._new_fluents[flu.name()] = new_flu
            self.add_fluent(new_flu)

        for flu, value in self.get_environment_().get_initial_values().items():
            if flu.is_fluent_exp():
                fluent_to_replace = flu.fluent()
                args = flu._content.args
                new_exp_init = self.sub_exp(fluent_to_replace, flu, args)
            else:  # example (not clear_s(pallet0)) "depot"
                fluent_to_replace = flu._content.args[0].fluent()
                args = flu._content.args[0]._content.args
                new_exp_init = self.sub_exp(fluent_to_replace, flu, args)
            self.set_initial_value(new_exp_init, value)

        for ag in self.get_agents():
            for flu in ag.get_fluents():
                if flu not in self._fluents:
                    self.add_fluent(flu)
                else:
                    pass

            for act in ag.get_actions():
                if act not in self._actions:
                    self.add_action(act)
                else:
                    pass

            for flu, value in ag.get_initial_values().items():
                if flu not in self._initial_value:
                    if value != None:
                        self.set_initial_value(flu, value)
                    else:
                        raise UPTypeError(flu, 'Initial value is not set!')


            for goal in ag.get_goals():
                if goal not in self._goals:

                    self.add_goal(goal)

            '''for act in self._actions:
                act.add_precondition(myAgent)
            self.add_fluent(myAgent, default_initial_value=False)
            self.set_initial_value(myAgent(depot0), True)'''
        return self

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
                #for par in act._params: #l1, l2 , l1_0. l2_1 ...
                #    setattr(par._content.payload, '_name', str(getattr(par._content.payload, '_name')) + "_" + str(self.get_agents().index(ag)))
                self.plan.append(act)
        return self.plan

    def pddl_writer(self):
        w = PDDLWriter(self)
        prob_str = w.get_problem()
        problems = []
        for i in range(len(self.get_agents())):
            n_prob = i
            query = prob_str
            for a in range(len(self.get_agents())):
                if (a != n_prob):
                    p = re.compile(r'[({\[]([a-z]*.[a-z]*.'+ str(a) + ').*?[)\]}]', re.MULTILINE)
                    subst = ""
                    query = re.sub(p, subst, query)

            problems.append(query)
            problem = open(str(self.name) + '_problem_' + str(i), "w")
            problem.write(query)
            problem.close()
        domain = open(str(self.name) +'_domain', "w")
        domain.write(w.get_domain())
        domain.close()
        return problems

    def write_ma_problem_(self, problems, ag_list_problems):
        wrt_domain = False
        for prob in problems:
            for ag in ag_list_problems:
                w = PDDLWriter_MA(ag, prob)
                if wrt_domain == False:
                    w.write_domain(f' domain_{prob._name}')
                    wrt_domain = True
                w.write_problem(f' problem_{prob._name}_{ag}')
                w.write_agents_txt('agent-list.txt')

    def write_ma_problem(self, problems):

        for prob, agent_list in self._agent_list_problems.items():
            if type(problems) is list:
                name = problems[0]._name
                for p in problems:
                    if p._name == prob:
                        problem = p
            else:
                problem = problems
                name = problem._name
            write_domain = False
            for ag in agent_list:
                w = PDDLWriter_MA(ag, problem)
                if write_domain == False:
                    w.write_domain(f'Domain{problem._name.capitalize()}.pddl')
                    write_domain = True
                w.write_problem(f'Problem{name.capitalize()}{ag.capitalize()}.pddl')
                w.write_agents_txt('agent-list.txt')


    def FMAP_palnner(self):
        #path = "/home/alee8/Scrivania/unified-planning/unified_planning/FMAP"
        #path_file = "home/alee8/Scrivania/unified-planning/unified_planning/test/examples/"
        path = "/home/alee8/Scrivania/unified-planning/unified_planning/FMAP"
        path_file = "Domains/depots/Pfile01/ok/"
        cwd = os.getcwd()
        #os.chdir(path)
        try:
            os.chdir(path)
            print("Inserting inside-", os.getcwd())
        # Caching the exception
        except:
            print("Something wrong with specified\
                  directory. Exception- ", sys.exc_info())

        out = StringIO()
        out.write(f'java -jar FMAP.jar')
        name = next(iter(self._agent_list_problems))
        for prob, agents_list in self._agent_list_problems.items():
            for agent in agents_list:
                out.write(f' {agent} {path_file}Domain{prob.capitalize()}.pddl {path_file}Problem{name.capitalize()}{agent.capitalize()}.pddl')
        #out.write(f' {path_file}agent-list.txt')
        #out.write(f' agent-list.txt')
        command = out.getvalue()
        #from os import walk
        #filenames = next(walk(path_file), (None, None, []))[2]
        print(command)
        #os.system(command)
        plan = os.popen(command).read()
        os.chdir(cwd)
        name = f'FMAP_{name}_plan'
        self.write_FMAP_plan(name, plan)
        return plan


    def add_agent_list(self, problem, agent_list):
        prob = problem._name
        if prob not in self._agent_list_problems:
            self._agent_list_problems[prob] = []
        if agent_list not in self._agent_list_problems[prob]:
            self._agent_list_problems[prob].append(agent_list)



    def add_agent_list_(self, problem, agent_list):
        prob = problem
        if prob not in self._agent_list_problems:
            self._agent_list_problems[prob] = []
        if agent_list not in self._agent_list_problems[prob]:
            self._agent_list_problems[prob].append(agent_list)


    def write_FMAP_plan(self, filename: str, plan):
        '''Dumps to file the FMAP plan.'''
        with open(filename, 'w') as f:
            f.write(plan)