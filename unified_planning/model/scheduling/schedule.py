from typing import Callable, Optional, List, Union, Dict

from unified_planning.model.expression import ConstantExpression
from unified_planning.environment import Environment
from unified_planning.model import AbstractProblem, Parameter, Timepoint, FNode
from unified_planning.model.scheduling import Activity
from unified_planning.plans import PlanKind, ActionInstance
from unified_planning.plans.plan import Plan

Variable = Union[Parameter, Timepoint]
Value = ConstantExpression


class Schedule(Plan):
    """Solution to a scheduling problem."""

    def __init__(
        self,
        assignment: Optional[Dict[Variable, Value]] = None,
        activities: Optional[List[Activity]] = None,
        environment: Optional["Environment"] = None,
    ):
        # Associate each variable (timepoint or parameter) of the problem to its value in the solution
        super().__init__(PlanKind.SCHEDULE, environment)

        self._assignment: Dict[Variable, FNode] = {}

        # All activities present in the solution
        self._activities: List[Activity] = []

        if assignment is not None:
            for var, val in assignment.items():
                self.set(var, val)

        if activities is not None:
            self._activities += activities

    def get(self, var: Variable) -> FNode:
        if var not in self.assignment:
            raise ValueError(f"Missing variable {var} in assignment")
        return self._assignment[var]

    def set(self, var: Variable, value: Value):
        (value,) = self.environment.expression_manager.auto_promote(value)
        self._assignment[var] = value

    def __repr__(self):
        return f"Schedule(activities={[a.name for a in self._activities]}, assignment={self._assignment})"

    def __str__(self):
        def start_time(a: Activity):
            return self.get(a.start).constant_value()

        s = ["Schedule:\n"]
        for a in sorted(self.activities, key=start_time):
            s.append("    [")
            s.append(str(self.get(a.start)))
            s.append(", ")
            s.append(str(self.get(a.end)))
            s.append("] ")
            s.append(a.name)
            if len(a.parameters) > 0:

                def fmt(p):
                    prefix = a.name + "."
                    assert p.name.startswith(prefix)
                    return f"{p.name[len(prefix):]}={self.get(p)}"

                s.append("(")
                s.append(", ".join(map(fmt, a.parameters)))
                s.append(")")
            s.append("\n")
        return "".join(s)

    def __hash__(self):
        h = sum(map(lambda a: hash(a.name), self.activities))
        h += sum(map(lambda kv: hash(kv[0]) + hash(kv[1]), self.assignment.items()))
        return h

    def __eq__(self, other):
        if not isinstance(other, Schedule):
            return False
        return (
            set(self.activities) == set(other.activities)
            and self.assignment == other.assignment
        )

    @property
    def assignment(self) -> Dict[Variable, FNode]:
        """Returns the an assignment of each variable of the problem to its value in the solution."""
        return self._assignment

    @property
    def activities(self) -> List[Activity]:
        """Returns the list of all activities that appear in the solution."""
        return self._activities

    def replace_action_instances(
        self, replace_function: Callable[[ActionInstance], Optional[ActionInstance]]
    ) -> "Plan":
        return self

    def convert_to(self, plan_kind: PlanKind, problem: AbstractProblem) -> "Plan":
        if plan_kind == PlanKind.SCHEDULE:
            return self
        else:
            raise ValueError(f"Schedule cannot be converted to {plan_kind.name}")
