from functools import partial
from utils import _get_test_cases  # type: ignore

get_test_cases = partial(_get_test_cases, "performance.classical")
