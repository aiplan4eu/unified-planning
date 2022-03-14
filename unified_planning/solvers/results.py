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

class LogMessage:
    '''This class is composed by a message and an integer indicating this message level, like Debug, Info, Warning or Error.'''
    def __init__(self, level: int, message: str):
        assert level in LOG_LEVEL
        self._level = level
        self._message = message

    def __eq__(self, other: object) -> bool:
        if isinstance(other, LogMessage):
            return self._level == other._level and self._message == other._message
        else:
            return False
    
    def __repr__(self) -> str:
        return f'Log Level: {__LOG_LEVEL_STR__[self._level]}\nLog message:\n{self._message}'

    def level(self) -> int:
        '''Returns the LogMessage level.'''
        return self._level
    
    def message(self) -> str:
        '''Returns the LogMessage message.'''
        return self._message

class PlanGenerationResult:
    '''Class that represents the result of a plan generation call.'''
    def __init__(self, status: int, plan: Optional['up.plan.Plan'], planner_name: str = '', metrics: Dict[str, str] = {}, log_messages: List[LogMessage] = []):
        assert status in ALL_STATUS
        self._status = status
        self._plan = plan
        self._planner_name = planner_name
        self._metrics = metrics
        self._log_messages = log_messages
        # Checks that plan and status are consistent
        if self._status in POSITIVE_OUTCOMES and self._plan is None:
            raise UPUsageError(f'The Result status is {self.status_as_str()} but no plan is set.')
        elif self._status in NEGATIVE_OUTCOMES and self._plan is not None:
            raise UPUsageError(f'The Result status is {self.status_as_str()} but the plan is {str(plan)}.\nWith this status the plan must be None.')

    def __repr__(self) -> str:
        output = f'Plan Generation Report\nStatus: {self.status_as_str()}\n'
        if self._planner_name != '':
            output = f'planner: {self._planner_name}\n{output}'
        output = f'{output}plan: {str(self._plan)}\n'
        if self._metrics != {}:
            metrics_str: str = ''
            for mn, m in self._metrics.items():
                metrics_str = f'{metrics_str}    {mn}: {m}\n'
            output = f'{output}metrics: {metrics_str}'
        if self._log_messages != []:
            log_messages_str = "    \n".join(str(self._log_messages))
            output = f'{output}    {log_messages_str}'
        return output
    
    def plan(self) -> Optional['up.plan.Plan']:
        '''Returns the Plan Generation Report plan.
        If the plan is None check the status with self.status() to get an int
        or self.status_as_str() to get a str.'''
        return self._plan
    
    def planner_name(self) -> str:
        '''Returns the planner name.
        An empty string means the planner did not set a name.'''
        return self._planner_name

    def metrics(self) -> Dict[str, str]:
        '''Returns the set of values that the planner specifically reported.'''
        return self._metrics
    
    def log_messages(self) -> List[LogMessage]:
        '''Returns all the messages the planner gave about his activity.'''
        return self._log_messages

    def status(self) -> int:
        '''Returns the status as an int.'''
        return self._status
    
    def status_as_str(self) -> str:
        '''Returns the status as a str.'''
        return __STATUS_STR__[self._status]
