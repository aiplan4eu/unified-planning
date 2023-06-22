# Copyright 2021-2023 AIPlan4EU project
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
from collections import namedtuple

import unified_planning.plans
from unified_planning.plans import Schedule
from unified_planning.shortcuts import *
from unified_planning.model.scheduling import *


Example = namedtuple("Example", ["problem", "plan"])


def basic():
    pb = SchedulingProblem(name="sched:basic")

    Resource = UserType("Resource")
    r1 = pb.add_object("r1", Resource)
    r2 = pb.add_object("r2", Resource)
    g1 = pb.add_object("g1", Resource)
    # level (in {0,1}) of each `Resource` object
    lvl = pb.add_fluent("lvl", IntType(0, 1), default_initial_value=1, r=Resource)

    red = pb.add_fluent("red", BoolType(), r=Resource)
    pb.set_initial_value(red(r1), True)
    pb.set_initial_value(red(r2), True)
    pb.set_initial_value(red(g1), False)

    workers = pb.add_resource("workers", 4)
    machine1 = pb.add_resource("machine1", 1)
    machine2 = pb.add_resource("machine2", 1)

    a1 = pb.add_activity("a1", duration=3)
    a1.uses(workers)
    a1.uses(machine1)

    a2 = pb.add_activity("a2", duration=6)
    a2_r = a2.add_parameter("r", Resource)  # Resource to use: r in {r1, r2, g1}
    # restrict r to {r1, r2} (resources that satisfy red(_))
    pb.add_constraint(red(a2_r))
    a2.uses(workers)
    a2.uses(machine2)
    a2.uses(lvl(a2_r))

    pb.add_constraint(LT(a1.end, a2.start))

    # One worker is unavailable over [17, 25)
    pb.add_decrease_effect(17, workers, 1)
    pb.add_increase_effect(25, workers, 1)

    assignment = {a1.start: 1, a1.end: 4, a2.start: 5, a2.end: 11, a2_r: r1}
    solution = Schedule(assignment=assignment, activities=[a1, a2])  # type: ignore[arg-type]

    return Example(pb, solution)


def resource_set():
    def create_resource_set(name: str, capacity: int):
        # create n objects: one for each element in the resource set
        rtype = UserType(f"rset_{name}")
        for i in range(capacity):
            pb.add_object(f"{name}{i}", rtype)
        # create a fluent that will create a state-variable in [0,1] for each resource object
        fluent = pb.add_fluent(
            f"rset_{name}",
            typename=IntType(0, 1),
            resource=rtype,
            default_initial_value=1,
        )
        return fluent, rtype

    def use_resource_set(activity, resource_fluent, resource_object_type):
        # create a variable whose value will identify the resource object to use
        var = activity.add_parameter("used_resource_instance", resource_object_type)
        # use the resource pointed out by our variable
        activity.add_decrease_effect(activity.start, resource_fluent(var), 1)
        activity.add_increase_effect(activity.end, resource_fluent(var), 1)

    pb = SchedulingProblem(name="sched:resource_set")
    resource_set_fluent, resource_set_parameter_type = create_resource_set("R", 4)
    act = pb.add_activity("a", duration=10)
    use_resource_set(act, resource_set_fluent, resource_set_parameter_type)

    return Example(pb, None)


def non_numeric():
    pb = SchedulingProblem()
    busy = pb.add_fluent("busy", default_initial_value=False)

    def create_activiy(name: str) -> Activity:
        a = pb.add_activity(name, duration=5)
        a.add_condition(a.start, Not(busy))
        a.add_effect(a.start, busy, True)
        a.add_effect(a.end - 1, busy, False)
        return a

    a = create_activiy("a")
    b = create_activiy("b")

    sol = unified_planning.plans.Schedule(
        [a, b], {a.start: 0, a.end: 5, b.start: 5, b.end: 9}
    )

    return Example(pb, sol)


if __name__ == "__main__":
    print(resource_set().problem)
    print("=========")
    print(non_numeric().problem)
