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


import unified_planning
from unified_planning.shortcuts import *
from unified_planning.test import TestCase, main
from unified_planning.environment import get_env
from unified_planning.walkers import Dnf, Nnf, Simplifier, Substituter


class TestDnf(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.sub = Substituter(get_env())
        self.simp = Simplifier(get_env())

    def _subs_simp(self, exp, subs):
        ne = self.sub.substitute(exp, subs)
        return self.simp.simplify(ne)

    def test_nnf_dnf_1(self):
        n = Nnf(get_env())
        dnf = Dnf(get_env())

        a = FluentExp(Fluent('a'))
        b = FluentExp(Fluent('b'))
        c = FluentExp(Fluent('c'))
        # !(a => (b && c))
        e1 = Not(Implies(a, And(b, c)))
        nnf1 = n.get_nnf_expression(e1)
        self.assertIn("(a and ((not b) or (not c)))", str(nnf1))
        dnf1 = dnf.get_dnf_expression(e1)
        self.assertIn("((a and (not b)) or (a and (not c)))", str(dnf1))

    def test_dnf_2(self):
        dnf = Dnf(get_env())

        a = FluentExp(Fluent('a'))
        b = FluentExp(Fluent('b'))
        c = FluentExp(Fluent('c'))
        d = FluentExp(Fluent('d'))
        # a && (!b || (!c && d))
        e2 = And(a, Or(Not(b), And(Not(c), d)))
        dnf2 = dnf.get_dnf_expression(e2)
        self.assertIn("((a and (not b)) or (a and (not c) and d))", str(dnf2))

    def test_nnf_dnf_3(self):
        n = Nnf(get_env())
        dnf = Dnf(get_env())

        a = FluentExp(Fluent('a'))
        b = FluentExp(Fluent('b'))
        c = FluentExp(Fluent('c'))
        # (a => b) Iff (a => c)
        e3 = Iff(Implies(a, b), Implies(a, c))
        nnf3 = n.get_nnf_expression(e3)
        dnf3 = dnf.get_dnf_expression(e3)
        self.assertIn("(((not a) or b) and ((not a) or c)) or ((a and (not b)) and (a and (not c)))", str(nnf3))
        self.assertIn("(not a) or ((not a) and c) or (b and (not a)) or (b and c) or (a and (not b) and (not c)", str(dnf3))

    def test_nnf_dnf_4(self):
        n = Nnf(get_env())
        dnf = Dnf(get_env())

        a = FluentExp(Fluent('a'))
        b = FluentExp(Fluent('b'))
        # (a && ( a => b)) Iff (b || ( ((a => b ) && (b => a)) Iff ( a Iff b)))
        e4 = Iff(And(a, Implies(a, b)), Or(b, Iff(And(Implies(a, b), Implies(b, a)), Iff(a, b))))
        nnf4 = n.get_nnf_expression(e4)
        dnf4 = dnf.get_dnf_expression(e4)
        subs = {a : True, b : True}
        self.assertEqual(self._subs_simp(e4, subs), self._subs_simp(nnf4, subs))
        self.assertEqual(self._subs_simp(e4, subs), self._subs_simp(dnf4, subs))
        subs = {a : True, b : False}
        self.assertEqual(self._subs_simp(e4, subs), self._subs_simp(nnf4, subs))
        self.assertEqual(self._subs_simp(e4, subs), self._subs_simp(dnf4, subs))
        subs = {a : False, b : False}
        self.assertEqual(self._subs_simp(e4, subs), self._subs_simp(nnf4, subs))
        self.assertEqual(self._subs_simp(e4, subs), self._subs_simp(dnf4, subs))
        subs = {a : False, b : True}
        self.assertEqual(self._subs_simp(e4, subs), self._subs_simp(nnf4, subs))
        self.assertEqual(self._subs_simp(e4, subs), self._subs_simp(dnf4, subs))

    def test_nnf_dnf_5(self):
        n = Nnf(get_env())
        dnf = Dnf(get_env())

        a = FluentExp(Fluent('a'))
        b = FluentExp(Fluent('b'))
        c = FluentExp(Fluent('c'))
        d = FluentExp(Fluent('d'))
        #((a && (c => a)) => d) Iff (( b => d) => c)
        e5 = Iff(Implies(And(a, Implies(c, a)), d), Implies(Implies(b, d), c))
        nnf5 = n.get_nnf_expression(e5)
        dnf5 = dnf.get_dnf_expression(e5)
        subs = {a : False, b : False, c : False, d : False}
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(nnf5, subs))
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(dnf5, subs))
        subs = {a : False, b : False, c : False, d : True}
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(nnf5, subs))
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(dnf5, subs))
        subs = {a : False, b : False, c : True, d : False}
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(nnf5, subs))
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(dnf5, subs))
        subs = {a : False, b : False, c : True, d : True}
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(nnf5, subs))
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(dnf5, subs))
        subs = {a : False, b : True, c : False, d : True}
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(nnf5, subs))
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(dnf5, subs))
        subs = {a : False, b : True, c : False, d : True}
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(nnf5, subs))
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(dnf5, subs))
        subs = {a : False, b : True, c : True, d : False}
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(nnf5, subs))
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(dnf5, subs))
        subs = {a : False, b : True, c : True, d : True}
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(nnf5, subs))
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(dnf5, subs))
        subs = {a : True, b : False, c : False, d : False}
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(nnf5, subs))
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(dnf5, subs))
        subs = {a : True, b : False, c : False, d : True}
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(nnf5, subs))
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(dnf5, subs))
        subs = {a : True, b : False, c : True, d : False}
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(nnf5, subs))
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(dnf5, subs))
        subs = {a : True, b : False, c : True, d : True}
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(nnf5, subs))
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(dnf5, subs))
        subs = {a : True, b : True, c : False, d : True}
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(nnf5, subs))
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(dnf5, subs))
        subs = {a : True, b : True, c : False, d : True}
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(nnf5, subs))
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(dnf5, subs))
        subs = {a : True, b : True, c : True, d : False}
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(nnf5, subs))
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(dnf5, subs))
        subs = {a : True, b : True, c : True, d : True}
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(nnf5, subs))
        self.assertEqual(self._subs_simp(e5, subs), self._subs_simp(dnf5, subs))
