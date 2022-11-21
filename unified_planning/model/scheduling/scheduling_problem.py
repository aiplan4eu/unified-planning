from collections import OrderedDict
from fractions import Fraction
from typing import Optional, List, Union, Dict

import unified_planning as up
from unified_planning.model import Type, Parameter, Timepoint, TimepointKind, Timing, Fluent, FNode


def todo():
    raise NotImplementedError


class SchedulingProblem(up.model.problem.Problem):
    """A scheduling problem shares most of its construct with a planning problem with the following differences:
       - there are no action in a scheduling problem
       - it defines a set of variables and timepoints over which constriants can be stated
       - it provides some shortcuts to deal with typical scheduling constructs (activities, resources, ...)
       """

    def __init__(
        self,
        name: Optional[str] = None,
        env: Optional["up.environment.Environment"] = None,
        *,
        initial_defaults: Dict[
            "up.model.types.Type",
            Union[
                "up.model.fnode.FNode",
                "up.model.object.Object",
                bool,
                int,
                float,
                Fraction,
            ],
        ] = {},
    ):
        super().__init__(name=name, env=env, initial_defaults=initial_defaults)
        self._variables: OrderedDict[str, Parameter] = OrderedDict()


    def _name_exists(self, name: str) -> bool:
        return name not in self._variables

    def add_variable(self, name: str, type: Type) -> Parameter:
        assert not self._name_exists(name)
        param = Parameter(name, type)
        self._variables[name] = param
        return param

    def add_activity(self, name: str, duration: Optional[int]) -> 'Activity':
        return Activity(name, duration, self)

    def add_resource(self, name: str, capacity: int) -> Fluent:
        """Declares a new resource: a numeric fluent in `[0, CAPACITY]` where capacity is the
        initial value of the fluent and denote the capacity of the resource."""
        type = self._env.type_manager.IntType(0, capacity)
        return self.add_fluent(name, type, default_initial_value=capacity)

    def enforce(self, contraint: FNode):
        """Enforce a boolean expression to be true in any solution"""
        todo()

    def add_effect(self, timing: 'up.model.timing.Timing', fluent: Union['up.model.fnode.FNode', 'up.model.fluent.Fluent'],
                   value: 'up.model.expression.Expression', condition: 'up.model.expression.BoolExpression' = True):
        todo()

    def add_increase_effect(self, timing: 'up.model.timing.Timing', fluent: Union['up.model.fnode.FNode', 'up.model.fluent.Fluent'],
                            value: 'up.model.expression.Expression', condition: 'up.model.expression.BoolExpression' = True):
        todo()

    def add_decrease_effect(self, timing: 'up.model.timing.Timing', fluent: Union['up.model.fnode.FNode', 'up.model.fluent.Fluent'],
                            value: 'up.model.expression.Expression', condition: 'up.model.expression.BoolExpression' = True):
        todo()


class Activity:
    """Activity is essentially an interval with start and end timing that facilitates defining constraints in the
    associated SchedulingProblem"""

    def __init__(self, name: str, duration: Optional[int], problem: SchedulingProblem):
        self._problem = problem
        start_tp = Timepoint(TimepointKind.START, container=name)
        self.start = Timing(0, start_tp)
        if duration is not None:
            self.end = Timing(duration, start_tp)
        else:
            self.end = Timing(0, Timepoint(TimepointKind.END, container=name))

    def uses(self, resource: Fluent, amount: int = 1):
        self._problem.add_decrease_effect(self.start, resource, amount)
        self._problem.add_increase_effect(self.end, resource, amount)


if __name__ == "__main__":
    from unified_planning.shortcuts import *
    pb = SchedulingProblem()

    workers = pb.add_resource("workers", 4)
    machine1 = pb.add_resource("machine1", 1)
    machine2 = pb.add_resource("machine2", 1)

    a1 = pb.add_activity("a1", duration=3)
    a1.uses(workers)
    a1.uses(machine1)

    a2 = pb.add_activity("a2", duration=6)
    a2.uses(workers)
    a2.uses(machine2)

    pb.enforce(LT(a1.end, a2.start))

    # One worker is unavailable over [17, 25)
    pb.add_decrease_effect(GlobalStartTiming(17), workers, 1)
    pb.add_increase_effect(GlobalStartTiming(25), workers, 1)


