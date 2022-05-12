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
import sys
import unified_planning as up
from unified_planning.model import ProblemKind
from typing import IO, Dict, Tuple, Optional, List, Union, Type


DEFAULT_SOLVERS = {'enhsp' : ('up_enhsp', 'ENHSPsolver'),
                   'fast_downward' : ('up_fast_downward', 'FastDownwardPDDLSolver'),
                   'fast_downward_optimal' : ('up_fast_downward', 'FastDownwardOptimalPDDLSolver'),
                   'lpg' : ('up_lpg', 'LPGsolver'),
                   'tamer' : ('up_tamer.solver', 'SolverImpl'),
                   'pyperplan' : ('up_pyperplan.solver', 'SolverImpl'),
                   'sequential_plan_validator' : ('unified_planning.solvers.plan_validator', 'SequentialPlanValidator'),
                   'up_grounder' : ('unified_planning.solvers.grounder', 'Grounder'),
                   'tarski_grounder' : ('unified_planning.solvers.tarski_grounder', 'TarskiGrounder')}


def format_table(header: List[str], rows: List[List[str]]) -> str:
    row_template = '|'
    for i in range(len(header)):
        l = max(len(r[i]) for r in [header] + rows)
        row_template += f' {{:<{str(l)}}} |'
    header_str = row_template.format(*header)
    row_len = len(header_str)
    rows_str = [f'{"-"*row_len}', f'{header_str}', f'{"="*row_len}']
    for row in rows:
        rows_str.append(f'{row_template.format(*row)}')
        rows_str.append(f'{"-"*row_len}')
    return '\n'.join(rows_str)


class Factory:
    def __init__(self, solvers: Dict[str, Tuple[str, str]] = DEFAULT_SOLVERS):
        self.solvers: Dict[str, Type['up.solvers.solver.Solver']] = {}
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
                          problem_kind: ProblemKind = ProblemKind(),
                          optimality_guarantee: Optional[Union['up.solvers.solver.OptimalityGuarantee', str]] = None) -> Type['up.solvers.solver.Solver']:
        if name is not None:
            if name in self.solvers:
                return self.solvers[name]
            else:
                raise up.exceptions.UPNoRequestedSolverAvailableException
        problem_features = list(problem_kind.features)
        planners_features = []
        for name, SolverClass in self.solvers.items():
            if getattr(SolverClass, 'is_'+solver_kind)():
                if SolverClass.supports(problem_kind) \
                   and (optimality_guarantee is None or SolverClass.satisfies(optimality_guarantee)):
                    return SolverClass
                else:
                    x = [name] + [str(SolverClass.supports(ProblemKind({f}))) for f in problem_features]
                    if optimality_guarantee is not None:
                        x.append(str(SolverClass.satisfies(optimality_guarantee)))
                    planners_features.append(x)
        header = ['Planner'] + problem_features
        if optimality_guarantee is not None:
            header.append('OPTIMALITY_GUARANTEE')
        msg = f'No available solver supports all the problem features:\n{format_table(header, planners_features)}'
        raise up.exceptions.UPNoSuitableSolverAvailableException(msg)

    def _get_solver(self, solver_kind: str, name: Optional[str] = None,
                    names: Optional[List[str]] = None,
                    params: Union[Dict[str, str], List[Dict[str, str]]] = None,
                    problem_kind: ProblemKind = ProblemKind(),
                    optimality_guarantee: Optional[Union['up.solvers.solver.OptimalityGuarantee', str]] = None,
                    credits_stream: Optional[IO[str]] = sys.stdout) -> Optional['up.solvers.solver.Solver']:
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
                SolverClass.credits(credits_stream)
                solvers.append((SolverClass, param))
            p_solver = up.solvers.parallel.Parallel(solvers)
            return p_solver
        else:
            if params is None:
                params = {}
            assert isinstance(params, Dict)
            SolverClass = self._get_solver_class(solver_kind, name, problem_kind, optimality_guarantee)
            if SolverClass is None:
                raise
            SolverClass.credits(credits_stream)
            return SolverClass(**params)
        return None

    def OneshotPlanner(self, *, name: Optional[str] = None,
                       names: Optional[List[str]] = None,
                       params: Union[Dict[str, str], List[Dict[str, str]]] = None,
                       problem_kind: ProblemKind = ProblemKind(),
                       optimality_guarantee: Optional[Union['up.solvers.solver.OptimalityGuarantee', str]] = None,
                       credits_stream: Optional[IO[str]] = sys.stdout) -> Optional['up.solvers.solver.Solver']:
        """
        Returns a oneshot planner. There are three ways to call this method:
        - using 'name' (the name of a specific planner) and 'params' (planner dependent options).
          e.g. OneshotPlanner(name='tamer', params={'heuristic': 'hadd'})
        - using 'names' (list of specific planners name) and 'params' (list of
          planners dependent options) to get a Parallel solver.
          e.g. OneshotPlanner(names=['tamer', 'tamer'],
                              params=[{'heuristic': 'hadd'}, {'heuristic': 'hmax'}])
        - using 'problem_kind' and 'optimality_guarantee'.
          e.g. OneshotPlanner(problem_kind=problem.kind, optimality_guarantee=SOLVED_OPTIMALLY)
        """
        return self._get_solver('oneshot_planner', name, names, params, problem_kind, optimality_guarantee, credits_stream)

    def PlanValidator(self, *, name: Optional[str] = None,
                       names: Optional[List[str]] = None,
                       params: Union[Dict[str, str], List[Dict[str, str]]] = None,
                       problem_kind: ProblemKind = ProblemKind(),
                       credits_stream: Optional[IO[str]] = sys.stdout) -> Optional['up.solvers.solver.Solver']:
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
          e.g. PlanValidator(problem_kind=problem.kind)
        """
        return self._get_solver('plan_validator', name, names, params, problem_kind, credits_stream=credits_stream)

    def Grounder(self, *, name: Optional[str] = None, params: Union[Dict[str, str], List[Dict[str, str]]] = None,
                       problem_kind: ProblemKind = ProblemKind(),
                       credits_stream: Optional[IO[str]] = sys.stdout) -> Optional['up.solvers.solver.Solver']:
        """
        Returns a Grounder. There are three ways to call this method:
        - using 'name' (the name of a specific grounder) and 'params'
          (grounder dependent options).
          e.g. Grounder(name='tamer', params={'opt': 'val'})
        - using 'problem_kind' parameter.
          e.g. Grounder(problem_kind=problem.kind)
        """
        return self._get_solver('grounder', name, None, params, problem_kind, credits_stream=credits_stream)

    def credits(self, stream: IO[str] = sys.stdout, full_credits: bool = False):
        for Solver in self.solvers.values():
            Solver.credits(stream, full_credits)
            stream.write(f'This engine supports the following features:\n{str(Solver.supported_kind())}\n\n')
