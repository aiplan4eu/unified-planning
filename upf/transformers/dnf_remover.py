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
"""This module defines the dnf remover class."""


from itertools import product
from upf.fnode import FNode
from upf.plan import SequentialPlan, ActionInstance, TimeTriggeredPlan
from upf.problem import Problem
from upf.action import ActionInterface, Action
from upf.dnf import Dnf
from upf.exceptions import UPFProblemDefinitionError
from upf.simplifier import Simplifier
from upf.temporal import DurativeAction, Interval, Timing
from upf.transformers.remover import Remover
from typing import Dict, List, Tuple, Union


class DnfRemover(Remover):
    '''Dnf remover class:
    this class requires a problem and offers the capability
    to transform a problem with preconditions not in the DNF form
    into one with all the preconditions in DNF form.
    '''
    def __init__(self, problem: Problem):
        Remover.__init__(problem)
        self._action_mapping = {}
        #NOTE no simplification are made. But it's possible to add them in key points

    def get_rewritten_problem(self) -> Problem:
        '''Creates a problem that is a copy of the original problem
        but every precondition is compiled into one with preconditions in DNF.'''
        if self._new_problem is not None:
            return self._new_problem
        #NOTE that a different environment might be needed when multi-threading
        self._new_problem = self._create_problem_copy_without_actions()
        self._create_problem_copy("dnf")
        self._new_problem_add_fluents()
        self._new_problem_add_objects()
        self._new_problem_add_initial_values()
        self._new_problem_add_goals()

        self._handle_actions()

        return self._new_problem

    def _handle_actions(self):
        dnf = Dnf(self._env)
        for a in self._problem.actions().values():
            self.count = 0
            if isinstance(a, Action):
                new_precond = dnf.get_dnf_expression(self._env.expression_manager.And(a.preconditions()))
                if new_precond.is_or():
                    for and_exp in new_precond.args():
                        na = self._create_new_action_with_given_precond(and_exp, a)
                        self._new_problem.add_action(na)
                else:
                    na = self._create_new_action_with_given_precond(new_precond, a)
                    self._new_problem.add_action(na)
            elif isinstance(a, DurativeAction):
                temporal_list: List[Union[Timing, Interval]] = []
                conditions: List[List[FNode]] = []
                # save the timing, calculate the dnf of the and of all the conditions at the same time
                # and then save it in conditions.
                # conditions contains lists of Fnodes, where [a,b,c] means a or b or c
                for t, cl in a.conditions().items():
                    temporal_list.append(t)
                    new_cond = dnf.get_dnf_expression(self._env.expression_manager.And(cl))
                    if new_cond.is_or():
                        conditions.append(new_cond.args())
                    else:
                        conditions.append([new_cond])
                for i, cl in a.durative_conditions().items():
                    temporal_list.append(i)
                    new_cond = dnf.get_dnf_expression(self._env.expression_manager.And(cl))
                    if new_cond.is_or():
                        conditions.append(new_cond.args())
                    else:
                        conditions.append([new_cond])
                conditions_tuple: Tuple[List[FNode], ...] = product(*conditions)
                for cond_list in conditions_tuple:
                    nda = self._create_new_durative_action_with_given_conds_at_given_times(temporal_list, cond_list, a)
                    self._new_problem.add_action(nda)
            else:
                raise NotImplementedError

    def _create_new_durative_action_with_given_conds_at_given_times(self, temporal_list, cond_list, original_action) -> DurativeAction:
        new_action = DurativeAction(f"{original_action.name()}__{self.count}__", {ap.name(): ap.type() for ap in original_action.parameters()}, self._env) # type: ignore
        self.count = self.count + 1
        if self._problem.has_action(new_action.name()):
            raise UPFProblemDefinitionError(f"DurativeAction: {new_action.name()} of problem: {self._problem.name()} has invalid name. Double underscore '__' is reserved by the naming convention.")
        for t, c in zip(temporal_list, cond_list):
            if c.is_and():
                for co in c.args():
                    self._add_condition(new_action, t, co)
            else:
                self._add_condition(new_action, t, c)
        for t, el in original_action.effects().items():
            for e in el:
                new_action._add_effect_instance(t, e)
        self._action_mapping[new_action] = original_action
        return new_action

    def _add_condition(self, new_action, time, condition):
        if isinstance(time, Timing):
            new_action.add_condition(time, condition)
        elif isinstance(time, Interval):
            new_action.add_durative_condition(time, condition)
        else:
            raise NotImplementedError

    def _create_new_action_with_given_precond(self, precond, original_action):
        new_action = self._create_action_copy(original_action, self.count)
        self.count += 1
        if precond.is_and():
            for leaf in precond.args():
                new_action.add_precondition(leaf)
        else:
            new_action.add_precondition(precond)
        for e in original_action.effects():
            new_action._add_effect_instance(e)
        self._action_mapping[new_action] = original_action
        return new_action

    def _create_problem_copy_without_actions(self):
        '''Creates the shallow copy of a problem, without adding the actions
        '''
        self._new_problem: Problem = Problem("dnf_" + str(self._problem.name()), self._env)
        for f in self._problem.fluents().values():
            self._new_problem.add_fluent(f)
        for o in self._problem.all_objects():
            self._new_problem.add_object(o)
        for fl, v in self._problem.initial_values().items():
            self._new_problem.set_initial_value(fl, v)
        for g in self._problem.goals():
            self._new_problem.add_goal(g)
        return self._new_problem

    def rewrite_back_plan(self, plan: Union[SequentialPlan, TimeTriggeredPlan]) -> Union[SequentialPlan, TimeTriggeredPlan]:
        '''Takes the sequential plan of the DNF problem (created with
        the method "self.get_rewritten_problem()" and translates the plan back
        to be a plan of the original problem.'''
        if isinstance(plan, SequentialPlan):
            dnf_actions = plan.actions()
            original_actions = []
            for ai in dnf_actions:
                original_actions.append(self._new_action_instance_original_name(ai))
            return SequentialPlan(original_actions)
        elif isinstance(plan, TimeTriggeredPlan):
            dnf_temporal_actions = plan.actions()
            original_temporal_actions = []
            for s, ai, d in dnf_temporal_actions:
                original_temporal_actions.append((s, self._new_action_instance_original_name(ai), d))
            return TimeTriggeredPlan(original_temporal_actions)
        else:
            raise NotImplementedError

    def _new_action_instance_original_name(self, ai: ActionInstance) -> ActionInstance:
        #original action
        oa = self._action_mapping[ai.action()]
        return ActionInstance(oa, ai.actual_parameters())
