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
"""This module defines the conditional effects remover class."""

import upf.types
import upf.operators as op
from upf.environment import get_env, Environment
from upf.fnode import FNode
from upf.exceptions import UPFProblemDefinitionError, UPFTypeError
from upf.problem_kind import ProblemKind
from upf.operators_extractor import OperatorsExtractor
from upf.problem import Problem
from upf.action import Action
from typing import List, Dict, Tuple


class ConditionalEffectsRemover():
    def __init__(self, problem: Problem):
        self._problem = problem
        self._action_mapping: Dict[str, str] = {}

    def get_unconditional_problem():
        #cycle over all the actions
        #Note that a different environment might be needed when multy-threading
        new_problem: Problem = Problem("unconditional_" + self._problem.name(), self._problem.env())
        action_stack: List[Tuple(str, Action)] = []
        for f in self._problem.fluents().values():
            new_problem.add_fluent(f)
        for o in self._problem.objects().values():
            new_problem.add_object(o)
        for f, v in self._problem.initial_values().items():
            new_problem.set_initial_value(f, v)
        for g in self._problem.goals():
            new_problem.add_goal(g)
        for n, a in self._problem.actions().items():
            if a.has_conditional_effects():
                action_stack.append((n, a))
            else:
                new_problem.add_action(a)

        while len(action_stack) > 0:
            original_action_name, action = action_stack.pop()
            for e in action.effects():
            non_conditional_effects
