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
from unified_planning.shortcuts import *
from unified_planning.engines import SequentialSimulator, SimulatorMixin
from unified_planning.model import UPCOWState
from unified_planning.test import TestCase, main
from unified_planning.test.examples import get_example_problems
from itertools import product
from typing import cast


class TestSimulator(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def simulate_on_hierarchical_blocks_world(
        self, simulator: SimulatorMixin, problem: "up.model.Problem"
    ):
        # This test takes a simulator and the problem and makes some testing.
        self.assertEqual(problem.name, "hierarchical_blocks_world")
        em = problem.env.expression_manager
        move = problem.action("move")
        clear = problem.fluent("clear")
        on = problem.fluent("on")
        ts_1 = problem.object("ts_1")
        ts_2 = problem.object("ts_2")
        ts_3 = problem.object("ts_3")
        block_1 = problem.object("block_1")
        block_2 = problem.object("block_2")
        block_3 = problem.object("block_3")
        state = UPCOWState(problem.initial_values)
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
        events = simulator.get_events(move, (block_2, block_1, ts_2))
        self.assertEqual(
            len(events), 1
        )  # only 1 even corresponds to in Instantaneous Action
        state = cast(UPCOWState, simulator.apply(events[0], state))
        self.assertIsNotNone(
            state
        )  # If the state is None it means the action was not applicable

        events = simulator.get_events(move, (block_1, block_3, block_2))
        self.assertEqual(
            len(events), 1
        )  # only 1 even corresponds to in Instantaneous Action
        state = cast(UPCOWState, simulator.apply(events[0], state))
        self.assertIsNotNone(
            state
        )  # If the state is None it means the action was not applicable

        events = simulator.get_events(move, (block_3, ts_1, ts_3))
        self.assertEqual(
            len(events), 1
        )  # only 1 even corresponds to in Instantaneous Action
        state = cast(UPCOWState, simulator.apply(events[0], state))
        self.assertIsNotNone(
            state
        )  # If the state is None it means the action was not applicable

        events = simulator.get_events(move, (block_1, block_2, ts_1))
        self.assertEqual(
            len(events), 1
        )  # only 1 even corresponds to in Instantaneous Action
        state = cast(UPCOWState, simulator.apply(events[0], state))
        self.assertIsNotNone(
            state
        )  # If the state is None it means the action was not applicable
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
        event = simulator.get_events(move, (block_3, ts_1, ts_3))[0]
        self.assertFalse(simulator.is_applicable(event, state))

    def test_with_sequential_simualtor_instance(self):
        problem = self.problems["hierarchical_blocks_world"].problem
        simulator = SequentialSimulator(problem)
        self.simulate_on_hierarchical_blocks_world(simulator, problem)

    def test_with_smulator_from_factory(self):
        problem = self.problems["hierarchical_blocks_world"].problem
        with Simulator(problem) as simulator:
            self.simulate_on_hierarchical_blocks_world(simulator, problem)
