import importlib
import pkgutil
import argparse
from typing import List
from abc import ABC, abstractmethod
from typing import Dict

import unified_planning
from unified_planning.test import TestCase


# Define the default timeout for anytime and oneshot
DEFAULT_TIMEOUT = 3.0


def _get_test_cases(package_name: str) -> Dict[str, TestCase]:

    stack = [(package_name, True, "")]
    res = {}
    while len(stack) > 0:
        to_add = {}

        current_package_name, is_folder, modname = stack.pop()

        try:
            module = importlib.import_module(current_package_name)
        except:
            assert False

        to_expand = False
        if current_package_name != package_name:
            try:
                to_add = module.get_test_cases()
                if not isinstance(to_add, dict):
                    assert (
                        False
                    ), f"Error in {current_package_name} that returned {type(to_add)} instead of dict"
            except AttributeError:
                to_expand = is_folder
        else:
            to_expand = True
        for test_case_name, test_case in to_add.items():
            test_case_name = f"{modname}:{test_case_name}"
            count = 0
            # If the name is already in the results, add a counter to guarantee unicity
            while test_case_name in res:
                test_case_name = f"{test_case_name}_{count}"
                count += 1
            res[test_case_name] = test_case

        if to_expand:
            for _, pkgname, ispkg in pkgutil.iter_modules(module.__path__):
                path_name = f"{modname}:{pkgname}" if modname else pkgname
                stack.append((f"{current_package_name}.{pkgname}", ispkg, path_name))
    return res


class bcolors:
    """Just a holder for terminal colors"""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARN = "\033[93m"
    ERR = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class ResultSet(ABC):
    @abstractmethod
    def ok(self) -> bool:
        pass

    def __add__(self, other: "ResultSet") -> "ResultSet":
        return ResultList([self, other])


class Void(ResultSet):
    def ok(self):
        return True

    def __str__(self):
        return ""


class Ok(ResultSet):
    def __init__(self, msg: str = ""):
        self.msg = msg

    def ok(self) -> bool:
        return True

    def __str__(self):
        if self.msg == "":
            return ""
        else:
            return f"{bcolors.OKGREEN}OK({self.msg}){bcolors.ENDC} "


class Warn(ResultSet):
    def __init__(self, msg: str = ""):
        self.msg = msg

    def ok(self) -> bool:
        return True

    def __str__(self):
        return f"{bcolors.WARN}WARN({self.msg}){bcolors.ENDC} "


class Err(ResultSet):
    def __init__(self, msg: str = ""):
        self.msg = msg

    def ok(self) -> bool:
        return False

    def __str__(self):
        return f"{bcolors.ERR}Err({self.msg}){bcolors.ENDC} "


class ResultList(ResultSet):
    def __init__(self, results: List[ResultSet]):
        self.results = results

    def ok(self) -> bool:
        return all(r.ok() for r in self.results)

    def __str__(self):
        return "".join(set(map(str, self.results)))


def get_report_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Perform a Unified Planning Operation mode.",
        allow_abbrev=False,
    )

    parser.add_argument(
        "engines",
        type=str,
        nargs="*",
        help="The tests run only in the engines specified here. If no engines are specified, the tests will run on every engine installed.",
        default=[],
    )

    parser.add_argument(
        "-f",
        "--filter",
        "--filters",
        type=str,
        nargs="+",
        help="Runs only the test that contains one of the given filters; if no filters are specified, runs the engines on all the problems.",
        dest="filters",
        default=[],
    )

    mutually_exclusive = parser.add_mutually_exclusive_group()

    mutually_exclusive.add_argument(
        "-e",
        "--extra-packages",
        type=str,
        nargs="+",
        help="Accepts other packages to search for new test_cases; with this parameter the up tests, all the tests in the up_benchmarks and all the tests in the given packages run.",
        dest="extra_packages",
        default=[],
    )
    mutually_exclusive.add_argument(
        "-p",
        "--packages",
        type=str,
        nargs="+",
        help="gathers the tests by searching the get_test_cases method inside given packages",
        dest="packages",
        default=[],
    )

    parser.add_argument(
        "-m",
        "--mode",
        "--modes",
        type=str,
        nargs="+",
        choices=["oneshot", "anytime", "validation", "grounding"],
        help="Performs only the specified modes; if not specified tests all the modes.",
        dest="modes",
        default=["oneshot", "anytime", "validation", "grounding"],
    )

    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        dest="timeout",
        help=f"The timeout in seconds for the anytime and oneshot mode, defaults to {DEFAULT_TIMEOUT}s. Set a number <= 0 to have no timeout",
        default=DEFAULT_TIMEOUT,
    )

    return parser
