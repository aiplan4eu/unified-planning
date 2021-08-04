    

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

    def test_and_constant(self):
        s = Simplifier(get_env())
        x = upf.Fluent('x')
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
        self.assertEqual(x, r4)




class TestArithmeticOperators(TestCase):
    def setUp(self):
        TestCase.setUp(self)

    
        
    def test_plus_constant(self):
        #simple plus
        s = Simplifier(get_env())
        data1 = 5
        data2 = 3
        fnode1 = Int(data1)
        fnode2 = Int(data2)
        fnode1_2 = Plus(fnode1, fnode2)
        result1_2 = s.simplify(fnode1_2)
        self.assertTrue(result1_2.constant_value() == 8)
        data_list = [1,5,6,2,3,4,-3,5]
        fnode_of_data_list = Plus(data_list)
        fnode_simplified = s.simplify(fnode_of_data_list)
        self.assertTrue(fnode_simplified.is_int_constant())
        self.assertTrue(fnode_simplified.constant_value() == 23)
        

    def test_plus_fluent(self):
        #plus with fluent
        s = Simplifier(get_env())
        data2 = 3
        x = upf.Fluent('x', IntType())
        fnode2 = Int(data2)
        fnodex_2 = Plus(x, fnode2)
        data_list = [1,5,6,2,3,4,-3,5]

        fnode_of_data_list = Plus(data_list)
        fnode_of_data_list = Plus(fnode_of_data_list, fnodex_2)
        fnode_simplified = s.simplify(fnode_of_data_list)
        #self.assertEqual(fnode_simplified, Plus(upf.Fluent('x', IntType()), Int(26)))
        self.assertEqual(fnode_simplified, Plus(x ,Int(26)))






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

    def test_times_fluent(self):
        #plus with fluent
        s = Simplifier(get_env())
        data2 = 3
        x = upf.Fluent('x', IntType())
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
        #self.assertEqual(fnode_simplified, Div( Div(x, Int(3s)), Int(1)))
        #self.assertEqual(fnode_simplified, Div( Div(x, Real(Fraction(3))), Real(Fraction(1))))
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
       
        

if __name__ == "__main__":
    main()
