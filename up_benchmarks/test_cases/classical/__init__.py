import importlib
import pkgutil
import unified_planning
from unified_planning.test import TestCase

from typing import Dict


def get_test_cases() -> Dict[str, TestCase]:

    packages = ["test_cases.classical"]
    res = {}
    while len(packages) > 0:

        package_name = packages.pop()
        # module = sys.modules[package_name]
        module = importlib.import_module(package_name)

        print(module)
        if package_name != "test_cases.classical":
            to_add = module.get_test_cases()
        else:
            to_add = {}
        for test_case_name, test_case in to_add.items():
            while test_case_name in res:
                test_case_name = f"{package_name}:{test_case_name}"
            res[test_case_name] = test_case

        for _, modname, ispkg in pkgutil.iter_modules(module.__path__):
            if ispkg:
                packages.append(f"{package_name}.{modname}")
    return res
