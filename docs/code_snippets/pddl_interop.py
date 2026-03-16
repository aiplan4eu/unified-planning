from unified_planning.shortcuts import *
from unified_planning.io import PDDLReader
import os

counters_files_location = os.path.join(
    os.getcwd(), "unified_planning", "test", "pddl", "counters"
)
domain_filename = os.path.join(counters_files_location, "domain.pddl")
problem_filename = os.path.join(counters_files_location, "problem.pddl")


reader = PDDLReader()
# Reader used with both domain and problem file
# domain_filename = ... # path of the PDDL domain file
# problem_filename = ... # path of the PDDL problem file
problem = reader.parse_problem(domain_filename, problem_filename)

# Reader used with only domain file to create different instance
# of the same domain but different problem
problems = []
# domain_filename = ... # path of the PDDL domain file
partial_problem = reader.parse_problem(domain_filename)
Counter = partial_problem.user_type("counter")
for i in range(2, 7):
    new_problem = partial_problem.clone()
    new_problem.add_objects([Object(f"c_{j}", Counter) for j in range(i)])
    problems.append(new_problem)
objects_numbers = [len(p.all_objects) for p in problems]
print(objects_numbers)
# [2, 3, 4, 5, 6]


assert objects_numbers == [2, 3, 4, 5, 6]

hddl_domain_filename = domain_filename
hddl_problem_filename = problem_filename
domain_filename = os.path.join(counters_files_location, "written_domain.pddl")
problem_filename = os.path.join(counters_files_location, "written_problem.pddl")

from unified_planning.io import PDDLWriter

# Get the problem to use in the Operation Modes
# problem = ...
writer = PDDLWriter(problem)
# domain_filename = ... # Path to file where the PDDL domain will be printed.
writer.write_domain(domain_filename)
# problem_filename = ... # Path to file where the PDDL problem will be printed.
writer.write_problem(problem_filename)

reader = PDDLReader()
# The files where the HDDL domain and problem are
# hddl_domain_filename = ...
# hddl_problem_filename = ...

# Reader used to parse HDDL files and return a up.model.htn.HierarchicalProblem
hierarchical_problem = reader.parse_problem(hddl_domain_filename, hddl_problem_filename)
# hierarchical_problem = ... # Use the problem in the UP
writer = PDDLWriter(hierarchical_problem)
# domain_filename = ... # Path to file where the HDDL domain will be printed.
writer.write_domain(domain_filename)
# problem_filename = ... # Path to file where the HDDL problem will be printed.
writer.write_problem(problem_filename)


os.remove(domain_filename)
os.remove(problem_filename)


from unified_planning.interop.tarski import convert_problem_to_tarski


# problem = ... # get or create the Problem using the UP
tarski_problem: "tarski.fstrips.Problem" = convert_problem_to_tarski(problem)
# You get a Tarski problem, which you can use to interact with the Tarski library


from unified_planning.interop.tarski import convert_problem_from_tarski
from unified_planning.shortcuts import get_environment


# From a Tarski problem, you can generate the equivalent UP problem.
problem = convert_problem_from_tarski(get_environment(), tarski_problem)
