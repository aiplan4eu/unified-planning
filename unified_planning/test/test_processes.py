# Copyright 2021-2023 AIPlan4EU project
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

from random import shuffle

import unified_planning
from unified_planning.shortcuts import *
from unified_planning.test import unittest_TestCase


class TestProcesses(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)

    def test_state(self):
        x = Fluent("x", BoolType())
        pr = Process("Name")
        pr.add_precondition(x)

        self.assertNotEqual({x}, pr.preconditions)

    def test_fluent_used_only_in_process_precondition_is_not_unused(self):
        # a fluent read only by a Process precondition must not be reported as unused:
        # pruning it would leave the precondition referencing an undeclared fluent
        problem = Problem("proc_precondition")
        x = Fluent("x", RealType())
        y = Fluent("y", RealType())
        problem.add_fluent(x, default_initial_value=0.0)
        problem.add_fluent(y, default_initial_value=0.0)

        proc = Process("proc")
        proc.add_precondition(GE(x, 1))
        proc.add_increase_continuous_effect(y, 1)
        problem.add_process(proc)

        self.assertNotIn(x, problem.get_unused_fluents())

    def test_process_and_event_agree_on_precondition_only_fluents(self):
        # Process and Event preconditions must be scanned the same way when
        # computing unused fluents
        process_problem = Problem("proc_precondition")
        x = Fluent("x", RealType())
        y = Fluent("y", RealType())
        process_problem.add_fluent(x, default_initial_value=0.0)
        process_problem.add_fluent(y, default_initial_value=0.0)
        proc = Process("proc")
        proc.add_precondition(GE(x, 1))
        proc.add_increase_continuous_effect(y, 1)
        process_problem.add_process(proc)

        event_problem = Problem("event_precondition")
        x2 = Fluent("x", RealType())
        y2 = Fluent("y", RealType())
        event_problem.add_fluent(x2, default_initial_value=0.0)
        event_problem.add_fluent(y2, default_initial_value=0.0)
        ev = Event("ev")
        ev.add_precondition(GE(x2, 1))
        ev.add_increase_effect(y2, 1)
        event_problem.add_event(ev)

        self.assertEqual(
            {f.name for f in process_problem.get_unused_fluents()},
            {f.name for f in event_problem.get_unused_fluents()},
        )
