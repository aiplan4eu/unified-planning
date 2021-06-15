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
from upf.solver import Solver
from typing import Dict, List, Tuple
from multiprocessing import Process, Queue


class Parallel(Solver):
    def __init__(self, solvers: List[Tuple[type, Dict[str, str]]]):
        self.solvers = solvers

    def is_oneshot_planner(self) -> bool:
        return True

    def is_plan_validator(self) -> bool:
        return True

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

    def solve(self, problem: 'upf.Problem') -> 'upf.Plan':
        return self._run_parallel('solve', problem)

    def validate(self, problem: 'upf.Problem', plan: 'upf.Plan') -> bool:
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
