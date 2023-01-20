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


from itertools import product
from numbers import Real
import unified_planning as up
import unified_planning.plans as plans
from unified_planning.environment import Environment
from unified_planning.exceptions import UPUsageError
from unified_planning.model import DeltaSimpleTemporalNetwork, TimepointKind
from unified_planning.plans.plan import ActionInstance
from fractions import Fraction
from dataclasses import dataclass
from typing import (
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)


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

    def __repr__(self) -> str:
        mappings: Dict[TimepointKind, str] = {
            TimepointKind.GLOBAL_START: "START PLAN",
            TimepointKind.GLOBAL_END: "END PLAN",
            TimepointKind.START: "START ACTION",
            TimepointKind.END: "END ACTION",
        }
        res: List[str] = []
        res.append(mappings[self.kind])
        if self.action_instance is not None:
            res.append(str(self.action_instance))
        return " ".join(res)

    @property
    def environment(self) -> Optional[Environment]:
        if self.action_instance is not None:
            return self.action_instance.action.env
        return None


def flatten_dict_structure(
    d: Dict[STNPlanNode, List[Tuple[Optional[Real], Optional[Real], STNPlanNode]]]
) -> Iterator[Tuple[STNPlanNode, Optional[Real], Optional[Real], STNPlanNode]]:
    """
    This method takes a dict containing a List of tuples of 3 elements, and
    returns an Iterator of Tuples of 4 elements, where the first one is the key
    and the other 3 are the elements in the list.

    :param d: The dictionary to flatten.
    """
    for k, v in d.items():
        if not v:
            yield (k, None, None, k)
        for tup in v:
            yield (k, *tup)


class STNPlan(plans.plan.Plan):
    """
    Represents a `STNPlan`. A Simple Temporal Network plan is a generalization of
    a `TimeTriggeredPlan`, where the only constraints are among the start and the
    end of the different `ActionInstances` or among the `start` and the `end` of the
    plan.

    An `STNPlan` is consistent if exists a time assignment for each `STNPlanNode`
    that does not violate any constraint; otherwise the `STNPlan` is inconsistent.
    """

    def __init__(
        self,
        constraints: Union[
            List[Tuple[STNPlanNode, Optional[Real], Optional[Real], STNPlanNode]],
            Dict[STNPlanNode, List[Tuple[Optional[Real], Optional[Real], STNPlanNode]]],
        ],
        environment: Optional["Environment"] = None,
        _stn: Optional[DeltaSimpleTemporalNetwork[Fraction]] = None,
    ):
        """
        Constructs the `STNPlan` with 2 different possible representations:
        one as a `List` of `Tuples`, where each `Tuple` contains: `STNPlanNode A`,
        the lower bound `L`, the upper bound `U` and the other `STNPlanNode B`

        the other one as a `Dict` from  `STNPlanNode A` to the `List` of `Tuples`,
        where each `Tuple` contains: the lower bound `L`, the upper bound `U`
        and the other `STNPlanNode B`.

        The semantic is the same for the 2 representations and the temporal
        constraints are represented like  `L <= Time(A) - Time(B) <= U`, where
        `Time[STNPlanNode]` is the time in which the STNPlanNode happen.

        :param constraints: The data structure to create the `STNPlan`, explained
            in details above.
        :param environment: The environment in which the `ActionInstances` in the
            constraints are created; this parameters is ignored if there is
            another environment in the action instances given in the constraints.
        :param _stn: Internal parameter, not to be used!
        :return: The created `STNPlan`.
        """
        assert (
            _stn is None or not constraints
        ), "_stn and constraints can't be both given"
        # if we have a specific env or we don't have any actions
        env = environment
        if (env is not None or not constraints) and _stn is None:
            plans.plan.Plan.__init__(self, plans.plan.PlanKind.STN_PLAN, env)
        # If we don't have a specific env, use the env of the first action
        elif _stn is not None:
            for r_node, cl in _stn.get_constraints().items():
                assert isinstance(r_node, STNPlanNode), "Given _stn is wrong"
                if r_node.environment is not None:
                    env = r_node.environment
                else:
                    for _, l_node in cl:
                        assert isinstance(l_node, STNPlanNode), "Given _stn is wrong"
                        if l_node.environment is not None:
                            env = l_node.environment
                            break
                if env is not None:
                    break
            plans.plan.Plan.__init__(self, plans.plan.PlanKind.STN_PLAN, env)
            self._stn: DeltaSimpleTemporalNetwork[Fraction] = _stn
            return
        elif isinstance(constraints, Dict):
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
            plans.plan.Plan.__init__(self, plans.plan.PlanKind.STN_PLAN, env)
        else:
            assert isinstance(constraints, List), "Typing not respected"
            for a_node, _, _, b_node in constraints:
                if a_node.environment is not None:
                    env = a_node.environment
                    break
                elif b_node.environment is not None:
                    env = b_node.environment
                    break
            plans.plan.Plan.__init__(self, plans.plan.PlanKind.STN_PLAN, env)

        # Create and populate the DeltaSTN
        self._stn = DeltaSimpleTemporalNetwork()
        start_plan = STNPlanNode(TimepointKind.GLOBAL_START)
        end_plan = STNPlanNode(TimepointKind.GLOBAL_END)
        self._stn.insert_interval(start_plan, end_plan, left_bound=Fraction(0))
        if isinstance(constraints, List):
            gen: Iterator[
                Tuple[STNPlanNode, Optional[Real], Optional[Real], STNPlanNode]
            ] = iter(constraints)
        else:
            assert isinstance(constraints, Dict), "Typing not respected"
            gen = flatten_dict_structure(constraints)
        f0 = Fraction(0)
        for a_node, lower_bound, upper_bound, b_node in gen:
            if (
                a_node.environment is not None
                and a_node.environment != self._environment
            ) or (
                b_node.environment is not None
                and b_node.environment != self._environment
            ):
                raise UPUsageError(
                    "Different environments given inside the same STNPlan!"
                )
            self._stn.insert_interval(start_plan, a_node, left_bound=f0)
            self._stn.insert_interval(a_node, end_plan, left_bound=f0)
            self._stn.insert_interval(start_plan, b_node, left_bound=f0)
            self._stn.insert_interval(b_node, end_plan, left_bound=f0)
            lb = None if lower_bound is None else Fraction(float(lower_bound))
            ub = None if upper_bound is None else Fraction(float(upper_bound))
            self._stn.insert_interval(a_node, b_node, left_bound=lb, right_bound=ub)

    def __repr__(self) -> str:
        return str(self._stn)

    # def __eq__(self, oth: object) -> bool:
    #     pass  # TODO

    # def __hash__(self) -> int:
    #     pass  # TODO

    def __contains__(self, item: object) -> bool:
        if isinstance(item, ActionInstance):
            return any(
                n.action_instance is not None
                and item.is_semantically_equivalent(n.action_instance)
                for n in self._stn.distances
            )
        else:
            return False

    def get_constraints(
        self,
    ) -> Dict[
        STNPlanNode, List[Tuple[Optional[Fraction], Optional[Fraction], STNPlanNode]]
    ]:
        """
        Returns all the constraints given by this `STNPlan`. Subsumed constraints
        are removed, this means that the constraints returned by this method are
        only the stricter.

        The mapping returned is from the node `A` to the `List` of  `Tuple`
        containing `lower_bound L`, `upper_bound U` and the node `B`.
        The semantic is `L <= Time(A) - Time(B) <= U`, where `Time[STNPlanNode]`
        is the time in which the `STNPlanNode` happen. `L` or `U` can be `None`,
        this means that the lower/upper bound is not set.
        """
        upper_bounds: Dict[Tuple[STNPlanNode, STNPlanNode], Fraction] = {}
        lower_bounds: Dict[Tuple[STNPlanNode, STNPlanNode], Fraction] = {}
        for b_node, l in self._stn.get_constraints().items():
            for upper_bound, a_node in l:
                if upper_bound > 0:
                    # Sets the upper bound for b-a; b-a is represented as the
                    # Tuple[smaller_node, bigger_node], so it is (a, b).
                    key = (a_node, b_node)
                    upper_bounds[key] = min(
                        upper_bound, upper_bounds.get(key, upper_bound)
                    )
                else:
                    # If the bound is negative, it is represented as a lower bound for a-b
                    # instead of an upper bound for b-a (b-a <= x) -> (a-b >= -x)
                    key = (b_node, a_node)
                    lower_bounds[key] = max(
                        -upper_bound, lower_bounds.get(key, -upper_bound)
                    )
        constraints: Dict[
            STNPlanNode,
            List[Tuple[Optional[Fraction], Optional[Fraction], STNPlanNode]],
        ] = {}
        seen_couples: Set[Tuple[STNPlanNode, STNPlanNode]] = set()
        for (left_node, right_node), upper_bound in upper_bounds.items():
            key = (left_node, right_node)
            seen_couples.add(key)
            lower_bound = lower_bounds.get(key, None)
            cl = constraints.setdefault(left_node, [])
            cl.append((lower_bound, upper_bound, right_node))
        for (left_node, right_node), lower_bound in lower_bounds.items():
            key = (left_node, right_node)
            if key not in seen_couples:
                seen_couples.add(key)
                cl = constraints.setdefault(left_node, [])
                cl.append((lower_bound, None, right_node))
        return constraints

    def replace_action_instances(
        self,
        replace_function: Callable[
            ["plans.plan.ActionInstance"], Optional["plans.plan.ActionInstance"]
        ],
    ) -> "plans.plan.Plan":
        """
        Returns a new `STNPlan` where every `ActionInstance` of the current plan is replaced using the given `replace_function`.

        :param replace_function: The function that applied to an `ActionInstance A` returns the `ActionInstance B`; `B`
            replaces `A` in the resulting `Plan`.
        :return: The `STNPlan` where every `ActionInstance` is replaced using the given `replace_function`.
        """
        replaced_action_instances: Dict[ActionInstance, Optional[ActionInstance]] = {}
        replaced_nodes: Dict[STNPlanNode, STNPlanNode] = {}
        nodes_to_remove: Set[STNPlanNode] = set()
        for node in self._stn.distances:
            assert isinstance(node, STNPlanNode)
            ai = node.action_instance
            if ai is None:
                replaced_nodes[node] = node
                continue
            replaced_ai = replaced_action_instances.setdefault(ai, replace_function(ai))
            if replaced_ai is None:
                nodes_to_remove.add(node)
                replaced_nodes[node] = node
            else:
                replaced_nodes[node] = STNPlanNode(node.kind, replaced_ai)

        stn_constraints = self._stn.get_constraints()

        # right_nodes are the nodes to the right of the nodes that must be remove.
        right_nodes: Dict[STNPlanNode, Set[Tuple[STNPlanNode, Fraction]]] = {}
        left_nodes: Dict[STNPlanNode, Set[Tuple[STNPlanNode, Fraction]]] = {}
        new_constraints: Dict[STNPlanNode, List[Tuple[Fraction, STNPlanNode]]] = {}
        for r_node, constraints in stn_constraints.items():
            replaced_r_node = replaced_nodes[r_node]
            new_rrn_constraints: List[
                Tuple[Fraction, STNPlanNode]
            ] = []  # rrn = replaced_right_node
            # the nodes added on left_nodes_set are on the left of the current node
            left_nodes_set: Optional[Set[Tuple[STNPlanNode, Fraction]]] = (
                left_nodes.setdefault(replaced_r_node, set())
                if replaced_r_node in nodes_to_remove
                else None
            )
            for bound, l_node in constraints:
                replaced_l_node = replaced_nodes[l_node]
                if left_nodes_set is not None:
                    left_nodes_set.add((replaced_l_node, bound))
                if replaced_l_node in nodes_to_remove:
                    right_nodes.setdefault(replaced_l_node, set()).add(
                        (replaced_r_node, bound)
                    )
                new_rrn_constraints.append((bound, replaced_l_node))
            new_constraints[replaced_r_node] = new_rrn_constraints

        for ntr in nodes_to_remove:
            left_nodes_set = left_nodes.get(ntr, set())
            assert left_nodes_set is not None
            right_nodes_set = right_nodes.get(ntr, set())
            for (l_node, l_dist), (r_node, r_dist) in product(
                left_nodes_set, right_nodes_set
            ):
                r_node_constraints = new_constraints.setdefault(r_node, [])
                sum_dist = l_dist + r_dist
                r_node_constraints.append((sum_dist, l_node))
                if l_node in nodes_to_remove:
                    right_nodes.setdefault(l_node, set()).add((r_node, sum_dist))
                if r_node in nodes_to_remove:
                    left_nodes.setdefault(r_node, set()).add((l_node, sum_dist))

        new_stn: DeltaSimpleTemporalNetwork = DeltaSimpleTemporalNetwork()
        for r_node, constraints in new_constraints.items():
            if not r_node in nodes_to_remove:
                for bound, l_node in constraints:
                    if not l_node in nodes_to_remove:
                        new_stn.add(r_node, l_node, bound)

        return STNPlan(constraints={}, environment=self._environment, _stn=new_stn)

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
        elif plan_kind == plans.plan.PlanKind.TIME_TRIGGERED_PLAN:
            raise NotImplementedError
        else:
            raise UPUsageError(f"{type(self)} can't be converted to {plan_kind}.")

    def is_consistent(self) -> bool:
        """
        Returns True if if exists a time assignment for each STNPlanNode that
        does not violate any constraint; False otherwise.
        """
        return self._stn.check_stn()
