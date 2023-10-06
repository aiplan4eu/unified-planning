import importlib
import pkgutil
import unified_planning
from unified_planning.test import TestCase


import sys

# print(dir(sys.modules[__name__]))

import sys

modname = globals()["__name__"]
module = sys.modules[modname]
# print(repr(modname))
# print(repr(module))
# print(dir(module))


# import up_benchmarks.test_cases as test_cases

import inspect
from typing import Dict


def get_test_cases() -> Dict[str, TestCase]:

    packages = ["test_cases"]
    res = {}
    while len(packages) > 0:

        package_name = packages.pop()
        module = importlib.import_module(package_name)

        to_expand = False
        if package_name != "test_cases":
            try:
                to_add = module.get_test_cases()
            except AttributeError:
                to_expand = True
        else:
            to_add = {}
            to_expand = True
        for test_case_name, test_case in to_add.items():
            while test_case_name in res:
                test_case_name = f"{package_name}:{test_case_name}"
            res[test_case_name] = test_case

        if to_expand:
            for _, modname, ispkg in pkgutil.iter_modules(module.__path__):
                if ispkg:
                    packages.append(f"{package_name}.{modname}")
    return res
