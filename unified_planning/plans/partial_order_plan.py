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


import networkx as nx
import unified_planning as up
import unified_planning.plans as plans
from unified_planning.environment import Environment
from unified_planning.exceptions import UPUsageError
from unified_planning.plans.plan import ActionInstance
from unified_planning.plans.sequential_plan import SequentialPlan
from typing import Callable, Dict, Iterator, List, Optional


class PartialOrderPlan(plans.plan.Plan):
    """Represents a partial order plan. Actions are represent as an adjacency list graph."""

    def __init__(
        self,
        adjacency_list: Dict[
            "plans.plan.ActionInstance", List["plans.plan.ActionInstance"]
        ],
        environment: Optional["Environment"] = None,
        _graph: Optional[nx.DiGraph] = None,
    ):
        """Constructs the PartialOrderPlan using the adjacency list representation.

        :param adjacency_list: The Dictionary representing the adjacency list for this PartialOrderPlan.
        :param env: The environment in which the ActionInstances in the adjacency_list are created.
        :param _graph: The graph that is semnatically equivalent to the adjacency_list.
            NOTE: This parameter is for internal use only and it's maintainance is not guaranteed by any means.
        :return: The created PartialOrderPlan.
        """
        # if we have a specific env or we don't have any actions
        if environment is not None or not adjacency_list:
            plans.plan.Plan.__init__(
                self, plans.plan.PlanKind.PARTIAL_ORDER_PLAN, environment
            )
        # If we don't have a specific env, use the env of the first action
        else:
            assert len(adjacency_list) > 0
            for ai in adjacency_list.keys():
                plans.plan.Plan.__init__(
                    self, plans.plan.PlanKind.PARTIAL_ORDER_PLAN, ai.action.env
                )
                break
        if _graph is not None:
            # sanity checks
            assert len(adjacency_list) == 0
            assert all(isinstance(n, ActionInstance) for n in _graph.nodes)
            assert all(
                isinstance(f, ActionInstance) and isinstance(t, ActionInstance)
                for f, t in _graph.edges
            )
            self._graph = _graph
        else:
            for (
                ai_k,
                ai_v_list,
            ) in (
                adjacency_list.items()
            ):  # check that given env and the env in the actions is the same
                if ai_k.action.env != self._environment:
                    raise UPUsageError(
                        "The environment given to the plan is not the same of the actions in the plan."
                    )
                for ai in ai_v_list:
                    if ai.action.env != self._environment:
                        raise UPUsageError(
                            "The environment given to the plan is not the same of the actions in the plan."
                        )
            self._graph = nx.convert.from_dict_of_lists(
                adjacency_list, create_using=nx.DiGraph
            )

    def __repr__(self) -> str:
        return str(self._graph)

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, PartialOrderPlan):
            return nx.is_isomorphic(
                self._graph,
                oth._graph,
                node_match=_semantically_equivalent_action_instances,
            )
        else:
            return False

    def __hash__(self) -> int:
        return hash(nx.weisfeiler_lehman_graph_hash(self._graph))

    def __contains__(self, item: object) -> bool:
        if isinstance(item, ActionInstance):
            return any(item.is_semantically_equivalent(a) for a in self._graph.nodes)
        else:
            return False

    @property
    def get_adjacency_list(
        self,
    ) -> Dict["plans.plan.ActionInstance", List["plans.plan.ActionInstance"]]:
        """Returns the graph of action instances as an adjacency list."""
        return nx.convert.to_dict_of_lists(self._graph)

    def replace_action_instances(
        self,
        replace_function: Callable[
            ["plans.plan.ActionInstance"], "plans.plan.ActionInstance"
        ],
    ) -> "plans.plan.Plan":
        new_adj_list: Dict[
            "plans.plan.ActionInstance", List["plans.plan.ActionInstance"]
        ] = {}
        # Populate the new adjacency list with the replaced action instances
        for node in self._graph.nodes:
            new_adj_list[replace_function(node)] = [
                replace_function(successor) for successor in self._graph.neighbors(node)
            ]
        new_env = self._environment
        for ai in new_adj_list.keys():
            new_env = ai.action.env
            break
        return PartialOrderPlan(new_adj_list, new_env)

    def to_sequential_plan(self) -> SequentialPlan:
        """Returns one between all possible SequentialPlans that respects the ordering constaints given by this PartialOrderPlan."""
        return SequentialPlan(list(nx.topological_sort(self._graph)), self._environment)

    def all_sequential_plans(self) -> Iterator[SequentialPlan]:
        """Returns all possible SequentialPlans that respects the ordering constaints given by this PartialOrderPlan."""
        for sorted_plan in nx.all_topological_sorts(self._graph):
            yield SequentialPlan(list(sorted_plan), self._environment)

    def get_neighbors(
        self, action_instance: ActionInstance
    ) -> Iterator[ActionInstance]:
        try:
            retval = self._graph.neighbors(action_instance)
        except nx.NetworkXError:
            raise UPUsageError(
                f"The action instance {str(action_instance)} does not belong to this Partial Order Plan. \n Note that 2 Action Instances are equals if and only if they are the exact same object."
            )
        return retval


def _semantically_equivalent_action_instances(
    action_instance_1: ActionInstance, action_instance_2: ActionInstance
) -> bool:
    return action_instance_1.is_semantically_equivalent(action_instance_2)
