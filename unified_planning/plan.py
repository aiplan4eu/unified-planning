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
from typing import Dict, Iterator, Optional, Tuple, List
from fractions import Fraction


ALL_STATUS = list(range(0, 8))

(
SATISFIED, OPTIMAL, UNSATISFIED, SEARCH_SPACE_EXHAUSTED,
TIMEOUT, MEMOUT, INTERNAL_ERROR, UNSUPPORTED_PROBLEM
) = ALL_STATUS

POSITIVE_OUTCOMES = frozenset([SATISFIED, OPTIMAL])

NEGATIVE_OUTCOMES = frozenset([UNSATISFIED, SEARCH_SPACE_EXHAUSTED, TIMEOUT, MEMOUT, INTERNAL_ERROR, UNSUPPORTED_PROBLEM])

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

    def only_action_instances(self) -> Iterator[ActionInstance]: #NOTE this name is not optimal
        '''Returns only the ActionInstances of the plan, without time of duration.'''
        for _, a, _ in self._actions:
            yield a

class Report:
    '''Base class for unified_planning reports, given by the solvers to the user through the Solver.solve() method.'''
    def __init__(self, plan: Optional[Plan], planner_name: str = '', metrics: Dict[str, str] = {}, log_messages: List[str] = []):
        self._plan = plan
        self._planner_name = planner_name
        self._metrics = metrics
        self._log_messages = log_messages
    
    def plan(self) -> Optional[Plan]:
        '''Returns the IntermediateReport plan.
        If the plan is None check the status with self.status() to get an int
        or self.status_as_str() to get a str.'''
        return self._plan
    
    def planner_name(self) -> str:
        '''Returns the planner name.
        An empty string means the planner did not set a name.'''
        return self._planner_name

    def metrics(self) -> Dict[str, str]:
        '''Returns the set of values that the planner specifically reported, if any.'''
        return self._metrics
    
    def log_messages(self) -> List[str]:
        '''Returns all the messages the planner gave about his activity.'''
        return self._log_messages

class IntermediateReport(Report):
    '''Represents an intermediate report that a planner gives to the user through the clabback parameter of the Solver.solve() method.'''
    def __init__(self, plan: Optional[Plan], planner_name: str = '', metrics: Dict[str, str] = {}, log_messages: List[str] = []):
        Report.__init__(self, plan, planner_name, metrics, log_messages)
    
    def __repr__(self) -> str:
        output = 'Intermediate Report:\n'
        if self._planner_name != '':
            output = f'planner: {self._planner_name}\n{output}'
        output = f'{output}plan: {str(self._plan)}\n'
        if self._metrics != {}:
            metrics_str: str = ''
            for mn, m in self._metrics.items():
                metrics_str = f'{metrics_str}    {mn}: {m}\n'
            output = f'{output}metrics: {metrics_str}'
        if self._log_messages != []:
            log_messages_str = "\n".join(self._log_messages)
            output = f'{output}{log_messages_str}'
        return output


class FinalReport(Report):
    '''Represents the final report that a planner gives to the user.'''
    def __init__(self, status: int, plan: Optional[Plan], planner_name: str = '', metrics: Dict[str, str] = {}, log_messages: List[str] = []):
        Report.__init__(self, plan, planner_name, metrics, log_messages)
        self._status = status
        # Checks that plan and status are consistent
        if self._status in POSITIVE_OUTCOMES and self._plan is None:
            raise #TODO: insert a proper exception. Or this should be an assert? Because it does not depend on USER but on SOLVEr
        elif self._status in NEGATIVE_OUTCOMES and self._plan is not None:
            raise #TODO: insert a proper exception
    
    def __repr__(self) -> str:
        output = f'FinalReport:\n{status_to_str(self._status)}\n'
        if self._planner_name != '':
            output = f'planner: {self._planner_name}\n{output}'
        output = f'{output}plan: {str(self._plan)}\n'
        if self._metrics != {}:
            metrics_str: str = ''
            for mn, m in self._metrics.items():
                metrics_str = f'{metrics_str}    {mn}: {m}\n'
            output = f'{output}metrics: {metrics_str}'
        if self._log_messages != []:
            log_messages_str = "\n".join(self._log_messages)
            output = f'{output}{log_messages_str}'
        return output

    def status(self) -> int:
        '''Returns the status as an int.'''
        return self._status
    
    def status_as_str(self) -> str:
        '''Returns the status as a str.'''
        return __STATUS_STR__[self._status]


def status_to_str(id: int) -> str:
    '''Returns a string representation of the given status.'''
    return __STATUS_STR__[id]

__STATUS_STR__ = {
    SATISFIED: 'SATISFIED',
    OPTIMAL: 'OPTIMAL',
    UNSATISFIED: 'UNSATISFIED', 
    SEARCH_SPACE_EXHAUSTED: 'SEARCH_SPACE_EXHAUSTED',
    TIMEOUT: 'TIMEOUT',
    MEMOUT: 'MEMOUT',
    INTERNAL_ERROR: 'INTERNAL_ERROR',
    UNSUPPORTED_PROBLEM: 'UNSUPPORTED_PROBLEM'
}
