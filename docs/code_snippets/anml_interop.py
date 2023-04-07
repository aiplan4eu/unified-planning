from unified_planning.io import ANMLReader
from unified_planning.io import ANMLWriter
import os


problem_filename = os.path.join(
    os.getcwd(), "unified_planning", "test", "anml", "match.anml"
)
file_name = os.path.join(
    os.path.dirname(problem_filename), "anml_code_snippet_file.anml"
)

reader = ANMLReader()
# problem_filename = ... # Path to the ANML problem file
problem = reader.parse_problem(problem_filename)


# problem = ... # get or create the Problem using the UP
writer = ANMLWriter(problem)
# file_name = ... # Path to file where the ANML problem will be printed.
writer.write_problem(file_name)

os.remove(file_name)
