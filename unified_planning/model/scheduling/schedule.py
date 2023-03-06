from dataclasses import dataclass
from typing import Callable, Optional, List, Union, Dict

from unified_planning.model.expression import ConstantExpression

from unified_planning.model import AbstractProblem, Parameter, Timepoint
from unified_planning.model.scheduling import Activity
from unified_planning.plans import PlanKind, ActionInstance

from unified_planning.plans.plan import Plan

Variable = Union[Parameter, Timepoint]
Value = ConstantExpression


@dataclass
class Schedule(Plan):

    # Associate each variable (timepoint or parameter) of the problem to its value in the solution
    assignment: Dict[Variable, Value]

    # All activities present in the solution
    activities: List[Activity]

    def get(self, var: Variable) -> Value:
        if var not in self.assignment:
            raise ValueError(f"Missing variable {var} in assignment")
        return self.assignment[var]

    def __repr__(self):

        s = []
        for a in self.activities:
            s.append("[")
            s.append(str(self.get(a.start)))
            s.append(", ")
            s.append(str(self.get(a.end)))
            s.append("] ")
            s.append(a.name)
            if len(a.parameters) > 0:
                s.append("(")
                s.append(", ".join(map(lambda p: str(self.get(p)), a.parameters)))
                s.append(")")
            s.append("\n")
        return "".join(s)

    def replace_action_instances(
        self, replace_function: Callable[[ActionInstance], Optional[ActionInstance]]
    ) -> "Plan":
        return self

    def convert_to(self, plan_kind: PlanKind, problem: AbstractProblem) -> "Plan":
        if plan_kind == PlanKind.SCHEDULE:
            return self
        else:
            raise ValueError(f"Schedule cannot be converted to {plan_kind.name}")
