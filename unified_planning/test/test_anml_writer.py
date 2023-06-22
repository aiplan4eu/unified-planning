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


from unified_planning.shortcuts import *
from unified_planning.test import TestCase, main, skipIfEngineNotAvailable
from unified_planning.test.examples import get_example_problems
from unified_planning.io import ANMLWriter
import tempfile
import os


class TestANMLWriter(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_basic(self):
        problem = self.problems["basic"].problem
        aw = ANMLWriter(problem)
        anml_problem = aw.get_problem()
        self.assertIn("fluent boolean x;\n", anml_problem)
        self.assertIn("action a() {\n", anml_problem)
        self.assertIn("   [ start ] (not x);\n", anml_problem)
        self.assertIn("   [ start ] x := true;\n", anml_problem)
        self.assertIn("};\n", anml_problem)
        self.assertIn("[ start ] x := false;\n", anml_problem)
        self.assertIn("[ end ] x;\n", anml_problem)
        self.assertEqual(anml_problem.count("\n"), 7)

    def test_hierarchical_blocks_world(self):
        problem = self.problems["hierarchical_blocks_world"].problem
        aw = ANMLWriter(problem)
        anml_problem = aw.get_problem()
        self.assertIn("type Entity;\n", anml_problem)
        self.assertIn("type Location < Entity;\n", anml_problem)
        self.assertIn("type Movable < Location;\n", anml_problem)
        self.assertIn("type Unmovable < Location;\n", anml_problem)
        self.assertIn("type TableSpace < Unmovable;\n", anml_problem)
        self.assertIn("type Block < Movable;\n", anml_problem)
        self.assertIn("fluent boolean clear(Location space);\n", anml_problem)
        self.assertIn(
            "fluent boolean on(Movable object_, Location space);\n", anml_problem
        )
        self.assertIn(
            "action move(Movable item, Location l_from, Location l_to) {\n",
            anml_problem,
        )
        self.assertIn("   [ start ] clear(item);\n", anml_problem)
        self.assertIn("   [ start ] clear(l_to);\n", anml_problem)
        self.assertIn("   [ start ] on(item, l_from);\n", anml_problem)
        self.assertIn("   [ start ] clear(l_from) := true;\n", anml_problem)
        self.assertIn("   [ start ] on(item, l_from) := false;\n", anml_problem)
        self.assertIn("   [ start ] clear(l_to) := false;\n", anml_problem)
        self.assertIn("[ start ] on(item, l_to) := true;\n", anml_problem)
        self.assertIn("};\n", anml_problem)
        self.assertIn("instance TableSpace ts_1, ts_2, ts_3;\n", anml_problem)
        self.assertIn("instance Block block_1, block_2, block_3;\n", anml_problem)
        self.assertIn("[ start ] clear(ts_2) := true;\n", anml_problem)
        self.assertIn("[ start ] clear(ts_3) := true;\n", anml_problem)
        self.assertIn("[ start ] clear(block_2) := true;\n", anml_problem)
        self.assertIn("[ start ] on(block_3, ts_1) := true;\n", anml_problem)
        self.assertIn("[ start ] on(block_1, block_3) := true;\n", anml_problem)
        self.assertIn("[ start ] on(block_2, block_1) := true;\n", anml_problem)
        self.assertIn("[ start ] clear(ts_1) := false;\n", anml_problem)
        self.assertIn("[ start ] clear(block_1) := false;\n", anml_problem)
        self.assertIn("[ start ] clear(block_3) := false;\n", anml_problem)
        self.assertIn("[ start ] on(block_1, ts_1) := false;\n", anml_problem)
        self.assertIn("[ start ] on(block_2, ts_1) := false;\n", anml_problem)
        self.assertIn("[ start ] on(block_1, ts_2) := false;\n", anml_problem)
        self.assertIn("[ start ] on(block_2, ts_2) := false;\n", anml_problem)
        self.assertIn("[ start ] on(block_3, ts_2) := false;\n", anml_problem)
        self.assertIn("[ start ] on(block_1, ts_3) := false;\n", anml_problem)
        self.assertIn("[ start ] on(block_2, ts_3) := false;\n", anml_problem)
        self.assertIn("[ start ] on(block_3, ts_3) := false;\n", anml_problem)
        self.assertIn("[ start ] on(block_1, block_1) := false;\n", anml_problem)
        self.assertIn("[ start ] on(block_3, block_1) := false;\n", anml_problem)
        self.assertIn("[ start ] on(block_1, block_2) := false;\n", anml_problem)
        self.assertIn("[ start ] on(block_2, block_2) := false;\n", anml_problem)
        self.assertIn("[ start ] on(block_3, block_2) := false;\n", anml_problem)
        self.assertIn("[ start ] on(block_2, block_3) := false;\n", anml_problem)
        self.assertIn("[ start ] on(block_3, block_3) := false;\n", anml_problem)
        self.assertIn("[ end ] on(block_1, ts_3);\n", anml_problem)
        self.assertIn("[ end ] on(block_2, block_1);\n", anml_problem)
        self.assertIn("[ end ] on(block_3, block_2);\n", anml_problem)
        self.assertEqual(anml_problem.count("\n"), 46)

    def test_timed_connected_locations(self):
        problem = self.problems["timed_connected_locations"].problem
        aw = ANMLWriter(problem)
        anml_problem = aw.get_problem()
        expected_result = """type Location;
fluent boolean is_at(Location position);
constant boolean is_connected(Location location_1, Location location_2);
action move(Location l_from, Location l_to) {
   duration >= 6 and duration <= 6;
   [ start, start ] is_at(l_from);
   [ start, start ] (not is_at(l_to));
   [ start, start ] (exists(Location mid_loc) { ((not ((mid_loc == l_from) or (mid_loc == l_to))) and (is_connected(l_from, mid_loc) or is_connected(mid_loc, l_from)) and (is_connected(l_to, mid_loc) or is_connected(mid_loc, l_to))) });
   [ start, end ] (exists(Location mid_loc) { ((not ((mid_loc == l_from) or (mid_loc == l_to))) and (is_connected(l_from, mid_loc) or is_connected(mid_loc, l_from)) and (is_connected(l_to, mid_loc) or is_connected(mid_loc, l_to))) });
   [ start + 1 ] is_at(l_from) := false;
   [ end - 5 ] is_at(l_to) := true;
};
instance Location l1, l2, l3, l4, l5;
[ start ] is_at(l1) := true;
is_connected(l1, l2) := true;
is_connected(l2, l3) := true;
is_connected(l3, l4) := true;
is_connected(l4, l5) := true;
[ start ] is_at(l2) := false;
[ start ] is_at(l3) := false;
[ start ] is_at(l4) := false;
[ start ] is_at(l5) := false;
is_connected(l1, l1) := false;
is_connected(l2, l1) := false;
is_connected(l3, l1) := false;
is_connected(l4, l1) := false;
is_connected(l5, l1) := false;
is_connected(l2, l2) := false;
is_connected(l3, l2) := false;
is_connected(l4, l2) := false;
is_connected(l5, l2) := false;
is_connected(l1, l3) := false;
is_connected(l3, l3) := false;
is_connected(l4, l3) := false;
is_connected(l5, l3) := false;
is_connected(l1, l4) := false;
is_connected(l2, l4) := false;
is_connected(l4, l4) := false;
is_connected(l5, l4) := false;
is_connected(l1, l5) := false;
is_connected(l2, l5) := false;
is_connected(l3, l5) := false;
is_connected(l5, l5) := false;
[ end ] is_at(l5);
"""
        self.assertEqual(anml_problem, expected_result)

    def test_matchcellar(self):
        problem = self.problems["matchcellar"].problem
        aw = ANMLWriter(problem)
        anml_problem = aw.get_problem()
        expected_result = """type Match;
type Fuse;
fluent boolean handfree;
fluent boolean light;
fluent boolean match_used(Match match);
fluent boolean fuse_mended(Fuse fuse);
action light_match(Match m) {
   duration >= 6 and duration <= 6;
   [ start, start ] (not match_used(m));
   [ start ] match_used(m) := true;
   [ start ] light := true;
   [ end ] light := false;
};
action mend_fuse(Fuse f) {
   duration >= 5 and duration <= 5;
   [ start, start ] handfree;
   [ start, end ] light;
   [ start ] handfree := false;
   [ end ] fuse_mended(f) := true;
   [ end ] handfree := true;
};
instance Match m1, m2, m3;
instance Fuse f1, f2, f3;
[ start ] light := false;
[ start ] handfree := true;
[ start ] match_used(m1) := false;
[ start ] match_used(m2) := false;
[ start ] match_used(m3) := false;
[ start ] fuse_mended(f1) := false;
[ start ] fuse_mended(f2) := false;
[ start ] fuse_mended(f3) := false;
[ end ] fuse_mended(f1);
[ end ] fuse_mended(f2);
[ end ] fuse_mended(f3);
"""
        self.assertEqual(anml_problem, expected_result)

    def test_robot_fluent_of_user_type(self):
        problem = self.problems["robot_fluent_of_user_type"].problem
        aw = ANMLWriter(problem)
        anml_problem = aw.get_problem()
        expected_result = """type Location;
type Robot;
fluent Location is_at(Robot robot);
action move(Robot robot, Location l_from, Location l_to) {
   [ start ] (is_at(robot) == l_from);
   [ start ] (not (is_at(robot) == l_to));
   [ start ] is_at(robot) := l_to;
};
instance Location l1, l2;
instance Robot r1, r2;
[ start ] is_at(r1) := l2;
[ start ] is_at(r2) := l1;
[ end ] (is_at(r1) == l1);
[ end ] (is_at(r2) == l2);
"""
        self.assertEqual(anml_problem, expected_result)

    def test_robot(self):
        problem = self.problems["robot"].problem
        aw = ANMLWriter(problem)
        anml_problem = aw.get_problem()
        expected_result = """type Location;
fluent boolean robot_at(Location position);
fluent float [0.0, 100.0] battery_charge;
action move(Location l_from, Location l_to) {
   [ start ] (10 <= battery_charge);
   [ start ] (not (l_from == l_to));
   [ start ] robot_at(l_from);
   [ start ] (not robot_at(l_to));
   [ start ] robot_at(l_from) := false;
   [ start ] robot_at(l_to) := true;
   [ start ] battery_charge := (battery_charge - 10);
};
instance Location l1, l2;
[ start ] robot_at(l1) := true;
[ start ] robot_at(l2) := false;
[ start ] battery_charge := 100;
[ end ] robot_at(l2);
"""
        self.assertEqual(anml_problem, expected_result)

    def test_ad_hoc_1(self):
        when = UserType("when")
        fl = Fluent("4ction")
        obj = Object("predicate", when)
        act = InstantaneousAction("variable", fluent=when)
        fluent = act.parameter("fluent")
        act.add_effect(fl, True, Equals(fluent, obj))
        problem = Problem("ad_hoc")
        problem.add_fluent(fl)
        problem.add_action(act)
        problem.add_object(obj)
        problem.set_initial_value(fl, False)
        aw = ANMLWriter(problem)
        anml_problem = aw.get_problem()
        expected_result = """type when_;
fluent boolean f_4ction;
action variable_(when_ fluent_) {
   when [ start ] (fluent_ == predicate_)
   {[ start ] f_4ction := true;
   }
};
instance when_ predicate_;
[ start ] f_4ction := false;
"""
        self.assertEqual(anml_problem, expected_result)

    @skipIfEngineNotAvailable("tamer")
    def test_with_pytamer(self):
        import pytamer

        with tempfile.TemporaryDirectory() as tempdir:
            temp_file_name = os.path.join(tempdir, "test_file.anml")
            with OneshotPlanner(name="tamer") as tamer:
                for example in self.problems.values():
                    problem = example.problem
                    kind = problem.kind
                    if (
                        tamer.supports(kind)
                        and not kind.has_increase_effects()
                        and not kind.has_decrease_effects()
                    ):
                        aw = ANMLWriter(problem)
                        aw.write_problem(temp_file_name)
                        tamer_env = pytamer.tamer_env_new()
                        pytamer_problem = pytamer.tamer_parse_anml(
                            tamer_env, temp_file_name
                        )
                        tamer_actions = list(
                            pytamer.tamer_problem_get_actions(pytamer_problem)
                        )
                        self.assertEqual(len(tamer_actions), len(problem.actions))
                        for ta in tamer_actions:
                            up_act = problem.action(pytamer.tamer_action_get_name(ta))
                            ta_params = list(pytamer.tamer_action_get_parameters(ta))
                            self.assertEqual(len(up_act.parameters), len(ta_params))
                        tamer_fluents_and_constants = list(
                            pytamer.tamer_problem_get_fluents(pytamer_problem)
                        )
                        number_of_fluents = len(tamer_fluents_and_constants)
                        tamer_fluents_and_constants.extend(
                            list(pytamer.tamer_problem_get_constants(pytamer_problem))
                        )
                        self.assertEqual(
                            len(tamer_fluents_and_constants), len(problem.fluents)
                        )
                        for n, tf in enumerate(tamer_fluents_and_constants):
                            if n < number_of_fluents:  # the current element is a fluent
                                up_fluent = problem.fluent(
                                    pytamer.tamer_fluent_get_name(tf)
                                )
                                tf_sign = list(pytamer.tamer_fluent_get_parameters(tf))
                            else:  # The current element is a constant
                                up_fluent = problem.fluent(
                                    pytamer.tamer_constant_get_name(tf)
                                )
                                tf_sign = list(
                                    pytamer.tamer_constant_get_parameters(tf)
                                )
                            self.assertEqual(len(up_fluent.signature), len(tf_sign))
                        tamer_objects = list(
                            pytamer.tamer_problem_get_instances(pytamer_problem)
                        )
                        for to in tamer_objects:
                            problem.object(pytamer.tamer_instance_get_name(to))
                        self.assertEqual(len(tamer_objects), len(problem.all_objects))
