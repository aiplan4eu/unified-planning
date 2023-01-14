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
from typing import Callable, Dict, Optional, List, Tuple


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
        return self._action_instance.action.env

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
        new_root = self.root_node.replace_action_instances(replace_function)
        new_env = new_root.action_instance.action.env
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
