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
from unified_planning.test import TestCase
from unified_planning.test.examples import get_example_problems
from unified_planning.transformers.transformer import Transformer

class TestQuantifiersRemover(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_transformer(self):
        problem = self.problems['basic'].problem
        a = problem.action('a')
        t = Transformer(problem, 't')
        t._new_problem = problem
        self.assertEqual(t.get_fresh_name(a.name), 't_a_0')
        with self.assertRaises(NotImplementedError):
            t.get_original_action(a)
        with self.assertRaises(NotImplementedError):
            t.get_transformed_actions(a)
        with self.assertRaises(NotImplementedError):
            t.get_rewritten_problem()
        with self.assertRaises(NotImplementedError):
            t.rewrite_back_plan(None) # type: ignore
