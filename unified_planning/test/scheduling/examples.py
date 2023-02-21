from collections import namedtuple

from unified_planning.shortcuts import *
from unified_planning.model.scheduling import *


Example = namedtuple("Example", ["problem", "plan"])


def basic():
    pb = SchedulingProblem(name="sched:basic")

    Resource = UserType("Resource")
    r1 = pb.add_object("r1", Resource)
    r2 = pb.add_object("r2", Resource)
    pb.add_fluent("lvl", IntType(0, 1), default_initial_value=1, r=Resource)

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
    pb.add_decrease_effect(17, workers, 1)
    pb.add_increase_effect(25, workers, 1)
    return Example(pb, None)


def resource_set():
    def create_resource_set(name: str, capacity: int):
        rtype = UserType(f"rset_{name}")
        for i in range(capacity):
            pb.add_object(f"{name}{i}", rtype)
        fluent = pb.add_fluent(
            f"rset_{name}",
            typename=IntType(0, 1),
            resource=rtype,
            default_initial_value=1,
        )
        return fluent, rtype

    def use_resource_set(activity, fluent, rtype):
        var = activity.add_parameter("used_resource_instance", rtype)
        activity.add_decrease_effect(activity.start, fluent(var), 1)
        activity.add_increase_effect(activity.end, fluent(var), 1)

    pb = SchedulingProblem(name="sched:resource_set")
    resource_set_fluent, resource_set_parameter_type = create_resource_set("R", 4)
    act = pb.add_activity("a", duration=10)
    use_resource_set(act, resource_set_fluent, resource_set_parameter_type)

    return Example(pb, None)


resource_set()
