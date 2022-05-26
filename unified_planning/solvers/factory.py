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
import io
import inspect
import unified_planning as up
from unified_planning.environment import Environment, get_env
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
    def __init__(self, env: 'Environment', solvers: Dict[str, Tuple[str, str]] = DEFAULT_SOLVERS):
        self._env = env
        self.solvers: Dict[str, Type['up.solvers.solver.Solver']] = {}
        self._credit_disclaimer_printed = False
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

    def _print_credits(self, all_credits: List[Optional['up.solvers.Credits']]):
        '''
        This function prints the credits of the engine(s) used by an operation mode
        '''
        credits: List['up.solvers.Credits'] = [c for c in all_credits if c is not None]
        if len(credits) == 0:
            return

        operation_mode_name = inspect.stack()[2].function
        line = inspect.stack()[3].lineno
        fname = inspect.stack()[3].filename

        class PaleWriter():
            def __init__(self, stream: IO[str]):
                self._stream = stream

            def write(self, txt:str):
                self._stream.write('\033[96m')
                self._stream.write(txt)
                self._stream.write('\033[0m')

        if self.env.credits_stream is not None:
            w = PaleWriter(self.env.credits_stream)

            if not self._credit_disclaimer_printed:
                self._credit_disclaimer_printed = True
                w.write(f'\033[1mNOTE: To disable printing of planning engine credits, add this line to your code: `up.shortcuts.get_env().credits_stream = None`\n')
            w.write('  *** Credits ***\n')
            w.write(f'  * In operation mode `{operation_mode_name}` at line {line} of `{fname}`, ')
            if len(credits) > 1:
                w.write('you are using a parallel planning engine with the following components:\n')
            else:
                w.write('you are using the following planning engine:\n')
            for c in credits:
                c.write_credits(w) #type: ignore
            w.write('\n')

    def _get_solver(self, solver_kind: str, name: Optional[str] = None,
                    names: Optional[List[str]] = None,
                    params: Union[Dict[str, str], List[Dict[str, str]]] = None,
                    problem_kind: ProblemKind = ProblemKind(),
                    optimality_guarantee: Optional[Union['up.solvers.solver.OptimalityGuarantee', str]] = None
                    ) -> 'up.solvers.solver.Solver':
        if names is not None:
            assert name is None
            if params is None:
                params = [{} for i in range(len(names))]
            assert isinstance(params, List) and len(names) == len(params)
            solvers = []
            all_credits = []
            for name, param in zip(names, params):
                SolverClass = self._get_solver_class(solver_kind, name)
                all_credits.append(SolverClass.get_credits(**param))
                solvers.append((SolverClass, param))
            self._print_credits(all_credits)
            p_solver = up.solvers.parallel.Parallel(solvers)
            return p_solver
        else:
            if params is None:
                params = {}
            assert isinstance(params, Dict)
            SolverClass = self._get_solver_class(solver_kind, name, problem_kind, optimality_guarantee)
            credits = SolverClass.get_credits(**params)
            self._print_credits([credits])
            return SolverClass(**params)

    @property
    def env(self) -> 'Environment':
        '''Returns the environment in which this factory is created'''
        return self._env

    def OneshotPlanner(self, *, name: Optional[str] = None,
                       names: Optional[List[str]] = None,
                       params: Union[Dict[str, str], List[Dict[str, str]]] = None,
                       problem_kind: ProblemKind = ProblemKind(),
                       optimality_guarantee: Optional[Union['up.solvers.solver.OptimalityGuarantee', str]] = None
                       ) -> 'up.solvers.solver.Solver':
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
        return self._get_solver('oneshot_planner', name, names, params, problem_kind, optimality_guarantee)

    def PlanValidator(self, *, name: Optional[str] = None,
                       names: Optional[List[str]] = None,
                       params: Union[Dict[str, str], List[Dict[str, str]]] = None,
                       problem_kind: ProblemKind = ProblemKind()
                       ) -> 'up.solvers.solver.Solver':
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
        return self._get_solver('plan_validator', name, names, params, problem_kind)

    def Grounder(self, *, name: Optional[str] = None, params: Union[Dict[str, str], List[Dict[str, str]]] = None,
                       problem_kind: ProblemKind = ProblemKind()
                       ) -> 'up.solvers.solver.Solver':
        """
        Returns a Grounder. There are three ways to call this method:
        - using 'name' (the name of a specific grounder) and 'params'
          (grounder dependent options).
          e.g. Grounder(name='tamer', params={'opt': 'val'})
        - using 'problem_kind' parameter.
          e.g. Grounder(problem_kind=problem.kind)
        """
        return self._get_solver('grounder', name, None, params, problem_kind)

    def print_solvers_info(self, stream: IO[str] = sys.stdout, full_credits: bool = True):
        stream.write('These are the solvers currently available:\n')
        for Solver in self.solvers.values():
            credits = Solver.get_credits()
            if credits is not None:
                stream.write('---------------------------------------\n')
                credits.write_credits(stream, full_credits)
                stream.write(f'This engine supports the following features:\n{str(Solver.supported_kind())}\n\n')
