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
"""This module defines an interface for a generic PDDL planner."""

import tempfile
import os
import shutil
import upf
from upf.shortcuts import *
from upf.io.pddl_writer import PDDLWriter
from subprocess import Popen, PIPE
from typing import Optional


class PDDLSolver(upf.Solver):
    """Represents the solver interface."""
    def __init__(self, needs_requirements=True):
        upf.Solver.__init__(self)
        self._needs_requirements = needs_requirements

    def is_oneshot_planner(self) -> bool:
        return True

    def _get_cmd(self, domanin_filename: str, problem_filename: str, plan_filename: str) -> List[str]:
        raise NotImplementedError

    def _plan_from_file(self, problem: 'upf.Problem', plan_filename: str) -> 'upf.Plan':
        actions = []
        objects = {}
        for ut in problem.user_types().values():
            for obj in problem.objects(ut):
                objects[obj.name()] = obj
        with open(plan_filename) as plan:
            for line in plan.readlines():
                start = line.find('(') + 1
                end = line.find(')', start)
                l = line[start:end].split()
                a = l[0]
                params = l[1:]
                action = problem.action(a)
                parameters = []
                for p in params:
                    parameters.append(ObjectExp(objects[p]))
                actions.append(upf.ActionInstance(action, tuple(parameters)))
        return upf.SequentialPlan(actions)

    def solve(self, problem: 'upf.Problem') -> Optional['upf.Plan']:
        w = PDDLWriter(problem, self._needs_requirements)
        tempdir = tempfile.mkdtemp()
        domanin_filename = os.path.join(tempdir, 'domain.pddl')
        problem_filename = os.path.join(tempdir, 'problem.pddl')
        plan_filename = os.path.join(tempdir, 'plan.txt')
        w.write_domain(domanin_filename)
        w.write_problem(problem_filename)

        cmd = self._get_cmd(domanin_filename, problem_filename, plan_filename)
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()

        if not os.path.isfile(plan_filename):
            print(err.decode())
            plan = None
        else:
            plan = self._plan_from_file(problem, plan_filename)

        shutil.rmtree(tempdir)

        return plan

    def destroy(self):
        pass
