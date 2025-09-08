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
from unified_planning.engines import CompilationKind

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
        problem.set_initial_value(x, 1)

        y = Fluent("y", IntType())
        problem.add_fluent(y)
        problem.set_initial_value(y, 1)

        z = Fluent("z", IntType())
        problem.add_fluent(z)
        problem.set_initial_value(z, 1)

        tda = DurativeAction("tda")
        tda.set_closed_duration_interval(5, 10)
        tda.add_effect(StartTiming(), x, x + 1)
        tda.add_effect(EndTiming(), x, x + 1)
        tda.add_effect(StartTiming(), y, y + 1)
        tda.add_effect(EndTiming(), z, y + 1)
        tda.add_condition(StartTiming(), Equals(x, 1))
        tda.add_condition(EndTiming(), Not(Equals(y, 1)))

        # start 1, 1, 1
        # during 2, 2, 1
        # end 3, 2, 3

        problem.add_action(tda)

        t2s = TimedToSequential()
        comp_res = t2s.compile(problem, CompilationKind.TIMED_TO_SEQUENTIAL)
        assert comp_res.problem is not None
        self.assertTrue(not comp_res.problem.kind.has_continuous_time())
