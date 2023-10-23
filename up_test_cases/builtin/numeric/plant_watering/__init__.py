import os
from functools import partial

from utils import _get_pddl_test_cases

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PDDL_FILES_DIR = os.path.join(FILE_DIR, "pddl_files")

# problems_filenames = ["4_1", "4_2", "4_3"]  # TODO choose which to keep

get_test_cases = partial(_get_pddl_test_cases, PDDL_FILES_DIR, filter=("4_1",))
