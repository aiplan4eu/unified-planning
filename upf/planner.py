import importlib

from upf.problem import Problem
from contextlib import contextmanager
from dataclasses import dataclass
from typing import FrozenSet, Callable, List

class Solver():
    def solve(problem: Problem, heuristic: Callable[[FrozenSet[str]], float] = None) -> List[str]:
        raise NotImplementedError

    def destroy():
        raise NotImplementedError


class LinkedSolver(Solver):
    def __init__(self, module_name):
        self.module = importlib.import_module(module_name)

    def solve(self, problem: Problem, heuristic: Callable[[FrozenSet[str]], float] = None) -> List[str]:
        if heuristic is None:
            plan = self.module.solve(problem)
        else:
            plan = self.module.solve_with_heuristic(problem, heuristic)
        return plan

    def destroy(self):
        pass


@contextmanager
def Planner(module_name):
    a = LinkedSolver(module_name)
    try:
        yield a
    finally:
        a.destroy()
