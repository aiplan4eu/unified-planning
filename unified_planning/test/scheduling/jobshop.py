from unified_planning.shortcuts import *
from unified_planning.model.scheduling import *

# Text representation of the FT-O6 instance (Fisher and Thompson)
instance_name = "ft06"
instance = """nb_jobs nb_machines
6 6 0 0 0 0
Times
1 3 6 7 3 6
8 5 10 10 10 4
5 4 8 9 1 7
5 5 5 3 8 9
9 3 5 4 3 1
3 3 9 10 4 1
Machines
3 1 2 4 6 5
2 3 5 6 1 4
3 4 6 1 2 5
2 1 3 4 5 6
3 2 5 6 1 4
2 4 6 1 5 3
"""

lines = instance.splitlines()

def ints(line: str) -> List[int]:
    return list(map(int, line.rstrip().split()))
def int_matrix(lines) -> List[List[int]]   :
    return list(map(ints, lines))


header = lines.pop(0)
sizes = ints(lines.pop(0))
num_jobs = sizes[0]
num_machines = sizes[1]

first_times_line = 1
last_times_line = first_times_line + num_jobs - 1
times = int_matrix(lines[first_times_line:last_times_line +1])
print("Times: ", times)


first_machine_line = last_times_line + 2
last_machine_line = first_machine_line + num_jobs - 1
machines = int_matrix(lines[first_machine_line:last_machine_line+1])
print("Machines: ", machines)

problem = unified_planning.model.scheduling.SchedulingProblem(f'jobshop-{instance_name}')
machine_objects =[problem.add_resource(f"m{i}") for i in range(1, num_machines+1)]

# use the jobshop with operators extension: each activity requires an operator
# for its duration
num_operators = 3
operators = problem.add_resource("operators", capacity=3)

for j in range(num_jobs):
    prev_in_job: Optional[Activity] = None

    for t in range(num_machines):
        act = problem.add_activity(f"t_{j}_{t}", duration=times[j][t])
        machine = machine_objects[machines[j][t] - 1]
        act.uses(machine)
        act.uses(operators, amount=1)

        if prev_in_job is not None:
            act.add_constraint(get_environment().expression_manager.LE(prev_in_job.end, act.start))
        prev_in_job = act


problem.add_quality_metric(unified_planning.model.metrics.MinimizeMakespan())


print(problem)
