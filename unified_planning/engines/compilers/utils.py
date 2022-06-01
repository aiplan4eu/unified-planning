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
'''This module defines the different remover classes.'''


import unified_planning as up
import unified_planning.walkers
from unified_planning.model import FNode, Timing, TimeInterval, Action, InstantaneousAction, DurativeAction, Problem, Effect, Expression, SimulatedEffect, Parameter
from unified_planning.plan import SequentialPlan, TimeTriggeredPlan, ActionInstance, Plan
from typing import Dict, Iterable, List, Optional, OrderedDict, Tuple, Union


def check_and_simplify_conditions(problem: Problem, action: DurativeAction, simplifier,
                                  simplify_constants: bool = False) -> Tuple[bool, List[Tuple[TimeInterval, FNode]]]:
    '''Simplifies conditions and if it is False (a contraddiction)
    returns False, otherwise returns True.
    If the simplification is True (a tautology) removes all conditions at the given timing.
    If the simplification is still an AND rewrites back every "arg" of the AND
    in the conditions
    If the simplification is not an AND sets the simplification as the only
    condition at the given timing.
    Then, the new conditions are returned as a List[Tuple[Timing, FNode]] and the user can
    decide how to use the new conditions.'''
    #new action conditions
    nac: List[Tuple[TimeInterval, FNode]] = []
    # t = timing, lc = list condition
    for i, lc in action.conditions.items():
        #conditions (as an And FNode)
        c = problem.env.expression_manager.And(lc)
        #conditions simplified
        if simplify_constants:
            cs = simplifier.simplify(c, problem)
        else:
            cs = simplifier.simplify(c)
        if cs.is_bool_constant():
            if not cs.bool_constant_value():
                return (False, [],)
        else:
            if cs.is_and():
                for new_cond in cs.args:
                    nac.append((i, new_cond))
            else:
                nac.append((i, cs))
    return (True, nac)


def check_and_simplify_preconditions(problem: Problem, action: InstantaneousAction, simplifier,
                                     simplify_constants: bool = False) -> Tuple[bool, List[FNode]]:
    '''Simplifies preconditions and if it is False (a contraddiction)
    returns False, otherwise returns True.
    If the simplification is True (a tautology) removes all preconditions.
    If the simplification is still an AND rewrites back every "arg" of the AND
    in the preconditions
    If the simplification is not an AND sets the simplification as the only
    precondition.
    Then, the new preconditions are returned as a List[FNode] and the user can
    decide how to use the new preconditions.'''
    #action preconditions
    ap = action.preconditions
    if len(ap) == 0:
        return (True, [])
    #preconditions (as an And FNode)
    p = problem.env.expression_manager.And(ap)
    #preconditions simplified
    if simplify_constants:
        ps = simplifier.simplify(p, problem)
    else:
        ps = simplifier.simplify(p)
    #new action preconditions
    nap: List[FNode] = []
    if ps.is_bool_constant():
        if not ps.bool_constant_value():
            return (False, [])
    else:
        if ps.is_and():
            nap.extend(ps.args)
        else:
            nap.append(ps)
    action._set_preconditions(nap)
    return (True, nap)


def create_effect_with_given_subs(problem: Problem, old_effect: Effect,
                                  simplifier, substituter,
                                  subs: Dict[Expression, Expression]) -> Optional[Effect]:
    new_fluent = substituter.substitute(old_effect.fluent, subs)
    new_value = substituter.substitute(old_effect.value, subs)
    new_condition = simplifier.simplify(substituter.substitute(old_effect.condition, subs), problem)
    if new_condition == problem.env.expression_manager.FALSE():
        return None
    else:
        return Effect(new_fluent, new_value, new_condition, old_effect.kind)


def create_action_with_given_subs(problem: Problem, old_action: Action,
                                  simplifier, substituter,
                                  subs: Dict[Expression, Expression]) -> Optional[Action]:
    naming_list: List[str] = []
    for param, value in subs.items():
        assert isinstance(param, Parameter)
        assert isinstance(value, FNode)
        naming_list.append(str(value))
    if isinstance(old_action, InstantaneousAction):
        new_action = InstantaneousAction(get_fresh_name(problem, old_action.name, naming_list))
        for p in old_action.preconditions:
            new_action.add_precondition(substituter.substitute(p, subs))
        for e in old_action.effects:
            new_effect = create_effect_with_given_subs(problem, e, simplifier, substituter, subs)
            if new_effect is not None:
                new_action._add_effect_instance(new_effect)
        se = old_action.simulated_effect
        if se is not None:
            new_fluents = []
            for f in se.fluents:
                new_fluents.append(substituter.substitute(f, subs))
            def fun(_problem, _state, _):
                return se.function(_problem, _state, subs)
            new_action.set_simulated_effect(SimulatedEffect(new_fluents, fun))
        is_feasible, new_preconditions = check_and_simplify_preconditions(problem, new_action, simplifier, simplify_constants=True)
        if not is_feasible:
            return None
        new_action._set_preconditions(new_preconditions)
        return new_action
    elif isinstance(old_action, DurativeAction):
        new_durative_action = DurativeAction(get_fresh_name(problem, old_action.name, naming_list))
        new_durative_action.set_duration_constraint(old_action.duration)
        for i, cl in old_action.conditions.items():
            for c in cl:
                new_durative_action.add_condition(i, substituter.substitute(c, subs))
        for t, el in old_action.effects.items():
            for e in el:
                new_effect = create_effect_with_given_subs(problem, e, simplifier, substituter, subs)
                if new_effect is not None:
                    new_durative_action._add_effect_instance(t, new_effect)
        for t, se in old_action.simulated_effects.items():
            new_fluents = []
            for f in se.fluents:
                new_fluents.append(substituter.substitute(f, subs))
            def fun(_problem, _state, _):
                return se.function(_problem, _state, subs)
            new_durative_action.set_simulated_effect(t, SimulatedEffect(new_fluents, fun))
        is_feasible, new_conditions = check_and_simplify_conditions(problem, new_durative_action, simplifier, simplify_constants=True)
        if not is_feasible:
            return None
        new_durative_action.clear_conditions()
        for interval, c in new_conditions:
            new_durative_action.add_condition(interval, c)
        return new_durative_action
    else:
        raise NotImplementedError


def get_fresh_name(problem: Problem, original_name: str,
                   parameters_names: Iterable[str] = []) -> str:
    '''This method returns a fresh name for the problem, given a name and an iterable of names in input.'''
    name_list = [original_name]
    name_list.extend(parameters_names)
    new_name = '_'.join(name_list)
    base_name = new_name
    count = 0
    while problem.has_name(new_name):
        new_name = f'{base_name}_{str(count)}'
        count += 1
    return new_name


def lift_action_instance(action_instance: ActionInstance, map: Dict['up.model.Action', Tuple['up.model.Action', List['up.model.FNode']]]) -> ActionInstance:
    '''"map" is a map from every action in the "grounded_problem" to the tuple
        (original_action, parameters).

        Where the grounded actions is obtained by grounding
        the "original_action" with the specific "parameters".'''
    lifted_action, parameters = map[action_instance.action]
    return ActionInstance(lifted_action, tuple(parameters))


def replace_action(action_instance: ActionInstance, map: Dict['up.model.Action', 'up.model.Action']) -> ActionInstance:
    return ActionInstance(map[action_instance.action], action_instance.actual_parameters)
