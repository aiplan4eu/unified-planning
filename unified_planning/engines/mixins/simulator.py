
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

from typing import Iterator, List, Optional, Tuple, Union, cast
import unified_planning as up
from unified_planning.exceptions import UPUsageError


class Event:
    '''This is an abstract class representing an event.'''

    @property
    def conditions(self) -> List['up.model.FNode']:
        raise NotImplementedError

    @property
    def effects(self) -> List['up.model.Effect']:
        raise NotImplementedError

    @property
    def simulated_effect(self) -> Optional['up.model.SimulatedEffect']:
        raise NotImplementedError


class SimulatorMixin:
    '''
    SimulatorMixin abstract class.
    This class defines the interface that a simulator must implement.

    Important NOTE: The AbstractProblem instance is given at the constructor.
    '''

    def __init__(self, problem: 'up.model.AbstractProblem') -> None:
        '''
        Takes an instance of a problem and eventually some parameters, that represent
        some specific settings of the SimulatorMixin.
        :param problem: the problem that defines the domain in which the simulation exists.
        '''
        self._problem = problem

    def is_applicable(self, event: 'Event', state: 'up.model.ROState') -> bool:
        '''
        Returns True if the given event conditions are evaluated as True in the given state;
        returns False otherwise.
        :param state: the state where the event conditions are checked.
        :param event: the event whose conditions are checked.
        :return: Whether or not the event is applicable in the given state.
        '''
        return self._is_applicable(event, state)

    def _is_applicable(self, event: 'Event', state: 'up.model.ROState') -> bool:
        raise NotImplementedError

    def apply(self, event: 'Event', state: 'up.model.RWState') -> Optional['up.model.RWState']:
        '''
        Returns None if the event is not applicable in the given state, otherwise returns a new RWState,
        which is a copy of the given state but the applicable effects of the event are applied; therefore
        some fluent values are updated.
        :param state: the state where the event formulas are calculated.
        :param event: the event that has the information about the conditions to check and the effects to apply.
        :return: None if the event is not applicable in the given state, a new RWState with some updated values
         if the event is applicable.
        '''
        return self._apply(event, state)

    def _apply(self, event: 'Event', state: 'up.model.RWState') -> Optional['up.model.RWState']:
        raise NotImplementedError

    def apply_unsafe(self, event: 'Event', state: 'up.model.RWState') -> 'up.model.RWState':
        '''
        Returns a new RWState, which is a copy of the given state but the applicable effects of the event are applied; therefore
        some fluent values are updated.
        IMPORTANT NOTE: Assumes that self.is_applicable(state, event) returns True
        :param state: the state where the event formulas are evaluated.
        :param event: the event that has the information about the effects to apply.
        :return: A new RWState with some updated values.
        '''
        return self._apply_unsafe(event, state)

    def _apply_unsafe(self, event: 'Event', state: 'up.model.RWState') -> 'up.model.RWState':
        raise NotImplementedError

    def get_applicable_events(self, state: 'up.model.ROState') -> Iterator['Event']:
        '''
        Returns a view over all the events that are applicable in the given State;
        an Event is considered applicable in a given State, when all the Event condition
        simplify as True when evaluated in the State.
        :param state: the state where the formulas are evaluated.
        :return: an Iterator of applicable Events.
        '''
        return self._get_applicable_events(state)

    def _get_applicable_events(self, state: 'up.model.ROState') -> Iterator['Event']:
        raise NotImplementedError

    def get_events(self,
                   action: 'up.model.Action',
                   parameters: Union[Tuple['up.model.Expression', ...], List['up.model.Expression']]) -> List['Event']:
        '''
        Returns a list containing all the events derived from the given action, grounded with the given parameters.
        :param action: the action containing the information to create the event.
        :param parameters: the parameters needed to ground the action
        :return: the List of Events derived from this action with these parameters.
        '''
        if action not in cast(up.model.Problem, self._problem).actions:
            raise UPUsageError('The action given as parameter does not belong to the problem given to the SimulatorMixin.')
        if len(action.parameters) != len(parameters):
            raise UPUsageError('The parameters given action do not have the same length of the given parameters.')
        return self._get_events(action, parameters)

    def _get_events(self,
                   action: 'up.model.Action',
                   parameters: Union[Tuple['up.model.Expression', ...], List['up.model.Expression']]) -> List['Event']:
        raise NotImplementedError

    @staticmethod
    def is_simulator():
        return True
