# Copyright 2022 AIPlan4EU project
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

import unified_planning as up
import unified_planning.plans as plans
from unified_planning.exceptions import UPUsageError
from typing import Callable, Dict, Iterator, Optional, List, Set, Tuple, Deque
from collections import deque


class ContingentPlanNode:
    """This class represent a node in the tree representing a contingent plan."""

    def __init__(self, action_instance: "plans.plan.ActionInstance"):
        self._action_instance = action_instance
        self._children: List[
            Tuple[Dict["up.model.FNode", "up.model.FNode"], "ContingentPlanNode"]
        ] = []

    @property
    def action_instance(self) -> "plans.plan.ActionInstance":
        return self._action_instance

    @property
    def children(
        self,
    ) -> List[Tuple[Dict["up.model.FNode", "up.model.FNode"], "ContingentPlanNode"]]:
        return self._children

    @property
    def environment(self) -> "up.environment.Environment":
        return self._action_instance.action.environment

    def add_child(
        self,
        observation: Dict["up.model.FNode", "up.model.FNode"],
        node: "ContingentPlanNode",
    ):
        """Adds the given `ContingentPlanNode` as a new child for the given observation."""
        for k, v in observation.items():
            if not (
                k.environment == v.environment == node.environment == self.environment
            ):
                raise UPUsageError("Different environments can not be mixed.")
        self._children.append((observation, node))

    def replace_action_instances(
        self,
        replace_function: Callable[
            ["plans.plan.ActionInstance"], Optional["plans.plan.ActionInstance"]
        ],
    ) -> "ContingentPlanNode":
        """
        This method takes a function from `ActionInstance` to `ActionInstance`.
        If the returned `ActionInstance` is `None` it means that the `ActionInstance` should be removed.

        This method applies the given function to all the `ActionInstances` of the tree
        and returns an equivalent `ContingentPlanNode`.

        :param replace_function: The function from `ActionInstance` to `ActionInstance`.
        :return: The `ContingentPlanNode` in which every `ActionInstance` is modified by the given `replace_function`.
        """
        ai = replace_function(self._action_instance)
        if ai is not None:
            res = ContingentPlanNode(ai)
            for o, c in self._children:
                res.add_child(o, c.replace_action_instances(replace_function))
            return res
        else:
            assert (
                len(self._children) == 1
            ), "A SensingActionInstance can not be replaced by an empty Action."
            o, c = self._children[0]
            assert len(o) == 0
            return c.replace_action_instances(replace_function)

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, ContingentPlanNode):
            if not self._action_instance.is_semantically_equivalent(
                oth.action_instance
            ):
                return False
            if not len(self._children) == len(oth.children):
                return False
            for c in self._children:
                if c not in oth.children:
                    return False
            return True
        else:
            return False

    def __hash__(self) -> int:
        count: int = 0
        count += hash(self._action_instance.action) + hash(
            self._action_instance.actual_parameters
        )
        for o, c in self._children:
            count += hash(c)
            for k, v in o.items():
                count += hash(k) + hash(v)
        return count

    def __contains__(self, item: object) -> bool:
        if isinstance(item, plans.plan.ActionInstance):
            if item.is_semantically_equivalent(self._action_instance):
                return True
            for _, c in self._children:
                if item in c:
                    return True
            return False
        else:
            return False


class ContingentPlan(plans.plan.Plan):
    """Represents a contingent plan."""

    def __init__(
        self,
        root_node: Optional["ContingentPlanNode"] = None,
        environment: Optional["up.Environment"] = None,
    ):
        # if we have a specific environment or we don't have any actions
        if environment is not None or root_node is None:
            plans.plan.Plan.__init__(
                self, plans.plan.PlanKind.CONTINGENT_PLAN, environment
            )
        # If we don't have a specific environment and have at least 1 action, use the environment of the first action
        else:
            plans.plan.Plan.__init__(
                self,
                plans.plan.PlanKind.CONTINGENT_PLAN,
                root_node.action_instance.action.environment,
            )
        self._root_node = root_node

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, ContingentPlan) and self.environment == self.environment:
            return self.root_node == oth.root_node
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.root_node)

    def __str__(self) -> str:
        if self._root_node is None:
            return "ContingentPlan:\n  Actions:\n  Constraints:"
        em = self.environment.expression_manager
        nodes = list(visit_tree(self._root_node))
        # give an ID, starting from 0, to every Node in the Plan
        swap_couple = lambda x: (x[1], x[0])
        id: Dict[ContingentPlanNode, int] = dict(
            map(swap_couple, enumerate(visit_tree(self._root_node)))
        )
        convert_action_id = (
            lambda action_id: f"    {action_id[1]}) {action_id[0].action_instance}"
        )
        ret = ["ContingentPlan:", "  Actions:"]
        ret.extend(map(convert_action_id, id.items()))
        ret.append("  Constraints:")

        def handle_fluent(key_value):
            fluent, value = key_value
            ft = fluent.type
            if ft.is_bool_type() and value.is_true():
                return fluent
            elif ft.is_bool_type() and value.is_false():
                return em.Not(fluent)
            else:
                return em.Equals(fluent, value)

        def convert_node(node):
            node_id = id[node]
            node_res: List[str] = []
            for fluents, child in node.children:
                if fluents:
                    fluents_exp = em.And(map(handle_fluent, fluents.items()))
                    node_res.append(f"    {node_id} -> {id[child]} if {fluents_exp}")
                else:
                    node_res.append(f"    {node_id} -> {id[child]}")
            return "\n".join(node_res)

        ret.extend(map(convert_node, nodes))
        return "\n".join(ret)

    def __contains__(self, item: object) -> bool:
        if self.root_node is None:
            return False
        return item in self.root_node

    @property
    def root_node(self) -> Optional["ContingentPlanNode"]:
        """Returns the ContingentPlanNode."""
        return self._root_node

    def replace_action_instances(
        self,
        replace_function: Callable[
            ["plans.plan.ActionInstance"], Optional["plans.plan.ActionInstance"]
        ],
    ) -> "up.plans.plan.Plan":
        if self.root_node is None:
            return ContingentPlan(None, self._environment)
        new_root = self.root_node.replace_action_instances(replace_function)
        new_env = new_root.action_instance.action.environment
        return ContingentPlan(new_root, new_env)

    def convert_to(
        self,
        plan_kind: "plans.plan.PlanKind",
        problem: "up.model.AbstractProblem",
    ) -> "plans.plan.Plan":
        """
        This function takes a `PlanKind` and returns the representation of `self`
        in the given `plan_kind`. If the conversion does not make sense, raises
        an exception.

        :param plan_kind: The plan_kind of the returned plan.
        :param problem: The `Problem` of which this plan is referring to.
        :return: The plan equivalent to self but represented in the kind of
            `plan_kind`.
        """
        if plan_kind == self._kind:
            return self
        else:
            raise UPUsageError(f"{type(self)} can't be converted to {plan_kind}.")


def visit_tree(root_node: Optional[ContingentPlanNode]) -> Iterator[ContingentPlanNode]:
    """
    Method to visit all the Tree nodes once.

    :param root_node: The starting node of the tree.
    :return: The Iterator over all the Nodes in the tree.
    """
    stack: Deque[ContingentPlanNode] = deque()
    if root_node is not None:
        stack.append(root_node)
    already_visited: Set[ContingentPlanNode] = set()
    while stack:
        current_element: ContingentPlanNode = stack.popleft()
        if current_element not in already_visited:
            already_visited.add(current_element)
            get_second_element = lambda x: x[1]
            stack.extend(map(get_second_element, current_element.children))
            yield current_element
