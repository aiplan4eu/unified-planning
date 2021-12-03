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
"""This module defines the solver interface."""

import upf
import upf.model
from upf.plan import Plan, ActionInstance, SequentialPlan, TimeTriggeredPlan
from upf.model import ProblemKind, Problem, Action, FNode
from functools import partial
from typing import Optional, Tuple, Dict, List, Callable


class Solver:
    """Represents the solver interface."""

    def __init__(self, **kwargs):
        if len(kwargs) > 0:
            raise

    @staticmethod
    def name() -> str:
        raise NotImplementedError

    @staticmethod
    def is_oneshot_planner() -> bool:
        return False

    @staticmethod
    def is_plan_validator() -> bool:
        return False

    @staticmethod
    def is_grounder() -> bool:
        return False

    @staticmethod
    def supports(problem_kind: 'ProblemKind') -> bool:
        return len(problem_kind.features()) == 0

    def solve(self, problem: 'upf.model.Problem') -> Optional['upf.plan.Plan']:
        raise NotImplementedError

    def validate(self, problem: 'upf.model.Problem', plan: 'upf.plan.Plan') -> bool:
        raise NotImplementedError

    def _ground(self, problem: 'upf.model.Problem') -> Tuple[Problem, Dict[Action, Tuple[Action, List[FNode]]]]:
        '''This function should return the tuple (grounded_problem, trace_back_map), where
        "trace_back_map" is a map from every action in the "grounded_problem" to the tuple
        (original_action, parameters). Where the grounded actions is obtained by grounding
        the "original_action" with the specific "parameters". '''
        raise NotImplementedError

    def ground(self, problem: 'upf.model.Problem') -> Tuple[Problem, Callable[[Plan], Plan]]:
        '''This function should return the tuple (grounded_problem, trace_back_map), where
        "trace_back_map" is a map from every action in the "grounded_problem" to the tuple
        (original_action, parameters). Where the grounded actions is obtained by grounding
        the "original_action" with the specific "parameters". '''
        grounded_problem, rewrite_back_plan_map = self._ground(problem)
        return (grounded_problem, self._get_lift_plan_function(rewrite_back_plan_map))

    def _lift_plan(self, plan: Plan, map: Dict[Action, Tuple[Action, List[FNode]]]) -> Plan:
        if isinstance(plan, SequentialPlan):
            original_actions: List[ActionInstance] = []
            for ai in plan.actions():
                original_action, parameters = map[ai.action()]
                original_actions.append(ActionInstance(original_action, tuple(parameters)))
            return SequentialPlan(original_actions)
        elif isinstance(plan, TimeTriggeredPlan):
            s_original_actions_d = []
            for s, ai, d in plan.actions():
                original_action, parameters = map[ai.action()]
                s_original_actions_d.append((s, ActionInstance(original_action, tuple(parameters)), d))
            return TimeTriggeredPlan(s_original_actions_d)
        raise NotImplementedError

    def _get_lift_plan_function(self, map: Dict[Action, Tuple[Action, List[FNode]]]) -> Callable[[Plan], Plan]:
        '''This function returns a function that given a grounded plan retrieves the lifted plan
         (a plan of the problem before grounding).'''
        return partial(self._lift_plan, map=map)

    def destroy(self):
        raise NotImplementedError

    def __enter__(self):
        """Manages entering a Context (i.e., with statement)"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Manages exiting from Context (i.e., with statement)"""
        self.destroy()
