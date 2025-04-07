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
from unified_planning.shortcuts import *
from unified_planning.model.scheduling import *
from unified_planning.model.scheduling import SchedulingProblem, Activity
from typing import List, Tuple

# Text representation
MINI_FSP = """2   2   1
2   2   2   2   1   1    1   2   6
2   1   2   8   1   1   10
"""
MT06 = """6   6   1
6   1   3   1   1   1   3   1   2   6   1   4   7   1   6   3   1   5   6
6   1   2   8   1   3   5   1   5   10  1   6   10  1   1   10  1   4   4
6   1   3   5   1   4   4   1   6   8   1   1   9   1   2   1   1   5   7
6   1   2   5   1   1   5   1   3   5   1   4   3   1   5   8   1   6   9
6   1   3   9   1   2   3   1   5   5   1   6   4   1   1   3   1   4   1
6   1   2   3   1   4   3   1   6   9   1   1   10  1   5   4   1   3   1
"""

MT06_modified = """6   6   1
5   2   1   2   3   1   1   1   3   1   2   6   1   4   7   1   6   3
6   1   2   8   1   3   5   1   5   10  1   6   10  1   1   10  1   4   4
6   1   3   5   1   4   4   1   6   8   1   1   9   1   2   1   1   5   7
6   1   2   5   1   1   5   1   3   5   1   4   3   1   5   8   1   6   9
6   1   3   9   1   2   3   1   5   5   1   6   4   1   1   3   1   4   1
6   1   2   3   1   4   3   1   6   9   1   1   10  1   5   4   1   3   1
"""

MT10C1 = """10  11  1
10  2   1   29  11  29  1   2   78  1   3   9   1   4   36  1   5   49  1   6   11  1   7   62  1   8   56  1   9   44  1   10  21
10  2   1   43  11  43  1   3   90  1   5   75  1   10  11  1   4   69  1   2   28  1   7   46  1   6   46  1   8   72  1   9   30
10  1   2   91  2   1   85  11  85  1   4   39  1   3   74  1   9   90  1   6   10  1   8   12  1   7   89  1   10  45  1   5   33
10  1   2   81  1   3   95  2   1   71  11  71  1   5   99  1   7   9   1   9   52  1   8   85  1   4   98  1   10  22  1   6   43
10  1   3   14  2   1   6   11  6   1   2   22  1   6   61  1   4   26  1   5   69  1   9   21  1   8   49  1   10  72  1   7   53
10  1   3   84  1   2   2   1   6   52  1   4   95  1   9   48  1   10  72  2   1   47  11  47  1   7   65  1   5   6   1   8   25
10  1   2   46  2   1   37  11  37  1   4   61  1   3   13  1   7   32  1   6   21  1   10  32  1   9   89  1   8   30  1   5   55
10  1   3   31  2   1   86  11  86  1   2   46  1   6   74  1   5   32  1   7   88  1   9   19  1   10  48  1   8   36  1   4   79
10  2   1   76  11  76  1   2   69  1   4   76  1   6   51  1   3   85  1   10  11  1   7   40  1   8   89  1   5   26  1   9   74
10  1   2   85  2   1   13  11  13  1   3   61  1   7   7   1   9   64  1   10  76  1   6   47  1   4   52  1   5   90  1   8   45
"""


def parse_instance(instance: str):

    def ints(line: str) -> List[int]:
        return list(map(int, line.rstrip().split()))

    def int_matrix(lines) -> List[List[int]]:
        return list(map(ints, lines))

    lines = instance.splitlines()
    sizes = ints(lines.pop(0))
    num_jobs = sizes[0]
    num_machines = sizes[1]

    matrix = int_matrix(lines)
    assert num_jobs == len(matrix)

    jobs = []
    for job in matrix:
        num_tasks = job[0]
        i = 1
        tasks = [[] for t in range(num_tasks)]
        jobs.append(tasks)
        for t in range(num_tasks):
            machines = job[i]
            i += 1
            for m in range(machines):
                machine, processing_time = job[i : i + 2]

                tasks[t].append((processing_time, machine - 1))
                i += 2

    return jobs, num_machines


def create_scheduling_problem(instance: str, resource_encoding: bool=False) -> SchedulingProblem:
    """Encodes a Flexible Jobshop problem as a scheduling problems.
    Encoding can be in two styles:
        - resource (resource_encoding=True): model machine usage on numeric state variables
        - direct (resource_encoding=False): activities on the same machine are explicitly required not to overlap
    """
    jobs, num_machines = parse_instance(instance)

    problem = SchedulingProblem(f"sched:flexible-jobshop")
    machine_objects = []
    if resource_encoding:
        # create one resource per machine
        machine_objects = [
            problem.add_resource(f"m{i}", capacity=1) for i in range(num_machines)
        ]

    # list of all activites together with their machine index
    all_activities: List[Tuple[Activity, int]] = []

    for j, job in enumerate(jobs):
        task_activities: List[List[Activity]] = [[] for t in range(len(job))]
        for t, task in enumerate(job):
            for processing_time, machine in task:
                act = problem.add_activity(
                    f"job{j}_task{t}_machine{machine + 1}",
                    duration=processing_time,
                    optional=True,
                )
                if resource_encoding:
                    # state that the activity borrows the machine for its entire duration
                    act.uses(machine_objects[machine])
                task_activities[t].append(act)
                all_activities.append((act, machine))

            # precedence constraints
            if t > 0:
                prev_activities = task_activities[t - 1]
                for prev_act in prev_activities:
                    for act in task_activities[t]:
                        problem.add_constraint(
                            LE(prev_act.end, act.start),
                            scope=[prev_act.present, act.present],
                        )

            # exactly one activity constraint
            problem.add_constraint(Or(act.present for act in task_activities[t]))
            for i1, act1 in enumerate(task_activities[t]):
                for i2, act2 in enumerate(task_activities[t]):
                    if i1 > i2:
                        # act1.add_constraint(Not(act2.present))
                        # problem.add_constraint(Not(act2.present), scope=[act1.present])
                        # problem.add_constraint(Implies(act1.present, Not(act2.present)))
                        problem.add_constraint(Or(Not(act1.present), Not(act2.present)))

    if not resource_encoding:
        # Directly encode machine usage constraints as no overlaps between any two activities on the same machine
        for (a1, m1) in all_activities:
            for (a2, m2) in all_activities:
                if a1.name < a2.name and m1 == m2:
                    problem.add_constraint(Or(LE(a1.end, a2.start), LE(a2.end, a1.start)), scope=[a1.present, a2.present])

    problem.add_quality_metric(unified_planning.model.metrics.MinimizeMakespan())
    return problem


if __name__ == "__main__":

    pb = create_scheduling_problem(MT10C1, resource_encoding=False)
    print(pb)
    print(pb.kind)

    # # Export to protobuf for independent usage
    # from unified_planning.grpc.proto_writer import ProtobufWriter  # type: ignore[attr-defined]
    # pb_writer = ProtobufWriter()
    # problem_pb = pb_writer.convert(pb)
    # with open("/tmp/osched.upp", "wb") as file:
    #     file.write(problem_pb.SerializeToString())

    with OneshotPlanner(name="aries") as planner:
        res = planner.solve(pb)
        print(res)

    with AnytimePlanner(name="aries") as planner:
      for res in planner.get_solutions(pb):
        print(res)
