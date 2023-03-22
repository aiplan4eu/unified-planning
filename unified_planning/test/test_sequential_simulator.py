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


import unified_planning as up
import pytest
from unified_planning.shortcuts import *
from unified_planning.engines import UPSequentialSimulator, SequentialSimulatorMixin
from unified_planning.model import State
from unified_planning.test import TestCase, main
from unified_planning.test.examples import get_example_problems
from unified_planning.exceptions import UPUsageError, UPConflictingEffectsException
from itertools import product
from typing import cast


class TestSimulator(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def simulate_on_hierarchical_blocks_world(
        self, simulator: SequentialSimulatorMixin, problem: "up.model.Problem"
    ):
        # This test takes a simulator and the problem and makes some testing.
        self.assertEqual(problem.name, "hierarchical_blocks_world")
        em = problem.environment.expression_manager
        move = problem.action("move")
        clear = problem.fluent("clear")
        on = problem.fluent("on")
        ts_1 = problem.object("ts_1")
        ts_2 = problem.object("ts_2")
        ts_3 = problem.object("ts_3")
        block_1 = problem.object("block_1")
        block_2 = problem.object("block_2")
        block_3 = problem.object("block_3")
        state: Optional[State] = simulator.get_initial_state()
        assert state is not None
        # The initial state is:
        # ts_1, block_3, block_1, block_2
        # ts_2
        # ts_3, check clear fluent in the state.
        Location = problem.user_type("Location")
        clear_check = [block_2, ts_2, ts_3]
        for o in problem.objects(Location):
            if o in clear_check:
                self.assertEqual(state.get_value(clear(o)), em.TRUE())
            else:
                self.assertEqual(state.get_value(clear(o)), em.FALSE())
        # Then we want to reach a state like this:
        # ts_1, block_1
        # ts_2, block_2
        # ts_3, block_3
        # So the moves to simulate are:
        # move(block_2, from block_1, to ts_2)
        # move(block_1, from block_3, to block_2)
        # move(block_3, from ts_1, to ts_3)
        # move(block_1, from block_2, to ts_1)
        state = simulator.apply(state, move, (block_2, block_1, ts_2))
        assert state is not None

        state = simulator.apply(state, move, (block_1, block_3, block_2))
        assert state is not None

        state = simulator.apply(state, move, (block_3, ts_1, ts_3))
        assert state is not None

        state = simulator.apply(state, move, (block_1, block_2, ts_1))
        assert state is not None

        # now we check that the state is what we desired
        Movable = problem.user_type("Movable")
        check_on = [(block_1, ts_1), (block_2, ts_2), (block_3, ts_3)]
        for obj_tuple in product(problem.objects(Movable), problem.objects(Location)):
            if obj_tuple in check_on:
                self.assertEqual(state.get_value(on(*obj_tuple)), em.TRUE())
            else:
                self.assertEqual(state.get_value(on(*obj_tuple)), em.FALSE())
        # Now we want to check if we can apply the action move (block_3, from ts_1, to ts_3),
        # which we know is not because the block_3 is not on the table space 1 (ts_1)
        self.assertFalse(simulator.is_applicable(state, move, (block_3, ts_1, ts_3)))
        # Now we check if we reached the goal
        self.assertFalse(simulator.is_goal(state))
        # To reach the goal, which is designed like this:
        # ts_1
        # ts_2
        # ts_3, block_1, block_2, block_3
        # We must:
        # move(block_3, from ts_3, to block_2)
        # move(block_1, from ts_1, to ts_3)
        # move(block_3, from block_2, to ts_1)
        # move(block_2, from ts_2, to block_1)
        # move(block_3, from ts_1, to block_2)
        # And then we check if we reached the goal.
        state = simulator.apply(state, move, (block_3, ts_3, block_2))
        assert state is not None
        state = simulator.apply(state, move, (block_1, ts_1, ts_3))
        assert state is not None
        state = simulator.apply(state, move, (block_3, block_2, ts_1))
        assert state is not None
        state = simulator.apply(state, move, (block_2, ts_2, block_1))
        assert state is not None
        state = simulator.apply(state, move, (block_3, ts_1, block_2))
        assert state is not None

        self.assertTrue(simulator.is_goal(state))

    def test_with_sequential_simulator_instance(self):
        problem = self.problems["hierarchical_blocks_world"].problem
        simulator = UPSequentialSimulator(problem)
        self.simulate_on_hierarchical_blocks_world(simulator, problem)

    def test_with_simulator_from_factory(self):
        problem = self.problems["hierarchical_blocks_world"].problem
        with SequentialSimulator(problem) as simulator:
            self.simulate_on_hierarchical_blocks_world(simulator, problem)

    @pytest.mark.filterwarnings("ignore:We cannot establish")
    def test_check_disabling(self):
        problem = self.problems["matchcellar"].problem
        with self.assertRaises(UPUsageError) as e:
            UPSequentialSimulator(problem)
        self.assertIn("cannot establish whether", str(e.exception))
        with SequentialSimulator(problem, name="sequential_simulator") as simulator:
            pass

    def test_bounded_types(self):
        counter = Fluent("counter", IntType(0))
        increase = InstantaneousAction("increase")
        increase.add_increase_effect(counter, 1)
        decrease = InstantaneousAction("decrease")
        decrease.add_decrease_effect(counter, 1)
        problem = Problem("simple_counter")
        problem.add_fluent(counter, default_initial_value=1)
        problem.add_action(increase)
        problem.add_action(decrease)

        with SequentialSimulator(problem) as simulator:
            init = simulator.get_initial_state()
            self.assertTrue(simulator.is_applicable(init, increase))

            dec_state = simulator.apply(init, decrease)
            assert dec_state is not None
            self.assertFalse(simulator.is_applicable(dec_state, decrease))
            double_dec_state = simulator.apply(dec_state, decrease)
            self.assertIsNone(double_dec_state)

    def test_exceptions(self):

        condition1 = Fluent("condition1")
        condition2 = Fluent("condition2")
        condition3 = Fluent("condition3")
        fluent = Fluent("fluent", IntType())

        test_int = InstantaneousAction("test_int")
        test_int.add_effect(fluent, 5, condition1)
        test_int.add_effect(fluent, 6, condition2)
        test_int.add_increase_effect(fluent, 5, condition3)
        unset_cond_1 = InstantaneousAction("unset_cond_1")
        unset_cond_1.add_effect(condition1, False)
        unset_cond_2 = InstantaneousAction("unset_cond_2")
        unset_cond_2.add_effect(condition2, False)
        unset_cond_3 = InstantaneousAction("unset_cond_3")
        unset_cond_3.add_effect(condition3, False)

        problem = Problem("test_problem")
        problem.add_actions([test_int, unset_cond_1, unset_cond_2, unset_cond_3])
        problem.add_fluent(condition1, default_initial_value=True)
        problem.add_fluent(condition2, default_initial_value=True)
        problem.add_fluent(condition3, default_initial_value=True)
        problem.add_fluent(fluent, default_initial_value=0)

        with SequentialSimulator(problem=problem) as simulator:
            init = simulator.get_initial_state()

            self.assertTrue(simulator.is_applicable(init, test_int))
            self.assertIsNone(simulator.apply(init, test_int))

            new_state = simulator.apply(init, unset_cond_2)
            self.assertIsNone(simulator.apply(new_state, test_int))

            new_state = simulator.apply(new_state, unset_cond_3)
            test_state = simulator.apply(new_state, test_int)
            self.assertIsNotNone(test_state)

    def test_add_after_delete(self):
        bf = Fluent("bool_fluent")

        act = InstantaneousAction("act")
        act.add_effect(bf, True)
        act.add_effect(bf, False)

        problem = Problem("test_add_after_delete")
        problem.add_fluent(bf, default_initial_value=False)
        problem.add_action(act)
        problem.add_goal(bf)

        with SequentialSimulator(problem=problem) as simulator:
            init = simulator.get_initial_state()

            self.assertTrue(simulator.is_applicable(init, act))

            goal_state = simulator.apply_unsafe(init, act)

            self.assertTrue(simulator.is_goal(goal_state))
