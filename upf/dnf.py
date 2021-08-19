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
import upf.environment
from upf.walkers.identitydag import IdentityDagWalker
from upf.fnode import FNode
from upf.simplifier import Simplifier
from typing import List, Dict, Mapping
from itertools import product


class Nnf(IdentityDagWalker):
    """Performs substitution into an expression """
    def __init__(self, env: 'upf.environment.Environment'):
        IdentityDagWalker.__init__(self, env, True)
        self.env = env
        self.manager = env.expression_manager
        self.type_checker = env.type_checker


    def get_nnf_expression(self, expression: FNode) -> FNode:
        self._walk_again = True
        ret_val = expression
        while self._walk_again:
            self._walk_again = False
            ret_val = self.walk(ret_val)
        return ret_val


    def walk_iff(self, expression: FNode, args: List[FNode], **kwargs) -> FNode:
        assert len(args) == 2
        e1 = self.manager.And(args[0], args[1])
        na1 = self.manager.Not(args[0])
        na2 = self.manager.Not(args[1])
        e2 = self.manager.And(na1, na2)
        return self.manager.Or(e1, e2)

    def walk_implies(self, expression: FNode, args: List[FNode], **kwargs) -> FNode:
        assert len(args) == 2
        na1 = self.manager.Not(args[0])
        return self.manager.Or(na1, args[1])

    def walk_not(self, expression: FNode, args: List[FNode], **kwargs) -> FNode:
        assert len(args) == 1
        new_args: List[FNode] = []
        if args[0].is_bool_constant():
            if args[0].bool_constant_value():
                return self.manager.FALSE()
            else:
                return self.manager.TRUE()
        elif args[0].is_not():
            new_exp_l = args[0].args()
            return new_exp_l[0]
        elif args[0].is_or():
            for a in args[0].args():
                new_args.append(self.manager.Not(a))
            new_exp = self.manager.And(new_args)
            ##########################
            # self.walk inside walk not working..
            self._walk_again = True
            return new_exp
            #return self.walk(new_exp)
        elif args[0].is_and():
            for a in args[0].args():
                new_args.append(self.manager.Not(a))
            new_exp = self.manager.Or(new_args)
            ########################################
            self._walk_again = True
            return new_exp
            #return self.walk(new_exp)
        else:
            return self.manager.Not(args[0])

class Dnf(IdentityDagWalker):
    """Performs substitution into an expression """
    def __init__(self, env: 'upf.environment.Environment'):
        IdentityDagWalker.__init__(self, env, True)
        self.env = env
        self.manager = env.expression_manager
        self.type_checker = env.type_checker
        self._nnf = Nnf(self.env)
        self._simplifier = Simplifier(self.env)

    def get_dnf_expression(self, expression: FNode) -> FNode:
        nnf_exp = self._nnf.get_nnf_expression(expression)
        return self._simplifier.simplify(self.walk(nnf_exp))

    def walk_and(self, expression: FNode, args: List[FNode], **kwargs) -> FNode:
        new_args: List[List[FNode]] = []
        for a in args:
            if a.is_or():
                new_args.append(a.args())
            else:
                new_args.append([a])
        tuples = list(product(*new_args))
        and_list: List[FNode] = []
        for and_args in tuples:
            and_list.append(self.manager.And(and_args))
        return self.manager.Or(and_list)
