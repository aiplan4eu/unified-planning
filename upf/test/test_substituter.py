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

    def test_basic_substitution(self):
        s = Substituter(get_env())
        x = FluentExp(upf.Fluent('x', IntType()))
        subst = OrderedDict()
        subst[x] = 5
        e1 = Plus(x, 1)
        s1 = s.substitute(e1, subst)
        self.assertEqual(s1, Plus(5, 1))
