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


import upf
from upf.shortcuts import *
from upf.test import TestCase, main
from upf.environment import get_env
from upf.dnf_copy import Dnf, Nnf


class TestDnf(TestCase):
    def setUp(self):
        TestCase.setUp(self)

    def test_simple_nnf_dnf(self):
        n = Nnf(get_env())
        dnf = Dnf(get_env())
        a = FluentExp(upf.Fluent('a'))
        b = FluentExp(upf.Fluent('b'))
        c = FluentExp(upf.Fluent('c'))
        d = FluentExp(upf.Fluent('d'))
        # !(a => (b && c))
        e1 = Not(Implies(a, And(b, c)))
        nnf1 = n.get_nnf_expression(e1)
        self.assertIn("(a and ((not b) or (not c)))", str(nnf1))
        dnf1 = dnf.get_dnf_expression(e1)
        self.assertIn("((a and (not b)) or (a and (not c)))", str(dnf1))
        # a && (!b || (!c && d))
        e2 = And(a, Or(Not(b), And(Not(c), d)))
        dnf2 = dnf.get_dnf_expression(e2)
        self.assertIn("((a and (not b)) or (a and (not c) and d))", str(dnf2))
        # (a => b) Iff (a => c)
        e3 = Iff(Implies(a, b), Implies(a, c))
        nnf3 = n.get_nnf_expression(e3)
        dnf3 = dnf.get_dnf_expression(e3)
        self.assertIn("(((not a) or b) and ((not a) or c)) or ((a and (not b)) and (a and (not c)))", str(nnf3))
        self.assertIn("(not a) or ((not a) and c) or (b and (not a)) or (b and c) or (a and (not b) and (not c)", str(dnf3))
