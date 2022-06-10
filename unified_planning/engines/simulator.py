
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

from typing import Callable, Dict, Iterator, List, Optional, Tuple, Union, cast
import unified_planning as up
from unified_planning.engines.compilers import Grounder
from unified_planning.exceptions import UPUsageError
from unified_planning.plans import ActionInstance
from unified_planning.walkers import StateEvaluator


class Event:
    '''This is an abstract class representing an event.'''

    @property
    def conditions(self) -> List['up.model.FNode']:
        raise NotImplementedError

    @property
    def effects(self) -> List['up.model.Effect']:
        raise NotImplementedError


class InstantaneousEvent(Event):
    '''Implements the Event class for an Instantaneous Action.'''

    def __init__(self, conditions: List['up.model.FNode'], effects: List['up.model.Effect']):
        self._conditions = conditions
        self._effects = effects

    @property
    def conditions(self) -> List['up.model.FNode']:
        return self._conditions

    @property
    def effects(self) -> List['up.model.Effect']:
        return self._effects


class Simulator:
    #TODO: DOCUMENTATION

    def __init__(self, problem: 'up.model.Problem'):
        self._problem = problem
        self._grounder = Grounder()
        self._grounding_result = self._grounder.compile(self._problem, up.engines.CompilationKind.GROUNDER)

        self._grounded_problem: 'up.model.Problem' = cast(up.model.Problem, self._grounding_result.problem)
        self._map = cast(Callable[[ActionInstance], ActionInstance], self._grounding_result.map_back_action_instance)
        self._events: Dict[Tuple['up.model.Action', Tuple['up.model.FNode', ...]], List[Event]] = {}
        for grounded_action in self._grounded_problem.actions:
            if isinstance(grounded_action, up.model.InstantaneousAction):
                lifted_ai = self._map(ActionInstance(grounded_action))
                event_list = self._events.setdefault((lifted_ai.action, lifted_ai.actual_parameters), [])
                event_list.append(InstantaneousEvent(grounded_action.preconditions, grounded_action.effects))
            else:
                raise NotImplementedError

    def is_applicable(self, event: 'Event', state: 'up.model.ROState') -> bool:
        '''
        Returns True if the given event conditions are evaluated as True in the given state;
        returns False otherwise.
        :param state: the state where the event conditions are checked.
        :param event: the event whose conditions are checked.
        :return: Whether or not the event is applicable in the given state.
        '''
        se = StateEvaluator(self._problem)
        # Evaluate every condition and if the condition is False or the condition is not simplified as a
        # boolean constant in the given state, return False. Return True otherwise
        for c in event.conditions:
            evaluated_cond = se.evaluate(c, state)
            if not evaluated_cond.is_bool_constant() or not evaluated_cond.bool_constant_value():
                return False
        return True

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
        if not self.is_applicable(event, state):
            return None
        else:
            return self.apply_unsafe(event, state)

    def apply_unsafe(self, event: 'Event', state: 'up.model.RWState') -> 'up.model.RWState':
        '''
        Returns a new RWState, which is a copy of the given state but the applicable effects of the event are applied; therefore
        some fluent values are updated.
        IMPORTANT NOTE: Assumes that self.is_applicable(state, event) returns True
        :param state: the state where the event formulas are evaluated.
        :param event: the event that has the information about the effects to apply.
        :return: A new RWState with some updated values.
        '''
        se = StateEvaluator(self._problem)
        updated_values: Dict['up.model.FNode', 'up.model.FNode'] = {}
        em = self._problem.env.expression_manager
        for e in event.effects:
            cond = self._problem._env.expression_manager.TRUE()
            if e.is_conditional():
                cond = se.evaluate(e.condition, state)
            if cond.is_bool_constant() and cond.bool_constant_value():
                if e.is_assignment():
                    updated_values[e.fluent] = se.evaluate(e.value, state)
                elif e.is_increase():
                    updated_values[e.fluent] = se.evaluate(em.Plus(e.fluent, e.value), state)
                elif e.is_decrease():
                    updated_values[e.fluent] = se.evaluate(em.Minus(e.fluent, e.value), state)
                else:
                    raise NotImplementedError
        return state.set_values(updated_values)

    def get_applicable_events(self, state: 'up.model.ROState') -> Iterator['Event']:
        '''
        Returns a view over all the events that are applicable in the given State;
        an Event is considered applicable in a given State, when all the Event condition
        simplify as True when evaluated in the State.
        :param state: the state where the formulas are evaluated.
        :return: an Iterator of applicable Events.
        '''
        for action in self._grounded_problem.actions:
            ai = self._map(ActionInstance(action))
            for event in self.get_events(ai.action, ai.actual_parameters):
                if self.is_applicable(event, state):
                    yield event

    def get_events(self,
                   action: 'up.model.Action',
                   parameters: Union[Tuple['up.model.FNode', ...], List['up.model.FNode']]) -> List['Event']:
        '''
        Returns a list containing all the events derived from the given action, grounded with the given parameters.
        :param action: the action containing the information to create the event.
        :param parameters: the parameters needed to ground the action
        :return: an Iterator of applicable Events.
        '''
        if action not in self._problem.actions:
            raise UPUsageError('The action given as parameter does not belong to the problem given to the Simulator.')
        if len(action.parameters) != len(parameters):
            raise UPUsageError('The parameters given action do not have the same length of the given parameters.')
        return self._events.get((action,tuple(parameters)), [])
