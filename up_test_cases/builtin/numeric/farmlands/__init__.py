import os
from functools import partial

from up_test_cases.utils import _get_pddl_test_cases

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PDDL_FILES_DIR = os.path.join(FILE_DIR, "pddl_files")

# problems_filenames = ["2_100_1229", "2_200_1229", "2_300_1229", "8_400_1229", "10_400_1229", "10_1000_1229"] # TODO choose which to keep

get_test_cases = partial(_get_pddl_test_cases, PDDL_FILES_DIR, filter=("2_100_1229",))
