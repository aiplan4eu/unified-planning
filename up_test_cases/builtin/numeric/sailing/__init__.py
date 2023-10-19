import os
from functools import partial

from up_test_cases.utils import _get_pddl_test_cases

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PDDL_FILES_DIR = os.path.join(FILE_DIR, "pddl_files")

# problems_filenames = ["1_1_1229", "1_2_1229", "1_3_1229", "3_3_1229", "4_10_1229"] # TODO choose which to keep

# This test is disabled for time execution purposes. It can be enabled at any time!
TEST_DISABLED = True
if not TEST_DISABLED:
    get_test_cases = partial(_get_pddl_test_cases, PDDL_FILES_DIR, filter=("1_1_1229",))
