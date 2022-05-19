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


import networkx as nx # type: ignore
import unified_planning as up
import unified_planning.plans as plans
from unified_planning.model import FNode, InstantaneousAction
from unified_planning.walkers import Substituter, Simplifier, FreeVarsExtractor
from typing import Callable, Dict, Optional, Set, List, cast


class SequentialPlan(plans.plan.Plan):
    '''Represents a sequential plan.'''
    def __init__(self, actions: List['plans.plan.ActionInstance']):
        self._actions = actions

    def __repr__(self) -> str:
        return str(self._actions)

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, SequentialPlan):
            return self.actions == oth.actions
        else:
            return False

    @property
    def actions(self) -> List['plans.plan.ActionInstance']:
        '''Returns the sequence of action instances.'''
        return self._actions

    def replace_action_instances(self, replace_function: Callable[['plans.plan.ActionInstance'], 'plans.plan.ActionInstance']) -> 'up.plans.plan.Plan':
        return SequentialPlan([replace_function(ai) for ai in self._actions])

    def convert_to_partial_order_plan(self, _env: Optional['up.Environment'] = None) -> 'up.plans.partial_order_plan.PartialOrderPlan':
        env = up.environment.get_env(_env)
        subs = Substituter(env)
        simp = Simplifier(env)
        fve = FreeVarsExtractor()
        # last_modifier is the mapping from a grounded fluent to the last action instance that assigned a value to
        # that fluent
        last_modifier: Dict[FNode, 'plans.plan.ActionInstance'] = {}
        # all_required is the mapping from a grounded fluent to all the action instances that read the value of that
        # fluent in their preconditions (or in the condition of their conditional effects)
        all_required: Dict[FNode, List['plans.plan.ActionInstance']] = {}
        # graph stores the information gathered through the process
        graph = nx.DiGraph()
        for action_instance in self.actions:
            grounded_action = cast(InstantaneousAction, up.plans.plan.ground_action_instance(action_instance, subs, simp))
            graph.add_node(action_instance)

            # required_fluents contains all the fluents that this action_instance "reads"
            required_fluents: Set[FNode] = set()
            # add free vars of preconditions
            for prec in grounded_action.preconditions:
                required_fluents.union(fve.get(prec))
            # ---------------- CODE WITHOUT ADDING THE FLUENTS THE CURRENT ACTION INSTANCE WRITES TO THE REQUIRED
            # add free vars in the condition of conditional effects
            for eff in grounded_action.conditional_effects:
                required_fluents.union(fve.get(eff.condition))
            # ---------------- CODE ADDING THE FLUENTS THE CURRENT ACTION INSTANCE WRITES TO THE REQUIRED
            # add in the required_fluents all the free fluents this action instance deals with
            for eff in grounded_action.effects:
                required_fluents.union(fve.get(eff.condition))
                required_fluents.union(fve.get(eff.fluent))
                required_fluents.union(fve.get(eff.value))
            # ----------------- END OF "DUPLICATE" CODE

            # for every required fluent, add this action instance to the list of action instances that requires this fluent
            # and order the current action instance after the last modifier of the fluent
            for required_fluent in required_fluents:
                action_instance_list = all_required.get(required_fluent, None)
                if action_instance_list is None:
                    all_required[required_fluent] = [action_instance]
                else:
                    action_instance_list.append(action_instance)
                required_fluent_last_modifier = last_modifier.get(required_fluent, None)
                if required_fluent_last_modifier is not None:
                    graph.add_edge(required_fluent_last_modifier, action_instance)

            # for every effect, set current action instance as the last modifier and the current action instance is ordered
            # after every action instance that requires a fluent the current action instance modifies
            for eff in grounded_action.effects:
                assert eff.fluent.is_fluent_exp()
                last_modifier[eff.fluent] = action_instance
                dependent_action_instance_list = all_required.get(eff.fluent, None)
                if dependent_action_instance_list is not None:
                    for dependent_action_instance in dependent_action_instance_list:
                        graph.add_edge(dependent_action_instance, action_instance)

        # remove redundant edges and return the up.plans.partial_order_plan.PartialOrderPlan structure.
        return up.plans.partial_order_plan.PartialOrderPlan(nx.convert.to_dict_of_lists(nx.transitive_reduction(graph)))
