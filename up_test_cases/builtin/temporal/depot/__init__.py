import os
from functools import partial

from utils import _get_pddl_test_cases

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PDDL_FILES_DIR = os.path.join(FILE_DIR, "pddl_files")

# problems_filenames = ["1", "2", "3", "10", "11"] # TODO choose which to keep

get_test_cases = partial(
    _get_pddl_test_cases, PDDL_FILES_DIR, block=("2", "3", "10", "11")
)
