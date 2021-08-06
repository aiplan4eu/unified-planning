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


from collections import OrderedDict
from upf.shortcuts import *
from upf.test import TestCase, main
import upf
from upf.substituter import Substituter
from upf.environment import get_env


class TestSubstituter(TestCase):
    def setUp(self):
        TestCase.setUp(self)

    def test_id_walker(self):
        s = Substituter(get_env())
        #small test on already-done expressions to check the id-dagwalker
        x = FluentExp(upf.Fluent('x'))
        y = FluentExp(upf.Fluent('y', IntType()))
        t = Bool(True)
        f = Bool(False)
        # ((25/5)*30*2*2) - (20*5) (500) == (25*4*10) / 2 (500)
        e1 = Equals(Minus(Times([Div(25, 5), 30, 2, 2]), Times(20, 5)), Div(Times(25, 4, 10) ,2))
        r1 = s.substitute(e1)
        self.assertEqual(r1, e1)
        # T => !x
        e2 = Implies(e1, Not(x))
        r2 = s.substitute(e2)
        self.assertEqual(r2, e2)
        # !x || (T => x)
        e3 = Or(e2, Implies(e1, x))
        r3 = s.substitute(e3)
        self.assertEqual(r3, e3)

    def test_substitution(self):
        s = Substituter(get_env())
        xfluent = upf.Fluent('x', IntType())
        x = FluentExp(xfluent)
        afluent = upf.Fluent('a')
        a = FluentExp(afluent)
        bfluent = upf.Fluent('b')
        b = FluentExp(bfluent)
        cfluent = upf.Fluent('c')
        c = FluentExp(cfluent)
        dfluent = upf.Fluent('d')
        d = FluentExp(dfluent)
        subst = OrderedDict()
        subst[x] = Int(5)
        e1 = Plus(x, 1)
        s1 = s.substitute(e1, subst)
        self.assertEqual(s1, Plus(5, 1))

        subst = OrderedDict()
        subst[a] = c
        subst[And(c,b)] = d
        subst[And(a,b)] = c
        e2 = And(a, b)
        s2 = s.substitute(e2, subst)
        self.assertEqual(s2, c)
