# Copyright 2021 AIPlan4EU project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
