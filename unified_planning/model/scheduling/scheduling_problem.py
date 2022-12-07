from collections import OrderedDict
from fractions import Fraction
from typing import Optional, List, Union, Dict

import unified_planning as up
from unified_planning.model import Type, Parameter, Timepoint, TimepointKind, Timing, Fluent, FNode, TimeInterval
from unified_planning.model.scheduling.activity import Activity
from unified_planning.model.scheduling.chronicle import Chronicle


def todo():
    raise NotImplementedError




class SchedulingProblem(up.model.problem.Problem):
    """A scheduling problem shares most of its construct with a planning problem with the following differences:
       - there are no action in a scheduling problem
       - it defines a set of variables and timepoints over which constraints can be stated
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

        self._base: Chronicle = Chronicle(":", _env=env)
        self._activities: List[Activity] = []

    def __repr__(self) -> str:
        s = [super().__repr__()]
        s.append("\nBASE")
        s.append(str(self._base))

        s.append("\nActivities:\n  ")
        for act in self._activities:
            s.append(str(act))
            s.append("\n  ")

        return "".join(s)

    def _name_exists(self, name: str) -> bool:
        return name in self._base._parameters

    def add_variable(self, name: str, tpe: Type) -> Parameter:
        assert not self._name_exists(name)
        param = Parameter(name, tpe)
        self._base._parameters[name] = param
        return param

    def add_activity(self, name: str, duration: Optional[int]) -> 'Activity':
        act = Activity(name=name, duration=duration)
        self._activities.append(act)
        return act

    def add_resource(self, name: str, capacity: int = 1) -> Fluent:
        """Declares a new resource: a numeric fluent in `[0, CAPACITY]` where capacity is the
        initial value of the fluent and denote the capacity of the resource."""
        tpe = self._env.type_manager.IntType(0, capacity)
        return self.add_fluent(name, tpe, default_initial_value=capacity)

    def add_constraint(self, constraint: Union[
                "up.model.fnode.FNode",
                "up.model.fluent.Fluent",
                "up.model.parameter.Parameter",
                bool,
            ]):
        """Enforce a boolean expression to be true in any solution"""
        self._base.add_constraint(constraint)

    def add_condition(self, span: TimeInterval, condition: FNode):
        self._base.add_condition(span, condition)

    def add_effect(self, timing: 'up.model.timing.Timing', fluent: Union['up.model.fnode.FNode', 'up.model.fluent.Fluent'],
                   value: 'up.model.expression.Expression', condition: 'up.model.expression.BoolExpression' = True):
        self._base.add_effect(timing, fluent, value, condition)

    def add_increase_effect(self, timing: 'up.model.timing.Timing', fluent: Union['up.model.fnode.FNode', 'up.model.fluent.Fluent'],
                            value: 'up.model.expression.Expression', condition: 'up.model.expression.BoolExpression' = True):
        self._base.add_increase_effect(timing, fluent, value, condition)

    def add_decrease_effect(self, timing: 'up.model.timing.Timing', fluent: Union['up.model.fnode.FNode', 'up.model.fluent.Fluent'],
                            value: 'up.model.expression.Expression', condition: 'up.model.expression.BoolExpression' = True):
        self._base.add_decrease_effect(timing, fluent, value, condition)


if __name__ == "__main__":
    from unified_planning.shortcuts import *
    pb = SchedulingProblem()

    Resource = UserType("Resource")
    r1 = pb.add_object("r1", Resource)
    r2 = pb.add_object("r2", Resource)
    pb.add_fluent("lvl", IntType(0,1), default_initial_value=1, r=Resource)

    red = pb.add_fluent("red", BoolType(), r=Resource)
    pb.set_initial_value(red(r1), True)
    pb.set_initial_value(red(r2), True)

    workers = pb.add_resource("workers", 4)
    machine1 = pb.add_resource("machine1", 1)
    machine2 = pb.add_resource("machine2", 1)

    a1 = pb.add_activity("a1", duration=3)
    a1.uses(workers)
    a1.uses(machine1)

    a2 = pb.add_activity("a2", duration=6)
    a2_r = a2.add_parameter("r", Resource)
    pb.add_constraint(red(a2_r))
    a2.uses(workers)
    a2.uses(machine2)

    pb.add_constraint(LT(a1.end, a2.start))

    # One worker is unavailable over [17, 25)
    pb.add_decrease_effect(GlobalStartTiming(17), workers, 1)
    pb.add_increase_effect(GlobalStartTiming(25), workers, 1)

    # red = predicate("red")
    # r1 = Resource()
    # r2 = Resource()
    #
    # red(r1);
    # red(r3)
    #
    # lvl = Fluent("lvl", r=Resource, [0,1])
    #
    #
    # dvar r_of_a1: Resource
    # red(r_of_a1) == true
    # at start(a1)    lvl(r_of_a1) decrease by 1

    print(pb)
