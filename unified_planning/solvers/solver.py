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
"""This module defines the solver interface."""


import unified_planning as up
from unified_planning.plan import Plan
from unified_planning.model import ProblemKind, Problem
from typing import IO, Optional, Tuple, Callable, Union


OPTIMALITY_GUARANTEES = list(range(0, 2))

(
    SATISFICING, SOLVED_OPTIMALLY
) = OPTIMALITY_GUARANTEES


class Solver:
    """Represents the solver interface."""

    def __init__(self, **kwargs):
        if len(kwargs) > 0:
            raise

    @staticmethod
    def name() -> str:
        raise NotImplementedError

    @staticmethod
    def is_oneshot_planner() -> bool:
        return False

    @staticmethod
    def satisfies(optimality_guarantee: Union[int, str]) -> bool:
        return False

    @staticmethod
    def is_plan_validator() -> bool:
        return False

    @staticmethod
    def is_grounder() -> bool:
        return False

    @staticmethod
    def supports(problem_kind: 'ProblemKind') -> bool:
        return len(problem_kind.features()) == 0

    def solve(self, problem: 'up.model.Problem',
                    callback: Optional[Callable[['up.solvers.results.PlanGenerationResult'], None]] = None,
                    timeout: Optional[float] = None,
                    output_stream: Optional[IO[str]] = None) -> 'up.solvers.results.PlanGenerationResult':
        '''This method takes a up.model.Problem and returns a up.solvers.results.PlanGenerationResult,
        which contains information about the solution to the problem given by the planner.

        Parameters description:
        problem is the up.model.Problem to solve.
        callback is a function used by the planner to give reports to the user during the problem resolution.
        timeout is the time in seconds that the planner has at max to solve the problem.
        output_stream is a stream of strings where the planner writes his
        output (and also errors) while the planner is solving the problem.

        The only required parameter is "problem" but the planner should warn the user if callback, timeout or
        output_stream are not None and the user set them to something, expecting a behaviour that will not be satisfied.'''
        raise NotImplementedError

    def validate(self, problem: 'up.model.Problem', plan: 'up.plan.Plan') -> bool:
        raise NotImplementedError

    def ground(self, problem: 'up.model.Problem') -> Tuple[Problem, Callable[[Plan], Plan]]:
        '''
        Implement only if "self.is_grounder()" returns True.
        This function should return the tuple (grounded_problem, trace_back_plan), where
        "trace_back_plan" is a callable from a plan for the "grounded_problem" to a plan of the
        original problem.

        NOTE: to create a callable, the "functools.partial" method can be used, as we do in the
        "up.solvers.grounder".

        Also, the "up.solvers.grounder.lift_plan" function can be called, if retrieving the needed map
        fits the solver implementation better than retrieving a function.'''
        raise NotImplementedError

    def destroy(self):
        raise NotImplementedError

    def __enter__(self):
        """Manages entering a Context (i.e., with statement)"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Manages exiting from Context (i.e., with statement)"""
        self.destroy()
