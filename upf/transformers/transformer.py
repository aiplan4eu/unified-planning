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


import upf
from upf.model.fnode import FNode
from upf.model.action import Action, InstantaneousAction, DurativeAction
from upf.exceptions import UPFProblemDefinitionError
from upf.plan import SequentialPlan, TimeTriggeredPlan, ActionInstance
from upf.model.problem import Problem
from upf.model.timing import Timing
from typing import Dict, List, Optional, OrderedDict, Tuple, Union


class Transformer:
    '''Represents a generic remover with all the support methods shared among them.'''
    def __init__(self, problem: Problem):
        self._problem = problem
        self._env = problem.env
        self._new_problem: Optional[Problem] = None
        #Represents the map from the new action to the old action
        self._new_to_old: Optional[Dict[Action, Action]] = None
        #represents a mapping from the action of the original problem to action of the new one.
        self._old_to_new: Optional[Dict[Action, List[Action]]] = None
        self._simplifier = upf.walkers.Simplifier(self._env)

    def get_old_to_new_actions_mapping(self) -> Optional[Dict[Action, List[Action]]]:
        return self._old_to_new

    def _map_old_to_new_action(self, old_action, new_action):
        if old_action in self._old_to_new:
            self._old_to_new[old_action].append(new_action)
        else:
            self._old_to_new[old_action] = [new_action]

    def get_rewritten_problem(self) -> Problem:
        raise NotImplementedError

    def rewrite_back_plan(self, plan: Union[SequentialPlan, TimeTriggeredPlan]) -> Union[SequentialPlan, TimeTriggeredPlan]:
        '''Takes the sequential plan of the problem (created with
        the method "self.get_rewritten_problem()" and translates the plan back
        to be a plan of the original problem.'''
        #if the remover does not change the name of the actions
        if self._new_to_old is None:
            if isinstance(plan, SequentialPlan):
                actions = [ActionInstance(self._problem.action(ai.action().name()),
                                ai.actual_parameters()) for ai in plan.actions()]
                return SequentialPlan(actions)
            elif isinstance(plan, TimeTriggeredPlan):
                s_actions_d = [(s,
                                ActionInstance(self._problem.action(ai.action().name()),
                                ai.actual_parameters()), d) for s, ai, d in plan.actions()]
                return TimeTriggeredPlan(s_actions_d)
        else:
            if isinstance(plan, SequentialPlan):
                new_actions: List[ActionInstance] = plan.actions()
                old_actions: List[ActionInstance] = []
                for ai in new_actions:
                    if ai.action() in self._new_to_old:
                        old_actions.append(self._new_action_instance_original_name(ai))
                    else:
                        old_actions.append(ai)
                return SequentialPlan(old_actions)
            elif isinstance(plan, TimeTriggeredPlan):
                s_new_actions_d = plan.actions()
                s_old_actions_d = []
                for s, ai, d in s_new_actions_d:
                    if ai.action() in self._new_to_old:
                        s_old_actions_d.append((s, self._new_action_instance_original_name(ai), d))
                    else:
                        s_old_actions_d.append((s, ai, d))
                return TimeTriggeredPlan(s_old_actions_d)
        raise NotImplementedError

    def _new_action_instance_original_name(self, ai: ActionInstance) -> ActionInstance:
        #original action
        oa = self._new_to_old[ai.action()] # type: ignore
        return ActionInstance(oa, ai.actual_parameters())

    def _create_problem_copy(self, str_to_add: str):
        self._new_problem = Problem(str_to_add + "_" + str(self._problem.name()), self._env)

    def _new_problem_add_fluents(self):
        for f in self._problem.fluents().values():
            self._new_problem.add_fluent(f)

    def _new_problem_add_objects(self):
        for o in self._problem.all_objects():
            self._new_problem.add_object(o)

    def _new_problem_add_initial_values(self):
        for fl, v in self._problem.initial_values().items():
            self._new_problem.set_initial_value(fl, v)

    def _new_problem_add_timed_effects(self):
        for t, el in self._problem.timed_effects():
            for e in el:
                self._new_problem.add_timed_effect(t, e)

    def _new_problem_add_timed_goals(self):
        for t, gl in self._problem.timed_goals():
            for g in gl:
                self._new_problem.add_timed_goal(t, g)

    def _new_problem_add_maintain_goals(self):
        for i, gl in self._problem.maintain_goals():
            for g in gl:
                self._new_problem.add_maintain_goal(i, g)

    def _new_problem_add_goals(self):
        for g in self._problem.goals():
            self._new_problem.add_goal(g)

    def _create_action_copy(self, action: InstantaneousAction, id: Optional[int] = None) -> InstantaneousAction:
        if id is not None:
            new_action_name = f'{action.name()}__{str(id)}__'
            if self._problem.has_action(new_action_name):
                raise UPFProblemDefinitionError(f"InstantaneousAction: {new_action_name} of problem: {self._problem.name()} has invalid name. Double underscore '__' is reserved by the naming convention.")
        else:
            new_action_name = action.name()
        #here, if self._new_to_old is a Dict[str, Action] from name to action it would be possible to add
        # the mapping in the remover and not in every single other remover who needs it.
        return InstantaneousAction(new_action_name, OrderedDict((ap.name(), ap.type()) for ap in action.parameters()), self._env)

    def _action_add_preconditions(self, original_action: InstantaneousAction, new_action: InstantaneousAction):
        for p in original_action.preconditions():
            new_action.add_precondition(p)

    def _action_add_effects(self, original_action: InstantaneousAction, new_action: InstantaneousAction):
        for e in original_action.effects():
            new_action._add_effect_instance(e)

    def _create_durative_action_copy(self, action: DurativeAction, id: Optional[int] = None) -> DurativeAction:
        if id is not None:
            new_action_name = f'{action.name()}__{str(id)}__'
            if self._problem.has_action(new_action_name):
                raise UPFProblemDefinitionError(f"InstantaneousAction: {new_action_name} of problem: {self._problem.name()} has invalid name. Double underscore '__' is reserved by the naming convention.")
        else:
            new_action_name = action.name()
        #here, if self._new_to_old is a Dict[str, Action] from name to action it would be possible to add
        # the mapping in the remover and not in every single other remover who needs it.
        nda = DurativeAction(new_action_name, OrderedDict((ap.name(), ap.type()) for ap in action.parameters()), self._env)
        nda.set_duration_constraint(action.duration())
        return nda

    def _durative_action_add_conditions(self, original_action: DurativeAction, new_action: DurativeAction):
        for t, c in original_action.conditions().items():
            new_action.add_condition(t, c)

    def _durative_action_add_durative_conditions(self, original_action: DurativeAction, new_action: DurativeAction):
        for i, dc in original_action.durative_conditions().items():
            new_action.add_durative_condition(i, dc)

    def _durative_action_add_effects(self, original_action: DurativeAction, new_action: DurativeAction):
        for t, el in original_action.effects().items():
            for e in el:
                new_action._add_effect_instance(t, e)

    def _check_and_simplify_conditions(self, action: DurativeAction) -> bool:
        '''Simplifies conditions and if it is False (a contraddiction)
        returns False, otherwise returns True.
        If the simplification is True (a tautology) removes all conditions at the given timing.
        If the simplification is still an AND rewrites back every "arg" of the AND
        in the conditions
        If the simplification is not an AND sets the simplification as the only
        condition at the given timing.'''
        #action conditions
        #tlc = timing list condition
        tlc: Dict[Timing, List[FNode]] = action.conditions()
        if len(tlc) == 0:
            return True
        # t = timing, lc = list condition
        for t, lc in tlc.copy().items():
            #conditions (as an And FNode)
            c = self._env.expression_manager.And(lc)
            #conditions simplified
            cs = self._simplifier.simplify(c)
            #new action conditions
            nac: List[FNode] = []
            if cs.is_bool_constant():
                if not cs.bool_constant_value():
                    return False
            else:
                if cs.is_and():
                    nac.extend(cs.args())
                else:
                    nac.append(cs)
            action._set_conditions(t, nac)
        return True

    def _check_and_simplify_preconditions(self, action: InstantaneousAction) -> bool:
        '''Simplifies preconditions and if it is False (a contraddiction)
        returns False, otherwise returns True.
        If the simplification is True (a tautology) removes all preconditions.
        If the simplification is still an AND rewrites back every "arg" of the AND
        in the preconditions
        If the simplification is not an AND sets the simplification as the only
        precondition.'''
        #action preconditions
        ap = action.preconditions()
        if len(ap) == 0:
            return True
        #preconditions (as an And FNode)
        p = self._env.expression_manager.And(ap)
        #preconditions simplified
        ps = self._simplifier.simplify(p)
        #new action preconditions
        nap: List[FNode] = []
        if ps.is_bool_constant():
            if not ps.bool_constant_value():
                return False
        else:
            if ps.is_and():
                nap.extend(ps.args())
            else:
                nap.append(ps)
        action._set_preconditions(nap)
        return True
