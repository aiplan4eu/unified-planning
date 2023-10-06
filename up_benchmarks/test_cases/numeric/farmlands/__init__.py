import unified_planning
from unified_planning.io import PDDLReader
from unified_planning.test import TestCase
import os

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PDDL_FILES_DIR = os.path.join(FILE_DIR, "pddl_files")
DOMAIN_FILENAME = os.path.join(PDDL_FILES_DIR, "farmland_domain.pddl")
# _problems_filenames = ["2_100_1229", "2_200_1229", "2_300_1229", "8_400_1229", "10_400_1229", "10_1000_1229"] # TODO choose which to keep
_problems_filenames = ["2_100_1229"]
PROBLEMS_FILENAMES = list(
    map(
        lambda n: os.path.join(PDDL_FILES_DIR, f"farmland_{n}.pddl"),
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
