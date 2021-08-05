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



from fractions import Fraction
import upf
from upf.shortcuts import *
from upf.test import TestCase, main
from upf.simplifier import Simplifier
from upf.environment import get_env


class TestBoolOperators(TestCase):
    def setUp(self):
        TestCase.setUp(self)
          
    def test_and_constant(self):
        s = Simplifier(get_env())
        t = Bool(True)
        f = Bool(False)
        e1 = And(t, f)
        r1 = s.simplify(e1)
        self.assertEqual(r1, f)
        self.assertEqual(r1.constant_value(), False)
        e2 = And(t, e1)
        r2 = s.simplify(e2)
        self.assertEqual(r2, f)
        self.assertEqual(r2.constant_value(), False)
        e3 = And(t, t)
        r3 = s.simplify(e3)
        self.assertTrue(r3.is_constant())
        self.assertEqual(r3, t)

    def test_and_fluent(self):
        s = Simplifier(get_env())
        x = upf.Fluent('x')
        y = upf.Fluent('y')
        t = Bool(True)
        f = Bool(False)
        e1 = And(x, f)
        r1 = s.simplify(e1)
        self.assertEqual(r1, f)
        self.assertEqual(r1.constant_value(), False)
        e2 = And(x, e1)
        r2 = s.simplify(e2)
        self.assertEqual(r2, f)
        self.assertEqual(r2.constant_value(), False)
        e3 = And(x, t, t)
        e4 = And(e3, t)
        r4 = s.simplify(e4)
        self.assertEqual(FluentExp(x), r4)
        e5 = And(x, x)
        r5 = s.simplify(e5)
        self.assertEqual(r5, FluentExp(x))
        e6 = And(And(x, y), And(y, x))
        r6 = s.simplify(e6)
        self.assertEqual(r6, And(x, y))
        e7 = And(And(x, y), And(y, Not(x)))
        r7 = s.simplify(e7)
        self.assertEqual(r7, f)
        e8 = And(And(x, y), Not(x))
        r8 = s.simplify(e8)
        self.assertEqual(r8, f)

    def test_or_constant(self):
        s = Simplifier(get_env())
        t = Bool(True)
        f = Bool(False)
        e1 = Or(t, f)
        r1 = s.simplify(e1)
        self.assertEqual(r1, t)
        self.assertEqual(r1.constant_value(), True)
        e2 = Or(t, e1)
        r2 = s.simplify(e2)
        self.assertEqual(r2, t)
        self.assertEqual(r2.constant_value(), True)
        e3 = Or(f, f)
        r3 = s.simplify(e3)
        self.assertTrue(r3.is_constant())
        self.assertEqual(r3, f)

    def test_or_fluent(self):
        s = Simplifier(get_env())
        x = upf.Fluent('x')
        y = upf.Fluent('y')
        t = Bool(True)
        f = Bool(False)
        e1 = Or(x, t)
        r1 = s.simplify(e1)
        self.assertEqual(r1, t)
        self.assertEqual(r1.constant_value(), True)
        e2 = Or(x, e1)
        r2 = s.simplify(e2)
        self.assertEqual(r2, t)
        self.assertEqual(r2.constant_value(), True)
        e3 = Or(x, f, f)
        e4 = Or(e3, f)
        r4 = s.simplify(e4)
        self.assertEqual(FluentExp(x), r4)
        e5 = Or(x, x)
        r5 = s.simplify(e5)
        self.assertEqual(r5, FluentExp(x))
        e6 = Or(Or(x, y), Or(y, x))
        r6 = s.simplify(e6)
        self.assertEqual(r6, Or(x, y))
        e7 = Or(Or(x, y), Or(y, Not(x)))
        r7 = s.simplify(e7)
        self.assertEqual(r7, t)
        e8 = Or(Or(x, y), Not(x))
        r8 = s.simplify(e8)
        self.assertEqual(r8, t)

    def test_not(self):
        s = Simplifier(get_env())
        x = upf.Fluent('x')
        t = Bool(True)
        f = Bool(False)
        e1 = Or(x, Not(t))
        r1 = s.simplify(e1)
        self.assertEqual(r1, FluentExp(x))
        e2 = Not(Or(x, e1))
        r2 = s.simplify(e2)
        self.assertEqual(r2, Not(x))
        e3 = Or(x, f, f)
        e4 = Not(Or(e3, f))
        r4 = s.simplify(Not(e4))
        self.assertEqual(FluentExp(x), r4)
        e5 = Not(Not(x))
        r5 = s.simplify(e5)
        self.assertEqual(r5, FluentExp(x))

    def test_iff(self):
        s = Simplifier(get_env())
        x = FluentExp(upf.Fluent('x'))
        y = FluentExp(upf.Fluent('y'))
        t = Bool(True)
        f = Bool(False)
        e1 = Iff(x, y)
        r1 = s.simplify(e1)
        self.assertEqual(r1, e1)
        e2 = Iff(e1, e1)
        r2 = s.simplify(e2)
        self.assertEqual(r2, t)
        e3 = Iff(And(t, y), Or(y, f))
        r3 = s.simplify(e3)
        self.assertEqual(r3, t)
        e4 = Iff(And(x, y), And(y, x))
        r4 = s.simplify(e4)
        self.assertEqual(r4, e4)
        e5 = Iff(And(x, y), And(x, y))
        r5 = s.simplify(e5)
        self.assertEqual(r5, t)
        e6 = Iff(And(t, t), f)
        r6 = s.simplify(e6)
        self.assertEqual(r6, f)
        e7 = Iff(And(x, t), f)
        r7 = s.simplify(e7)
        self.assertEqual(r7, Not(x))
        e8 = Iff(And(x, t), t)
        r8 = s.simplify(e8)
        self.assertEqual(r8, x)
        e9 = Iff(f, And(x, t))
        r9 = s.simplify(e9)
        self.assertEqual(r9, Not(x))
        e10 = Iff(t, And(x, t))
        r10 = s.simplify(e10)
        self.assertEqual(r10, x)

    def test_implies(self):
        s = Simplifier(get_env())
        x = FluentExp(upf.Fluent('x'))
        y = FluentExp(upf.Fluent('y'))
        t = Bool(True)
        f = Bool(False)
        e1 = Implies(x, y)
        r1 = s.simplify(e1)
        self.assertEqual(r1, e1)
        e2 = Implies(e1, e1)
        r2 = s.simplify(e2)
        self.assertEqual(r2, t) 
        e3 = Implies(And(t, y), Or(y, f))
        r3 = s.simplify(e3)
        self.assertEqual(r3, t)
        e4 = Implies(And(x, y), And(y, x))
        r4 = s.simplify(e4)
        self.assertEqual(r4, e4)
        e5 = Implies(And(x, y), y)
        r5 = s.simplify(e5)
        self.assertEqual(r5, e5)
        e6 = Implies(And(x, y), t)
        r6 = s.simplify(e6)
        self.assertEqual(r6, t)
        e7 = Implies(And(x, f), Not(f))
        r7 = s.simplify(e7)
        self.assertEqual(r7, t)
        e8 = Implies(t, x)
        r8 = s.simplify(e8)
        self.assertEqual(r8, x)
        e9 = Implies(x, f)
        r9 = s.simplify(e9)
        self.assertEqual(r9, Not(x))

    def test_equals(self):
        s = Simplifier(get_env())
        x = FluentExp(upf.Fluent('x', IntType()))
        y = FluentExp(upf.Fluent('y', IntType()))
        t = Bool(True)
        f = Bool(False)
        i1 = Int(5)
        i2 = Int(6)
        i3 = Real(Fraction(6))
        e1 = Equals(x, y)
        r1 = s.simplify(e1)
        self.assertEqual(r1, e1)
        e2 = Equals(i1, i2)
        r2 = s.simplify(e2)
        self.assertEqual(r2, f)
        e3 = Equals(i2, i3)
        r3 = s.simplify(e3)
        self.assertEqual(r3, t)
        e4 = Equals(x, x)
        r4 = s.simplify(e4)
        self.assertEqual(r4, t)

    def test_le(self):
        s = Simplifier(get_env())
        x = FluentExp(upf.Fluent('x', IntType()))
        y = FluentExp(upf.Fluent('y', IntType()))
        t = Bool(True)
        f = Bool(False)
        i1 = Int(5)
        i2 = Int(6)
        i3 = Real(Fraction(6))
        e1 = LE(x, y)
        r1 = s.simplify(e1)
        self.assertEqual(r1, e1)
        e2 = LE(i1, i2)
        r2 = s.simplify(e2)
        self.assertEqual(r2, t)
        e3 = LE(i2, i3)
        r3 = s.simplify(e3)
        self.assertEqual(r3, t)
        e4 = LE(i2, i1)
        r4 = s.simplify(e4)
        self.assertEqual(r4, f)

    def test_lt(self):
        s = Simplifier(get_env())
        x = FluentExp(upf.Fluent('x', IntType()))
        y = FluentExp(upf.Fluent('y', IntType()))
        t = Bool(True)
        f = Bool(False)
        i1 = Int(5)
        i2 = Int(6)
        i3 = Real(Fraction(6))
        e1 = LT(x, y)
        r1 = s.simplify(e1)
        self.assertEqual(r1, e1)
        e2 = LT(i1, i2)
        r2 = s.simplify(e2)
        self.assertEqual(r2, t)
        e3 = LT(i2, i3)
        r3 = s.simplify(e3)
        self.assertEqual(r3, f)
        e4 = LT(i2, i1)
        r4 = s.simplify(e4)
        self.assertEqual(r4, f)

    def test_gt(self):
        s = Simplifier(get_env())
        x = FluentExp(upf.Fluent('x', IntType()))
        y = FluentExp(upf.Fluent('y', IntType()))
        t = Bool(True)
        f = Bool(False)
        i1 = Int(5)
        i2 = Int(6)
        i3 = Real(Fraction(6))
        e1 = GT(x, y)
        r1 = s.simplify(e1)
        self.assertEqual(r1, e1)
        e2 = GT(i1, i2)
        r2 = s.simplify(e2)
        self.assertEqual(r2, f)
        e3 = GT(i2, i3)
        r3 = s.simplify(e3)
        self.assertEqual(r3, f)
        e4 = GT(i2, i1)
        r4 = s.simplify(e4)
        self.assertEqual(r4, t)

    def test_ge(self):
        s = Simplifier(get_env())
        x = FluentExp(upf.Fluent('x', IntType()))
        y = FluentExp(upf.Fluent('y', IntType()))
        t = Bool(True)
        f = Bool(False)
        i1 = Int(5)
        i2 = Int(6)
        i3 = Real(Fraction(6))
        e1 = GE(x, y)
        r1 = s.simplify(e1)
        self.assertEqual(r1, e1)
        e2 = GE(i1, i2)
        r2 = s.simplify(e2)
        self.assertEqual(r2, f)
        e3 = GE(i2, i3)
        r3 = s.simplify(e3)
        self.assertEqual(r3, t)
        e4 = GE(i2, i1)
        r4 = s.simplify(e4)
        self.assertEqual(r4, t)

    
class TestArithmeticOperators(TestCase):
    def setUp(self):
        TestCase.setUp(self)
     
    def test_plus_constant(self):
        #simple plus
        s = Simplifier(get_env())
        data1 = Fraction(5.0)
        data2 = 3
        fnode1 = Real(data1)
        fnode2 = Int(data2)
        fnode1_2 = Plus(fnode1, fnode2)
        result1_2 = s.simplify(fnode1_2)
        self.assertTrue(result1_2.constant_value() == 8)
        data_list = [1,5,6,2,3,4,-3,5]
        fnode_of_data_list = Plus(data_list)
        fnode_simplified = s.simplify(fnode_of_data_list)
        self.assertTrue(fnode_simplified.is_int_constant())
        self.assertTrue(fnode_simplified.constant_value() == 23)
        data_list = [1,5,6,2,-10,-5,3,-2]
        fnode_of_data_list = Plus(data_list)
        fnode_simplified = s.simplify(fnode_of_data_list)
        self.assertTrue(fnode_simplified.is_int_constant())
        self.assertEqual(fnode_simplified.constant_value(), 0)
        
    def test_plus_fluent(self):
        #plus with fluent
        s = Simplifier(get_env())
        data2 = 3
        x = upf.Fluent('x', IntType())
        y = upf.Fluent('y', IntType())
        fnode2 = Int(data2)
        fnodex_2 = Plus(x, fnode2)
        data_list = [1,5,6,2,3,4,-3,5]

        fnode_of_data_list = Plus(data_list)
        fnode_of_data_list = Plus(fnode_of_data_list, fnodex_2)
        fnode_simplified = s.simplify(fnode_of_data_list)
        #self.assertEqual(fnode_simplified, Plus(upf.Fluent('x', IntType()), Int(26)))
        self.assertEqual(fnode_simplified, Plus(x ,Int(26)))

        data_list = [1,5,6,2,-10,-5,3,-2, x, y]
        fnode_of_data_list = Plus(data_list)
        fnode_simplified = s.simplify(fnode_of_data_list)
        self.assertEqual(fnode_simplified, Plus(x, y))

    def test_minus_constant(self):
        #simple minus
        s = Simplifier(get_env())
        data1 = 5
        data2 = 3
        fnode1 = Int(data1)
        fnode2 = Int(data2)
        fnode1_2 = Minus(fnode1, fnode2)
        result1_2 = s.simplify(fnode1_2)
        self.assertEqual(result1_2.constant_value(), 2)
        data_list = [1,5,6,2,3,4,-3,5]
        fnode_of_data_list = Int(data_list.pop(0))
        for a in data_list:
            fnode_of_data_list = Minus(fnode_of_data_list, Int(a))
        fnode_simplified = s.simplify(fnode_of_data_list)
        self.assertEqual(fnode_simplified.constant_value(), -21)

    def test_minus_fluent(self):
        #minus with fluent
        s = Simplifier(get_env())
        data2 = 3
        x = upf.Fluent('x', IntType())
        y = upf.Fluent('y', IntType())
        fnode2 = Int(data2)
        x_2 = Minus(x, fnode2)
        data_list = [1,5,6,2,3,4,-3,5]
        fnode_of_data_list = x_2
        for a in data_list:
            fnode_of_data_list = Minus(fnode_of_data_list, Int(a))
        fnode_simplified = s.simplify(fnode_of_data_list)
        fnode_of_data_list_expected = x_2
        for a in data_list:
            if a > 0:
                fnode_of_data_list_expected = Minus(fnode_of_data_list_expected, Int(a))
            else:
                fnode_of_data_list_expected = Plus(fnode_of_data_list_expected, Int(-a))
        self.assertEqual(fnode_simplified, fnode_of_data_list_expected)
        
        fnode_of_data_list = Int(0)
        for a in data_list:
            fnode_of_data_list = Minus(fnode_of_data_list, Int(a))
        x_fnode_of_data_list = Minus(x, fnode_of_data_list)
        fnode_simplified = s.simplify(x_fnode_of_data_list)
        self.assertEqual(fnode_simplified, Plus(x, Int(23)))

        e1 = Minus(x, y)
        r1 = s.simplify(e1)
        self.assertEqual(r1, e1)

    def test_times_constant(self):
        #simple times
        s = Simplifier(get_env())
        data1 = 5
        data2 = 3
        fnode1 = Int(data1)
        fnode2 = Int(data2)
        fnode1_2 = Times(fnode1, fnode2)
        result1_2 = s.simplify(fnode1_2)

        print(result1_2)
        self.assertTrue(result1_2.constant_value() == 15)
        data_list = [1,5,6,2,3,4,-3,5]
        fnode_of_data_list = Times(0, *data_list)
        fnode_simplified = s.simplify(fnode_of_data_list)
        self.assertTrue(fnode_simplified.is_int_constant())
        self.assertEqual(fnode_simplified.constant_value(), 0)
        data_list = [1,5,6,2,3,4,-3,5]
        fnode_of_data_list = Times(data_list)
        fnode_simplified = s.simplify(fnode_of_data_list)
        self.assertTrue(fnode_simplified.is_int_constant())
        self.assertEqual(fnode_simplified.constant_value(), -10800)

        e1 = Times(Int(5), Minus(-3, Plus(-5, 2)))
        r1 = s.simplify(e1)
        self.assertTrue(r1.is_constant())
        self.assertTrue(r1.constant_value() == 0)
        self.assertEqual(r1, Int(0))

    def test_times_fluent(self):
        #plus with fluent
        s = Simplifier(get_env())
        data2 = 3
        x = FluentExp(upf.Fluent('x', IntType()))
        fnode2 = Int(data2)
        x_2 = Times(x, fnode2)
        data_list = [1,5,6,2,3,4,-3,5]

        fnode_of_data_list = Int(0)
        for a in data_list:
            fnode_of_data_list = Times(fnode_of_data_list, Int(a))
        fnode_of_data_list = Times(fnode_of_data_list, x_2)
        fnode_simplified = s.simplify(fnode_of_data_list)
        self.assertEqual(fnode_simplified, Int(0))

        fnode_of_data_list = Int(1)
        for a in data_list:
            fnode_of_data_list = Times(fnode_of_data_list, Int(a))
        fnode_of_data_list = Times(fnode_of_data_list, x_2)
        fnode_simplified = s.simplify(fnode_of_data_list)
        self.assertEqual(fnode_simplified, Times(x, Int(-32400)))

        e1 = Times(x, Div(1, 5), Int(5))
        r1 = s.simplify(e1)
        self.assertEqual(r1, x)

    def test_div_constant(self):
        #simple div
        s = Simplifier(get_env())
        data1 = 5
        data2 = 3
        fnode1 = Int(data1)
        fnode2 = Int(data2)
        fnode1_2 = Div(fnode1, fnode2)
        result1_2 = s.simplify(fnode1_2)
        self.assertTrue(result1_2.is_constant())
        self.assertTrue(result1_2.constant_value() == Fraction(5, 3))
        data1 = 6
        data2 = 3
        fnode1 = Int(data1)
        fnode2 = Int(data2)
        fnode1_2 = Div(fnode1, fnode2)
        result1_2 = s.simplify(fnode1_2)
        self.assertTrue(result1_2.is_constant())
        self.assertTrue(result1_2.is_int_constant())
        self.assertTrue(result1_2.constant_value() == Fraction(2))
        self.assertTrue(result1_2 == Int(2))
        data1 = 6
        data2 = 4
        fnode1 = Int(data1)
        fnode2 = Int(data2)
        fnode1_2 = Div(fnode1, fnode2)
        result1_2 = s.simplify(fnode1_2)
        self.assertTrue(result1_2.is_constant())
        self.assertTrue(result1_2.is_real_constant())
        self.assertTrue(result1_2.constant_value() == Fraction(6, 4))
        self.assertTrue(result1_2 == Real(Fraction(6, 4)))

        data_list = ['1.0','0.5','10','0.25','0.125']
        fnode_of_data_list = Int(125)
        for a in data_list:
            fnode_of_data_list = Div(fnode_of_data_list, Real(Fraction(a)))
        fnode_simplified = s.simplify(fnode_of_data_list)
        print(fnode_of_data_list)
        print(fnode_simplified)
        self.assertTrue(fnode_simplified.is_real_constant())
        self.assertEqual(fnode_simplified.constant_value(), 800)

    def test_div_fluent(self):
        #div with fluent
        s = Simplifier(get_env())
        data2 = 3
        x = upf.Fluent('x', IntType())
        fnode2 = Int(data2)
        x_2 = Div(x, fnode2)
        data_list = [Fraction(5), Fraction(1, 5)]

        fnode_of_data_list = Int(1)
        for a in data_list:
            fnode_of_data_list = Div(fnode_of_data_list, Real(Fraction(a)))
        fnode_of_data_list = Div(x_2, fnode_of_data_list)
        fnode_simplified = s.simplify(fnode_of_data_list)
        self.assertEqual(fnode_simplified, Div( Div(x, Int(3)), Real(Fraction(1))))
        
        data_list = ['1.0','0.5','10','0.25','0.125']
        fnode_of_data_list = Int(1)
        for a in data_list:
            fnode_of_data_list = Div(fnode_of_data_list, Real(Fraction(a)))
        fnode_of_data_list = Div(fnode_of_data_list, x_2)
        print(fnode_of_data_list)
        fnode_simplified = s.simplify(fnode_of_data_list)
        print(fnode_simplified)
        self.assertEqual(fnode_simplified, Div(Fraction('6.4'), Div(x, Int(3))))


class TestGeneralSimplifier(TestCase):
    def test_general(self):
        s = Simplifier(get_env())
        x = FluentExp(upf.Fluent('x'))
        y = FluentExp(upf.Fluent('y', IntType()))
        t = Bool(True)
        f = Bool(False)
        # ((25/5)*30*2*2) - (20*5) (500) == (25*4*10) / 2 (500)
        e1 = Equals(Minus(Times([Div(25, 5), 30, 2, 2]), Times(20, 5)), Div(Times(25, 4, 10) ,2))
        r1 = s.simplify(e1)
        self.assertEqual(r1, t)
        # T => !x
        e2 = Implies(e1, Not(x))
        r2 = s.simplify(e2)
        self.assertEqual(r2, Not(x))
        # !x || (T => x)
        e3 = Or(e2, Implies(e1, x))
        r3 = s.simplify(e3)
        self.assertEqual(r3, t)
        

if __name__ == "__main__":
    main()
