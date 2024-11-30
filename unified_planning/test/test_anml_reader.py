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


import tempfile
from typing import cast
from unified_planning.shortcuts import *
from unified_planning.model import DurativeAction
from unified_planning.test import unittest_TestCase
from unified_planning.io import ANMLReader, ANMLWriter
from unified_planning.test.examples import get_example_problems
import os


FILE_PATH = os.path.dirname(os.path.abspath(__file__))
ANML_FILES_PATH = os.path.join(FILE_PATH, "anml")


class TestANMLReader(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()
        self.start_timing = StartTiming()
        self.start_interval = TimePointInterval(self.start_timing)
        self.end_timing = EndTiming()
        self.global_start_timing = GlobalStartTiming()
        self.global_end_timing = GlobalEndTiming()
        self.all_interval = ClosedTimeInterval(self.start_timing, self.end_timing)

    def test_basic(self):
        reader = ANMLReader()

        problem_filename = os.path.join(ANML_FILES_PATH, "basic.anml")
        problem = reader.parse_problem(problem_filename)
        em = problem.environment.expression_manager

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 1)
        self.assertEqual(len(problem.actions), 1)
        self.assertEqual(len(problem.goals), 1)
        self.assertEqual(len(problem.timed_goals), 0)
        self.assertEqual(len(problem.timed_effects), 0)
        a = cast(DurativeAction, problem.action("a"))
        self.assertEqual(a.duration, FixedDuration(em.Int(6)))
        self.assertEqual(len(a.conditions), 0)
        for timing, effect_list in a.effects.items():
            if timing == self.end_timing:
                self.assertEqual(len(effect_list), 1)
            else:
                self.assertTrue(False)

        with open(problem_filename, "r", encoding="utf-8") as file:
            problem_str = file.read()

        problem_2 = reader.parse_problem_string(problem_str, problem_filename)
        self.assertEqual(problem, problem_2)

    def test_match_reader(self):
        reader = ANMLReader()

        problem_filename = os.path.join(ANML_FILES_PATH, "match.anml")
        problem = reader.parse_problem(problem_filename)
        em = problem.environment.expression_manager

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 4)
        self.assertEqual(len(problem.actions), 2)
        self.assertEqual(len(list(problem.objects(problem.user_type("Match")))), 3)
        self.assertEqual(len(list(problem.objects(problem.user_type("Fuse")))), 3)
        self.assertEqual(len(problem.goals), 3)
        self.assertEqual(len(problem.timed_goals), 0)
        self.assertEqual(len(problem.timed_effects), 0)

        light_match = cast(DurativeAction, problem.action("light_match"))
        self.assertEqual(light_match.duration, FixedDuration(em.Int(6)))
        for interval, cond_list in light_match.conditions.items():
            self.assertEqual(interval, self.start_interval)
            self.assertEqual(len(cond_list), 1)
        for timing, effect_list in light_match.effects.items():
            if timing == self.start_timing:
                self.assertEqual(len(effect_list), 2)
            elif timing == self.end_timing:
                self.assertEqual(len(effect_list), 1)
            else:
                self.assertTrue(False)

        mend_fuse = cast(DurativeAction, problem.action("mend_fuse"))
        self.assertEqual(mend_fuse.duration, FixedDuration(em.Int(5)))
        for interval, cond_list in mend_fuse.conditions.items():
            if interval in (self.start_interval, self.all_interval):
                self.assertEqual(len(cond_list), 1)
            else:
                self.assertTrue(False)
        for timing, effect_list in mend_fuse.effects.items():
            if timing == self.start_timing:
                self.assertEqual(len(effect_list), 1)
            elif timing == self.end_timing:
                self.assertEqual(len(effect_list), 2)
            else:
                self.assertTrue(False)

        with open(problem_filename, "r", encoding="utf-8") as file:
            problem_str = file.read()

        problem_2 = reader.parse_problem_string(problem_str, problem_filename)
        self.assertEqual(problem, problem_2)

    def test_connected_locations_reader(self):
        reader = ANMLReader()

        problem_filename = os.path.join(ANML_FILES_PATH, "connected_locations.anml")
        problem = reader.parse_problem(problem_filename)

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 2)
        self.assertEqual(len(problem.actions), 1)
        self.assertEqual(len(list(problem.objects(problem.user_type("Location")))), 3)
        self.assertEqual(len(problem.goals), 1)
        self.assertEqual(len(problem.timed_goals), 0)
        self.assertEqual(len(problem.timed_effects), 0)

        move = cast(DurativeAction, problem.action("move"))
        for interval, cond_list in move.conditions.items():
            self.assertEqual(interval, self.start_interval)
            self.assertEqual(len(cond_list), 2)
        for timing, effect_list in move.effects.items():
            if timing == self.start_timing:
                self.assertEqual(len(effect_list), 2)
            else:
                self.assertTrue(False)

        with open(problem_filename, "r", encoding="utf-8") as file:
            problem_str = file.read()

        problem_2 = reader.parse_problem_string(problem_str, problem_filename)
        self.assertEqual(problem, problem_2)

    def test_constants_no_variable_duration_reader(self):
        reader = ANMLReader()

        problem_filename = os.path.join(
            ANML_FILES_PATH, "constants_no_variable_duration.anml"
        )
        problem = reader.parse_problem(problem_filename)
        em = problem.environment.expression_manager

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 4)
        self.assertEqual(len(problem.actions), 1)
        self.assertEqual(len(list(problem.objects(problem.user_type("Location")))), 5)
        self.assertEqual(len(problem.goals), 1)
        self.assertEqual(len(problem.timed_goals), 0)
        self.assertEqual(len(problem.timed_effects), 0)

        move = cast(DurativeAction, problem.action("move"))
        self.assertEqual(move.duration, FixedDuration(em.Int(4)))
        for interval, cond_list in move.conditions.items():
            self.assertEqual(interval, self.start_interval)
            self.assertEqual(len(cond_list), 3)
        for timing, effect_list in move.effects.items():
            if timing == self.start_timing:
                self.assertEqual(len(effect_list), 1)
            elif timing == self.end_timing:
                self.assertEqual(len(effect_list), 2)
            else:
                self.assertTrue(False)

        with open(problem_filename, "r", encoding="utf-8") as file:
            problem_str = file.read()

        problem_2 = reader.parse_problem_string(problem_str, problem_filename)
        self.assertEqual(problem, problem_2)

    def test_durative_goals_reader(self):
        reader = ANMLReader()

        problem_filename = os.path.join(ANML_FILES_PATH, "durative_goals.anml")
        problem = reader.parse_problem(problem_filename)
        em = problem.environment.expression_manager

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 2)
        self.assertEqual(len(problem.actions), 1)
        self.assertEqual(len(problem.all_objects), 0)
        self.assertEqual(len(problem.goals), 1)
        self.assertEqual(len(problem.timed_goals), 1)
        self.assertEqual(len(problem.timed_effects), 1)

        a = cast(DurativeAction, problem.action("a"))
        self.assertEqual(a.duration, FixedDuration(em.Int(1)))
        for interval, cond_list in a.conditions.items():
            self.assertEqual(interval, self.all_interval)
            self.assertEqual(len(cond_list), 1)
        for timing, effect_list in a.effects.items():
            if timing == self.end_timing:
                self.assertEqual(len(effect_list), 1)
            else:
                self.assertTrue(False)

        with open(problem_filename, "r", encoding="utf-8") as file:
            problem_str = file.read()

        problem_2 = reader.parse_problem_string(problem_str, problem_filename)
        self.assertEqual(problem, problem_2)

    def test_forall_reader(self):
        reader = ANMLReader()

        problem_filename = os.path.join(ANML_FILES_PATH, "forall.anml")
        problem = reader.parse_problem(problem_filename)
        em = problem.environment.expression_manager

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 2)
        self.assertEqual(len(problem.actions), 1)
        self.assertEqual(len(list(problem.objects(problem.user_type("Location")))), 3)
        self.assertEqual(len(problem.goals), 1)
        self.assertEqual(len(problem.timed_goals), 0)
        self.assertEqual(len(problem.timed_effects), 0)

        visit = cast(DurativeAction, problem.action("visit"))
        to_visit = visit.parameter("to_visit")
        Location = problem.user_type("Location")
        precedes = problem.fluent("precedes")
        visited = problem.fluent("visited")
        p = Variable("p", Location, problem.environment)
        cond_test = em.Forall(
            em.And(
                em.Or(em.Not(precedes(p, to_visit)), visited(p)),
                em.Not(visited(to_visit)),
            ),
            p,
        )
        l = Variable("l", Location, problem.environment)
        l2 = Variable("l2", Location, problem.environment)
        goal_test = em.Forall(
            em.And(
                visited(l), em.Forall(em.Or(em.Not(precedes(l2, l)), visited(l2)), l2)
            ),
            l,
        )
        self.assertEqual(
            visit.duration,
            FixedDuration(em.Int(3)),
        )
        for interval, cond_list in visit.conditions.items():
            self.assertEqual(interval, self.start_interval)
            self.assertEqual(len(cond_list), 1)
            self.assertEqual(cond_test, cond_list[0])
        for timing, effect_list in visit.effects.items():
            if timing == self.end_timing:
                self.assertEqual(len(effect_list), 1)
            else:
                self.assertTrue(False)
        for g in problem.goals:
            self.assertEqual(g, goal_test)

        with open(problem_filename, "r", encoding="utf-8") as file:
            problem_str = file.read()

        problem_2 = reader.parse_problem_string(problem_str, problem_filename)
        self.assertEqual(problem, problem_2)

    def test_basic_conditional_reader(self):
        reader = ANMLReader()

        problem_filename = os.path.join(ANML_FILES_PATH, "basic_conditional.anml")
        problem = reader.parse_problem(problem_filename)
        em = problem.environment.expression_manager

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 2)
        self.assertEqual(len(problem.actions), 1)
        self.assertEqual(len(problem.all_objects), 0)
        self.assertEqual(len(problem.goals), 2)
        self.assertEqual(len(problem.timed_goals), 0)
        self.assertEqual(len(problem.timed_effects), 1)

        a = cast(DurativeAction, problem.action("a"))
        self.assertEqual(
            a.duration,
            FixedDuration(em.Int(6)),
        )
        self.assertEqual(len(a.conditions), 0)
        for timing, effect_list in a.effects.items():
            if timing == self.end_timing:
                self.assertEqual(len(effect_list), 1)
                for e in effect_list:
                    self.assertTrue(e.is_conditional())
            else:
                self.assertTrue(False)

        with open(problem_filename, "r", encoding="utf-8") as file:
            problem_str = file.read()

        problem_2 = reader.parse_problem_string(problem_str, problem_filename)
        self.assertEqual(problem, problem_2)

    def test_hydrone_reader(self):
        reader = ANMLReader()

        problem_filename = os.path.join(ANML_FILES_PATH, "hydrone.anml")
        problem = reader.parse_problem(problem_filename)
        em = problem.environment.expression_manager

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 5)
        self.assertEqual(len(problem.actions), 1)
        self.assertEqual(len(list(problem.objects(problem.user_type("Location")))), 9)
        self.assertEqual(len(problem.goals), 3)
        self.assertEqual(len(problem.timed_goals), 0)
        self.assertEqual(len(problem.timed_effects), 0)

        move = cast(DurativeAction, problem.action("move"))
        distance_fluent = problem.fluent("distance")
        from_parameter = move.parameter("from")
        destination_parameter = move.parameter("destination")
        self.assertEqual(
            move.duration,
            FixedDuration(distance_fluent(from_parameter, destination_parameter)),
        )
        for interval, cond_list in move.conditions.items():
            self.assertEqual(interval, self.start_interval)
            self.assertEqual(len(cond_list), 5)
        for timing, effect_list in move.effects.items():
            if timing == self.start_timing:
                self.assertEqual(len(effect_list), 2)
            elif timing == self.end_timing:
                self.assertEqual(len(effect_list), 4)
            else:
                self.assertTrue(False)

        with open(problem_filename, "r", encoding="utf-8") as file:
            problem_str = file.read()

        problem_2 = reader.parse_problem_string(problem_str, problem_filename)
        self.assertEqual(problem, problem_2)

    def test_match_int_id_reader(self):
        reader = ANMLReader()

        problem_filename = os.path.join(ANML_FILES_PATH, "match_int_id.anml")
        problem = reader.parse_problem(problem_filename)
        em = problem.environment.expression_manager

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 4)
        self.assertEqual(len(problem.actions), 2)
        self.assertEqual(len(problem.all_objects), 0)
        self.assertEqual(len(problem.goals), 3)
        self.assertEqual(len(problem.timed_goals), 0)
        self.assertEqual(len(problem.timed_effects), 0)

        light_match = cast(DurativeAction, problem.action("light_match"))
        self.assertEqual(light_match.duration, FixedDuration(em.Int(5)))
        for interval, cond_list in light_match.conditions.items():
            self.assertEqual(interval, self.start_interval)
            self.assertEqual(len(cond_list), 1)
        for timing, effect_list in light_match.effects.items():
            if timing == self.start_timing:
                self.assertEqual(len(effect_list), 2)
            elif timing == self.end_timing:
                self.assertEqual(len(effect_list), 1)
            else:
                self.assertTrue(False)

        mend_fuse = cast(DurativeAction, problem.action("mend_fuse"))
        self.assertEqual(
            mend_fuse.duration, RightOpenDurationInterval(em.Int(3), em.Int(5))
        )
        for interval, cond_list in mend_fuse.conditions.items():
            if interval in (self.start_interval, self.all_interval):
                self.assertEqual(len(cond_list), 1)
            else:
                self.assertTrue(False)
        for timing, effect_list in mend_fuse.effects.items():
            if timing == self.start_timing:
                self.assertEqual(len(effect_list), 1)
            elif timing == self.end_timing:
                self.assertEqual(len(effect_list), 2)
            else:
                self.assertTrue(False)

        with open(problem_filename, "r", encoding="utf-8") as file:
            problem_str = file.read()

        problem_2 = reader.parse_problem_string(problem_str, problem_filename)
        self.assertEqual(problem, problem_2)

    def test_match_test_parser_reader(self):
        reader = ANMLReader()

        problem_filename = os.path.join(ANML_FILES_PATH, "match_test_parser.anml")
        problem = reader.parse_problem(problem_filename)
        em = problem.environment.expression_manager

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 6)
        self.assertEqual(len(problem.actions), 2)
        self.assertEqual(len(problem.all_objects), 2)
        self.assertEqual(len(problem.goals), 2)
        self.assertEqual(len(problem.timed_goals), 0)
        self.assertEqual(len(problem.timed_effects), 0)

        light_match = cast(DurativeAction, problem.action("action_LIGHT_MATCH"))
        self.assertEqual(light_match.duration, FixedDuration(em.Real(Fraction(5))))
        for interval, cond_list in light_match.conditions.items():
            self.assertEqual(interval, self.start_interval)
            self.assertEqual(len(cond_list), 1)
        for timing, effect_list in light_match.effects.items():
            if timing == self.start_timing:
                self.assertEqual(len(effect_list), 2)
            elif timing == self.end_timing:
                self.assertEqual(len(effect_list), 1)
            else:
                self.assertTrue(False)

        mend_fuse = cast(DurativeAction, problem.action("action_MEND_FUSE"))
        self.assertEqual(mend_fuse.duration, FixedDuration(em.Real(Fraction(2))))
        start_plus_one = StartTiming(1)
        for interval, cond_list in mend_fuse.conditions.items():
            if interval == self.start_interval:
                self.assertEqual(len(cond_list), 2)
            elif interval == OpenTimeInterval(self.start_timing, self.end_timing):
                self.assertEqual(len(cond_list), 1)
            elif interval == TimePointInterval(start_plus_one):
                self.assertEqual(len(cond_list), 1)
            elif interval == LeftOpenTimeInterval(start_plus_one, self.end_timing):
                self.assertEqual(len(cond_list), 2)
            else:
                self.assertTrue(False)
        for timing, effect_list in mend_fuse.effects.items():
            if timing == self.start_timing:
                self.assertEqual(len(effect_list), 2)
            elif timing == start_plus_one:
                self.assertEqual(len(effect_list), 2)
            elif timing == self.end_timing:
                self.assertEqual(len(effect_list), 2)
            else:
                self.assertTrue(False)

        with open(problem_filename, "r", encoding="utf-8") as file:
            problem_str = file.read()

        problem_2 = reader.parse_problem_string(problem_str, problem_filename)
        self.assertEqual(problem, problem_2)

    def test_simple_mais_reader(self):
        reader = ANMLReader()

        problem_filename = os.path.join(ANML_FILES_PATH, "simple_mais.anml")
        problem = reader.parse_problem(problem_filename)
        em = problem.environment.expression_manager

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 5)
        self.assertEqual(len(problem.actions), 6)
        self.assertEqual(len(problem.all_objects), 0)
        self.assertEqual(len(problem.goals), 1)
        self.assertEqual(len(problem.timed_goals), 0)
        self.assertEqual(len(problem.timed_effects), 0)

        recipe = cast(DurativeAction, problem.action("recipe"))
        self.assertEqual(recipe.duration, FixedDuration(em.Int(160)))
        possible_delays = [
            10,
            20,
            25,
            35,
            40,
            50,
            55,
            65,
            70,
            80,
            85,
            95,
            100,
            110,
            115,
            125,
            130,
            140,
            145,
            155,
        ]
        possible_timepoint_intervals = [
            TimePointInterval(StartTiming(d)) for d in possible_delays
        ]
        for interval, cond_list in recipe.conditions.items():
            if interval in possible_timepoint_intervals:
                self.assertEqual(len(cond_list), 1)
            else:
                self.assertTrue(False)
        for timing, effect_list in recipe.effects.items():
            if timing == self.start_timing:
                self.assertEqual(len(effect_list), 1)
            elif timing == self.end_timing:
                self.assertEqual(len(effect_list), 1)
            else:
                self.assertTrue(False)

        prepare_bar = cast(DurativeAction, problem.action("prepare_bar"))
        self.assertEqual(prepare_bar.duration, FixedDuration(em.Int(6)))
        for interval, cond_list in prepare_bar.conditions.items():
            if interval == self.start_interval:
                self.assertEqual(len(cond_list), 1)
            else:
                self.assertTrue(False)
        for timing, effect_list in prepare_bar.effects.items():
            if timing == self.end_timing:
                self.assertEqual(len(effect_list), 1)
            else:
                self.assertTrue(False)

        finish_bar = cast(DurativeAction, problem.action("finish_bar"))
        self.assertEqual(finish_bar.duration, FixedDuration(em.Int(6)))
        for interval, cond_list in finish_bar.conditions.items():
            if interval == self.start_interval:
                self.assertEqual(len(cond_list), 1)
            else:
                self.assertTrue(False)
        for timing, effect_list in finish_bar.effects.items():
            if timing == self.end_timing:
                self.assertEqual(len(effect_list), 1)
            else:
                self.assertTrue(False)

        load = cast(DurativeAction, problem.action("load"))
        self.assertEqual(load.duration, FixedDuration(em.Int(1)))
        for interval, cond_list in load.conditions.items():
            if interval == self.start_interval:
                self.assertEqual(len(cond_list), 1)
            else:
                self.assertTrue(False)
        for timing, effect_list in load.effects.items():
            if timing == self.end_timing:
                self.assertEqual(len(effect_list), 1)
            else:
                self.assertTrue(False)

        unload = cast(DurativeAction, problem.action("unload"))
        self.assertEqual(unload.duration, FixedDuration(em.Int(1)))
        for interval, cond_list in unload.conditions.items():
            if interval == self.start_interval:
                self.assertEqual(len(cond_list), 1)
            else:
                self.assertTrue(False)
        for timing, effect_list in unload.effects.items():
            if timing == self.end_timing:
                self.assertEqual(len(effect_list), 1)
            else:
                self.assertTrue(False)

        move_hoist = cast(DurativeAction, problem.action("move_hoist"))
        self.assertEqual(move_hoist.duration, FixedDuration(em.Int(1)))
        for interval, cond_list in move_hoist.conditions.items():
            if interval == self.start_interval:
                self.assertEqual(len(cond_list), 1)
            else:
                self.assertTrue(False)
        for timing, effect_list in move_hoist.effects.items():
            if timing == self.end_timing:
                self.assertEqual(len(effect_list), 1)
            else:
                self.assertTrue(False)

        with open(problem_filename, "r", encoding="utf-8") as file:
            problem_str = file.read()

        problem_2 = reader.parse_problem_string(problem_str, problem_filename)
        self.assertEqual(problem, problem_2)

    def test_tils_reader(self):
        reader = ANMLReader()

        problem_filename = os.path.join(ANML_FILES_PATH, "tils.anml")
        problem = reader.parse_problem(problem_filename)
        em = problem.environment.expression_manager

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 2)
        self.assertEqual(len(problem.actions), 1)
        self.assertEqual(len(problem.all_objects), 0)
        self.assertEqual(len(problem.goals), 1)
        self.assertEqual(len(problem.timed_goals), 0)
        self.assertEqual(len(problem.timed_effects), 2)

        a = cast(DurativeAction, problem.action("a"))
        self.assertEqual(a.duration, FixedDuration(em.Int(1)))
        for interval, cond_list in a.conditions.items():
            self.assertEqual(interval, self.all_interval)
            self.assertEqual(len(cond_list), 1)
        for timing, effect_list in a.effects.items():
            if timing == self.end_timing:
                self.assertEqual(len(effect_list), 1)
            else:
                self.assertTrue(False)

        with open(problem_filename, "r", encoding="utf-8") as file:
            problem_str = file.read()

        problem_2 = reader.parse_problem_string(problem_str, problem_filename)
        self.assertEqual(problem, problem_2)

    def test_hierarchical_blocks_world_reader(self):
        reader = ANMLReader()

        problem_filename = os.path.join(
            ANML_FILES_PATH, "hierarchical_blocks_world.anml"
        )
        problem = reader.parse_problem(problem_filename)
        em = problem.environment.expression_manager

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 2)
        self.assertEqual(len(problem.actions), 1)
        self.assertEqual(len(problem.goals), 3)
        self.assertEqual(len(problem.timed_goals), 0)
        self.assertEqual(len(problem.timed_effects), 0)
        types_with_6_objects = ("Entity", "Location")
        for ut in problem.user_types:
            if cast(up.model.types._UserType, ut).name in types_with_6_objects:
                self.assertEqual(len(list(problem.objects(ut))), 6)
            else:
                self.assertEqual(len(list(problem.objects(ut))), 3)

        move = cast(DurativeAction, problem.action("move"))
        self.assertEqual(move.duration, FixedDuration(em.Int(0)))
        for interval, cond_list in move.conditions.items():
            self.assertEqual(interval, self.start_interval)
            self.assertEqual(len(cond_list), 3)
        for timing, effect_list in move.effects.items():
            if timing == self.start_timing:
                self.assertEqual(len(effect_list), 4)
            else:
                self.assertTrue(False)

        with open(problem_filename, "r", encoding="utf-8") as file:
            problem_str = file.read()

        problem_2 = reader.parse_problem_string(problem_str, problem_filename)
        self.assertEqual(problem, problem_2)

    def test_safe_road_reader(self):
        reader = ANMLReader()
        problem_filename = os.path.join(ANML_FILES_PATH, "safe_road.anml")
        problem = reader.parse_problem(problem_filename)

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 2)
        self.assertEqual(len(problem.actions), 2)
        self.assertEqual(len(list(problem.objects(problem.user_type("location")))), 3)
        self.assertEqual(len(problem.goals), 2)
        self.assertEqual(len(problem.timed_goals), 0)
        self.assertEqual(len(problem.timed_effects), 0)

        check = cast(DurativeAction, problem.action("check"))
        for interval, cond_list in check.conditions.items():
            self.assertEqual(interval, self.start_interval)
            self.assertEqual(len(cond_list), 1)
        for timing, effect_list in check.effects.items():
            self.assertEqual(timing, self.start_timing)
            self.assertEqual(len(effect_list), 1)

        nd = cast(DurativeAction, problem.action("natural_disaster"))
        self.assertEqual(len(nd.conditions), 0)
        for timing, effect_list in nd.effects.items():
            if timing == self.start_timing:
                self.assertEqual(len(effect_list), 1)
                self.assertFalse(effect_list[0].is_forall())
            elif timing == self.end_timing:
                self.assertEqual(len(effect_list), 1)
                self.assertTrue(effect_list[0].is_forall())
            else:
                self.assertTrue(False)

        with open(problem_filename, "r", encoding="utf-8") as file:
            problem_str = file.read()

        problem_2 = reader.parse_problem_string(problem_str, problem_filename)
        self.assertEqual(problem, problem_2)

    def test_majsp(self):
        """This checks that the majsp problem is parsable without error"""
        reader = ANMLReader()
        problem_filename = os.path.join(ANML_FILES_PATH, "majsp.anml")
        reader.parse_problem(problem_filename)
        _problem = reader.parse_problem(problem_filename)

    def test_anml_io(self):
        for example in self.problems.values():
            problem = example.problem
            problems_to_skip = []
            if problem.name in problems_to_skip:
                continue
            kind = problem.kind
            if not kind.has_action_based() or kind.has_processes():
                continue
            with tempfile.TemporaryDirectory() as tempdir:
                problem_filename = os.path.join(tempdir, "problem.anml")

                w = ANMLWriter(problem)
                w.write_problem(problem_filename)
                reader = ANMLReader()
                parsed_problem = reader.parse_problem(problem_filename)
            self.assertEqual(len(problem.user_types), len(parsed_problem.user_types))
            self.assertEqual(len(problem.actions), len(parsed_problem.actions))
            for act, parsed_act in zip(problem.actions, parsed_problem.actions):
                if isinstance(act, InstantaneousAction):
                    conditions = (
                        {TimePointInterval(StartTiming()): act.preconditions}
                        if act.preconditions
                        else {}
                    )
                    effects = {StartTiming(): act.effects} if act.effects else {}
                else:
                    assert isinstance(act, DurativeAction)
                    conditions = act.conditions
                    effects = act.effects
                assert isinstance(parsed_act, DurativeAction)
                if conditions != parsed_act.conditions:
                    for i, cl in conditions.items():
                        parsed_cl = parsed_act.conditions[i]
                        self.assertEqual(len(cl), len(parsed_cl))
                if effects != parsed_act.effects:
                    for t, el in effects.items():
                        parsed_el = parsed_act.effects[t]
                        self.assertEqual(len(el), len(parsed_el))
                        for eff, parsed_eff in zip(el, parsed_el):
                            self.assertTrue(
                                eff.is_conditional() == parsed_eff.is_conditional()
                            )
                            self.assertTrue(eff.is_forall() == parsed_eff.is_forall())
