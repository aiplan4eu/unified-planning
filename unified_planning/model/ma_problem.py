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
from unified_planning.model.walkers import OperatorsExtractor
from unified_planning.model.fluent import Fluent
from unified_planning.model.action import *

from fractions import Fraction
from typing import List, Dict, Set, Union, Optional
#from unified_planning.model.problem import Problem
from unified_planning.exceptions import UPProblemDefinitionError, UPTypeError, UPValueError, UPExpressionDefinitionError
from unified_planning.model.agent import Agent
from unified_planning.io.pddl_writer import PDDLWriter
from unified_planning.environment import Environment
from unified_planning.model.environment_ma import Environment_ma
import collections
from typing import List, Union, cast

from unified_planning.io.pddl_writer_ma import PDDLWriter_MA

from unified_planning.model.walkers.substituter import Substituter
import re
import os
from typing import IO
from io import StringIO

from unified_planning.model.abstract_problem import AbstractProblem
from unified_planning.model.mixins import (
    ActionsSetMixin,
    FluentsSetMixin,
    ObjectsSetMixin,
    UserTypesSetMixin,
    AgentsSetMixin,
)




class MultiAgentProblem(
    #Problem,
    AbstractProblem,
    UserTypesSetMixin,
    FluentsSetMixin,
    ActionsSetMixin,
    ObjectsSetMixin,
    AgentsSetMixin,

):
    '''Represents a planning MultiAgentProblem.'''
    '''def __init__(self,
        name: str = None,
        env: "up.environment.Environment" = None,
        initial_defaults: Dict["up.model.types.Type", "ConstantExpression"] = {},
        *args,
        **kwargs
    ):
        super(MultiAgentProblem, self).__init__(
            *args, **kwargs
        )'''

    def __init__(
        self,
        name: str = None,
        env: "up.environment.Environment" = None,
        *,
        initial_defaults: Dict["up.model.types.Type", "ConstantExpression"] = {},

    ):

        AbstractProblem.__init__(self, name, env)
        UserTypesSetMixin.__init__(self, self.has_name)
        FluentsSetMixin.__init__(
            self, self.env, self._add_user_type, self.has_name, initial_defaults
        )
        ActionsSetMixin.__init__(self, self.env, self._add_user_type, self.has_name)
        ObjectsSetMixin.__init__(self, self.env, self._add_user_type, self.has_name)
        AgentsSetMixin.__init__(self, self.env, self._has_name_method)

        self.env_ = None
        self._initial_value: Dict["up.model.fnode.FNode", "up.model.fnode.FNode"] = {}
        self._goals: List["up.model.fnode.FNode"] = list()
        #self.agents_list = []
        self.plan = []
        self._shared_data_list: List['up.model.fluent.Fluent'] = []
        self._new_fluents: Dict['up.model.fluent.Fluent'] = {}
        self._new_objects: Dict['up.model.object.Object']  = {}
        self._shared_data: List['up.model.fluent.Fluent'] = []
        self._flu_fuctions: List['up.model.fluent.Fluent'] = []
        self._agent_list_problems = {}

        self._operators_extractor = up.model.walkers.OperatorsExtractor()
        self._timed_effects: Dict[
            "up.model.timing.Timing", List["up.model.effect.Effect"]
        ] = {}
        self._timed_goals: Dict[
            "up.model.timing.TimeInterval", List["up.model.fnode.FNode"]
        ] = {}
        self._metrics: List["up.model.metrics.PlanQualityMetric"] = []
    ######################################################################################
    def __repr__(self) -> str:
        s = []
        if not self.name is None:
            s.append(f"problem name = {str(self.name)}\n\n")
        if len(self.user_types) > 0:
            s.append(f"types = {str(list(self.user_types))}\n\n")
        s.append("fluents = [\n")
        for f in self.fluents:
            s.append(f"  {str(f)}\n")
        s.append("]\n\n")
        s.append("actions = [\n")
        for a in self.actions:
            s.append(f"  {str(a)}\n")
        s.append("]\n\n")
        if len(self.user_types) > 0:
            s.append("objects = [\n")
            for ty in self.user_types:
                s.append(f"  {str(ty)}: {str(list(self.objects(ty)))}\n")
            s.append("]\n\n")
        s.append("initial fluents default = [\n")
        for f in self._fluents:
            if f in self._fluents_defaults:
                v = self._fluents_defaults[f]
                s.append(f"  {str(f)} := {str(v)}\n")
        s.append("]\n\n")
        s.append("initial values = [\n")
        for ag in self.get_agents():
            for k, v in ag._initial_value.items():
                s.append(f" {str(ag._ID)} {str(k)} := {str(v)}\n")
            s.append("]\n\n\n\n --------------------- \n")

        for g in self.goals:
            s.append(f"  {str(g)}\n")
        s.append("]\n\n")
        if len(self.quality_metrics) > 0:
            s.append("quality metrics = [\n")
            for qm in self.quality_metrics:
                s.append(f"  {str(qm)}\n")
            s.append("]\n\n")
        return "".join(s)

    def __eq__(self, oth: object) -> bool:
        if not (isinstance(oth, Problem)) or self._env != oth._env:
            return False
        if self.kind != oth.kind or self._name != oth._name:
            return False
        if set(self._fluents) != set(oth._fluents) or set(self._goals) != set(
            oth._goals
        ):
            return False
        if set(self._user_types) != set(oth._user_types) or set(self._objects) != set(
            oth._objects
        ):
            return False
        if set(self._actions) != set(oth._actions):
            return False
        oth_initial_values = oth.initial_values
        if len(self.initial_values) != len(oth_initial_values):
            return False
        for fluent, value in self.initial_values.items():
            oth_value = oth_initial_values.get(fluent, None)
            if oth_value is None:
                return False
            elif value != oth_value:
                return False
        if len(self._timed_effects) != len(oth._timed_effects):
            return False
        for t, tel in self._timed_effects.items():
            oth_tel = oth._timed_effects.get(t, None)
            if oth_tel is None:
                return False
            elif set(tel) != set(oth_tel):
                return False
        if len(self._timed_goals) != len(oth._timed_goals):
            return False
        for i, tgl in self._timed_goals.items():
            oth_tgl = oth._timed_goals.get(i, None)
            if oth_tgl is None:
                return False
            elif set(tgl) != set(oth_tgl):
                return False
        return True

    def __hash__(self) -> int:
        res = hash(self._kind) + hash(self._name)
        for f in self._fluents:
            res += hash(f)
        for a in self._actions:
            res += hash(a)
        for ut in self._user_types:
            res += hash(ut)
        for o in self._objects:
            res += hash(o)
        for iv in self.initial_values.items():
            res += hash(iv)
        for t, el in self._timed_effects.items():
            res += hash(t)
            for e in set(el):
                res += hash(e)
        for i, gl in self._timed_goals.items():
            res += hash(i)
            for g in set(gl):
                res += hash(g)
        for g in self._goals:
            res += hash(g)
        return res

################################Cambiare_sopra_stampa_per_ogni_agente####

    def has_name(self, name: str) -> bool:
        """Returns true if the name is in the problem."""
        return (
            self.has_action(name)
            or self.has_fluent(name)
            or self.has_object(name)
            or self.has_type(name)
        )


    def add_shared_data(self, Fluent):
        if Fluent in self._shared_data:
            raise UPProblemDefinitionError('Name ' + Fluent.name + ' already defined!')
        self._shared_data.append(Fluent)


    def get_shared_data(self) -> List['up.model.fluent.Fluent']:
        '''Returns the shared_data fluents.'''
        return self._shared_data


    def add_shared_data_list(self, List_fluents):
        for shared_data in List_fluents:
            self._shared_data.append(shared_data)


    def add_flu_function(self, Fluent):
        if Fluent in self._flu_fuctions:
            raise UPProblemDefinitionError('Name ' + Fluent.name + ' already defined!')
        self._flu_fuctions.append(Fluent)

    def get_flu_functions(self) -> List['up.model.fluent.Fluent']:
        '''Returns the shared_data fluents.'''
        return self._flu_fuctions


    def add_flu_functions_list(self, List_fluents):
        for fluent in List_fluents:
            self._flu_fuctions.append(fluent)

    def add_quality_metric(self, metric: "up.model.metrics.PlanQualityMetric"):
        """Adds a quality metric"""
        self._metrics.append(metric)

    @property
    def quality_metrics(self) -> List["up.model.metrics.PlanQualityMetric"]:
        """Returns the quality metrics"""
        return self._metrics

    def _get_ith_fluent_exp(
        self, fluent: "up.model.fluent.Fluent", domain_sizes: List[int], idx: int
    ) -> "up.model.fnode.FNode":
        """Returns the ith ground fluent expression."""
        quot = idx
        rem = 0
        actual_parameters = []
        for i, p in enumerate(fluent.signature):
            ds = domain_sizes[i]
            rem = quot % ds
            quot //= ds
            v = domain_item(self, p.type, rem)
            actual_parameters.append(v)
        return fluent(*actual_parameters)

    @property
    def initial_values(self) -> Dict["up.model.fnode.FNode", "up.model.fnode.FNode"]:
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

    @property
    def explicit_initial_values(
        self,
    ) -> Dict["up.model.fnode.FNode", "up.model.fnode.FNode"]:
        """Returns the problem's defined initial values.
        IMPORTANT NOTE: For all the initial values of hte problem use Problem.initial_values."""
        return self._initial_value

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
        self._agents.append(Agents)

    def get_agents(self):
        return self._agents

    def remove_user_type(self, user_type):

        del (self.user_types_hierarchy[user_type])
        self.user_types.remove(user_type)
        key = None
        if user_type in self.user_types_hierarchy[key]:
            self.user_types_hierarchy[key].remove(user_type)

    def chose_agent(self, name_agent :str):
        for user_type in self.user_types:
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
        key = fluent_to_replace.name
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

            for obj in self.all_objects:
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
        for object in self.all_objects:
            if object._name == name_obj:
                obj_type_father = object.type._father
            else:
                pass

        return obj_type_father


    def set_agents_type(self):
        for ag in self.get_agents():
            name_agent = ag._ID
            for object in self.all_objects:
                if object._name == name_agent:
                    obj_type = object.type
                    if object.type._father == None:
                        agent = copy.copy(obj_type)
                        agent._name = 'agent'
                        agent._father = None
                        obj_type._father = agent
                        if agent not in self.user_types:
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
            for flu in ag.fluents:
                if flu not in self._fluents:
                    self.add_fluent(flu)
                else:
                    pass

            for act in ag.actions:
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

#############################################FROM_PROBLEM#############################################
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

    def add_goal(
            self, goal: Union["up.model.fnode.FNode", "up.model.fluent.Fluent", bool]
    ):
        """Adds a goal."""
        assert (
                isinstance(goal, bool) or goal.environment == self._env
        ), "goal does not have the same environment of the problem"
        (goal_exp,) = self._env.expression_manager.auto_promote(goal)
        assert self._env.type_checker.get_type(goal_exp).is_bool_type()
        if goal_exp != self._env.expression_manager.TRUE():
            self._goals.append(goal_exp)

    @property
    def goals(self) -> List["up.model.fnode.FNode"]:
        """Returns the goals."""
        return self._goals

    def clear_goals(self):
        """Removes the goals."""
        self._goals = []

    @property
    def kind(self) -> "up.model.problem_kind.ProblemKind":
        """Returns the problem kind of this planning problem.

        IMPORTANT NOTE: this property does a lot of computation, so it should be called as
        seldom as possible."""
        self._kind = up.model.problem_kind.ProblemKind()
        self._kind.set_problem_class("ACTION_BASED")
        for fluent in self._fluents:
            self._update_problem_kind_fluent(fluent)
        for action in self._actions:
            self._update_problem_kind_action(action)
        if len(self._timed_effects) > 0:
            self._kind.set_time("CONTINUOUS_TIME")
            self._kind.set_time("TIMED_EFFECT")
        for effect_list in self._timed_effects.values():
            for effect in effect_list:
                self._update_problem_kind_effect(effect)
        if len(self._timed_goals) > 0:
            self._kind.set_time("TIMED_GOALS")
            self._kind.set_time("CONTINUOUS_TIME")
        for goal_list in self._timed_goals.values():
            for goal in goal_list:
                self._update_problem_kind_condition(goal)
        for goal in self._goals:
            self._update_problem_kind_condition(goal)
        for metric in self._metrics:
            if isinstance(
                    metric, up.model.metrics.MinimizeExpressionOnFinalState
            ) or isinstance(metric, up.model.metrics.MaximizeExpressionOnFinalState):
                self._kind.set_quality_metrics("FINAL_VALUE")
            elif isinstance(metric, up.model.metrics.MinimizeActionCosts):
                self._kind.set_quality_metrics("ACTIONS_COST")
            elif isinstance(metric, up.model.metrics.MinimizeMakespan):
                self._kind.set_quality_metrics("MAKESPAN")
            elif isinstance(metric, up.model.metrics.MinimizeSequentialPlanLength):
                self._kind.set_quality_metrics("PLAN_LENGTH")
            else:
                assert False, "Unknown quality metric"
        return self._kind

    def _update_problem_kind_effect(self, e: "up.model.effect.Effect"):
        if e.is_conditional():
            self._update_problem_kind_condition(e.condition)
            self._kind.set_effects_kind("CONDITIONAL_EFFECTS")
        if e.is_increase():
            self._kind.set_effects_kind("INCREASE_EFFECTS")
        elif e.is_decrease():
            self._kind.set_effects_kind("DECREASE_EFFECTS")

    def _update_problem_kind_condition(self, exp: "up.model.fnode.FNode"):
        ops = self._operators_extractor.get(exp)
        if OperatorKind.EQUALS in ops:
            self._kind.set_conditions_kind("EQUALITY")
        if OperatorKind.NOT in ops:
            self._kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        if OperatorKind.OR in ops:
            self._kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        if OperatorKind.EXISTS in ops:
            self._kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        if OperatorKind.FORALL in ops:
            self._kind.set_conditions_kind("UNIVERSAL_CONDITIONS")

    def _update_problem_kind_type(self, type: "up.model.types.Type"):
        if type.is_user_type():
            self._kind.set_typing("FLAT_TYPING")
            if cast(up.model.types._UserType, type).father is not None:
                self._kind.set_typing("HIERARCHICAL_TYPING")
        elif type.is_int_type():
            self._kind.set_numbers("DISCRETE_NUMBERS")
        elif type.is_real_type():
            self._kind.set_numbers("CONTINUOUS_NUMBERS")

    def _update_problem_kind_fluent(self, fluent: "up.model.fluent.Fluent"):
        self._update_problem_kind_type(fluent.type)
        if fluent.type.is_int_type() or fluent.type.is_real_type():
            self._kind.set_fluents_type("NUMERIC_FLUENTS")
        elif fluent.type.is_user_type():
            self._kind.set_fluents_type("OBJECT_FLUENTS")
        for p in fluent.signature:
            self._update_problem_kind_type(p.type)

    def _update_problem_kind_action(self, action: "up.model.action.Action"):
        for p in action.parameters:
            self._update_problem_kind_type(p.type)
        if isinstance(action, up.model.action.InstantaneousAction):
            for c in action.preconditions:
                self._update_problem_kind_condition(c)
            for e in action.effects:
                self._update_problem_kind_effect(e)
            if action.simulated_effect is not None:
                self._kind.set_simulated_entities("SIMULATED_EFFECTS")
        elif isinstance(action, up.model.action.DurativeAction):
            lower, upper = action.duration.lower, action.duration.upper
            if lower != upper:
                self._kind.set_time("DURATION_INEQUALITIES")
            free_vars = self.env.free_vars_extractor.get(
                lower
            ) | self.env.free_vars_extractor.get(upper)
            if len(free_vars) > 0:
                static_fluents = self.get_static_fluents()
                only_static = True
                for fv in free_vars:
                    if fv.fluent() not in static_fluents:
                        only_static = False
                        break
                if only_static:
                    self._kind.set_expression_duration("STATIC_FLUENTS_IN_DURATION")
                else:
                    self._kind.set_expression_duration("FLUENTS_IN_DURATION")
            for i, lc in action.conditions.items():
                if i.lower.delay != 0 or i.upper.delay != 0:
                    self._kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
                for c in lc:
                    self._update_problem_kind_condition(c)
            for t, le in action.effects.items():
                if t.delay != 0:
                    self._kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
                for e in le:
                    self._update_problem_kind_effect(e)
            if len(action.simulated_effects) > 0:
                self._kind.set_simulated_entities("SIMULATED_EFFECTS")
            self._kind.set_time("CONTINUOUS_TIME")
        else:
            raise NotImplementedError

#############################################FROM_PROBLEM#############################################


    def solve_OneshotPlanner(self):
        with OneshotPlanner(name='pyperplan') as planner:
            solve_plan = planner.solve(self)
            print("Pyperplan returned: %s" % solve_plan)
        return

    '''def extract_plans(self, plan_problem):
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
        return problems'''


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
                #passo l'agente e il problema. L'agente mi servirà sia per il dominio
                #che per il problema ex: myAgent "depot0", distributor0" ecc.
                w = PDDLWriter_MA(ag, problem)
                if write_domain == False:
                    w.write_domain(f'Domain{problem._name.capitalize()}.pddl')
                    write_domain = True
                w.write_problem(f'Problem{name.capitalize()}{ag.capitalize()}.pddl')
                w.write_agents_txt('agent-list.txt')


    def FMAP_planner(self):
        #path = "/home/alee8/Scrivania/unified-planning/unified_planning/FMAP"
        #path_file = "home/alee8/Scrivania/unified-planning/unified_planning/test/examples/"
        path = "../../FMAP"
        #path_file = "Domains/depots/Pfile01/ok/"
        path_file = "../test/examples/"
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
        #name è uguale al primo nome del problema dentro agent_list
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


    def write_FMAP_plan(self, filename: str, plan):
        '''Dumps to file the FMAP plan.'''
        with open(filename, 'w') as f:
            f.write(plan)