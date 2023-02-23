from dataclasses import dataclass, field
from typing import Union, Dict, Optional, Tuple, List, OrderedDict, Callable

from unified_planning.model.abstract_problem import AbstractProblem

from unified_planning.exceptions import UPUsageError
from unified_planning.model.fnode import FNode
from unified_planning.plans.time_triggered_plan import TimeTriggeredPlan
from unified_planning.plans.sequential_plan import SequentialPlan
from unified_planning.plans.plan import Plan, PlanKind
from unified_planning.model.htn import Method
from unified_planning.plans.plan import ActionInstance


FlatPlan = Union[SequentialPlan, TimeTriggeredPlan]


@dataclass
class Decomposition:
    """A decomposition associates each of a set of task identifiers to either a method or an action that achieves it."""

    subtasks: Dict[str, Union["MethodInstance", ActionInstance]] = field(
        default_factory=dict
    )

    def __repr__(self):
        s = []
        for id, dec in self.subtasks.items():
            s.append(id)
            s.append(" -> ")
            s.append(str(dec).replace("\n", "\n  "))  # indent
            s.append("\n")
        if len(s) > 0:
            s.pop(-1)  # remove last line break
        return "".join(s)

    def _accumulate_instances(
        self,
        id_prefix: str,
        out: List[Tuple[str, Union["MethodInstance", ActionInstance]]],
    ):
        for id, dec in self.subtasks.items():
            if isinstance(dec, ActionInstance):
                out.append((f"{id_prefix}{id}", dec))
            else:
                assert isinstance(dec, MethodInstance)
                method_id = f"{id_prefix}{id}::{dec.method.name}"
                out.append((method_id, dec))
                dec.decomposition._accumulate_instances(method_id + "::", out)

    def _replace_action_instances(
        self, replace_function: Callable[[ActionInstance], Optional[ActionInstance]]
    ) -> "Decomposition":
        def replace(instance):
            if isinstance(instance, ActionInstance):
                rep = replace_function(instance)
                if rep is None:
                    raise UPUsageError(
                        "Cannot remove an action from a hierarchical plan"
                    )
                return rep
            else:
                assert isinstance(instance, MethodInstance)
                return instance._replace_action_instances(replace_function)

        return Decomposition(
            {task: replace(dec) for task, dec in self.subtasks.items()}
        )


@dataclass
class MethodInstance:
    """An instantiation of a method, including its parameter and a decomposition for each of its subtasks."""

    method: Method
    parameters: Dict[str, FNode]
    decomposition: "Decomposition" = Decomposition()

    def __repr__(self):
        params = [self.parameters[p.name] for p in self.method.parameters]
        return (
            f"{self.method.name}({', '.join(map(str, params))})\n{self.decomposition}"
        )

    def _replace_action_instances(
        self, replace_function: Callable[[ActionInstance], Optional[ActionInstance]]
    ) -> "MethodInstance":
        return MethodInstance(
            self.method,
            self.parameters,
            self.decomposition._replace_action_instances(replace_function),
        )


class HierarchicalPlan(Plan):
    """A `HierarchicalPlan` represents a solution to a `HierarchicalProblem`.
    It provides the combination of a "flat plan" a set of action with ordering information,
    and for each task in the initial task network, its decomposition into methods and primitive actions.
    """

    def __init__(self, flat_plan: FlatPlan, decomposition: Decomposition):
        super().__init__(PlanKind.HIERARCHICAL_PLAN)
        self._flat_plan = flat_plan
        self._decomposition = decomposition

    @property
    def decomposition(self) -> Decomposition:
        """The decomposition of the initial task network."""
        return self._decomposition

    @property
    def action_plan(self) -> FlatPlan:
        """A flat plan that contains hierarchical information."""
        return self._flat_plan

    def _instances(self) -> List[Tuple[str, Union["MethodInstance", ActionInstance]]]:
        out: List[Tuple[str, Union["MethodInstance", ActionInstance]]] = []
        self.decomposition._accumulate_instances("", out)
        return out

    def actions(self) -> List[Tuple[str, ActionInstance]]:
        """Returns a list of all actions in the plan, together with a unique and stable identifier."""
        return list(
            filter(lambda ins: isinstance(ins[1], ActionInstance), self._instances())  # type: ignore[arg-type]
        )

    def methods(self) -> List[Tuple[str, MethodInstance]]:
        """Returns a list of all methods in the plan, together with a unique and stable identifier."""
        return list(
            filter(lambda ins: isinstance(ins[1], MethodInstance), self._instances())  # type: ignore[arg-type]
        )

    def replace_action_instances(
        self, replace_function: Callable[[ActionInstance], Optional[ActionInstance]]
    ) -> "Plan":
        decomposition = self._decomposition._replace_action_instances(replace_function)
        flat_plan = self._flat_plan.replace_action_instances(replace_function)
        assert isinstance(flat_plan, (SequentialPlan, TimeTriggeredPlan))

        return HierarchicalPlan(flat_plan, decomposition)

    def convert_to(self, plan_kind: PlanKind, problem: AbstractProblem) -> "Plan":
        if plan_kind == PlanKind.HIERARCHICAL_PLAN:
            return self
        elif plan_kind in [PlanKind.SEQUENTIAL_PLAN, PlanKind.TIME_TRIGGERED_PLAN]:
            # NOTE: we cannot rely on automatic conversion to PARTIAL_ORDER_PLAN or STN_PLAN
            #       because, the hierarchy induces constraints on action orders that would not be accounted for
            #       by translators only aware of the flat structure
            return self._flat_plan.convert_to(plan_kind, problem)
        else:
            raise NotImplementedError(
                f"Unavailable conversion from hierarchical plan to {plan_kind.name}"
            )
