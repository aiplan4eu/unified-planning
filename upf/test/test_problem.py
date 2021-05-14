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
from upf.expression import *
from upf.test import TestCase, main


class TestProblem(TestCase):
    def test_basic(self):
        x = upf.Fluent('x')
        self.assertEqual(x.name(), 'x')
        self.assertEqual(x.arity(), 0)
        self.assertTrue(x.type().is_bool_type())

        a = upf.Action('a')
        a.add_precondition(Iff(x, False))
        a.add_effect(x, True)
        self.assertEqual(a.name(), 'a')
        self.assertEqual(len(a.preconditions()), 1)
        self.assertEqual(len(a.effects()), 1)

        problem = upf.Problem('basic')
        problem.add_fluent(x)
        problem.add_action(a)
        problem.set_initial_value(x, False)
        problem.add_goal(x)
        self.assertEqual(problem.name(), 'basic')
        self.assertEqual(len(problem.fluents()), 1)
        self.assertEqual(problem.fluent('x'), x)
        self.assertEqual(len(problem.actions()), 1)
        self.assertEqual(problem.action('a'), a)
        self.assertTrue(problem.initial_value(x) is not None)
        self.assertEqual(len(problem.goals()), 1)


if __name__ == "__main__":
    main()
