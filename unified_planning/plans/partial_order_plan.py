# Copyright 2021-2023 AIPlan4EU project
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
from unified_planning.model.multi_agent.agent import Agent
import random


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
        """
        Constructs the PartialOrderPlan using the adjacency list representation.

        :param adjacency_list: The Dictionary representing the adjacency list for this PartialOrderPlan.
        :param environment: The environment in which the ActionInstances in the adjacency_list are created.
        :param _graph: The graph that is semantically equivalent to the adjacency_list.
            NOTE: This parameter is for internal use only and it's maintainance is not guaranteed by any means.
        :return: The created PartialOrderPlan.
        """
        # if we have a specific environment or we don't have any actions
        if environment is not None or not adjacency_list:
            plans.plan.Plan.__init__(
                self, plans.plan.PlanKind.PARTIAL_ORDER_PLAN, environment
            )
        # If we don't have a specific environment, use the environment of the first action
        else:
            assert len(adjacency_list) > 0
            for ai in adjacency_list.keys():
                plans.plan.Plan.__init__(
                    self, plans.plan.PlanKind.PARTIAL_ORDER_PLAN, ai.action.environment
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
            ):  # check that given environment and the environment in the actions is the same
                if ai_k.action.environment != self._environment:
                    raise UPUsageError(
                        "The environment given to the plan is not the same of the actions in the plan."
                    )
                for ai in ai_v_list:
                    if ai.action.environment != self._environment:
                        raise UPUsageError(
                            "The environment given to the plan is not the same of the actions in the plan."
                        )
            self._graph = nx.convert.from_dict_of_lists(
                adjacency_list, create_using=nx.DiGraph
            )

    def __repr__(self) -> str:
        return f"PartialOrderPlan({repr(self.get_adjacency_list)})"

    def __str__(self) -> str:
        ret = ["PartialOrderPlan:", "  actions:"]

        # give an ID, starting from 0, to every ActionInstance in the Plan
        swap_couple = lambda x: (x[1], x[0])
        id: Dict[ActionInstance, int] = dict(
            map(swap_couple, enumerate(nx.topological_sort(self._graph)))
        )
        convert_action_id = lambda action_id: f"    {action_id[1]}) {action_id[0]}"
        ret.extend(map(convert_action_id, id.items()))

        ret.append("  constraints:")
        adj_list = self.get_adjacency_list

        def convert_action_adjlist(action_adjlist):
            action = action_adjlist[0]
            adj_list = action_adjlist[1]
            get_id_as_str = lambda ai: str(id[ai])
            adj_list_str = " ,".join(map(get_id_as_str, adj_list))
            return f"    {id[action]} < {adj_list_str}"

        ret.extend(
            map(
                convert_action_adjlist,
                ((act, adj) for act, adj in adj_list.items() if adj),
            )
        )

        return "\n".join(ret)

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
            ["plans.plan.ActionInstance"], Optional["plans.plan.ActionInstance"]
        ],
    ) -> "plans.plan.Plan":
        """
        Returns a new `PartialOrderPlan` where every `ActionInstance` of the current plan is replaced using the given `replace_function`.

        :param replace_function: The function that applied to an `ActionInstance A` returns the `ActionInstance B`; `B`
            replaces `A` in the resulting `Plan`.
        :return: The `PartialOrderPlan` where every `ActionInstance` is replaced using the given `replace_function`.
        """
        # first replace all nodes and store the mapping, then use the mapping to
        # recreate the adjacency list representing the new graph
        # ai = action_instance
        original_to_replaced_ai: Dict[
            "plans.plan.ActionInstance", "plans.plan.ActionInstance"
        ] = {}
        for ai in self._graph.nodes:
            replaced_ai = replace_function(ai)
            if replaced_ai is not None:
                original_to_replaced_ai[ai] = replaced_ai

        new_adj_list: Dict[
            "plans.plan.ActionInstance", List["plans.plan.ActionInstance"]
        ] = {}

        # Populate the new adjacency list with the replaced action instances

        for ai in self._graph.nodes:
            replaced_ai = original_to_replaced_ai.get(ai, None)
            if replaced_ai is not None:
                replaced_ai = original_to_replaced_ai[ai]
                replaced_neighbors = []
                for successor in self._graph.neighbors(ai):
                    replaced_successor = original_to_replaced_ai.get(successor, None)
                    if replaced_successor is not None:
                        replaced_neighbors.append(replaced_successor)
                new_adj_list[replaced_ai] = replaced_neighbors

        new_env = self._environment
        for ai in new_adj_list.keys():
            new_env = ai.action.environment
            break
        return up.plans.PartialOrderPlan(new_adj_list, new_env)

    def convert_to(
        self,
        plan_kind: "plans.plan.PlanKind",
        problem: "up.model.AbstractProblem",
    ) -> "plans.plan.Plan":
        """
        This function takes a `PlanKind` and returns the representation of `self`
        in the given `plan_kind`. If the conversion does not make sense, raises
        an exception.

        For the conversion to `SequentialPlan`, returns one  all possible
        `SequentialPlans` that respects the ordering constraints given by
        this `PartialOrderPlan`.

        :param plan_kind: The plan_kind of the returned plan.
        :param problem: The `Problem` of which this plan is referring to.
        :return: The plan equivalent to self but represented in the kind of
            `plan_kind`.
        """
        if plan_kind == self._kind:
            return self
        elif plan_kind == plans.plan.PlanKind.SEQUENTIAL_PLAN:
            return SequentialPlan(
                list(nx.topological_sort(self._graph)), self._environment
            )
        else:
            raise UPUsageError(f"{type(self)} can't be converted to {plan_kind}.")

    def all_sequential_plans(self) -> Iterator[SequentialPlan]:
        """Returns all possible `SequentialPlans` that respects the ordering constraints given by this `PartialOrderPlan`."""
        for sorted_plan in nx.all_topological_sorts(self._graph):
            yield SequentialPlan(list(sorted_plan), self._environment)

    def get_neighbors(
        self, action_instance: ActionInstance
    ) -> Iterator[ActionInstance]:
        """
        Returns an `Iterator` over all the neighbors of the given `ActionInstance`.

        :param action_instance: The `ActionInstance` of which neighbors must be retrieved.
        :return: The `Iterator` over all the neighbors of the given `action_instance`.
        """
        try:
            retval = self._graph.neighbors(action_instance)
        except nx.NetworkXError:
            raise UPUsageError(
                f"The action instance {str(action_instance)} does not belong to this Partial Order Plan. \n Note that 2 Action Instances are equals if and only if they are the exact same object."
            )
        return retval

    def get_graph_file(self, file_name: str) -> str:
        adjacency_list = self.get_adjacency_list
        graphviz_out = self.GraphvizGenerator.create_graphviz_output(adjacency_list)
        with open(f"{file_name}.dot", "w") as f:
            f.write(graphviz_out)
        return graphviz_out

    class GraphvizGenerator:
        available_colors = [
            "firebrick2",
            "gold2",
            "cornflowerblue",
            "darkorange1",
            "darkgreen",
            "coral4",
            "darkviolet",
            "deeppink1",
            "deepskyblue4",
            "burlywood4",
            "gray32",
            "lightsteelblue4",
        ]
        random_color_counter = 0

        @classmethod
        def get_next_agent_color(cls) -> str:
            if cls.random_color_counter < len(cls.available_colors):
                color = cls.available_colors[cls.random_color_counter]
                cls.random_color_counter += 1
            else:
                # Se gli available_colors sono esauriti, genera un colore casuale
                color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
            return color

        @classmethod
        def create_graphviz_output(
            cls,
            adjacency_list: Dict[
                "plans.plan.ActionInstance", List["plans.plan.ActionInstance"]
            ],
        ) -> str:
            """
            Creates Graphviz output with colors for agents if present, otherwise without colors.

            :param adjacency_list: The adjacency list representing the partial order plan.
            :return: The Graphviz representation as a string.
            """
            for action_instance, _ in adjacency_list.items():
                if action_instance.agent is not None:
                    return cls._create_graphviz_output_with_agents(adjacency_list)
            return cls._create_graphviz_output_simple(adjacency_list)

        @classmethod
        def _create_graphviz_output_with_agents(
            cls,
            adjacency_list: Dict[
                "plans.plan.ActionInstance", List["plans.plan.ActionInstance"]
            ],
        ) -> str:
            agent_colors = {}
            graphviz_out = ""
            graphviz_out += "digraph {\n"

            # Scansione della adjacency_list per identificare gli agenti
            for start, end_list in adjacency_list.items():
                agent_name = start.agent
                if agent_name not in agent_colors:
                    # Generazione di un colore per l'agente
                    color = cls.get_next_agent_color()
                    agent_colors[agent_name] = color

            # Creazione del grafo con colori degli agenti
            for start, end_list in adjacency_list.items():
                agent_name = start.agent
                agent_color = agent_colors.get(agent_name, "black")
                graphviz_out += f'\t"{start}" [color="{agent_color}"]\n'
                for end in end_list:
                    graphviz_out += f'\t"{start}" -> "{end}"\n'

            # Creazione della legenda
            graphviz_out += "\t// Legenda\n"
            graphviz_out += "\t{\n"
            graphviz_out += "\t\trank = max;\n"
            graphviz_out += '\t\tlabel="Legenda";\n'
            graphviz_out += '\t\tlabelloc="b";\n'
            graphviz_out += '\t\trankdir="LR";\n'

            for agent_name, agent_color in agent_colors.items():
                if agent_name is not None and isinstance(agent_name, Agent):
                    graphviz_out += f'\t\t"{agent_name.name}" [shape=none, margin=0, label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"><TR><TD WIDTH="30" HEIGHT="30" ALIGN="CENTER" BGCOLOR="{agent_color}"></TD><TD>{agent_name.name}</TD></TR></TABLE>>];\n'

            graphviz_out += "\t}\n"
            graphviz_out += "}"

            return graphviz_out

        @classmethod
        def _create_graphviz_output_simple(
            cls,
            adjacency_list: Dict[
                "plans.plan.ActionInstance", List["plans.plan.ActionInstance"]
            ],
        ) -> str:
            """
            Creates Graphviz output without agents.

            :param adjacency_list: The adjacency list representing the partial order plan.
            :return: The Graphviz representation as a string.
            """
            graphviz_out = ""
            graphviz_out += "digraph {\n"
            for start, end_list in adjacency_list.items():
                for end in end_list:
                    graphviz_out += f'\t"{start}" -> "{end}"\n'
            graphviz_out += "}"
            return graphviz_out


def _semantically_equivalent_action_instances(
    action_instance_1: ActionInstance, action_instance_2: ActionInstance
) -> bool:
    return action_instance_1.is_semantically_equivalent(action_instance_2)
