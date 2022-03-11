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
'''This module defines the different plan classes.'''


import unified_planning
import unified_planning.model
from unified_planning.exceptions import UPUsageError
from typing import Dict, Optional, Tuple, List
from fractions import Fraction


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

class Plan:
    '''Represents a generic plan.'''
    pass


class ActionInstance:
    '''Represents an action instance with the actual parameters.'''
    def __init__(self, action: 'unified_planning.model.Action', params: Tuple['unified_planning.model.FNode', ...] = tuple()):
        assert len(action.parameters()) == len(params)
        self._action = action
        self._params = tuple(params)

    def __repr__(self) -> str:
        s = []
        if len(self._params) > 0:
            s.append('(')
            first = True
            for p in self._params:
                if not first:
                    s.append(', ')
                s.append(str(p))
                first = False
            s.append(')')
        return self._action.name + ''.join(s)

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, ActionInstance):
            return self.action() == oth.action() and self.actual_parameters() == oth.actual_parameters()
        else:
            return False

    def action(self) -> 'unified_planning.model.Action':
        '''Returns the action.'''
        return self._action

    def actual_parameters(self) -> Tuple['unified_planning.model.FNode', ...]:
        '''Returns the actual parameters.'''
        return self._params


class SequentialPlan(Plan):
    '''Represents a sequential plan.'''
    def __init__(self, actions: List[ActionInstance]):
        self._actions = actions

    def __repr__(self) -> str:
        return str(self._actions)

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, SequentialPlan):
            return self.actions() == oth.actions()
        else:
            return False

    def actions(self) -> List[ActionInstance]:
        '''Returns the sequence of action instances.'''
        return self._actions


class TimeTriggeredPlan(Plan):
    '''Represents a time triggered plan.'''
    def __init__(self, actions: List[Tuple[Fraction, ActionInstance, Optional[Fraction]]]):
        '''The first Fraction represents the absolute time in which the action
        Action starts, while the last Fraction represents the duration
        of the action to fullfill the problem goals.
        The Action can be an InstantaneousAction, this is represented with a duration set
        to None.
        '''
        self._actions = actions

    def __repr__(self) -> str:
        return str(self._actions)

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, TimeTriggeredPlan):
            return self.actions() == oth.actions()
        else:
            return False

    def actions(self) -> List[Tuple[Fraction, ActionInstance, Optional[Fraction]]]:
        '''Returns the sequence of action instances.'''
        return self._actions


class PlanGenerationResult:
    '''Class that represents the result of a plan generation call.'''
    def __init__(self, status: int, plan: Optional[Plan], planner_name: str = '', metrics: Dict[str, str] = {}, log_messages: List[str] = []):
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
            log_messages_str = "    \n".join(self._log_messages)
            output = f'{output}    {log_messages_str}'
        return output
    
    def plan(self) -> Optional[Plan]:
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
    
    def log_messages(self) -> List[str]:
        '''Returns all the messages the planner gave about his activity.'''
        return self._log_messages

    def status(self) -> int:
        '''Returns the status as an int.'''
        return self._status
    
    def status_as_str(self) -> str:
        '''Returns the status as a str.'''
        return __STATUS_STR__[self._status]
