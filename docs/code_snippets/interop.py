from unified_planning.shortcuts import *
from unified_planning.io import PDDLReader
import os

matchcellar_files_location = os.path.join(
    os.getcwd(), "unified_planning", "test", "pddl", "matchcellar"
)
domain_filename = os.path.join(matchcellar_files_location, "domain.pddl")
problem_filename = os.path.join(matchcellar_files_location, "problem.pddl")


reader = PDDLReader()
# Reader used with both domain and problem file
# domain_filename = ... # path of the PDDL domain file
# problem_filename = ... # path of the PDDL problem file
problem = reader.parse_problem(domain_filename, problem_filename)

# Reader used with only domain file to create different instance
# of the same domain but different problem
problems = []
# domain_filename = ... # path of the PDDL domain file
problem = reader.parse_problem(domain_filename)
Match = problem.user_type("match")
Fuse = problem.user_type("fuse")
for i in range(2, 7):
    new_problem = problem.clone()
    new_problem.add_objects([Object(f"m_{j}", Match) for j in range(i)])
    new_problem.add_objects([Object(f"f_{j}", Fuse) for j in range(i)])
    problems.append(new_problem)
objects_numbers = [len(p.all_objects) for p in problems]
print(objects_numbers)
# [4, 6, 8, 10, 12]

assert objects_numbers == [4, 6, 8, 10, 12]
