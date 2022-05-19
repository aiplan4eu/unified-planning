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


import unified_planning as up
import unified_planning.model
from unified_planning.model import FNode, Action, InstantaneousAction, Expression, Effect
from unified_planning.walkers import Substituter, Simplifier
from typing import Callable, Dict, Optional, Set, Tuple, List
from fractions import Fraction


'''This module defines the different plan classes.'''


class ActionInstance:
    '''Represents an action instance with the actual parameters.'''
    def __init__(self, action: 'unified_planning.model.Action', params: Tuple['unified_planning.model.FNode', ...] = tuple()):
        assert len(action.parameters) == len(params)
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

    @property
    def action(self) -> 'Action':
        '''Returns the action.'''
        return self._action

    @property
    def actual_parameters(self) -> Tuple['FNode', ...]:
        '''Returns the actual parameters.'''
        return self._params

def ground_action_instance(action_instance: ActionInstance, substituter: 'Substituter', simplifier: 'Simplifier') -> 'Action':
    old_action = action_instance.action
    if isinstance(old_action, InstantaneousAction):
        assert len(old_action.parameters) == len(action_instance.actual_parameters)
        if len(old_action.parameters) == 0:
            return old_action.clone()
        new_action = InstantaneousAction(_name=old_action.name, _env=old_action._env)
        assignments: Dict[Expression, Expression] = {param : value for param, value in zip(old_action.parameters, action_instance.actual_parameters)}
        for prec in old_action.preconditions:
            new_action.add_precondition(simplifier.simplify(substituter.substitute(prec, assignments)))
        for eff in old_action.effects:
            new_action._add_effect_instance(
                Effect(
                    simplifier.simplify(substituter.substitute(eff.fluent, assignments)),
                    simplifier.simplify(substituter.substitute(eff.value, assignments)),
                    simplifier.simplify(substituter.substitute(eff.condition, assignments)),
                    eff.kind
                )
            )
        if old_action.simulated_effect is not None:
            raise NotImplementedError
            # TODO: deal with simulated effects!
        return new_action
    else:
        raise NotImplementedError


class Plan:
    '''Represents a generic plan.'''
    def replace_action_instances(self, replace_function: Callable[[ActionInstance], ActionInstance]) -> 'Plan':
        '''This function takes a function from ActionInstance to ActionInstance and returns a new Plan
        that have the ActionInstance modified by the "replace_function" function.'''
        raise NotImplementedError
