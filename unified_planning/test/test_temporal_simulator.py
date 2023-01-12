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
from unified_planning.engines import (
    SimulatorMixin,
    TemporalSimulator,
    TemporalEvent,
    TemporalEventKind,
)
from unified_planning.model import COWState, TemporalCOWState, COWState
from unified_planning.test import TestCase, main
from unified_planning.test.examples import get_example_problems
from typing import cast


class TestSimulator(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def _check_applicability(
        self,
        state: TemporalCOWState,
        applicable: List[TemporalEvent],
        inapplicable: List[TemporalEvent],
        simulator: SimulatorMixin,
        expected_events: int,
    ):
        self.assertEqual(expected_events, len(applicable) + len(inapplicable))
        self.assertTrue(all(simulator.is_applicable(ev, state) for ev in applicable))
        self.assertTrue(
            all(not simulator.is_applicable(ev, state) for ev in inapplicable)
        )

    def simulate_on_matchcellar(
        self, simulator: SimulatorMixin, problem: "up.model.Problem"
    ):
        # This test takes a simulator and the problem and makes some testing.
        self.assertEqual(problem.name, "MatchCellar")
        light_match = problem.action("light_match")
        mend_fuse = problem.action("mend_fuse")
        handfree = problem.fluent("handfree")
        light = problem.fluent("light")
        match_used = problem.fluent("match_used")
        fuse_mended = problem.fluent("fuse_mended")
        f1 = problem.object("f1")
        f2 = problem.object("f2")
        f3 = problem.object("f3")
        m1 = problem.object("m1")
        m2 = problem.object("m2")
        m3 = problem.object("m3")
        Match = problem.user_type("Match")
        Fuse = problem.user_type("Fuse")
        state: TemporalCOWState = cast(TemporalCOWState, simulator.get_initial_state())
        self.assertTrue(state.get_value(handfree()).bool_constant_value())
        self.assertFalse(state.get_value(light()).bool_constant_value())
        self.assertTrue(
            all(
                not state.get_value(match_used(o)).bool_constant_value()
                for o in problem.objects(Match)
            )
        )
        self.assertTrue(
            all(
                not state.get_value(fuse_mended(o)).bool_constant_value()
                for o in problem.objects(Fuse)
            )
        )

        ev_light_m1 = cast(
            List[TemporalEvent], simulator.get_events(light_match, [m1], 6)
        )
        self.assertEqual(2, len(ev_light_m1))
        self.assertEqual(TemporalEventKind.START_ACTION, ev_light_m1[0].kind)
        self.assertEqual(TemporalEventKind.END_ACTION, ev_light_m1[1].kind)
        ev_mend_f1 = cast(List[TemporalEvent], simulator.get_events(mend_fuse, [f1], 5))
        self.assertEqual(4, len(ev_mend_f1))
        self.assertEqual(TemporalEventKind.START_ACTION, ev_mend_f1[0].kind)
        self.assertEqual(TemporalEventKind.START_CONDITION, ev_mend_f1[1].kind)
        self.assertEqual(TemporalEventKind.END_CONDITION, ev_mend_f1[2].kind)
        self.assertEqual(TemporalEventKind.END_ACTION, ev_mend_f1[3].kind)
        ev_light_m2 = cast(
            List[TemporalEvent], simulator.get_events(light_match, [m2], 6)
        )
        self.assertEqual(2, len(ev_light_m2))
        self.assertEqual(TemporalEventKind.START_ACTION, ev_light_m2[0].kind)
        self.assertEqual(TemporalEventKind.END_ACTION, ev_light_m2[1].kind)
        ev_mend_f2 = cast(List[TemporalEvent], simulator.get_events(mend_fuse, [f2], 5))
        self.assertEqual(4, len(ev_mend_f2))
        self.assertEqual(TemporalEventKind.START_ACTION, ev_mend_f2[0].kind)
        self.assertEqual(TemporalEventKind.START_CONDITION, ev_mend_f2[1].kind)
        self.assertEqual(TemporalEventKind.END_CONDITION, ev_mend_f2[2].kind)
        self.assertEqual(TemporalEventKind.END_ACTION, ev_mend_f2[3].kind)
        ev_light_m3 = cast(
            List[TemporalEvent], simulator.get_events(light_match, [m3], 6)
        )
        self.assertEqual(2, len(ev_light_m3))
        self.assertEqual(TemporalEventKind.START_ACTION, ev_light_m3[0].kind)
        self.assertEqual(TemporalEventKind.END_ACTION, ev_light_m3[1].kind)
        ev_mend_f3 = cast(List[TemporalEvent], simulator.get_events(mend_fuse, [f3], 5))
        self.assertEqual(4, len(ev_mend_f3))
        self.assertEqual(TemporalEventKind.START_ACTION, ev_mend_f3[0].kind)
        self.assertEqual(TemporalEventKind.START_CONDITION, ev_mend_f3[1].kind)
        self.assertEqual(TemporalEventKind.END_CONDITION, ev_mend_f3[2].kind)
        self.assertEqual(TemporalEventKind.END_ACTION, ev_mend_f3[3].kind)

        total_events = (
            3 * 2 + 3 * 4
        )  # 2 events * 3 light_match + 4 events * 3 mend_fuse
        applicable = [ev_light_m1[0], ev_light_m2[0], ev_light_m3[0]]
        inapplicable = [
            ev_light_m1[1],
            ev_light_m2[1],
            ev_light_m3[1],
            *ev_mend_f1,
            *ev_mend_f2,
            *ev_mend_f3,
        ]
        self._check_applicability(
            cast(TemporalCOWState, state),
            applicable,
            inapplicable,
            simulator,
            total_events,
        )
        state_light_m1 = cast(COWState, simulator.apply(ev_light_m1[0], state))
        assert state_light_m1 is not None
        applicable = [
            ev_light_m1[1],
            ev_light_m2[0],
            ev_light_m3[0],
            ev_mend_f1[0],
            ev_mend_f2[0],
            ev_mend_f3[0],
        ]
        inapplicable = [
            ev_light_m1[0],
            ev_light_m2[1],
            ev_light_m3[1],
            *ev_mend_f1[1:],
            *ev_mend_f2[1:],
            *ev_mend_f3[1:],
        ]
        self._check_applicability(
            cast(TemporalCOWState, state_light_m1),
            applicable,
            inapplicable,
            simulator,
            total_events,
        )

        # start mend_f1 action and check that light_m1 can be finished but after
        # the mend_f1 durative condition starts (ev_mend_f1[1]) light_m1 can't be finished
        # because it would violate the "light" constraint
        state_mended_f1 = cast(COWState, simulator.apply(ev_mend_f1[0], state_light_m1))
        assert state_mended_f1 is not None
        applicable = [
            ev_light_m1[1],
            ev_light_m2[0],
            ev_light_m3[0],
            ev_mend_f1[1],
        ]
        inapplicable = [
            ev_light_m1[0],
            ev_light_m2[1],
            ev_light_m3[1],
            ev_mend_f1[0],
            *ev_mend_f1[2:],
            *ev_mend_f2,
            *ev_mend_f3,
        ]
        self._check_applicability(
            cast(TemporalCOWState, state_mended_f1),
            applicable,
            inapplicable,
            simulator,
            total_events,
        )
        state_mended_f1 = cast(
            COWState, simulator.apply(ev_mend_f1[1], state_mended_f1)
        )
        assert state_mended_f1 is not None
        applicable = [
            ev_light_m2[0],
            ev_light_m3[0],
            ev_mend_f1[2],
        ]
        inapplicable = [
            ev_light_m1[1],
            ev_light_m1[0],
            ev_light_m2[1],
            ev_light_m3[1],
            *ev_mend_f1[0:2],
            ev_mend_f1[3],
            *ev_mend_f2,
            *ev_mend_f3,
        ]
        self._check_applicability(
            cast(TemporalCOWState, state_mended_f1),
            applicable,
            inapplicable,
            simulator,
            total_events,
        )

        # Apply all the sequence to mend f1 and end the action light m1
        state_mended_f1 = cast(
            COWState, simulator.apply(ev_mend_f1[2], state_mended_f1)
        )
        assert state_mended_f1 is not None
        state_mended_f1 = cast(
            COWState, simulator.apply(ev_mend_f1[3], state_mended_f1)
        )
        assert state_mended_f1 is not None
        state_mended_f1 = cast(
            COWState, simulator.apply(ev_light_m1[1], state_mended_f1)
        )
        assert state_mended_f1 is not None

        # check validity of the state
        applicable = [ev_light_m2[0], ev_light_m3[0]]
        inapplicable = [
            *ev_light_m1,
            ev_light_m2[1],
            ev_light_m3[1],
            *ev_mend_f1,
            *ev_mend_f2,
            *ev_mend_f3,
        ]
        self._check_applicability(
            cast(TemporalCOWState, state_mended_f1),
            applicable,
            inapplicable,
            simulator,
            total_events,
        )

        self.assertTrue(state_mended_f1.get_value(match_used(m1)).bool_constant_value())
        self.assertTrue(
            state_mended_f1.get_value(fuse_mended(f1)).bool_constant_value()
        )
        self.assertFalse(
            state_mended_f1.get_value(match_used(m2)).bool_constant_value()
        )
        self.assertFalse(
            state_mended_f1.get_value(fuse_mended(f2)).bool_constant_value()
        )
        self.assertFalse(
            state_mended_f1.get_value(match_used(m3)).bool_constant_value()
        )
        self.assertFalse(
            state_mended_f1.get_value(fuse_mended(f3)).bool_constant_value()
        )

        self.assertFalse(simulator.is_goal(state_mended_f1))

        # apply all the events in the right order to obtain the goal, but don't apply the ev_light_m3[1] event
        chain_apply = [
            ev_light_m2[0],
            *ev_mend_f2,
            ev_light_m2[1],
            ev_light_m3[0],
            *ev_mend_f3,
        ]
        not_goal: COWState = state_mended_f1
        for ev in chain_apply:
            not_goal = cast(COWState, simulator.apply(ev, not_goal))
            assert not_goal is not None
        self.assertFalse(simulator.is_goal(not_goal))
        self.assertEqual(0, len(simulator.get_unsatisfied_goals(not_goal)))

        goal: COWState = cast(COWState, simulator.apply(ev_light_m3[1], not_goal))
        assert goal is not None
        self.assertTrue(simulator.is_goal(goal))

    def simulate_on_temporal_basic(
        self, simulator: SimulatorMixin, problem: "up.model.Problem"
    ):
        # The aim of this test is the robustness of the time constraints in the problem.
        self.assertEqual(problem.name, "temporal_basic")
        a = problem.action("a")
        b = problem.action("b")
        x = problem.fluent("x")
        y = problem.fluent("y")

        state: COWState = cast(COWState, simulator.get_initial_state())
        self.assertFalse(state.get_value(x()).bool_constant_value())
        self.assertFalse(state.get_value(y()).bool_constant_value())

        ev_a = cast(List[TemporalEvent], simulator.get_events(a, [], 2))
        self.assertEqual(2, len(ev_a))
        self.assertEqual(TemporalEventKind.START_ACTION, ev_a[0].kind)
        self.assertEqual(TemporalEventKind.END_ACTION, ev_a[1].kind)

        ev_b = cast(List[TemporalEvent], simulator.get_events(b, [], 4))
        self.assertEqual(2, len(ev_b))
        self.assertEqual(TemporalEventKind.START_ACTION, ev_b[0].kind)
        self.assertEqual(TemporalEventKind.END_ACTION, ev_b[1].kind)

        print_dict = {
            ev_a[0]: "Start A",
            ev_a[1]: "End A",
            ev_b[0]: "Start B",
            ev_b[1]: "End B",
        }

        total_events = 2 * 2  # 2 events * 2 actions
        applicable = [ev_a[0], ev_b[0]]
        inapplicable = [ev_a[1], ev_b[1]]
        self._check_applicability(
            cast(TemporalCOWState, state),
            applicable,
            inapplicable,
            simulator,
            total_events,
        )

        state = cast(COWState, simulator.apply(ev_a[0], state))
        assert state is not None

        applicable = [ev_a[1], ev_b[0]]
        inapplicable = [ev_a[0], ev_b[1]]
        self._check_applicability(
            cast(TemporalCOWState, state),
            applicable,
            inapplicable,
            simulator,
            total_events,
        )

        state = cast(COWState, simulator.apply(ev_b[0], state))
        assert state is not None

        applicable = [ev_a[1], ev_b[1]]
        inapplicable = [ev_a[0], ev_b[0]]
        self._check_applicability(
            cast(TemporalCOWState, state),
            applicable,
            inapplicable,
            simulator,
            total_events,
        )

        # Now, a is shorter (2) than b (4), so, if b_end (ev_b[1]) is applied,
        # a_end (ev_a[1]) can't be applied.
        false_state = cast(COWState, simulator.apply(ev_b[1], state))
        assert false_state is not None

        # no events are applicable.
        applicable = []
        inapplicable = [*ev_a, *ev_b]
        self._check_applicability(
            cast(TemporalCOWState, false_state),
            applicable,
            inapplicable,
            simulator,
            total_events,
        )

        state = cast(COWState, simulator.apply(ev_a[1], state))
        assert state is not None
        self.assertFalse(simulator.is_goal(state))
        state = cast(COWState, simulator.apply(ev_b[1], state))
        assert state is not None

        self.assertTrue(simulator.is_goal(state))
        # to_print = str(false_state.stn)
        # for ev, repr in print_dict.items():
        #     to_print = to_print.replace(str(ev), repr)

    def test_with_temporal_simulator_instance(self):
        problem = self.problems["matchcellar"].problem
        simulator = TemporalSimulator(problem)
        self.simulate_on_matchcellar(simulator, problem)
        problem = self.problems["temporal_basic"].problem
        simulator = TemporalSimulator(problem)
        self.simulate_on_temporal_basic(simulator, problem)

    def test_with_simulator_from_factory(self):
        problem = self.problems["matchcellar"].problem
        with Simulator(problem) as simulator:
            self.simulate_on_matchcellar(simulator, problem)
        problem = self.problems["temporal_basic"].problem
        with Simulator(problem) as simulator:
            self.simulate_on_temporal_basic(simulator, problem)
