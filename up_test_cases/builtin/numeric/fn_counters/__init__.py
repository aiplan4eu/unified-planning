import unified_planning
from unified_planning.io import PDDLReader
from unified_planning.test import TestCase
import os

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PDDL_FILES_DIR = os.path.join(FILE_DIR, "pddl_files")
DOMAIN_FILENAME = os.path.join(PDDL_FILES_DIR, "fn_counters_domain.pddl")
# _problems_filenames = ["2", "4", "8"] # TODO choose which to keep
_problems_filenames = ["2"]
PROBLEMS_FILENAMES = list(
    map(
        lambda n: os.path.join(PDDL_FILES_DIR, f"fn_counters_{n}.pddl"),
        _problems_filenames,
    )
)

test_cases = None


def get_test_cases():
    global test_cases
    if test_cases is None:
        res = {}
        reader = PDDLReader()
        for problem_filename in PROBLEMS_FILENAMES:
            problem = reader.parse_problem(DOMAIN_FILENAME, problem_filename)
            problem.name = os.path.basename(problem_filename)

            res[problem.name] = TestCase(problem=problem, solvable=True)

        test_cases = res
    assert test_cases is not None
    return test_cases
