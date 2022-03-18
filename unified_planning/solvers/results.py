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
from dataclasses import dataclass, field
from typing import Dict, Optional, List

ALL_STATUS = list(range(0, 9))

(
SATISFIED, # Valid plan found.
OPTIMAL, # Optimal plan found.
UNSATISFIED, # The problem is impossible, no valid plan exists.
SEARCH_SPACE_EXHAUSTED, # The planner could not find a plan, but it's not sure that the problem is impossible (The planner is incomplete)
TIMEOUT, # The planner ran out of time
MEMOUT, # The planner ran out of memory
INTERNAL_ERROR, # The planner had an internal error
UNSUPPORTED_PROBLEM, # The problem given is not supported by the planner
INTERMEDIATE # The report is not a final one but it's given through the callback function
) = ALL_STATUS

__STATUS_STR__ = {
    SATISFIED: 'SATISFIED',
    OPTIMAL: 'OPTIMAL',
    UNSATISFIED: 'UNSATISFIED',
    SEARCH_SPACE_EXHAUSTED: 'SEARCH_SPACE_EXHAUSTED',
    TIMEOUT: 'TIMEOUT',
    MEMOUT: 'MEMOUT',
    INTERNAL_ERROR: 'INTERNAL_ERROR',
    UNSUPPORTED_PROBLEM: 'UNSUPPORTED_PROBLEM',
    INTERMEDIATE: 'INTERMEDIATE'
}

POSITIVE_OUTCOMES = frozenset([SATISFIED, OPTIMAL])

NEGATIVE_OUTCOMES = frozenset([UNSATISFIED, SEARCH_SPACE_EXHAUSTED, UNSUPPORTED_PROBLEM])


LOG_LEVEL = list(range(0, 4))

(
DEBUG,
INFO,
WARNING,
ERROR
) = LOG_LEVEL

__LOG_LEVEL_STR__ = {
    DEBUG: 'DEBUG',
    INFO: 'INFO',
    WARNING: 'WARNING',
    ERROR: 'ERROR'
}

@dataclass
class LogMessage:
    '''This class is composed by a message and an integer indicating this message level, like Debug, Info, Warning or Error.'''
    level: int
    message: str

    def __post__init(self):
        assert self.level in LOG_LEVEL

    def level_as_str(self):
        '''Returns the LogMessage level as a str.'''
        return __LOG_LEVEL_STR__[self.level]

@dataclass
class PlanGenerationResult:
    '''Class that represents the result of a plan generation call.'''
    status: int
    plan: Optional['up.plan.Plan']
    planner_name: str = ''
    metrics: Dict[str, str] = field(default=dict) # type: ignore
    log_messages: List[LogMessage] = field(default=list) # type: ignore

    def __post__init(self):
        assert self.status in ALL_STATUS
        # Checks that plan and status are consistent
        if self.status in POSITIVE_OUTCOMES and self.plan is None:
            raise UPUsageError(f'The Result status is {self.status_as_str()} but no plan is set.')
        elif self.status in NEGATIVE_OUTCOMES and self.plan is not None:
            raise UPUsageError(f'The Result status is {self.status_as_str()} but the plan is {str(self.plan)}.\nWith this status the plan must be None.')
        return self

    def status_as_str(self) -> str:
        '''Returns the status as a str.'''
        return __STATUS_STR__[self.status]
