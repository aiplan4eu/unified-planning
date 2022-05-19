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
from unified_planning.plans.sequential_plan import SequentialPlan
from typing import Callable, Dict, List


class PartialOrderPlan(plans.plan.Plan):
    '''Represents a partial order plan. Actrions are represent as an adjagency list graph.'''
    def __init__(self, actions: Dict['plans.plan.ActionInstance', List['plans.plan.ActionInstance']]):
        self._graph = nx.convert.from_dict_of_lists(actions)

    def __repr__(self) -> str:
        return str(self._graph )

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, PartialOrderPlan):
            return self._graph  == self._graph
        else:
            return False

    @property
    def actions(self) -> Dict['plans.plan.ActionInstance', List['plans.plan.ActionInstance']]:
        '''Returns the graph of action instances as an adjagency list.'''
        return nx.convert.to_dict_of_lists(self._graph)

    def replace_action_instances(self, replace_function: Callable[['plans.plan.ActionInstance'], 'plans.plan.ActionInstance']) -> 'plans.plan.Plan':
        old_adj_list = nx.convert.to_dict_of_lists(self._graph)
        new_adj_list: Dict['plans.plan.ActionInstance', List['plans.plan.ActionInstance']] = {}
        # Populate the new adjacency list with the replaced action instances
        for node, successor_list in old_adj_list:
            new_adj_list[replace_function(node)] = [replace_function(successor) for successor in successor_list]
        return PartialOrderPlan(new_adj_list)

    def convert_to_sequential_plan(self) -> SequentialPlan:
        return SequentialPlan(list(nx.topological_sort(self._graph)))
