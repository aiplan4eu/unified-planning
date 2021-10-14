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
"""This module defines the different remover classes."""


from upf.action import ActionInterface, Action
from upf.exceptions import UPFProblemDefinitionError
from upf.plan import SequentialPlan, TimeTriggeredPlan, ActionInstance
from upf.problem import Problem
from upf.simplifier import Simplifier
from upf.temporal import DurativeAction
from typing import Dict, Optional, OrderedDict, Union


class Remover:
    """Represents a generic remover with all the support methods shared among them."""
    def __init__(self, problem: Problem):
        self._problem = problem
        self._env = problem.env
        self._new_problem: Optional[Problem] = None
        self._action_mapping: Optional[Dict[ActionInterface, ActionInterface]] = None
        self._simplifier = Simplifier(self._env)

    def get_rewritten_problem(self) -> Problem:
        raise NotImplementedError

    def rewrite_back_plan(self, plan: Union[SequentialPlan, TimeTriggeredPlan]) -> Union[SequentialPlan, TimeTriggeredPlan]:
        '''Takes the sequential plan of the problem (created with
        the method "self.get_rewritten_problem()" and translates the plan back
        to be a plan of the original problem.'''
        #if the remover does not change the name of the actions
        if self._action_mapping is None:
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
                new_actions = plan.actions()
                old_actions = []
                for ai in new_actions:
                    if ai.action() in self._action_mapping:
                        old_actions.append(self._new_action_instance_original_name(ai))
                    else:
                        old_actions.append(ai)
                return SequentialPlan(old_actions)
            elif isinstance(plan, TimeTriggeredPlan):
                new_durative_actions = plan.actions()
                old_durative_actions = []
                for s, ai, d in new_durative_actions:
                    if ai.action() in self._action_mapping:
                        old_durative_actions.append((s, self._new_action_instance_original_name(ai), d))
                    else:
                        old_durative_actions.append((s, ai, d))
                return TimeTriggeredPlan(old_durative_actions)
        raise NotImplementedError

    def _new_action_instance_original_name(self, ai: ActionInstance) -> ActionInstance:
        #original action
        oa = self._action_mapping[ai.action()] # type: ignore
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

    def _new_problem_add_mantain_goals(self):
        for i, gl in self._problem.mantain_goals():
            for g in gl:
                self._new_problem.add_mantain_goal(i, g)

    def _new_problem_add_goals(self):
        for g in self._problem.goals():
            self._new_problem.add_goal(g)

    def _create_action_copy(self, action: Action, id: Optional[int] = None) -> Action:
        if id is not None:
            new_action_name = f'{action.name()}__{str(id)}__'
            if self._problem.has_action(new_action_name):
                raise UPFProblemDefinitionError(f"Action: {new_action_name} of problem: {self._problem.name()} has invalid name. Double underscore '__' is reserved by the naming convention.")
        else:
            new_action_name = action.name()
        #here, if self._action_mapping is a Dict[str, ActionInterface] from name to action it would be possible to add
        # the mapping in the remover and not in every single other remover who needs it.
        return Action(new_action_name, OrderedDict((ap.name(), ap.type()) for ap in action.parameters()), self._env)

    def _action_add_preconditions(self, original_action: Action, new_action: Action):
        for p in original_action.preconditions():
            new_action.add_precondition(p)

    def _create_durative_action_copy(self, action: DurativeAction, id: Optional[int] = None) -> DurativeAction:
        if id is not None:
            new_action_name = f'{action.name()}__{str(id)}__'
            if self._problem.has_action(new_action_name):
                raise UPFProblemDefinitionError(f"Action: {new_action_name} of problem: {self._problem.name()} has invalid name. Double underscore '__' is reserved by the naming convention.")
        else:
            new_action_name = action.name()
        #here, if self._action_mapping is a Dict[str, ActionInterface] from name to action it would be possible to add
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
