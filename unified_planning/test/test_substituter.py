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


from unified_planning.shortcuts import *
from unified_planning.test import TestCase, main
from unified_planning.model.walkers import Substituter
from unified_planning.environment import get_environment
from unified_planning.exceptions import UPTypeError


class TestSubstituter(TestCase):
    def setUp(self):
        TestCase.setUp(self)

    def test_id_walker(self):
        s = Substituter(get_environment())
        # small test on already-done expressions to check the id-dagwalker
        x = FluentExp(Fluent("x"))
        y = FluentExp(Fluent("y", IntType()))
        t = Bool(True)
        f = Bool(False)
        subs: Dict[Expression, Expression] = {y: 3}
        # ((25/5)*30*2*2) - (20*5) (500) == (25*4*10) / 2 (500)
        e1 = Equals(
            Minus(Times([Div(25, 5), 30, 2, 2]), Times(20, 5)), Div(Times(25, 4, 10), 2)
        )
        r1 = s.substitute(e1, subs)
        self.assertEqual(r1, e1)
        # T => !x
        e2 = Implies(e1, Not(x))
        r2 = s.substitute(e2)
        self.assertEqual(r2, e2, subs)
        # !x || (T => x)
        e3 = Or(e2, Implies(e1, x))
        r3 = s.substitute(e3, subs)
        self.assertEqual(r3, e3)

    def test_substitution(self):
        s = Substituter(get_environment())
        xfluent = Fluent("x", IntType())
        x = FluentExp(xfluent)
        subst: Dict[Expression, Expression] = {}
        subst[x] = Int(5)
        e1 = Plus(x, 1)
        s1 = s.substitute(e1, subst)
        self.assertEqual(s1, Plus(5, 1))
        # Testing that (a & b) with sbust = {a <- c, (c & b) <- d, (a & b) <- c} is c
        a = Fluent("a")
        b = Fluent("b")
        c = FluentExp(Fluent("c"))
        d = Fluent("d")
        subst = {}
        subst[a] = c
        subst[And(c, b)] = d
        subst[And(a, b)] = c
        e2 = And(a, b)
        s2 = s.substitute(e2, subst)
        self.assertEqual(s2, c)

        with self.assertRaises(UPTypeError):
            subst = {}
            subst[a] = c
            subst[And(c, b)] = d
            subst[And(a, b)] = Int(5)
            e3 = And(a, b)
            s3 = s.substitute(e3, subst)

        subst = {}
        subst[a] = c
        subst[And(c, b)] = d
        e4 = And(a, b, And(c, b))
        s4 = s.substitute(e4, subst)
        self.assertEqual(s4, And(c, b, d))

        subst = {}
        subst[a] = c
        subst[c] = d
        e5 = And(a, c, And(a, c))
        s5 = s.substitute(e5, subst)
        self.assertEqual(s5, And(c, d, And(c, d)))

        with self.assertRaises(UPTypeError):
            subst = {}
            subst[a] = c
            subst[And(c, b)] = Plus(1, 2)
            e6 = Int(1)
            s.substitute(e6, subst)


if __name__ == "__main__":
    main()
