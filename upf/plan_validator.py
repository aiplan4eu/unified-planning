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


from typing import Dict
import upf.environment
from upf.simplifier import Simplifier
from upf.substituter import Substituter
from upf.problem import Problem
from upf.plan import Plan, ActionInstance, SequentialPlan
from upf.fluent import Fluent
from upf.fnode import FNode
from upf.expression import Expression


class PlanValidator(object):
    """Performs plan validation."""
    def __init__(self, env: 'upf.environment.Environment'):
        self._env = env
        self.manager = env.expression_manager
        self.type_checker = env.type_checker
        self._simplifier = Simplifier(self._env)
        self._substituter = Substituter(self._env)
        self._subst: Dict[Expression, Expression] = {}

    def is_valid_plan(self, problem, plan) -> bool:
        self._problem = problem
        self._plan = plan
        self._subst = self._problem.initial_values()
        for ai in self._plan.actions():
            for p in ai.action().preconditions():
                ps = self._subs_simplify(p)
                if not (ps.is_bool_constant() and ps.bool_constant_value()):
                    return False
            for e in ai.action().effects():
                cond = True
                if e.is_conditional():
                    ec = self._subs_simplify(e.condition())
                if not (ec.is_bool_constant() and ec.bool_constant_value()):
                    cond = False
                if cond:
                    if e.is_assignment():
                        self._subst[e.fluent()] = self._subs_simplify(e.value())
                    elif e.is_increase():
                        self._subst[e.fluent()] = self._subs_simplify(self.manager.Plus(e.fluent(), e.value()))
                    elif e.is_decrease():
                        self._subst[e.fluent()] = self._subs_simplify(self.manager.Minus(e.fluent(), e.value()))
        for g in self._problem.goals():
            gs = self._subs_simplify(g)
            if not (gs.is_bool_constant() and gs.bool_constant_value()):
                    return False
        return True

    def _subs_simplify(self, expression: FNode) -> FNode:
        es = self._substituter.substitute(expression, self._subst)
        return self._simplifier.simplify(es)
