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


from fractions import Fraction
import unified_planning as up
import unified_planning.solvers as solvers
from unified_planning.plan import Plan, ActionInstance, SequentialPlan, TimeTriggeredPlan
from unified_planning.model import ProblemKind
from unified_planning.exceptions import UPException
from typing import Callable, Dict, Iterable, List, Optional, Tuple, cast
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
        raise UPException('The Parallel solver type depends on its actual solvers')

    @staticmethod
    def is_plan_validator() -> bool:
        raise UPException('The Parallel solver type depends on its actual solvers')

    @staticmethod
    def supports(problem_kind: 'ProblemKind') -> bool:
        raise UPException('The Parallel supported features depends on its actual solvers')

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

    def solve(self, problem: 'up.model.Problem', callback: Optional[Callable[['up.plan.IntermediateReport'], None]] = None) -> 'up.plan.FinalReport':
        final_report = self._run_parallel('solve', problem, callback)
        plan = final_report.plan()
        objects = {}
        for ut in problem.user_types():
            for obj in problem.objects(ut):
                objects[obj.name()] = obj
        em = problem.env.expression_manager
        if isinstance(plan, up.plan.SequentialPlan):
            actions = _handle_plan_actions(plan.actions(), objects, problem, em)
            return up.plan.FinalReport(final_report.status(), SequentialPlan(actions), final_report.planner_name(), final_report.metrics(), final_report.log_messages())
        elif isinstance(plan, up.plan.TimeTriggeredPlan):
            actions = _handle_plan_actions(plan.only_action_instances(), objects, problem, em)
            t_actions_d = [(t, a, d) for (t, _, d), a in zip(plan.actions(), actions)]
            return up.plan.FinalReport(final_report.status(), TimeTriggeredPlan(t_actions_d), final_report.planner_name(), final_report.metrics(), final_report.log_messages())
        else:
            raise NotImplementedError

    def validate(self, problem: 'up.model.Problem', plan: Plan) -> bool:
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

def _handle_plan_actions(actions: Iterable[ActionInstance], objects: Dict[str, 'up.model.Object'],problem: 'up.model.Problem', em: 'up.model.ExpressionManager') -> List[ActionInstance]:
    retval = []
    for a in actions:
        new_a = problem.action(a.action().name)
        params = []
        for p in a.actual_parameters():
            if p.is_object_exp():
                obj = objects[p.object().name()]
                params.append(em.ObjectExp(obj))
            elif p.is_bool_constant():
                params.append(em.Bool(p.is_true()))
            elif p.is_int_constant():
                params.append(em.Int(cast(int, p.constant_value())))
            elif p.is_real_constant():
                params.append(em.Real(cast(Fraction, p.constant_value())))
            else:
                raise
        retval.append(ActionInstance(new_a, tuple(params)))
    return retval
