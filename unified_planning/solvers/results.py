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
'''This module defines the PlanGenerationResult class.'''


import unified_planning as up
from unified_planning.exceptions import UPUsageError
from unified_planning.model import Problem
from unified_planning.plan import Plan
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, Optional, List


class ValidationResultStatus(Enum):
    VALID = auto() # The plan is valid for the problem, it satisfies all the hard constraints
    INVALID = auto() # The plan is invalid for the problem, it does not satisfy all the hard constraints

class PlanGenerationResultStatus(Enum):
    SOLVED_SATISFICING = auto() # Valid plan found.
    SOLVED_OPTIMALLY = auto() # Optimal plan found.
    UNSOLVABLE_PROVEN = auto() # The problem is impossible, no valid plan exists.
    UNSOLVABLE_INCOMPLETELY = auto() # The planner could not find a plan, but it's not sure that the problem is impossible (The planner is incomplete)
    TIMEOUT = auto() # The planner ran out of time
    MEMOUT = auto() # The planner ran out of memory
    INTERNAL_ERROR = auto() # The planner had an internal error
    UNSUPPORTED_PROBLEM = auto() # The problem given is not supported by the planner
    INTERMEDIATE = auto()# The report is not a final one but it's given through the callback function


POSITIVE_OUTCOMES = frozenset([PlanGenerationResultStatus.SOLVED_SATISFICING, PlanGenerationResultStatus.SOLVED_OPTIMALLY])

NEGATIVE_OUTCOMES = frozenset([PlanGenerationResultStatus.UNSOLVABLE_PROVEN, PlanGenerationResultStatus.UNSOLVABLE_INCOMPLETELY, PlanGenerationResultStatus.UNSUPPORTED_PROBLEM])


class LogLevel(Enum):
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()


@dataclass
class LogMessage:
    '''This class is composed by a message and an integer indicating this message level, like Debug, Info, Warning or Error.'''
    level: LogLevel
    message: str


@dataclass
class PlanGenerationResult:
    '''Class that represents the result of a plan generation call.'''
    status: PlanGenerationResultStatus
    plan: Optional['up.plan.Plan']
    planner_name: str = ''
    metrics: Dict[str, str] = field(default=dict) # type: ignore
    log_messages: List[LogMessage] = field(default=list) # type: ignore

    def __post__init(self):
        # Checks that plan and status are consistent
        if self.status in POSITIVE_OUTCOMES and self.plan is None:
            raise UPUsageError(f'The Result status is {str(self.status)} but no plan is set.')
        elif self.status in NEGATIVE_OUTCOMES and self.plan is not None:
            raise UPUsageError(f'The Result status is {str(self.status)} but the plan is {str(self.plan)}.\nWith this status the plan must be None.')
        self.metrics = {}
        self.log_messages = [] #NOTE Here, is this init right? Since it is done after the __init__ the value might be deleted
        return self

@dataclass
class ValidationResult:
    '''Class that represents the result of a validate call.'''
    status: ValidationResultStatus
    error_info: str = ''

    def _post_init(self):
        # Check that status and error_info are consistent with eachother
        if self.status == ValidationResultStatus.VALID and self.error_info != '':
            raise UPUsageError(f'The Validation Result Status is {str(self.status)} but the error_info string is set.')


@dataclass
class GroundingResult:
    '''Class that represents the result of a Solver.ground call.'''
    problem: Optional[Problem]
    rewrite_back_plan: Optional[Callable[[Plan], Plan]] #NOTE maybe "lift_plan" is a better name

    def _post_init(self):
        # Check that grounded problem and rewrite_back_plan are consistent with eachother
        if self.problem is None and self.rewrite_back_plan is not None:
            raise UPUsageError(f'The Grounded Problem is None but the rewrite_back_plan Callable is not None.')
        if self.problem is not None and self.rewrite_back_plan is None:
            raise UPUsageError(f'The Grounded Problem is {str(self.problem)} but the rewrite_back_plan Callable is None.')
