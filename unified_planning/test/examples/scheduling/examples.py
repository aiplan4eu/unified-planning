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

import unified_planning.plans
from unified_planning.plans import Schedule
from unified_planning.shortcuts import *
from unified_planning.model.scheduling import *
from unified_planning.test import TestCase


def basic():
    pb = SchedulingProblem(name="sched:basic")

    machine1 = pb.add_resource("machine1", capacity=1)
    machine2 = pb.add_resource("machine2", capacity=1)
    workers = pb.add_resource("workers", capacity=4)

    a1 = pb.add_activity("a1", duration=20)
    a1.uses(machine1)
    a1.uses(workers, amount=2)

    a2 = pb.add_activity("a2", duration=20)
    a2.uses(machine2)
    a2.uses(workers, amount=2)

    # One worker is unavailable over [10, 17)
    pb.add_decrease_effect(10, workers, 1)
    pb.add_increase_effect(17, workers, 1)

    assignment = {a1.start: 0, a1.end: 20, a2.start: 17, a2.end: 37}
    solution = Schedule(assignment=assignment, activities=[a1, a2])  # type: ignore[arg-type]

    return TestCase(problem=pb, solvable=True, valid_plans=[solution])


def resource_set():
    def create_resource_set(name: str, capacity: int):
        # create n objects: one for each element in the resource set
        rtype = UserType(f"rset_{name}")
        objects = [pb.add_object(f"{name}{i}", rtype) for i in range(capacity)]
        # create a fluent that will create a state-variable in [0,1] for each resource object
        fluent = pb.add_fluent(
            f"rset_{name}",
            typename=IntType(0, 1),
            resource=rtype,
            default_initial_value=1,
        )
        return fluent, rtype, objects

    def use_resource_set(activity, resource_fluent, resource_object_type):
        # create a variable whose value will identify the resource object to use
        var = activity.add_parameter("used_resource_instance", resource_object_type)
        # use the resource pointed out by our variable
        activity.add_decrease_effect(activity.start, resource_fluent(var), 1)
        activity.add_increase_effect(activity.end, resource_fluent(var), 1)

    pb = SchedulingProblem(name="sched:resource_set")
    (rset_fluent, rset_parameter_type, rset_objects) = create_resource_set("R", 4)
    act = pb.add_activity("a", duration=10)
    use_resource_set(act, rset_fluent, rset_parameter_type)

    sol = unified_planning.plans.Schedule(
        [act],
        {
            act.start: 0,
            act.end: 10,
            act.get_parameter("used_resource_instance"): rset_objects[0],
        },
    )

    return TestCase(problem=pb, solvable=True, valid_plans=[sol])


def non_numeric():
    pb = SchedulingProblem(name="sched:symbolic")
    busy = pb.add_fluent("busy", default_initial_value=False)

    def create_activiy(name: str) -> Activity:
        a = pb.add_activity(name, duration=5)
        a.add_condition(a.start, Not(busy))
        a.add_effect(a.start + 1, busy, True)
        a.add_effect(a.end, busy, False)
        return a

    a = create_activiy("a")
    b = create_activiy("b")

    pb.add_constraint(LE(b.end, a.start))

    sol = unified_planning.plans.Schedule(
        [a, b], {a.start: 5, a.end: 10, b.start: 0, b.end: 5}
    )

    return TestCase(problem=pb, solvable=True, valid_plans=[sol])

def optional():
    pb = SchedulingProblem(name="sched:optional")
    busy = pb.add_fluent("busy", default_initial_value=False)

    def create_activiy(name: str) -> Activity:
        a = pb.add_activity(name, duration=5, optional=True)
        a.add_condition(a.start, Not(busy))
        a.add_effect(a.start + 1, busy, True)
        a.add_effect(a.end, busy, False)
        return a

    a = create_activiy("a")
    b = create_activiy("b")
    c = create_activiy("c")

    pb.add_constraint(LE(b.end, a.start), [a.present, b.present])
    pb.add_constraint(And(a.present, b.present))

    a.add_deadline(12)
    c.add_release_date(5)
    c.add_deadline(10)

    print(pb)

    sol = unified_planning.plans.Schedule(
        [a, b], {a.start: 5, a.end: 10, b.start: 0, b.end: 5}
    )
    print(sol)

    return TestCase(problem=pb, solvable=True, valid_plans=[sol])

def test_protobuf(problem):
    import unified_planning.grpc.generated.unified_planning_pb2 as up_pb2
    from unified_planning.grpc.proto_reader import ProtobufReader  # type: ignore[attr-defined]
    from unified_planning.grpc.proto_writer import ProtobufWriter  # type: ignore[attr-defined]

    pb_writer = ProtobufWriter()
    pb_reader = ProtobufReader()
    problem_pb = pb_writer.convert(problem)
    with open("/tmp/osched.upp", "wb") as file:
        file.write(problem_pb.SerializeToString())
    problem_up = pb_reader.convert(problem_pb)

    pb_features = set(
        [up_pb2.Feature.Name(feature) for feature in problem_pb.features]  # type: ignore[attr-defined]
    )
    assert set(problem.kind.features) == pb_features
    assert problem == problem_up

if __name__ == "__main__":
    # print(resource_set().problem)
    # print("=========")
    # print(non_numeric().problem)
    # print("=========")
    # print(optional().problem)
    pb = optional().problem
    test_protobuf(pb)
