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


import upf.environment
import upf.walkers as walkers
import upf.operators as op
from upf.fnode import FNode

class IdentityDagWalker(walkers.DagWalker):
    """This class traverses a formula and rebuilds it recursively
    identically.
    This could be useful when only some nodes needs to be rewritten
    but the structure of the formula has to be kept.
    """

    def __init__(self, env: 'upf.environment.Environment', invalidate_memoization=False):
        walkers.DagWalker.__init__(self, invalidate_memoization)
        self.env = env
        self.manager = env.expression_manager


    def walk_and(self, args, **kwargs):
        return self.manager.And(args)

    def walk_or(self, args, **kwargs):
        return self.manager.Or(args)

    def walk_not(self, args, **kwargs):
        return self.manager.Not(args[0])

    def walk_iff(self, args, **kwargs):
        return self.manager.Iff(args[0], args[1])

    def walk_implies(self, args, **kwargs):
        return self.manager.Implies(args[0], args[1])

    def walk_equals(self, args, **kwargs):
        return self.manager.Equals(args[0], args[1])

    def walk_le(self, args, **kwargs):
        return self.manager.LE(args[0], args[1])

    def walk_lt(self, args, **kwargs):
        return self.manager.LT(args[0], args[1])

    def walk_plus(self, args, **kwargs):
        return self.manager.Plus(args)

    def walk_times(self, args, **kwargs):
        return self.manager.Times(args)

    def walk_minus(self, args, **kwargs):
        return self.manager.Minus(args[0], args[1])

    def walk_div(self, args, **kwargs):
        return self.manager.Div(args[0], args[1])

    def walk_fluent_exp(self, expression: FNode, args: List[FNode]) -> FNode:
        return self.manager.FluentExp(expression.fluent(), tuple(args))

    @walkers.handles(op.IRA_OPERATORS)
    @walkers.handles(op.CONSTANTS)
    @walkers.handles(op.PARAM_EXP, op.OBJECT_EXP)
    def walk_identity(self, expression: FNode, args: List[FNode]) -> FNode:
        return expression
