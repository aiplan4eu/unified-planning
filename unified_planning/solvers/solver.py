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
from unified_planning.model import ProblemKind, AbstractProblem
from dataclasses import dataclass
from enum import Enum, auto
from typing import IO, Optional, Tuple, Callable, Union



class OptimalityGuarantee(Enum):
    SATISFICING = auto()
    SOLVED_OPTIMALLY = auto()

@dataclass
class Credits:
    name: str
    author: str
    contact: str
    website: str
    license: str
    short_description: str
    long_description: str

    def write_credits(self, stream: IO[str], full_credits: bool = False):
        stream.write(f'  * Engine name: {self.name}\n  * Developers:  {self.author}\n')
        if not full_credits:
            stream.write('  * Description: ')
            stream.write(self.short_description.replace('\n', '\n  *              '))
            stream.write('\n')
        else:
            stream.write(f'  * Contacts:    {self.contact}\n')
            stream.write(f'  * Website:     {self.website}\n')
            stream.write(f'  * License:     {self.license}\n  * Description: ')
            stream.write(self.long_description.replace('\n', '\n  *              '))
            stream.write('\n')


class Solver:
    """Represents the solver interface."""

    def __init__(self, **kwargs):
        if len(kwargs) > 0:
            raise

    @property
    def name(self) -> str:
        raise NotImplementedError

    @staticmethod
    def is_oneshot_planner() -> bool:
        return False

    @staticmethod
    def satisfies(optimality_guarantee: Union[OptimalityGuarantee, str]) -> bool:
        return False

    @staticmethod
    def is_plan_validator() -> bool:
        return False

    @staticmethod
    def is_grounder() -> bool:
        return False

    @staticmethod
    def supported_kind() -> ProblemKind:
        return ProblemKind()

    @staticmethod
    def supports(problem_kind: 'ProblemKind') -> bool:
        return len(problem_kind.features) == 0

    def solve(self, problem: 'up.model.AbstractProblem',
              callback: Optional[Callable[['up.solvers.results.PlanGenerationResult'], None]] = None,
              timeout: Optional[float] = None,
              output_stream: Optional[IO[str]] = None) -> 'up.solvers.results.PlanGenerationResult':
        '''This method takes a up.model.AbstractProblem and returns a up.solvers.results.PlanGenerationResult,
        which contains information about the solution to the problem given by the planner.

        :param problem: is the up.model.AbstractProblem to solve.
        :param callback: is a function used by the planner to give reports to the user during the problem resolution, defaults to None.
        :param timeout: is the time in seconds that the planner has at max to solve the problem, defaults to None.
        :param output_stream: is a stream of strings where the planner writes his
        output (and also errors) while the planner is solving the problem, defaults to None
        :return: the up.solvers.results.PlanGenerationResult created by the planner; a data structure containing the up.plan.Plan found
        and some additional information about it.

        The only required parameter is "problem" but the planner should warn the user if callback, timeout or
        output_stream are not None and the planner ignores them.'''
        raise NotImplementedError

    def validate(self, problem: 'up.model.AbstractProblem', plan: 'up.plan.Plan') -> 'up.solvers.results.ValidationResult':
        raise NotImplementedError

    def ground(self, problem: 'up.model.AbstractProblem') -> 'up.solvers.results.GroundingResult':
        '''
        Implement only if "self.is_grounder()" returns True.
        This function returns an instance of the up.solvers.results.GroundingResult class.
        This class acts as a wrapper for the Tuple(grounded_problem, trace_back_plan), where
        "trace_back_plan" is a callable from a plan for the "grounded_problem" to a plan of the
        original problem.

        NOTE: to create a callable, the "functools.partial" method can be used, as we do in the
        "up.solvers.grounder".

        Also, the "up.solvers.grounder.lift_plan" function can be called, if retrieving the needed map
        fits the solver implementation better than retrieving a Callable.'''
        raise NotImplementedError

    @staticmethod
    def get_credits(**kwargs) -> Optional[Credits]:
        '''
        This method returns the credits for this solver, that will be printed when the solver is used.
        If this function returns None, it means no credits to print.
        '''
        return None

    def destroy(self):
        raise NotImplementedError

    def __enter__(self):
        """Manages entering a Context (i.e., with statement)"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Manages exiting from Context (i.e., with statement)"""
        self.destroy()
