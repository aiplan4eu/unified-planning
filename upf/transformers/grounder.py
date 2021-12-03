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
"""This module defines the grounder class."""


import upf
from upf.model import Problem, Action, Type, Object, Expression, Effect, ActionParameter, DurativeAction, InstantaneousAction, FNode
from upf.model.types import _domain_size,  _domain_item
from upf.transformers.transformer import Transformer
from upf.plan import SequentialPlan, TimeTriggeredPlan, ActionInstance
from upf.walkers import Substituter
from itertools import product
from typing import Dict, List, Tuple, Union


class Grounder(Transformer):
    '''Grounder class:
    this class requires a problem and offers the capability
    to transform it into a grounded problem, therefore the
    resulting problem will not have lifted actions anymore,
    but only grounded actions.
    '''
    def __init__(self, problem: Problem, name: str = 'grnd'):
        Transformer.__init__(self, problem, name)
        #Represents the map from the new action to the old action
        self._new_to_old: Dict[Action, Action] = {}
        #represents a mapping from the action of the original problem to action of the new one.
        self._old_to_new: Dict[Action, List[Action]] = {}
        self._substituter = Substituter(self._problem.env)
        #this data structure maps the grounded action with the objects the action grounds
        self._map_parameters: Dict[Action, List[FNode]] = {}

    def get_rewrite_back_map(self) -> Dict[Action, Tuple[Action, List[FNode]]]:
        '''Returns a map from an action of the grounded problem to the
        corresponding action of the original problem and the list of the
        parameters applied to the original action to obtain the grounded
        action.'''
        if self._new_problem is None:
            raise
        trace_back_map: Dict[Action, Tuple[Action, List[FNode]]] = {}
        for grounded_action in self._new_problem.actions():
            trace_back_map[grounded_action] = (self.get_original_action(grounded_action), self._map_parameters[grounded_action])
        return trace_back_map

    def get_rewritten_problem(self) -> Problem:
        '''Creates a problem that is a copy of the original problem
        but every action is substituted by it's grounded derivates.'''
        if self._new_problem is not None:
            return self._new_problem
        #NOTE that a different environment might be needed when multi-threading
        self._new_problem = self._problem.clone()
        self._new_problem.name = f'{self._name}_{self._problem.name}'
        self._new_problem.clear_actions()
        for old_action in self._problem.actions():
            #contains the type of every parameter of the action
            type_list: List[Type] = [param.type() for param in old_action.parameters()]
            #if the action does not have parameters, it does not need to be grounded.
            if len(type_list) == 0:
                new_action = old_action.clone()
                self._new_problem.add_action(new_action)
                self._new_to_old[new_action] = old_action
                self._old_to_new[old_action] = [new_action]
                continue
            # a list containing the list of object in the problem of the given type.
            # So, if the problem has 2 Locations l1 and l2, and 2 Robots r1 and r2, and
            # the action move_to takes as parameters a Robot and a Location,
            # the variable state at this point will be the following:
            # type_list = [Robot, Location]
            # objects_list = [[r1, r2], [l1, l2]]
            # the product of *objects_list will be:
            # [(r1, l1), (r1, l2), (r2, l1), (r2,l2)]
            ground_size = 1
            domain_sizes = []
            for t in type_list:
                ds = _domain_size(self._new_problem, t)
                domain_sizes.append(ds)
                ground_size *= ds
            items_list: List[List[FNode]] = []
            for i, (size, type) in enumerate(zip(domain_sizes, type_list)):
                items_list.append([])
                for j in range(size):
                    items_list[i].append(_domain_item(self._new_problem, type, j))
            for grounded_params in product(*items_list):
                subs: Dict[Expression, Expression] = dict(zip(old_action.parameters(), list(grounded_params)))
                is_feasible, new_action = self._create_action_with_given_subs(old_action, subs)
                if is_feasible:
                    self._map_parameters[new_action] = self._new_problem.env.expression_manager.auto_promote(subs.values())
                    self._new_problem.add_action(new_action)
                    self._new_to_old[new_action] = old_action
                    self._map_old_to_new_action(old_action, new_action)
        return self._new_problem

    def _create_effect_with_given_subs(self, old_effect: Effect, subs: Dict[Expression, Expression]) -> Effect:
        new_fluent = self._substituter.substitute(old_effect.fluent(), subs)
        new_value = self._substituter.substitute(old_effect.value(), subs)
        new_condition = self._substituter.substitute(old_effect.condition(), subs)
        return Effect(new_fluent, new_value, new_condition, old_effect.kind())

    def _create_action_with_given_subs(self, old_action: Action, subs: Dict[Expression, Expression]) -> Tuple[bool, Action]:
        naming_list: List[str] = []
        for param, value in subs.items():
            assert isinstance(param, ActionParameter)
            assert isinstance(value, FNode)
            naming_list.append(param.name())
            naming_list.append(str(value))
        new_name = f'{old_action.name}_{"_".join(naming_list)}'
        if isinstance(old_action, InstantaneousAction):
            new_action = InstantaneousAction(self.get_fresh_name(new_name))
            for p in old_action.preconditions():
                new_action.add_precondition(self._substituter.substitute(p, subs))
            for e in old_action.effects():
                new_action._add_effect_instance(self._create_effect_with_given_subs(e, subs))
            is_feasible, new_preconditions = self._check_and_simplify_preconditions(new_action)
            if not is_feasible:
                return (False, new_action)
            new_action._set_preconditions(new_preconditions)
            return (True, new_action)
        elif isinstance(old_action, DurativeAction):
            new_durative_action = DurativeAction(self.get_fresh_name(old_action.name))
            new_durative_action.set_duration_constraint(old_action.duration())
            for t, cl in old_action.conditions().items():
                for c in cl:
                    new_durative_action.add_condition(t, self._substituter.substitute(c, subs))
            for i, cl in old_action.durative_conditions().items():
                for c in cl:
                    new_durative_action.add_durative_condition(i, self._substituter.substitute(c, subs))
            for t, el in old_action.effects().items():
                for e in el:
                    new_durative_action._add_effect_instance(t, self._create_effect_with_given_subs(e, subs))
            is_feasible, new_conditions = self._check_and_simplify_conditions(new_durative_action)
            if not is_feasible:
                return (False, new_durative_action)
            new_durative_action.clear_conditions()
            for t, c in new_conditions:
                new_durative_action.add_condition(t, c)
            return (True, new_durative_action)
        else:
            raise NotImplementedError

    def _map_old_to_new_action(self, old_action, new_action):
        if old_action in self._old_to_new:
            self._old_to_new[old_action].append(new_action)
        else:
            self._old_to_new[old_action] = [new_action]

    def get_original_action(self, action: Action) -> Action:
        '''After the method get_rewritten_problem is called, this function maps
        the actions of the transformed problem into the actions of the original problem.'''
        return self._new_to_old[action]

    def get_transformed_actions(self, action: Action) -> List[Action]:
        '''After the method get_rewritten_problem is called, this function maps
        the actions of the original problem into the actions of the transformed problem.'''
        return self._old_to_new[action]

    def rewrite_back_plan(self, plan: Union[SequentialPlan, TimeTriggeredPlan]) -> Union[SequentialPlan, TimeTriggeredPlan]:
        '''Takes the sequential plan of the problem (created with
        the method "self.get_rewritten_problem()" and translates the plan back
        to be a plan of the original problem, considering the absence of parameters
        in the actions of the plan.'''
        if isinstance(plan, SequentialPlan):
            new_actions: List[ActionInstance] = plan.actions()
            old_actions: List[ActionInstance] = []
            for ai in new_actions:
                old_actions.append(ActionInstance(self.get_original_action(ai.action()), tuple(self._map_parameters[ai.action()])))
            return SequentialPlan(old_actions)
        elif isinstance(plan, TimeTriggeredPlan):
            s_new_actions_d = plan.actions()
            s_old_actions_d = []
            for s, ai, d in s_new_actions_d:
                s_old_actions_d.append((s, ActionInstance(self.get_original_action(ai.action()), tuple(self._map_parameters[ai.action()])), d))
            return TimeTriggeredPlan(s_old_actions_d)
        raise NotImplementedError
