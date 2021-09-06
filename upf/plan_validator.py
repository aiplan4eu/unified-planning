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


from typing import Dict, Union, List, Set
import upf.environment
from upf.simplifier import Simplifier
from upf.substituter import Substituter
from upf.fnode import FNode
from upf.expression import Expression
from upf.quantifiers_remover import ExpressionQuantifierRemover
from upf.problem import Problem


class PlanValidator(object):
    """Performs plan validation."""
    def __init__(self, env: 'upf.environment.Environment'):
        self._env = env
        self.manager = env.expression_manager
        self.type_checker = env.type_checker
        self._simplifier = Simplifier(self._env)
        self._substituter = Substituter(self._env)
        self._eqr = ExpressionQuantifierRemover(self._env)
        self._last_error: Union[str, None] = None

    def is_valid_plan(self, problem, plan) -> bool:
        self._last_error = None
        assignments = problem.initial_values()
        count = 0 #used for better error indexing
        for ai in plan.actions():
            count = count + 1
            new_assignments: Dict[Expression, Expression] = {}
            for ap, oe in zip(ai.action().parameters(), ai.actual_parameters()):
                assignments[ap] = oe
            for p in ai.action().preconditions():
                ps = self._subs_simplify(p, assignments, problem)
                if not (ps.is_bool_constant() and ps.bool_constant_value()):
                    self._last_error = f'Precondition {p} of {str(count)}-th action instance {str(ai)} is not satisfied.'
                    return False
            for e in ai.action().effects():
                cond = True
                if e.is_conditional():
                    ec = self._subs_simplify(e.condition(), assignments, problem)
                    assert ec.is_bool_constant()
                    cond = ec.bool_constant_value()
                if cond:
                    ge = self._get_ground_fluent(e.fluent(), assignments, problem)
                    if e.is_assignment():
                        new_assignments[ge] = self._subs_simplify(e.value(), assignments, problem)
                    elif e.is_increase():
                        new_assignments[ge] = self._subs_simplify(self.manager.Plus(e.fluent(),
                                                e.value()), assignments, problem)
                    elif e.is_decrease():
                        new_assignments[ge] = self._subs_simplify(self.manager.Minus(e.fluent(),
                                                e.value()), assignments, problem)
            assignments.update(new_assignments)
            for ap in ai.action().parameters():
                del assignments[ap]
        for g in problem.goals():
            gs = self._subs_simplify(g, assignments, problem)
            if not (gs.is_bool_constant() and gs.bool_constant_value()):
                    self._last_error = f'Goal {str(g)} is not reached by the plan.'
                    return False
        return True

    def get_last_error_info(self):
        assert not self._last_error is None
        return self._last_error

    def _get_ground_fluent(self, fluent:FNode, assignments: Dict[Expression, Expression], problem: Problem) -> FNode:
        assert fluent.is_fluent_exp()
        new_args = []
        for p in fluent.args():
            new_args.append(self._subs_simplify(p, assignments, problem))
        return self.manager.FluentExp(fluent.fluent(), tuple(new_args))

    def _subs_simplify(self, expression: FNode, assignments: Dict[Expression, Expression], problem: Problem) -> FNode:
        old_exp = None
        new_exp = self._eqr.remove_quantifiers(expression, problem)
        while old_exp != new_exp:
        #This do-while loop is necessary because when we have a FluentExp with
        #  some parameters, the first substitution substitutes the parameters with
        #  the object: then every ground fluent is substituted with it's value.
        #  It is a while loop because sometimes more than 2 substitutions can be
        #  required.
            old_exp = new_exp
            new_exp = self._substituter.substitute(new_exp, assignments)
        r = self._simplifier.simplify(new_exp)
        assert r.is_constant()
        return r
