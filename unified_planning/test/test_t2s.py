# Copyright 2025 Unified Planning library and its maintainers
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


from unified_planning.environment import get_environment
from unified_planning.shortcuts import *
from unified_planning.test import (
    unittest_TestCase,
)
from unified_planning.test.examples import get_example_problems

from unified_planning.engines.compilers.timed_to_sequential import TimedToSequential


class TestT2S(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.environment = get_environment()
        self.problems = get_example_problems()

    def test_base_example(self):
        problem = Problem("wompwomp")

        x = Fluent("x", IntType())
        problem.add_fluent(x)
        problem.set_initial_value(x, 10)

        y = Fluent("y", IntType())
        problem.add_fluent(y)
        problem.set_initial_value(y, 10)

        z = Fluent("z", IntType())
        problem.add_fluent(z)
        problem.set_initial_value(z, 10)

        w = Fluent("w", IntType())
        problem.add_fluent(w)
        problem.set_initial_value(w, 10)

        tda = DurativeAction("tda")
        tda.set_closed_duration_interval(5, 10)

        tda.add_increase_effect(StartTiming(), x, 1)
        tda.add_increase_effect(StartTiming(), x, 1)
        tda.add_decrease_effect(EndTiming(), x, 2)
        tda.add_increase_effect(StartTiming(), y, 3)
        tda.add_effect(EndTiming(), z, y + 4)
        tda.add_decrease_effect(EndTiming(), w, x)

        tda.add_condition(StartTiming(), Equals(x, 1))
        # tda.add_condition(StartTiming() + 2, Equals(x, 5))
        tda.add_condition(EndTiming(), Not(Equals(y, 1)))
        tda.add_condition(EndTiming(), Equals(x, 1))

        problem.add_action(tda)

        t2s = TimedToSequential()
        comp_res = t2s.compile(problem)
        assert comp_res.problem is not None
        self.assertTrue(not comp_res.problem.kind.has_continuous_time())
        assert isinstance(comp_res.problem, Problem)
        comp_tda = comp_res.problem.action("tda")
        expected_tda = InstantaneousAction("tda")
        expected_tda.add_precondition(Equals(x, 1))
        # expected_tda.add_precondition(Equals(Plus(x, 1), 5))
        expected_tda.add_precondition(Not(Equals(Plus(y, 3), 1)))
        expected_tda.add_precondition(Equals(Plus(Plus(x, 1), 1), 1))
        expected_tda.add_effect(x, Minus(Plus(Plus(x, 1), 1), 2))
        # expected_tda.add_effect(y, Plus(y, 3))
        expected_tda.add_increase_effect(y, 3)
        expected_tda.add_effect(z, Plus(Plus(y, 3), 4))
        expected_tda.add_effect(w, Minus(w, Plus(Plus(x, 1), 1)))

        self.assertEqual(expected_tda, comp_tda)

        print("expected preconds:\nx==1\n!(y+3==1)")

        print("expected effects:\nx=x+1-2\ny=y+3\nz=y+3+4\nw=w-(x+1)")
