import os
from functools import partial

from utils import _get_pddl_test_cases

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PDDL_FILES_DIR = os.path.join(FILE_DIR, "pddl_files")

get_test_cases = partial(_get_pddl_test_cases, PDDL_FILES_DIR, filter=("1", "2", "3"))
