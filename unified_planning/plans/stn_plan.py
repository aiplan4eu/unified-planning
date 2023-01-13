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


from numbers import Real
import unified_planning as up
import unified_planning.plans as plans
from unified_planning.environment import Environment
from unified_planning.exceptions import UPUsageError
from unified_planning.model import DeltaSimpleTemporalNetwork, TimepointKind
from unified_planning.plans.plan import ActionInstance
from fractions import Fraction
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Tuple, Union


@dataclass(unsafe_hash=True, frozen=True)
class STNPlanNode:
    """
    This class represents a node of the `STNPlan`.
    :param kind: The `TimepointKind` of this node, it can be `global`, referring
        to the `START` or the `END` of the `Plan` itself, or `not global`,
        representing the `START` or the `END` of the given `ActionInstance`.
    :param action_instance: Optionally, the `ActionInstance` that this node
        represents. If the `kind` is `global`, this field must be `None`.
    """

    kind: TimepointKind
    action_instance: Optional[ActionInstance] = None

    def __post_init___(self):
        if (
            self.kind in (TimepointKind.GLOBAL_START, TimepointKind.GLOBAL_END)
            and self.action_instance is not None
        ):
            raise UPUsageError(
                f"A global kind represents Start/End of the plan;",
                "the ActionInstance is not accepted.",
            )
        if (
            self.kind in (TimepointKind.START, TimepointKind.END)
            and self.action_instance is None
        ):
            raise UPUsageError(
                f"kind represents Start/End of an ActionInstance",
                "but the ActionInstance is not given.",
            )

    @property
    def environment(self) -> Optional[Environment]:
        if self.action_instance is not None:
            return self.action_instance.action.env
        return None


def iterate_over_dict(d: Dict[Any, Iterable[Tuple[Any]]]) -> Iterator[Any]:
    for k, v in d.items():
        for tup in v:
            yield (k, *tup)


class STNPlan(plans.plan.Plan):
    """Represents a partial order plan. Actions are represent as an adjacency list graph."""

    # TODO docum
    def __init__(
        self,
        constraints: Union[
            List[Tuple[STNPlanNode, Optional[Real], Optional[Real], STNPlanNode]],
            Dict[STNPlanNode, List[Tuple[Optional[Real], Optional[Real], STNPlanNode]]],
        ],
        environment: Optional["Environment"] = None,
    ):
        """
        Constructs the `STNPlan` with 2 different possible representations:
        one as a `List` of `Tuples`, where each `Tuple` contains: `STNPlanNode A`,
        the lower bound `L`, the upper bound `U` and the other `STNPlanNode B`

        the other one as a `Dict` from  `STNPlanNode A` to the `List` of `Tuples`,
        where each `Tuple` contains: the lower bound `L`, the upper bound `U`
        and the other `STNPlanNode B`.

        The semantic is the same for the 2 representations and the temporal
        constraints are represented like  `L <= Time(A) - Time(B)] <= U`, where
        `Time[STNPlanNode]` is the time in which the STNPlanNode happen.

        :param constraints: The data structure to create the STNPlan, explained
            in details above.
        :param environment: The environment in which the ActionInstances in the
            constraints are created.
        :return: The created STNPlan.
        """
        # if we have a specific env or we don't have any actions
        if environment is not None or not constraints:
            plans.plan.Plan.__init__(self, plans.plan.PlanKind.STN_PLAN, environment)
        # If we don't have a specific env, use the env of the first action
        elif isinstance(constraints, Dict):
            assert len(constraints) > 0
            env = None
            for k_node, l in constraints.items():
                if k_node.environment is not None:
                    env = k_node.environment
                else:
                    for _, _, v_node in l:
                        if v_node.environment is not None:
                            env = v_node.environment
                            break
                if env is not None:
                    break
            plans.plan.Plan.__init__(self, plans.plan.PlanKind.PARTIAL_ORDER_PLAN, env)
        else:
            assert isinstance(constraints, List), "Typing not respected"
            env = None
            for a_node, _, _, b_node in constraints:
                if a_node.environment is not None:
                    env = a_node.environment
                    break
                elif b_node.environment is not None:
                    env = b_node.environment
                    break
            plans.plan.Plan.__init__(self, plans.plan.PlanKind.PARTIAL_ORDER_PLAN, env)

        self._stn = DeltaSimpleTemporalNetwork()
        start_plan = STNPlanNode(TimepointKind.GLOBAL_START)
        end_plan = STNPlanNode(TimepointKind.GLOBAL_END)
        self._stn.insert_interval(start_plan, end_plan, left_bound=0)
        if isinstance(constraints, List):
            gen: Iterator[
                Tuple[STNPlanNode, Optional[Real], Optional[Real], STNPlanNode]
            ] = constraints
        else:
            assert isinstance(constraints, Dict), "Typing not respected"
            gen = iterate_over_dict(constraints)
        for a_node, lower_bound, upper_bound, b_node in gen:
            self._stn.insert_interval(start_plan, a_node, left_bound=0)
            self._stn.insert_interval(a_node, end_plan, left_bound=0)
            self._stn.insert_interval(start_plan, b_node, left_bound=0)
            self._stn.insert_interval(b_node, end_plan, left_bound=0)
            self._stn.insert_interval(
                a_node, b_node, left_bound=lower_bound, right_bound=upper_bound
            )

    def __repr__(self) -> str:
        pass  # TODO

    def __eq__(self, oth: object) -> bool:
        pass  # TODO

    def __hash__(self) -> int:
        pass  # TODO

    def __contains__(self, item: object) -> bool:
        # if isinstance(item, ActionInstance):
        #     return any(item.is_semantically_equivalent(a) for a in self._graph.nodes)
        # else:
        #     return False
        pass  # TODO

    def get_constraints(
        self,
    ) -> Dict[STNPlanNode, List[Tuple[Optional[Real], Optional[Real], STNPlanNode]]]:
        upper_bounds: Dict[Tuple[STNPlanNode, STNPlanNode], Real] = {}
        lower_bounds: Dict[Tuple[STNPlanNode, STNPlanNode], Real] = {}
        for b_node, l in self._stn.get_constraints().items():
            for upper_bound, a_node in l:
                if upper_bound >= 0:
                    upper_bounds[(a_node, b_node)] = upper_bound
                else:
                    lower_bounds[(a_node, b_node)] = -upper_bound
        constraints: Dict[
            Tuple[STNPlanNode, STNPlanNode], Tuple[Optional[Real], Optional[Real]]
        ] = {}
        for k, upper_bound in upper_bounds.items():
            lower_bound = lower_bounds.get(k, None)
            constraints[k] = (lower_bound, upper_bound)
        for k, lower_bound in lower_bounds.items():
            if k not in upper_bounds:
                constraints[k] = (lower_bound, None)

        ret_map: Dict[
            STNPlanNode, List[Tuple[Optional[Real], Optional[Real], STNPlanNode]]
        ] = {}
        for (a_node, b_node), (lower_bound, upper_bound) in constraints.items():
            a_node_constraints = ret_map.setdefault(a_node, [])
            a_node_constraints.append((lower_bound, upper_bound, b_node))
        return ret_map

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
        pass  # TODO

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
        else:
            raise UPUsageError(f"{type(self)} can't be converted to {plan_kind}.")
