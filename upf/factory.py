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
from upf.solver import Solver
from upf.parallel import Parallel
from typing import Dict, Tuple, Optional, List, Union


DEFAULT_SOLVERS = {'tamer' : ('upf_tamer', 'SolverImpl')}


class Factory:
    def __init__(self, solvers: Dict[str, Tuple[str, str]] = DEFAULT_SOLVERS):
        self.solvers: Dict[str, type] = {}
        for name, (module_name, class_name) in solvers.items():
            try:
                self.add_solver(name, module_name, class_name)
            except ImportError:
                pass

    def add_solver(self, name: str, module_name: str, class_name: str):
        module = importlib.import_module(module_name)
        SolverImpl = getattr(module, class_name)
        self.solvers[name] = SolverImpl

    def _get_solver_class(self, solver_kind: str, name: Optional[str] = None,
                          problem_kind: ProblemKind = ProblemKind()) -> Optional[type]:
        if name is not None:
            return self.solvers[name]
        for SolverClass in self.solvers.values():
            solver = SolverClass()
            if getattr(solver, 'is_'+solver_kind)() and solver.supports(problem_kind):
                return SolverClass
        return None

    def _get_solver(self, solver_kind: str, name: Optional[str] = None,
                    names: Optional[List[str]] = None,
                    params: Union[Dict[str, str], List[Dict[str, str]]] = None,
                    problem_kind: ProblemKind = ProblemKind()) -> Optional[Solver]:
        if names is not None:
            assert name is None
            if params is None:
                params = [{} for i in range(len(names))]
            assert isinstance(params, List) and len(names) == len(params)
            solvers = []
            for name, param in zip(names, params):
                SolverClass = self._get_solver_class(solver_kind, name)
                if SolverClass is None:
                    raise
                solvers.append((SolverClass, param))
            return Parallel(solvers)
        else:
            if params is None:
                params = {}
            assert isinstance(params, Dict)
            SolverClass = self._get_solver_class(solver_kind, name, problem_kind)
            if SolverClass is None:
                raise
            return SolverClass(**params)
        return None

    def OneshotPlanner(self, *, name: Optional[str] = None,
                       names: Optional[List[str]] = None,
                       params: Union[Dict[str, str], List[Dict[str, str]]] = None,
                       problem_kind: ProblemKind = ProblemKind()) -> Optional[Solver]:
        return self._get_solver('oneshot_planner', name, names, params, problem_kind)

    def PlanValidator(self, *, name: Optional[str] = None,
                       names: Optional[List[str]] = None,
                       params: Union[Dict[str, str], List[Dict[str, str]]] = None,
                       problem_kind: ProblemKind = ProblemKind()) -> Optional[Solver]:
        return self._get_solver('plan_validator', name, names, params, problem_kind)
