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
#

import importlib
from upf.problem_kind import ProblemKind
from upf.planner import Solver
from typing import Dict, Tuple, Optional


DEFAULT_SOLVERS = {'tamer' : ('upf_tamer', 'SolverImpl')}


class Factory:
    def __init__(self, solvers: Dict[str, Tuple[str, str]] = DEFAULT_SOLVERS):
        self.solvers: Dict[str, Solver] = {}
        for name, (module_name, class_name) in solvers.items():
            try:
                self.add_solver(name, module_name, class_name)
            except ImportError:
                pass

    def add_solver(self, name: str, module_name: str, class_name: str):
        module = importlib.import_module(module_name)
        SolverImpl = getattr(module, class_name)
        self.solvers[name] = SolverImpl()

    def OneshotPlanner(self, problem_kind: ProblemKind = ProblemKind(),
                       name: Optional[str] = None) -> Optional[Solver]:
        if name is not None:
            assert name in self.solvers
            return self.solvers[name]
        for solver in self.solvers.values():
            if solver.is_oneshot_planner() and solver.support(problem_kind):
                return solver
        return None

    def PlanValidator(self, problem_kind: ProblemKind = ProblemKind(),
                      name: Optional[str] = None) -> Optional[Solver]:
        if name is not None:
            assert name in self.solvers
            return self.solvers[name]
        for solver in self.solvers.values():
            if solver.is_plan_validator() and solver.support(problem_kind):
                return solver
        return None
