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


from unified_planning.shortcuts import *
from unified_planning.test import TestCase, main
from unified_planning.test.examples import get_example_problems
from unified_planning.io import ANMLWriter

class TestPythonWriter(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_basic(self):
        problem = self.problems['basic'].problem
        aw = ANMLWriter(problem)
        anml_problem = aw.get_problem()
        self.assertIn('fluent boolean x;\n', anml_problem)
        self.assertIn('action a() {\n', anml_problem)
        self.assertIn('   [ start ] (not x);\n', anml_problem)
        self.assertIn('   [ start ] x := true;\n', anml_problem)
        self.assertIn('}\n', anml_problem)
        self.assertIn('[ start ] x := false;\n', anml_problem)
        self.assertIn('[ end ] x;\n', anml_problem)
        self.assertEqual(anml_problem.count('\n'), 7)

    def test_hierarchical_blocks_world(self):
        problem = self.problems['hierarchical_blocks_world'].problem
        aw = ANMLWriter(problem)
        anml_problem = aw.get_problem()
        self.assertIn('type Entity;\n', anml_problem)
        self.assertIn('type Location < Entity;\n', anml_problem)
        self.assertIn('type Movable < Location;\n', anml_problem)
        self.assertIn('type Unmovable < Location;\n', anml_problem)
        self.assertIn('type TableSpace < Unmovable;\n', anml_problem)
        self.assertIn('type Block < Movable;\n', anml_problem)
        self.assertIn('fluent boolean clear;\n', anml_problem)
        self.assertIn('fluent boolean on;\n', anml_problem)
        self.assertIn('action move(Movable item, Location l_from, Location l_to) {\n', anml_problem)
        self.assertIn('   [ start ] clear(item);\n', anml_problem)
        self.assertIn('   [ start ] clear(l_to);\n', anml_problem)
        self.assertIn('   [ start ] on(item, l_from);\n', anml_problem)
        self.assertIn('   [ start ] clear(l_from) := true;\n', anml_problem)
        self.assertIn('   [ start ] on(item, l_from) := false;\n', anml_problem)
        self.assertIn('   [ start ] clear(l_to) := false;\n', anml_problem)
        self.assertIn('[ start ] on(item, l_to) := true;\n', anml_problem)
        self.assertIn('}\n', anml_problem)
        self.assertIn('instance TableSpace ts_1, ts_2, ts_3;\n', anml_problem)
        self.assertIn('instance Block block_1, block_2, block_3;\n', anml_problem)
        self.assertIn('[ start ] clear(ts_2) := true;\n', anml_problem)
        self.assertIn('[ start ] clear(ts_3) := true;\n', anml_problem)
        self.assertIn('[ start ] clear(block_2) := true;\n', anml_problem)
        self.assertIn('[ start ] on(block_3, ts_1) := true;\n', anml_problem)
        self.assertIn('[ start ] on(block_1, block_3) := true;\n', anml_problem)
        self.assertIn('[ start ] on(block_2, block_1) := true;\n', anml_problem)
        self.assertIn('[ start ] clear(ts_1) := false;\n', anml_problem)
        self.assertIn('[ start ] clear(block_1) := false;\n', anml_problem)
        self.assertIn('[ start ] clear(block_3) := false;\n', anml_problem)
        self.assertIn('[ start ] on(block_1, ts_1) := false;\n', anml_problem)
        self.assertIn('[ start ] on(block_2, ts_1) := false;\n', anml_problem)
        self.assertIn('[ start ] on(block_1, ts_2) := false;\n', anml_problem)
        self.assertIn('[ start ] on(block_2, ts_2) := false;\n', anml_problem)
        self.assertIn('[ start ] on(block_3, ts_2) := false;\n', anml_problem)
        self.assertIn('[ start ] on(block_1, ts_3) := false;\n', anml_problem)
        self.assertIn('[ start ] on(block_2, ts_3) := false;\n', anml_problem)
        self.assertIn('[ start ] on(block_3, ts_3) := false;\n', anml_problem)
        self.assertIn('[ start ] on(block_1, block_1) := false;\n', anml_problem)
        self.assertIn('[ start ] on(block_3, block_1) := false;\n', anml_problem)
        self.assertIn('[ start ] on(block_1, block_2) := false;\n', anml_problem)
        self.assertIn('[ start ] on(block_2, block_2) := false;\n', anml_problem)
        self.assertIn('[ start ] on(block_3, block_2) := false;\n', anml_problem)
        self.assertIn('[ start ] on(block_2, block_3) := false;\n', anml_problem)
        self.assertIn('[ start ] on(block_3, block_3) := false;\n', anml_problem)
        self.assertIn('[ end ] on(block_1, ts_3);\n', anml_problem)
        self.assertIn('[ end ] on(block_2, block_1);\n', anml_problem)
        self.assertIn('[ end ] on(block_3, block_2);\n', anml_problem)
        self.assertEqual(anml_problem.count('\n'), 46)

    def test_timed_connected_locations(self):
        problem = self.problems['timed_connected_locations'].problem
        aw = ANMLWriter(problem)
        anml_problem = aw.get_problem()
        expected_result = '''type Location;
fluent boolean is_at;
constant boolean is_connected;
action move(Location l_from, Location l_to) {
   [ start, start ] is_at(l_from);
   [ start, start ] (not is_at(l_to));
   [ start, start ] (exists(Location mid_loc) { ((not ((mid_loc == l_from) or (mid_loc == l_to))) and (is_connected(l_from, mid_loc) or is_connected(mid_loc, l_from)) and (is_connected(l_to, mid_loc) or is_connected(mid_loc, l_to))) });
   [ start, end ] (exists(Location mid_loc) { ((not ((mid_loc == l_from) or (mid_loc == l_to))) and (is_connected(l_from, mid_loc) or is_connected(mid_loc, l_from)) and (is_connected(l_to, mid_loc) or is_connected(mid_loc, l_to))) });
   [ start + 1 ] is_at(l_from) := false;
   [ end + 5 ] is_at(l_to) := true;
}
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
'''
        self.assertEqual(anml_problem, expected_result)

    def test_matchcellar(self):
        problem = self.problems['matchcellar'].problem
        aw = ANMLWriter(problem)
        anml_problem = aw.get_problem()
        expected_result = '''type Match;
type Fuse;
fluent boolean handfree;
fluent boolean light;
fluent boolean match_used;
fluent boolean fuse_mended;
action light_match(Match m) {
   [ start, start ] (not match_used(m));
   [ start ] match_used(m) := true;
   [ start ] light := true;
   [ end ] light := false;
}
action mend_fuse(Fuse f) {
   [ start, start ] handfree;
   [ start, end ] light;
   [ start ] handfree := false;
   [ end ] fuse_mended(f) := true;
   [ end ] handfree := true;
}
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
'''
        self.assertEqual(anml_problem, expected_result)

    def test_robot_fluent_of_user_type(self):
        problem = self.problems['robot_fluent_of_user_type'].problem
        aw = ANMLWriter(problem)
        anml_problem = aw.get_problem()
        expected_result = '''type Location;
type Robot;
fluent Location is_at;
action move(Robot robot, Location l_from, Location l_to) {
   [ start ] (is_at(robot) == l_from);
   [ start ] (not (is_at(robot) == l_to));
   [ start ] is_at(robot) := l_to;
}
instance Location l1, l2;
instance Robot r1, r2;
[ start ] is_at(r1) := l2;
[ start ] is_at(r2) := l1;
[ end ] (is_at(r1) == l1);
[ end ] (is_at(r2) == l2);
'''
        self.assertEqual(anml_problem, expected_result)

    def test_robot(self):
        problem = self.problems['robot'].problem
        aw = ANMLWriter(problem)
        anml_problem = aw.get_problem()
        expected_result = '''type Location;
fluent boolean robot_at;
fluent rational[0, 100] battery_charge;
action move(Location l_from, Location l_to) {
   [ start ] (10 <= battery_charge);
   [ start ] (not (l_from == l_to));
   [ start ] robot_at(l_from);
   [ start ] (not robot_at(l_to));
   [ start ] robot_at(l_from) := false;
   [ start ] robot_at(l_to) := true;
   [ start ] battery_charge := (battery_charge - 10);
}
instance Location l1, l2;
[ start ] robot_at(l1) := true;
[ start ] robot_at(l2) := false;
[ start ] battery_charge := 100;
[ end ] robot_at(l2);
'''
        self.assertEqual(anml_problem, expected_result)

    def test_ad_hoc_1(self):
        when = UserType('when')
        fl = Fluent('action')
        obj = Object('predicate', when)
        act = InstantaneousAction('variable', fluent=when)
        fluent = act.parameter('fluent')
        act.add_effect(fl, True, Equals(fluent, obj))
        problem = Problem('ad_hoc')
        problem.add_fluent(fl)
        problem.add_action(act)
        problem.add_object(obj)
        problem.set_initial_value(fl, False)
        aw = ANMLWriter(problem)
        anml_problem = aw.get_problem()
        expected_result = '''type when_;
fluent boolean action_;
action variable_(when_ fluent_) {
   when [ start ] (fluent_ == predicate_)
   {[ start ] action_ := true;
   }
}
instance when_ predicate_;
[ start ] action_ := false;
'''
        self.assertEqual(anml_problem, expected_result)
