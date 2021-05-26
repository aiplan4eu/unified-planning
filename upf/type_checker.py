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

import upf.walkers as walkers
import upf.operators as op
from upf.typing import BOOL


class TypeChecker(walkers.DagWalker):
    def __init__(self):
        walkers.DagWalker.__init__(self)

    def get_type(self, expression):
        """ Returns the pysmt.types type of the expression """
        res = self.walk(expression)
        if res is None:
            raise PysmtTypeError("The expression '%s' is not well-formed" \
                                 % str(expression))
        return res

    def walk_type_to_type(self, expression, args, type_in, type_out):
        assert expression is not None
        for x in args:
            if x is None or x != type_in:
                return None
        return type_out

    @walkers.handles(op.AND, op.OR, op.NOT, op.IMPLIES, op.IFF)
    def walk_bool_to_bool(self, expression, args, **kwargs):
        return self.walk_type_to_type(expression, args, BOOL, BOOL)

    def walk_equals(self, formula, args, **kwargs):
        if args[0].is_bool_type():
            raise PysmtTypeError("The expression '%s' is not well-formed."
                                 "Equality operator is not supported for Boolean"
                                 " terms. Use Iff instead." \
                                 % str(formula))
        return self.walk_type_to_type(formula, args, args[0], BOOL)

    @walkers.handles(op.BOOL_CONSTANT)
    def walk_identity_bool(self, expression, args, **kwargs):
        assert expression is not None
        assert len(args) == 0
        return BOOL

    def walk_fluent_exp(self, expression, args, **kwargs):
        assert expression.is_fluent_exp()
        f = expression.fluent()

        if len(args) != len(f.signature()):
            return None

        for (arg, p_type) in zip(args, f.signature()):
            if arg != p_type:
                return None

        return f.type()

    def walk_param_exp(self, expression, args, **kwargs):
        assert expression is not None
        assert len(args) == 0
        return expression.parameter().type()

    def walk_object_exp(self, expression, args, **kwargs):
        assert expression is not None
        assert len(args) == 0
        return expression.object().type()
