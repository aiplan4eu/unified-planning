import unified_planning
from unified_planning.test import TestCase

import up_benchmarks.test_cases as test_cases

import inspect
from typing import Dict

submodules = list(inspect.getmembers(test_cases, inspect.ismodule))
print(submodules)


def get_test_cases() -> Dict[str, TestCase]:
    res = {}
    for module_name, module in submodules:
        try:
            to_add = module.get_test_cases()
        except AttributeError:
            to_add = {}
    for test_case_name, test_case in to_add.items():
        while test_case_name in res:
            test_case_name = f"{module_name}_{test_case_name}"
        res[test_case_name] = test_case
    return res
