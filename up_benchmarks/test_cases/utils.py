import importlib
import pkgutil
import unified_planning
from unified_planning.test import TestCase


from typing import Dict


def _get_test_cases(package_name: str) -> Dict[str, TestCase]:

    stack = [(package_name, True)]
    res = {}
    while len(stack) > 0:

        current_package_name, is_folder = stack.pop()
        module = importlib.import_module(current_package_name)

        to_expand = False
        if current_package_name != package_name:
            try:
                to_add = module.get_test_cases()
                if to_add is None:
                    print(current_package_name)
                    assert False
            except AttributeError:
                to_expand = is_folder
        else:
            to_add = {}
            to_expand = True
        for test_case_name, test_case in to_add.items():
            while test_case_name in res:
                test_case_name = f"{current_package_name}:{test_case_name}"
            res[test_case_name] = test_case

        if to_expand:
            for _, modname, ispkg in pkgutil.iter_modules(module.__path__):
                stack.append((f"{current_package_name}.{modname}", ispkg))
    return res
