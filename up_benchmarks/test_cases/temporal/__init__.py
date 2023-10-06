import importlib
import pkgutil
import unified_planning
from unified_planning.test import TestCase

from typing import Dict


def get_test_cases() -> Dict[str, TestCase]:

    packages = ["test_cases.temporal"]
    res = {}
    while len(packages) > 0:

        package_name = packages.pop()
        module = importlib.import_module(package_name)

        to_expand = False
        if package_name != "test_cases.temporal":
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
