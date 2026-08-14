from functools import partial

from utils import _get_test_cases  # type: ignore[import-not-found]

get_test_cases = partial(_get_test_cases, "performance")
