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
from typing import Callable, Dict, Optional, List


class ContingentPlanNode:
    def __init__(
        self,
        action_instance: "plans.plan.ActionInstance",
        observation: Optional[
            Dict["up.model.fnode.FNode", "up.model.fnode.FNode"]
        ] = None,
    ):
        self.action_instance = action_instance
        self.observation = observation
        self.children: List["ContingentPlanNode"] = []

    def add_child(self, obj: "ContingentPlanNode"):
        self.children.append(obj)

    def replace_action_instances(
        self,
        replace_function: Callable[
            ["plans.plan.ActionInstance"], Optional["plans.plan.ActionInstance"]
        ],
    ) -> List["ContingentPlanNode"]:
        children: List["ContingentPlanNode"] = []
        for c in self.children:
            for child in c.replace_action_instances(replace_function):
                children.append(child)
        ai = replace_function(self.action_instance)
        if ai is not None:
            res = ContingentPlanNode(ai, self.observation)
            for child in children:
                res.add_child(child)
            return [res]
        else:
            return children

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, ContingentPlanNode):
            if not self.action_instance.is_semantically_equivalent(oth.action_instance):
                return False
            if not self.observation == oth.observation:
                return False
            if not self.children == oth.children:
                return False
            return True
        else:
            return False

    def __hash__(self) -> int:
        count: int = 0
        count += hash(self.action_instance.action) + hash(
            self.action_instance.actual_parameters
        )
        if self.observation is not None:
            for k, v in self.observation.items():
                count += hash(k) + hash(v)
        for c in self.children:
            count += hash(c)
        return count

    def __contains__(self, item: object) -> bool:
        if isinstance(item, plans.plan.ActionInstance):
            if item.is_semantically_equivalent(self.action_instance):
                return True
            for c in self.children:
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
        # if we have a specific env or we don't have any actions
        if environment is not None or root_node is None:
            plans.plan.Plan.__init__(
                self, plans.plan.PlanKind.CONTINGENT_PLAN, environment
            )
        # If we don't have a specific env and have at least 1 action, use the env of the first action
        else:
            plans.plan.Plan.__init__(
                self,
                plans.plan.PlanKind.CONTINGENT_PLAN,
                root_node.action_instance.action.env,
            )
        self._root_node = root_node

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, ContingentPlan) and self.environment == self.environment:
            return self.root_node == oth.root_node
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.root_node)

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
        new_nodes = self.root_node.replace_action_instances(replace_function)
        assert len(new_nodes) == 1
        new_root = new_nodes[0]
        new_env = new_root.action_instance.action.env
        return ContingentPlan(new_root, new_env)
