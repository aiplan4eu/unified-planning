
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
from unified_planning.engines.engine import Engine
from unified_planning.engines.mixins.simulator import Event, Simulator
from unified_planning.exceptions import UPUsageError
from unified_planning.plans import ActionInstance
from unified_planning.walkers import StateEvaluator


class InstantaneousEvent(Event):
    '''Implements the Event class for an Instantaneous Action.'''

    def __init__(self,
                 conditions: List['up.model.FNode'],
                 effects: List['up.model.Effect'],
                 simulated_effect: Optional['up.model.SimulatedEffect'] = None):
        self._conditions = conditions
        self._effects = effects
        self._simulated_effect = simulated_effect

    @property
    def conditions(self) -> List['up.model.FNode']:
        return self._conditions

    @property
    def effects(self) -> List['up.model.Effect']:
        return self._effects

    @property
    def simulated_effect(self) -> Optional['up.model.SimulatedEffect']:
        return self._simulated_effect


class SequentialSimulator(Engine, Simulator):
    '''
    Sequential Simulator implementation.
    '''

    def __init__(self, problem: 'up.model.Problem'):
        self._problem = problem
        pk = problem.kind
        assert SequentialSimulator.supports(pk)
        assert Grounder.supports(pk)
        grounder = Grounder()
        self._grounding_result = grounder.compile(self._problem, up.engines.CompilationKind.GROUNDING)

        self._grounded_problem: 'up.model.Problem' = cast(up.model.Problem, self._grounding_result.problem)
        self._map = cast(Callable[[ActionInstance], ActionInstance], self._grounding_result.map_back_action_instance)
        self._events: Dict[Tuple['up.model.Action', Tuple['up.model.FNode', ...]], List[Event]] = {}
        for grounded_action in self._grounded_problem.actions:
            if isinstance(grounded_action, up.model.InstantaneousAction):
                lifted_ai = self._map(ActionInstance(grounded_action))
                event_list = self._events.setdefault((lifted_ai.action, lifted_ai.actual_parameters), [])
                event_list.append(
                    InstantaneousEvent(
                        grounded_action.preconditions,
                        grounded_action.effects,
                        grounded_action.simulated_effect))
            else:
                raise NotImplementedError
        self._se = StateEvaluator(self._problem)

    def is_applicable(self, event: 'Event', state: 'up.model.ROState') -> bool:
        '''
        Returns True if the given event conditions are evaluated as True in the given state;
        returns False otherwise.
        :param state: the state where the event conditions are checked.
        :param event: the event whose conditions are checked.
        :return: Whether or not the event is applicable in the given state.
        '''
        # Evaluate every condition and if the condition is False or the condition is not simplified as a
        # boolean constant in the given state, return False. Return True otherwise
        for c in event.conditions:
            evaluated_cond = self._se.evaluate(c, state)
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
        updated_values: Dict['up.model.FNode', 'up.model.FNode'] = {}
        em = self._problem.env.expression_manager
        for e in event.effects:
            cond = self._problem._env.expression_manager.TRUE()
            if e.is_conditional():
                cond = self._se.evaluate(e.condition, state)
            if cond.is_bool_constant() and cond.bool_constant_value():
                if e.is_assignment():
                    updated_values[e.fluent] = self._se.evaluate(e.value, state)
                elif e.is_increase():
                    f_eval = self._se.evaluate(e.fluent, state)
                    v_eval = self._se.evaluate(e.value, state)
                    updated_values[e.fluent] = em.auto_promote(f_eval.constant_value() + v_eval.constant_value())[0]
                elif e.is_decrease():
                    f_eval = self._se.evaluate(e.fluent, state)
                    v_eval = self._se.evaluate(e.value, state)
                    updated_values[e.fluent] = em.auto_promote(f_eval.constant_value() - v_eval.constant_value())[0]
                else:
                    raise NotImplementedError
        if event.simulated_effect is not None:
            for f, v in zip(event.simulated_effect.fluents, event.simulated_effect.function(self._problem, state, {})):
                updated_values[f] = v
        return state.set_values(updated_values)

    def get_applicable_events(self, state: 'up.model.ROState') -> Iterator['Event']:
        '''
        Returns a view over all the events that are applicable in the given State;
        an Event is considered applicable in a given State, when all the Event condition
        simplify as True when evaluated in the State.
        :param state: the state where the formulas are evaluated.
        :return: an Iterator of applicable Events.
        '''
        for events in self._events.values():
            for event in events:
                if self.is_applicable(event, state):
                    yield event

    def get_events(self,
                   action: 'up.model.Action',
                   parameters: Union[Tuple['up.model.Expression', ...], List['up.model.Expression']]) -> List['Event']:
        '''
        Returns a list containing all the events derived from the given action, grounded with the given parameters.
        :param action: the action containing the information to create the event.
        :param parameters: the parameters needed to ground the action
        :return: the List of Events derived from this action with these parameters.
        '''
        if action not in self._problem.actions:
            raise UPUsageError('The action given as parameter does not belong to the problem given to the Simulator.')
        if len(action.parameters) != len(parameters):
            raise UPUsageError('The parameters given action do not have the same length of the given parameters.')
        params_exp = tuple(self._problem.env.expression_manager.auto_promote(parameters))
        return self._events.get((action, tuple(params_exp)), [])

    @property
    def name(self) -> str:
        return 'sequential_simulator'

    @staticmethod
    def supported_kind() -> 'up.model.ProblemKind':
        supported_kind = up.model.ProblemKind()
        supported_kind.set_problem_class('ACTION_BASED') # type: ignore
        supported_kind.set_typing('FLAT_TYPING') # type: ignore
        supported_kind.set_typing('HIERARCHICAL_TYPING') # type: ignore
        supported_kind.set_numbers('CONTINUOUS_NUMBERS') # type: ignore
        supported_kind.set_numbers('DISCRETE_NUMBERS') # type: ignore
        supported_kind.set_fluents_type('NUMERIC_FLUENTS') # type: ignore
        supported_kind.set_fluents_type('OBJECT_FLUENTS') # type: ignore
        supported_kind.set_conditions_kind('NEGATIVE_CONDITIONS') # type: ignore
        supported_kind.set_conditions_kind('DISJUNCTIVE_CONDITIONS') # type: ignore
        supported_kind.set_conditions_kind('EQUALITY') # type: ignore
        supported_kind.set_conditions_kind('EXISTENTIAL_CONDITIONS') # type: ignore
        supported_kind.set_conditions_kind('UNIVERSAL_CONDITIONS') # type: ignore
        supported_kind.set_effects_kind('CONDITIONAL_EFFECTS') # type: ignore
        supported_kind.set_effects_kind('INCREASE_EFFECTS') # type: ignore
        supported_kind.set_effects_kind('DECREASE_EFFECTS') # type: ignore
        supported_kind.set_simulated_entities('SIMULATED_EFFECTS') # type: ignore
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= SequentialSimulator.supported_kind()
