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
# limitations under the License

import os
from typing import cast
import warnings
import unified_planning
from unified_planning.model.contingent import ContingentProblem, SensingAction
from unified_planning.shortcuts import *
from unified_planning.test import unittest_TestCase, main
from unified_planning.io import PDDLReader, PDDLWriter
from unified_planning.test.examples import get_example_problems


FILE_PATH = os.path.dirname(os.path.abspath(__file__))
CONTINGENT_PDDL_DOMAINS_PATH = os.path.join(FILE_PATH, "contingent_pddl")


class TestPddlIO(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_logistic_conf_reader(self):
        reader = PDDLReader(disable_warnings=True)

        domain_filename = os.path.join(
            CONTINGENT_PDDL_DOMAINS_PATH, "logistic_conf", "domain.pddl"
        )
        problem_filename = os.path.join(
            CONTINGENT_PDDL_DOMAINS_PATH, "logistic_conf", "problem.pddl"
        )
        problem = reader.parse_problem(domain_filename, problem_filename)

        self.assertTrue(problem is not None)
        self.assertTrue(isinstance(problem, up.model.contingent.ContingentProblem))
        self.assertEqual(len(problem.fluents), 10)
        sensing_actions = [sa for sa in problem.sensing_actions]
        self.assertEqual(len(sensing_actions), 3)
        self.assertEqual(len(problem.actions), 12)

        for sa in sensing_actions:
            self.assertTrue(isinstance(sa, up.model.contingent.SensingAction))
            self.assertEqual(len(sa.parameters), 3)
            self.assertEqual(len(sa.preconditions), 1)
            self.assertEqual(len(sa.observed_fluents), 1)

    def test_colorballs_reader(self):
        reader = PDDLReader(disable_warnings=True)

        domain_filename = os.path.join(
            CONTINGENT_PDDL_DOMAINS_PATH, "colorballs", "domain.pddl"
        )
        problem_filename = os.path.join(
            CONTINGENT_PDDL_DOMAINS_PATH, "colorballs", "problem.pddl"
        )
        problem = reader.parse_problem(domain_filename, problem_filename)

        self.assertTrue(problem is not None)
        self.assertTrue(isinstance(problem, up.model.contingent.ContingentProblem))
        self.assertEqual(len(problem.fluents), 8)
        sensing_actions = [sa for sa in problem.sensing_actions]
        self.assertEqual(len(sensing_actions), 2)
        self.assertEqual(len(problem.actions), 5)

        for sa in sensing_actions:
            self.assertTrue(isinstance(sa, up.model.contingent.SensingAction))
            self.assertEqual(len(sa.parameters), 2)
            self.assertEqual(len(sa.preconditions), 1)
            self.assertEqual(len(sa.observed_fluents), 1)

    def _make_minimal_contingent_problem(self):
        BlockType = UserType("block")
        clear = Fluent("clear", BoolType(), b=BlockType)
        on = Fluent("on", BoolType(), b1=BlockType, b2=BlockType)
        sense_clear = SensingAction("sense_clear", b=BlockType)
        sense_clear.add_observed_fluent(clear(sense_clear.parameter("b")))
        b1 = Object("b1", BlockType)
        b2 = Object("b2", BlockType)
        prob = ContingentProblem("test_contingent")
        prob.add_fluent(clear, default_initial_value=False)
        prob.add_fluent(on, default_initial_value=False)
        prob.add_action(sense_clear)
        prob.add_object(b1)
        prob.add_object(b2)
        prob.add_oneof_initial_constraint([clear(b1), clear(b2)])
        prob.set_initial_value(on(b1, b2), True)
        prob.add_goal(on(b2, b1))
        return prob

    def test_contingent_writer_requirements(self):
        prob = self._make_minimal_contingent_problem()
        w = PDDLWriter(prob)
        domain = _normalized_pddl_str(w.get_domain())
        self.assertIn(":contingent", domain)

        # A regular problem must NOT have :contingent
        regular = Problem("regular")
        f = Fluent("f")
        regular.add_fluent(f, default_initial_value=False)
        regular.add_goal(f)
        w2 = PDDLWriter(regular)
        domain2 = _normalized_pddl_str(w2.get_domain())
        self.assertNotIn(":contingent", domain2)

    def test_contingent_writer_sensing_action_single_observe(self):
        BlockType = UserType("block")
        clear = Fluent("clear", BoolType(), b=BlockType)
        sense = SensingAction("sense_clear", b=BlockType)
        sense.add_observed_fluent(clear(sense.parameter("b")))
        b1 = Object("b1", BlockType)
        prob = ContingentProblem("p")
        prob.add_fluent(clear, default_initial_value=False)
        prob.add_action(sense)
        prob.add_object(b1)
        prob.add_goal(clear(b1))
        w = PDDLWriter(prob)
        domain = _normalized_pddl_str(w.get_domain())
        self.assertIn(":observe (clear ?b)", domain)
        # With a single observed fluent there must be no wrapping `and`
        self.assertNotIn(":observe (and", domain)

    def test_contingent_writer_sensing_action_multiple_observe(self):
        BlockType = UserType("block")
        clear = Fluent("clear", BoolType(), b=BlockType)
        on_table = Fluent("on_table", BoolType(), b=BlockType)
        sense = SensingAction("sense_both", b=BlockType)
        sense.add_observed_fluent(clear(sense.parameter("b")))
        sense.add_observed_fluent(on_table(sense.parameter("b")))
        b1 = Object("b1", BlockType)
        prob = ContingentProblem("p")
        prob.add_fluent(clear, default_initial_value=False)
        prob.add_fluent(on_table, default_initial_value=False)
        prob.add_action(sense)
        prob.add_object(b1)
        prob.add_goal(clear(b1))
        w = PDDLWriter(prob)
        domain = _normalized_pddl_str(w.get_domain())
        self.assertIn(":observe (and", domain)

    def test_contingent_writer_sensing_action_no_observe_warns(self):
        BlockType = UserType("block")
        clear = Fluent("clear", BoolType(), b=BlockType)
        sense = SensingAction("sense_empty", b=BlockType)  # no observed fluents
        b1 = Object("b1", BlockType)
        prob = ContingentProblem("p")
        prob.add_fluent(clear, default_initial_value=False)
        prob.add_action(sense)
        prob.add_object(b1)
        prob.add_goal(clear(b1))
        w = PDDLWriter(prob)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _ = w.get_domain()
        self.assertTrue(
            any("skipping :observe" in str(warning.message) for warning in caught),
            "Expected a warning about skipping :observe for empty SensingAction",
        )

    def test_contingent_writer_regular_action_no_observe(self):
        prob = self._make_minimal_contingent_problem()
        move = InstantaneousAction("move")
        prob.add_action(move)
        w = PDDLWriter(prob)
        domain = w.get_domain()
        # Find the block for "move" action and ensure no :observe after it
        move_idx = domain.find("(:action move")
        self.assertNotEqual(move_idx, -1)
        # The next action/end-of-domain after "move"
        next_action_idx = domain.find("(:action", move_idx + 1)
        if next_action_idx == -1:
            move_block = domain[move_idx:]
        else:
            move_block = domain[move_idx:next_action_idx]
        self.assertNotIn(":observe", move_block)

    def test_contingent_writer_unknown_in_init(self):
        BlockType = UserType("block")
        clear = Fluent("clear", BoolType(), b=BlockType)
        b1 = Object("b1", BlockType)
        prob = ContingentProblem("p")
        prob.add_fluent(clear, default_initial_value=False)
        prob.add_object(b1)
        prob.add_unknown_initial_constraint(clear(b1))
        prob.add_goal(clear(b1))
        w = PDDLWriter(prob)
        problem_str = _normalized_pddl_str(w.get_problem())
        self.assertIn("(unknown (clear b1))", problem_str)

    def test_contingent_writer_oneof_in_init(self):
        BlockType = UserType("block")
        clear = Fluent("clear", BoolType(), b=BlockType)
        b1 = Object("b1", BlockType)
        b2 = Object("b2", BlockType)
        prob = ContingentProblem("p")
        prob.add_fluent(clear, default_initial_value=False)
        prob.add_object(b1)
        prob.add_object(b2)
        prob.add_oneof_initial_constraint([clear(b1), clear(b2)])
        prob.add_goal(clear(b1))
        w = PDDLWriter(prob)
        problem_str = _normalized_pddl_str(w.get_problem())
        self.assertIn("(oneof", problem_str)
        self.assertIn("(clear b1)", problem_str)
        self.assertIn("(clear b2)", problem_str)

    def test_contingent_writer_or_in_init(self):
        BlockType = UserType("block")
        clear = Fluent("clear", BoolType(), b=BlockType)
        b1 = Object("b1", BlockType)
        b2 = Object("b2", BlockType)
        prob = ContingentProblem("p")
        prob.add_fluent(clear, default_initial_value=False)
        prob.add_object(b1)
        prob.add_object(b2)
        prob.add_or_initial_constraint([clear(b1), clear(b2)])
        prob.add_goal(clear(b1))
        w = PDDLWriter(prob)
        problem_str = _normalized_pddl_str(w.get_problem())
        self.assertIn("(or (clear b1) (clear b2))", problem_str)

    def test_contingent_writer_multiple_constraints_in_init(self):
        BlockType = UserType("block")
        clear = Fluent("clear", BoolType(), b=BlockType)
        on_table = Fluent("on_table", BoolType(), b=BlockType)
        b1 = Object("b1", BlockType)
        b2 = Object("b2", BlockType)
        prob = ContingentProblem("p")
        prob.add_fluent(clear, default_initial_value=False)
        prob.add_fluent(on_table, default_initial_value=False)
        prob.add_object(b1)
        prob.add_object(b2)
        prob.add_oneof_initial_constraint([clear(b1), clear(b2)])
        prob.add_or_initial_constraint([on_table(b1), on_table(b2)])
        prob.add_unknown_initial_constraint(clear(b1))
        prob.add_goal(clear(b2))
        w = PDDLWriter(prob)
        problem_str = _normalized_pddl_str(w.get_problem())
        self.assertIn("(oneof", problem_str)
        self.assertIn("(or", problem_str)
        self.assertIn("(unknown", problem_str)

    def test_contingent_writer_no_constraints_for_regular_problem(self):
        regular = Problem("regular")
        f = Fluent("f")
        regular.add_fluent(f, default_initial_value=True)
        regular.add_goal(f)
        w = PDDLWriter(regular)
        problem_str = _normalized_pddl_str(w.get_problem())
        self.assertNotIn("unknown", problem_str)
        self.assertNotIn("oneof", problem_str)
        # "(or " would only appear as a contingent constraint; goals use "(and ...)"
        self.assertNotIn("(or ", problem_str)

    def test_contingent_writer_keyword_mangling(self):
        BlockType = UserType("block")
        # Fluents named after contingent reserved words
        observe_fluent = Fluent("observe", BoolType(), b=BlockType)
        oneof_fluent = Fluent("oneof", BoolType(), b=BlockType)
        # Object named after a reserved word
        unknown_obj = Object("unknown", BlockType)
        sense = SensingAction("sense", b=BlockType)
        sense.add_observed_fluent(observe_fluent(sense.parameter("b")))
        prob = ContingentProblem("p")
        prob.add_fluent(observe_fluent, default_initial_value=False)
        prob.add_fluent(oneof_fluent, default_initial_value=False)
        prob.add_action(sense)
        prob.add_object(unknown_obj)
        prob.add_goal(observe_fluent(unknown_obj))
        w = PDDLWriter(prob)
        domain = w.get_domain()
        problem = w.get_problem()
        # The reserved words must be mangled (appended with '_')
        self.assertNotIn("(observe ", domain)  # as a predicate definition
        self.assertIn("observe_", domain)
        self.assertIn("oneof_", domain)
        self.assertIn("unknown_", problem)

    def test_contingent_roundtrip_minimal(self):
        prob = self._make_minimal_contingent_problem()
        w = PDDLWriter(prob)
        domain_str = w.get_domain()
        problem_str = w.get_problem()

        reader = PDDLReader()
        parsed = reader.parse_problem_string(domain_str, problem_str)

        self.assertIsInstance(parsed, ContingentProblem)
        parsed = cast(ContingentProblem, parsed)

        # PDDL writer adds "-problem" suffix to problem name, but otherwise should be identical
        self.assertEqual(parsed.name, prob.name + "-problem")

        parsed.name = prob.name  # ignore name for equality
        self.assertEqual(prob, parsed)

    def _assert_contingent_pddl_roundtrip(self, domain_subdir: str) -> None:
        """Read a contingent problem from PDDL, write it back, re-read it, and
        assert full structural equivalence between original and reread."""
        domain_file = os.path.join(
            CONTINGENT_PDDL_DOMAINS_PATH, domain_subdir, "domain.pddl"
        )
        problem_file = os.path.join(
            CONTINGENT_PDDL_DOMAINS_PATH, domain_subdir, "problem.pddl"
        )
        reader = PDDLReader()
        original = reader.parse_problem(domain_file, problem_file)

        w = PDDLWriter(original)
        reread = reader.parse_problem_string(w.get_domain(), w.get_problem())

        self.assertIsInstance(reread, ContingentProblem)
        reread = cast(ContingentProblem, reread)
        original = cast(ContingentProblem, original)

        # Top-level element counts
        self.assertEqual(len(original.actions), len(reread.actions))
        self.assertEqual(len(original.fluents), len(reread.fluents))
        self.assertEqual(len(original.user_types), len(reread.user_types))
        self.assertEqual(len(list(original.all_objects)), len(list(reread.all_objects)))
        self.assertEqual(len(original.goals), len(reread.goals))

        # Per-action structure (use the writer's reverse-rename map to compare original → reread)
        for reread_action in reread.actions:
            reread_action = cast(InstantaneousAction, reread_action)
            orig_action = cast(
                InstantaneousAction, w.get_item_named(reread_action.name)
            )
            self.assertIn(orig_action, original.actions)
            self.assertEqual(len(reread_action.parameters), len(orig_action.parameters))
            self.assertEqual(
                len(reread_action.preconditions), len(orig_action.preconditions)
            )
            self.assertEqual(len(reread_action.effects), len(orig_action.effects))
            if isinstance(reread_action, SensingAction):
                self.assertIsInstance(orig_action, SensingAction)
                self.assertEqual(
                    len(reread_action.observed_fluents),
                    len(cast(SensingAction, orig_action).observed_fluents),
                )

        # Contingent-specific: hidden fluents and oneof/or constraints
        self.assertEqual(len(original.hidden_fluents), len(reread.hidden_fluents))
        self.assertEqual(
            sorted(len(c) for c in original.oneof_constraints),
            sorted(len(c) for c in reread.oneof_constraints),
        )
        self.assertEqual(
            sorted(len(c) for c in original.or_constraints),
            sorted(len(c) for c in reread.or_constraints),
        )

    def test_contingent_colorballs_read_write_read_roundtrip(self):
        self._assert_contingent_pddl_roundtrip("colorballs")

    def test_contingent_logistic_conf_read_write_read_roundtrip(self):
        self._assert_contingent_pddl_roundtrip("logistic_conf")


def _normalized_pddl_str(w):
    return " ".join(w.split()).replace("( ", "(").replace(" )", ")")
