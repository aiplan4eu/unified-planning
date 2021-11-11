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


import upf
import upf.solvers as solvers
from upf.plan import Plan, SequentialPlan, ActionInstance
from upf.model import ProblemKind
from upf.exceptions import UPFException
from typing import Dict, List, Tuple
from multiprocessing import Process, Queue


class Parallel(solvers.solver.Solver):
    """Create a parallel instance of multiple Solvers."""

    def __init__(self, solvers: List[Tuple[type, Dict[str, str]]]):
        self.solvers = solvers

    @staticmethod
    def name() -> str:
        return 'Parallel'

    @staticmethod
    def is_oneshot_planner() -> bool:
        raise UPFException('The Parallel solver type depends on its actual solvers')

    @staticmethod
    def is_plan_validator() -> bool:
        raise UPFException('The Parallel solver type depends on its actual solvers')

    @staticmethod
    def supports(problem_kind: 'ProblemKind') -> bool:
        raise UPFException('The Parallel supported features depends on its actual solvers')

    def _run_parallel(self, fname, *args):
        signaling_queue = Queue()
        processes = []
        for idx, (solver_class, opts) in enumerate(self.solvers):
            options = opts
            _p = Process(name=str(idx),
                         target=_run,
                         args=(idx, solver_class, options,
                               signaling_queue, fname, *args))
            processes.append(_p)
            _p.start()
        while True:
            (idx, res) = signaling_queue.get(block=True)
            if isinstance(res, BaseException):
                raise res
            else:
                break
        for p in processes:
            p.terminate()
        return res

    def solve(self, problem: 'upf.model.Problem') -> 'upf.plan.Plan':
        plan = self._run_parallel('solve', problem)
        actions = []
        objects = {}
        for ut in problem.user_types().values():
            for obj in problem.objects(ut):
                objects[obj.name()] = obj
        em = problem.env.expression_manager
        for a in plan.actions():
            new_a = problem.action(a.action().name)
            params = []
            for p in a.actual_parameters():
                if p.is_object_exp():
                    obj = objects[p.object().name()]
                    params.append(em.ObjectExp(obj))
                elif p.is_bool_constant():
                    params.append(em.Bool(p.is_true()))
                elif p.is_int_constant():
                    params.append(em.Int(p.constant_value()))
                elif p.is_real_constant():
                    params.append(em.Real(p.constant_value()))
                else:
                    raise
            actions.append(ActionInstance(new_a, tuple(params)))
        return SequentialPlan(actions)

    def validate(self, problem: 'upf.model.Problem', plan: Plan) -> bool:
        return self._run_parallel('validate', problem, plan)

    def destroy(self):
        pass


def _run(idx: int, SolverClass: type, options: Dict[str, str], signaling_queue: Queue, fname: str, *args):
    with SolverClass(**options) as s:
        try:
            local_res = getattr(s, fname)(*args)
        except Exception as ex:
            signaling_queue.put((idx, ex))
            return
        signaling_queue.put((idx, local_res))
