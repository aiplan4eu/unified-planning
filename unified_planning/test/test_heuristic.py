# Copyright 2026 Unified Planning library and its maintainers
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
#

from fractions import Fraction
from typing import Callable, Optional, Union

from unified_planning.engines import (
    GoalCountingHeuristic,
    HeuristicGuarantee,
    OperationMode,
    UPSequentialSimulator,
)
from unified_planning.exceptions import UPNoSuitableEngineAvailableException
from unified_planning.model import State
from unified_planning.shortcuts import *
from unified_planning.test import main, unittest_TestCase
from unified_planning.test.examples import get_example_problems


class TestHeuristic(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_operation_mode(self):
        self.assertEqual(OperationMode.HEURISTIC.value, "heuristic")
        self.assertTrue(GoalCountingHeuristic.is_heuristic())
        # is_heuristic is injected by EngineMeta, so mypy cannot see it statically.
        self.assertFalse(getattr(UPSequentialSimulator, "is_heuristic")())

    def test_factory_and_shortcut(self):
        problem = self.problems["hierarchical_blocks_world"].problem
        with Heuristic(problem) as h:
            self.assertIsInstance(h, GoalCountingHeuristic)
        with Heuristic(problem, name="up_goal_counting") as h:
            self.assertIsInstance(h, GoalCountingHeuristic)

    def test_values_along_plan(self):
        test_case = self.problems["hierarchical_blocks_world"]
        problem = test_case.problem
        plan = test_case.valid_plans[0]
        with SequentialSimulator(problem) as sim, Heuristic(problem) as h:
            # Type-level check that value fits the heuristic argument of solve.
            _: Callable[[State], Optional[Union[float, Fraction]]] = h.value
            state = sim.get_initial_state()
            values = [h.value(state)]
            for ai in plan.actions:
                state = sim.apply(state, ai)
                values.append(h.value(state))
            # on(block_2, block_1) holds initially and is undone by the first move.
            self.assertEqual(values, [2, 3, 2, 1, 0])

    def test_nested_conjunctions(self):
        a, b, c = Fluent("a"), Fluent("b"), Fluent("c")
        problem = Problem("nested")
        for f in (a, b, c):
            problem.add_fluent(f, default_initial_value=False)
        problem.set_initial_value(a, True)
        problem.add_goal(And(a, And(b, c)))
        with SequentialSimulator(problem) as sim, Heuristic(problem) as h:
            self.assertEqual(h.value(sim.get_initial_state()), 2)

    def test_unsupported_kind(self):
        problem = self.problems["matchcellar"].problem
        with self.assertWarns(UserWarning):
            Heuristic(problem, name="up_goal_counting")
        with self.assertRaises(UPNoSuitableEngineAvailableException):
            Heuristic(problem)

    def test_guarantees(self):
        self.assertTrue(GoalCountingHeuristic.satisfies(HeuristicGuarantee.GOAL_AWARE))
        self.assertTrue(GoalCountingHeuristic.satisfies(HeuristicGuarantee.SAFE))
        self.assertFalse(GoalCountingHeuristic.satisfies(HeuristicGuarantee.ADMISSIBLE))
        self.assertFalse(GoalCountingHeuristic.satisfies(HeuristicGuarantee.CONSISTENT))


if __name__ == "__main__":
    main()
