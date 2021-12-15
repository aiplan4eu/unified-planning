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
import upf
from upf.model import ProblemKind
from typing import Dict, Tuple, Optional, List, Union, Type


DEFAULT_SOLVERS = {'tamer' : ('upf_tamer', 'SolverImpl'),
                   'pyperplan' : ('upf_pyperplan', 'SolverImpl'),
                   'sequential_plan_validator' : ('upf.solvers.plan_validator', 'SequentialPlanValidator'),
                   'grounder' : ('upf.solvers.grounder', 'Grounder')}


class Factory:
    def __init__(self, solvers: Dict[str, Tuple[str, str]] = DEFAULT_SOLVERS):
        self.solvers: Dict[str, Type['upf.solvers.solver.Solver']] = {}
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
                          problem_kind: ProblemKind = ProblemKind()) -> Optional[Type['upf.solvers.solver.Solver']]:
        if name is not None:
            return self.solvers[name]
        for SolverClass in self.solvers.values():
            if getattr(SolverClass, 'is_'+solver_kind)() and SolverClass.supports(problem_kind):
                return SolverClass
        return None

    def _get_solver(self, solver_kind: str, name: Optional[str] = None,
                    names: Optional[List[str]] = None,
                    params: Union[Dict[str, str], List[Dict[str, str]]] = None,
                    problem_kind: ProblemKind = ProblemKind()) -> Optional['upf.solvers.solver.Solver']:
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
            return upf.solvers.parallel.Parallel(solvers)
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
                       problem_kind: ProblemKind = ProblemKind()) -> Optional['upf.solvers.solver.Solver']:
        """
        Returns a oneshot planner. There are three ways to call this method:
        - using 'name' (the name of a specific planner) and 'params' (planner dependent options).
          e.g. OneshotPlanner(name='tamer', params={'heuristic': 'hadd'})
        - using 'names' (list of specific planners name) and 'params' (list of
          planners dependent options) to get a Parallel solver.
          e.g. OneshotPlanner(names=['tamer', 'tamer'],
                              params=[{'heuristic': 'hadd'}, {'heuristic': 'hmax'}])
        - using 'problem_kind' parameter.
          e.g. OneshotPlanner(problem_kind=problem.kind())
        """
        return self._get_solver('oneshot_planner', name, names, params, problem_kind)

    def PlanValidator(self, *, name: Optional[str] = None,
                       names: Optional[List[str]] = None,
                       params: Union[Dict[str, str], List[Dict[str, str]]] = None,
                       problem_kind: ProblemKind = ProblemKind()) -> Optional['upf.solvers.solver.Solver']:
        """
        Returns a plan validator. There are three ways to call this method:
        - using 'name' (the name of a specific plan validator) and 'params'
          (plan validator dependent options).
          e.g. PlanValidator(name='tamer', params={'opt': 'val'})
        - using 'names' (list of specific plan validators name) and 'params' (list of
          plan validators dependent options) to get a Parallel solver.
          e.g. PlanValidator(names=['tamer', 'tamer'],
                             params=[{'opt1': 'val1'}, {'opt2': 'val2'}])
        - using 'problem_kind' parameter.
          e.g. PlanValidator(problem_kind=problem.kind())
        """
        return self._get_solver('plan_validator', name, names, params, problem_kind)

    def Grounder(self, *, name: Optional[str] = None, params: Union[Dict[str, str], List[Dict[str, str]]] = None,
                       problem_kind: ProblemKind = ProblemKind()) -> Optional['upf.solvers.solver.Solver']:
        """
        Returns a Grounder. There are three ways to call this method:
        - using 'name' (the name of a specific grounder) and 'params'
          (grounder dependent options).
          e.g. Grounder(name='tamer', params={'opt': 'val'})
        - using 'problem_kind' parameter.
          e.g. Grounder(problem_kind=problem.kind())
        """
        return self._get_solver('grounder', name, None, params, problem_kind)
