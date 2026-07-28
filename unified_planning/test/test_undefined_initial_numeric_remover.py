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

from unified_planning.shortcuts import *
from unified_planning.test import unittest_TestCase
from unified_planning.test.examples import get_example_problems


class TestUndefinedInitialNumericRemover(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_basic_undef_numeric(self):
        problem = self.problems["basic_undef_numeric"].problem

        with Compiler(
            compilation_kind="UNDEFINED_INITIAL_NUMERIC_REMOVING",
            problem_kind=problem.kind,
        ) as compiler:
            compilation_res = compiler.compile(problem)
            compiled_problem = compilation_res.problem
            assert isinstance(compiled_problem, Problem)

        self.assertEqual(len(compiled_problem._fluents_with_undefined_values()), 0)
        self.assertTrue(compiled_problem.has_fluent("is_value_defined_value"))

        o1 = compiled_problem.object("o1")
        o2 = compiled_problem.object("o2")
        is_value_defined_value = compiled_problem.fluent("is_value_defined_value")
        is_value_defined_value_o1 = compiled_problem.initial_value(
            is_value_defined_value(o1)
        )
        is_value_defined_value_o2 = compiled_problem.initial_value(
            is_value_defined_value(o2)
        )
        self.assertTrue(
            is_value_defined_value_o1 is not None
            and is_value_defined_value_o1.constant_value()
        )
        self.assertTrue(
            is_value_defined_value_o2 is not None
            and is_value_defined_value_o2.constant_value() == False
        )

        for action in compiled_problem.actions:
            assert isinstance(action, InstantaneousAction)
            if action.name == "increase_one":
                self.assertEqual(len(action.preconditions), 1)
            elif action.name == "increase_both":
                self.assertEqual(len(action.preconditions), 2)

        self.assertTrue(is_value_defined_value(o1) in compiled_problem.goals)

    def test_undef_numeric_with_timed_effects(self):
        problem = self.problems["undef_numeric_with_timed_effects"].problem
        with Compiler(
            compilation_kind="UNDEFINED_INITIAL_NUMERIC_REMOVING",
            problem_kind=problem.kind,
        ) as compiler:
            compilation_res = compiler.compile(problem)
            compiled_problem = compilation_res.problem
            assert isinstance(compiled_problem, Problem)

        self.assertEqual(len(compiled_problem._fluents_with_undefined_values()), 0)
        self.assertTrue(compiled_problem.has_fluent("is_value_defined_value"))

        o1 = compiled_problem.object("o1")
        o2 = compiled_problem.object("o2")
        is_value_defined_value = compiled_problem.fluent("is_value_defined_value")
        is_value_defined_value_o1 = compiled_problem.initial_value(
            is_value_defined_value(o1)
        )
        is_value_defined_value_o2 = compiled_problem.initial_value(
            is_value_defined_value(o2)
        )
        self.assertTrue(
            is_value_defined_value_o1 is not None
            and is_value_defined_value_o1.constant_value()
        )
        self.assertTrue(
            is_value_defined_value_o2 is not None
            and is_value_defined_value_o2.constant_value() == False
        )

        for action in compiled_problem.actions:
            if action.name == "increase_one":
                assert isinstance(action, DurativeAction)
                self.assertEqual(len(action.conditions), 1)
            elif action.name == "increase_both":
                assert isinstance(action, InstantaneousAction)
                self.assertEqual(len(action.preconditions), 2)

        self.assertTrue(is_value_defined_value(o1) in compiled_problem.goals)
        self.assertTrue(is_value_defined_value(o2) in compiled_problem.goals)

        timed_effect_fluent_exps = {
            e.fluent
            for effects in compiled_problem.timed_effects.values()
            for e in effects
        }
        self.assertTrue(is_value_defined_value(o2) in timed_effect_fluent_exps)

        timed_goals = {
            g for goals in compiled_problem.timed_goals.values() for g in goals
        }
        self.assertTrue(is_value_defined_value(o1) in timed_goals)
        self.assertTrue(is_value_defined_value(o2) in timed_goals)

    def test_interpreted_functions_undef_numeric(self):
        problem = self.problems["interpreted_functions_undef_numeric"].problem

        with Compiler(
            compilation_kind="UNDEFINED_INITIAL_NUMERIC_REMOVING",
            problem_kind=problem.kind,
        ) as compiler:
            compilation_res = compiler.compile(problem)
            compiled_problem = compilation_res.problem
            assert isinstance(compiled_problem, Problem)

        self.assertEqual(len(compiled_problem._fluents_with_undefined_values()), 0)
        self.assertTrue(compiled_problem.has_fluent("is_value_defined_undef_value"))

        undef_o1 = compiled_problem.object("undef_o1")
        undef_o2 = compiled_problem.object("undef_o2")
        is_value_defined_undef_value = compiled_problem.fluent(
            "is_value_defined_undef_value"
        )
        is_value_defined_undef_value_o1 = compiled_problem.initial_value(
            is_value_defined_undef_value(undef_o1)
        )
        is_value_defined_undef_value_o2 = compiled_problem.initial_value(
            is_value_defined_undef_value(undef_o2)
        )
        self.assertTrue(
            is_value_defined_undef_value_o1 is not None
            and is_value_defined_undef_value_o1.constant_value()
        )
        self.assertTrue(
            is_value_defined_undef_value_o2 is not None
            and is_value_defined_undef_value_o2.constant_value() == False
        )

        for action in compiled_problem.actions:
            assert isinstance(action, InstantaneousAction)
            if action.name == "use_value":
                # the interpreted-function precondition plus the tracker it reads
                self.assertEqual(len(action.preconditions), 2)
                self.assertEqual(len(action.effects), 1)
            elif action.name == "set_value":
                # only undef_o1 is read (inside the interpreted function); the
                # assigned undef_value(o) gets its own tracker effect
                self.assertEqual(len(action.preconditions), 1)
                self.assertEqual(len(action.effects), 2)
            elif action.name == "use_chosen":
                # the tracker is instantiated on the interpreted-function argument
                self.assertEqual(len(action.preconditions), 2)
                self.assertEqual(len(action.effects), 1)
                tracker_preconditions = [
                    p
                    for p in action.preconditions
                    if p.is_fluent_exp() and p.fluent() == is_value_defined_undef_value
                ]
                self.assertEqual(len(tracker_preconditions), 1)
                (arg,) = tracker_preconditions[0].args
                self.assertTrue(arg.is_interpreted_function_exp())

    def test_interpreted_functions_undef_numeric_durative(self):
        problem = self.problems["interpreted_functions_undef_numeric_durative"].problem

        with Compiler(
            compilation_kind="UNDEFINED_INITIAL_NUMERIC_REMOVING",
            problem_kind=problem.kind,
        ) as compiler:
            compilation_res = compiler.compile(problem)
            compiled_problem = compilation_res.problem
            assert isinstance(compiled_problem, Problem)

        self.assertEqual(len(compiled_problem._fluents_with_undefined_values()), 0)
        self.assertTrue(
            compiled_problem.has_fluent("is_value_defined_undef_durative_value")
        )

        undef_o1 = compiled_problem.object("undef_o1")
        undef_o2 = compiled_problem.object("undef_o2")
        is_value_defined = compiled_problem.fluent(
            "is_value_defined_undef_durative_value"
        )
        is_value_defined_o1 = compiled_problem.initial_value(is_value_defined(undef_o1))
        is_value_defined_o2 = compiled_problem.initial_value(is_value_defined(undef_o2))
        self.assertTrue(
            is_value_defined_o1 is not None and is_value_defined_o1.constant_value()
        )
        self.assertTrue(
            is_value_defined_o2 is not None
            and is_value_defined_o2.constant_value() == False
        )

        undef_move = compiled_problem.action("undef_move")
        assert isinstance(undef_move, DurativeAction)
        # the duration is not rewritten, only conditions/effects are augmented
        self.assertEqual(undef_move.duration.lower, undef_move.duration.upper)
        self.assertTrue(undef_move.duration.lower.is_interpreted_function_exp())
        self.assertEqual(len(undef_move.conditions), 1)
        (conditions,) = undef_move.conditions.values()
        # the original interpreted-function condition plus the tracker it reads
        self.assertEqual(len(conditions), 2)
        self.assertIn(is_value_defined(undef_move.o), conditions)
