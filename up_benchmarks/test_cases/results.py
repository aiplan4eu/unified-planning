from typing import List
from abc import ABC, abstractmethod


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
        return "".join(map(str, self.results))
