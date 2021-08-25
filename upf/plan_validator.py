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

    def is_valid_plan(self, problem, plan) -> bool:
        self._problem = problem
        self._plan = plan
        self._assignments = self._problem.initial_values()
        for ai in self._plan.actions():
            new_assignments: Dict[FNode, FNode] = {}
            for ap, oe in zip(ai.action().parameters(), ai.parameters()):
                self._assignments[ap] = oe
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
                    ge = self._get_ground_fluent(e.fluent())
                    if e.is_assignment():
                        new_assignments[ge] = self._subs_simplify(e.value())
                    elif e.is_increase():
                        new_assignments[ge] = self._subs_simplify(self.manager.Plus(e.fluent(), e.value()))
                    elif e.is_decrease():
                        new_assignments[ge] = self._subs_simplify(self.manager.Minus(e.fluent(), e.value()))
            self._assignments.update(new_assignments)
            for ap in ai.action().parameters():
                del self._assignments[ap]
        for g in self._problem.goals():
            gs = self._subs_simplify(g)
            if not (gs.is_bool_constant() and gs.bool_constant_value()):
                    return False
        return True

    def _get_ground_fluent(self, fluent:FNode) -> FNode:
        assert fluent.is_fluent_exp()
        new_args = []
        for p in fluent.args():
            new_args.append(self._subs_simplify(p))
        return self.manager.FluentExp(fluent.fluent(), tuple(new_args))

    def _subs_simplify(self, expression: FNode) -> FNode:
        to_subst = True
        new_exp = expression
        while to_subst:
        #This do-while loop is necessary because when we have a FluentExp with
        #  some parameters, the first substitution substitutes the parameters with
        #  the object: then every ground fluent is substituted with it's value.
        #  It is a while loop because sometimes more than 2 substitutions can be
        #  required.
            old_exp = new_exp
            new_exp = self._substituter.substitute(new_exp, self._assignments)
            to_subst = not (old_exp == new_exp)
        r = self._simplifier.simplify(new_exp)
        assert r.is_constant()
        return r
