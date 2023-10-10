from functools import partial
from test_cases.utils import _get_test_cases  # type: ignore

get_test_cases = partial(_get_test_cases, "test_cases.temporal")
