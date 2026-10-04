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

from unified_planning.shortcuts import *
from unified_planning.exceptions import (
    UPUnboundedVariablesError,
    UPProblemDefinitionError,
    UPTypeError,
)
from unified_planning.io import PDDLWriter
from unified_planning.plans import ActionInstance
from unified_planning.engines.compilers import IntParametersAndVariablesRemover
from unified_planning.test import unittest_TestCase


class TestIntVariable(unittest_TestCase):
    def setUp(self):
        super().setUp()
        self.i = IntVariable("i", 0, 2)
        self.marked = Fluent("marked", index=IntType(0, 2))
        self.oracle = self.i.environment.free_vars_oracle

    def test_free_variables_and_scope(self):
        location = UserType("location")
        site = Variable("site", location)
        at = Fluent("at", site=location, index=IntType(0, 2))
        body = at(site, self.i)
        self.assertEqual(self.oracle.get_free_variables(body), {site, self.i})
        for quantifier in (Forall, Exists):
            with self.subTest(quantifier=quantifier.__name__):
                quantified = quantifier(body, self.i)
                self.assertEqual(self.oracle.get_free_variables(quantified), {site})
                self.assertEqual(
                    self.oracle.get_free_variables(quantifier(quantified, site)), set()
                )
                self.assertEqual(
                    self.oracle.get_free_variables(And(quantified, body)),
                    {site, self.i},
                )

    def test_pddl_requires_integer_variable_compilation(self):
        for context in ("forall", "exists", "effect"):
            with self.subTest(context=context):
                p = Problem("integer_quantifier")
                done = Fluent("done")
                p.add_fluent(done, default_initial_value=False)
                action = InstantaneousAction("finish")
                if context == "effect":
                    action.add_effect(done, True, self.i >= 0, forall=(self.i,))
                else:
                    quantifier = Forall if context == "forall" else Exists
                    action.add_precondition(quantifier(self.i >= 0, self.i))
                    action.add_effect(done, True)
                p.add_action(action)
                p.add_goal(done)
                with self.assertRaisesRegex(UPTypeError, "Compile integer variables"):
                    PDDLWriter(p).get_domain()
                compiled = IntParametersAndVariablesRemover().compile(p).problem
                assert isinstance(compiled, Problem)
                self.assertIn("(:action finish", PDDLWriter(compiled).get_domain())
                self.assertIn("(:goal", PDDLWriter(compiled).get_problem())

    def test_substitution_respects_integer_quantifiers(self):
        for quantifier in (Forall, Exists):
            with self.subTest(quantifier=quantifier.__name__):
                bound = quantifier(self.marked(self.i), self.i)
                expression = And(self.marked(self.i), bound)
                self.assertEqual(
                    expression.substitute({self.i: 1}), And(self.marked(1), bound)
                )

    def test_unused_integer_variables_are_removed(self):
        body = self.marked(0)
        for last in (0, 2):
            i = IntVariable("i", 1, last)
            for quantifier in (Forall, Exists):
                with self.subTest(last=last, quantifier=quantifier.__name__):
                    self.assertEqual(quantifier(body, i).simplify(), body)
                    self.assertEqual(
                        quantifier(self.marked(self.i), i, self.i).simplify(),
                        quantifier(self.marked(self.i), self.i),
                    )

        # The inner range depends on an outer variable absent from the body.
        j = IntVariable("j", 1, self.i + 0)
        self.assertEqual(Forall(Exists(body, j), self.i).simplify(), body)

    def test_effect_variables_and_unbound_uses(self):
        action = InstantaneousAction("mark")
        with self.assertRaises(UPUnboundedVariablesError):
            action.add_precondition(self.marked(self.i))
        with self.assertRaises(UPUnboundedVariablesError):
            action.add_effect(self.marked(self.i), True)
        j = IntVariable("j", 0, self.i + 0)
        action.add_effect(self.marked(self.i), True, forall=(self.i, self.i))
        self.assertEqual(action.effects[0].forall, (self.i,))

        # Unused variables are removed, including empty and dependent ranges.
        empty = IntVariable("empty", 1, 0)
        action = InstantaneousAction("mark")
        action.add_effect(self.marked(0), True, forall=(empty, empty, j))
        self.assertEqual(action.effects[0].forall, ())

    def test_dependent_variables_in_same_quantifier(self):
        pair = Fluent("pair", x=IntType(0, 2), y=IntType(0, 2))
        j = IntVariable("j", 1, self.i + 0)
        expected = [pair(1, 1), pair(2, 1), pair(2, 2)]
        compiler = IntParametersAndVariablesRemover()
        for quantifier, combine in ((Forall, And), (Exists, Or)):
            for variables in ((self.i, j), (j, self.i)):
                with self.subTest(quantifier=quantifier.__name__, variables=variables):
                    p = Problem("dependent_quantifier")
                    p.add_fluent(pair, default_initial_value=False)
                    p.add_goal(quantifier(pair(self.i, j), *variables).simplify())
                    compiled = compiler.compile(p).problem
                    assert isinstance(compiled, Problem)
                    self.assertEqual(compiled.goals, [combine(expected)])
                    p.clear_goals()
                    p.add_goal(quantifier(quantifier(pair(self.i, j), j), self.i))
                    nested = compiler.compile(p).problem
                    assert isinstance(nested, Problem)
                    self.assertEqual(nested.goals, compiled.goals)

        k = IntVariable("k", 1, j + 0)
        triple = Fluent("triple", x=IntType(0, 2), y=IntType(0, 2), z=IntType(0, 2))
        p = Problem("three_dependent_variables")
        p.add_fluent(triple, default_initial_value=False)
        p.add_goal(Exists(triple(self.i, j, k), k, j, self.i))
        compiled = compiler.compile(p).problem
        assert isinstance(compiled, Problem)
        self.assertEqual(
            compiled.goals,
            [Or(triple(1, 1, 1), triple(2, 1, 1), triple(2, 2, 1), triple(2, 2, 2))],
        )

    def test_dependent_forall_effects_with_action_parameter(self):
        pair = Fluent("pair", x=IntType(0, 2), y=IntType(0, 2))
        for action_type in (InstantaneousAction, DurativeAction):
            with self.subTest(action_type=action_type.__name__):
                p = Problem("dependent_effect")
                p.add_fluent(pair, default_initial_value=False)
                action = action_type("mark", n=IntType(0, 2))
                n = action.parameter("n")
                i = IntVariable("i", 1, n)
                j = IntVariable("j", i + 0, n)
                if isinstance(action, DurativeAction):
                    action.set_fixed_duration(1)
                    action.add_effect(StartTiming(), pair(i, j), True, forall=(j, i))
                else:
                    action.add_effect(pair(i, j), True, forall=(j, i))
                p.add_action(action)
                result = IntParametersAndVariablesRemover().compile(p)
                assert isinstance(result.problem, Problem)
                assert result.map_back_action_instance is not None
                self.assertEqual(len(result.problem.actions), 3)
                for compiled in result.problem.actions:
                    assert isinstance(compiled, (InstantaneousAction, DurativeAction))
                    original = result.map_back_action_instance(ActionInstance(compiled))
                    assert original is not None
                    n_value = original.actual_parameters[0].int_constant_value()
                    effects = (
                        compiled.effects.get(StartTiming(), [])
                        if isinstance(compiled, DurativeAction)
                        else compiled.effects
                    )
                    self.assertEqual(
                        {e.fluent for e in effects},
                        {
                            pair(x, y)
                            for x in range(1, n_value + 1)
                            for y in range(x, n_value + 1)
                        },
                    )
                    self.assertTrue(all(not e.forall for e in effects))

    def test_empty_dependent_quantifier(self):
        i = IntVariable("i", 0, 0)
        j = IntVariable("j", 1, i + 0)
        pair = Fluent("pair", x=IntType(0, 2), y=IntType(0, 2))
        for quantifier in (Forall, Exists):
            with self.subTest(quantifier=quantifier.__name__):
                p = Problem("empty_dependent_range")
                p.add_goal(quantifier(pair(i, j), j, i).simplify())
                p.add_fluent(pair, default_initial_value=False)
                compiled = IntParametersAndVariablesRemover().compile(p).problem
                assert isinstance(compiled, Problem)
                self.assertEqual(
                    compiled.goals, [] if quantifier is Forall else [Bool(False)]
                )

    def test_unbound_and_circular_range_dependencies(self):
        compiler = IntParametersAndVariablesRemover()
        j = IntVariable("j", 1, self.i + 0)
        p = Problem("unbound_range")
        p.add_fluent(self.marked, default_initial_value=False)
        for quantifier in (Forall, Exists):
            goals = (
                quantifier(self.marked(j), j),
                quantifier(self.marked(j), j, self.i),
                quantifier(quantifier(self.marked(j), j), self.i),
            )
            for goal in goals:
                for simplify in (False, True):
                    with self.subTest(goal=goal, simplify=simplify):
                        p.clear_goals()
                        p.add_goal(goal.simplify() if simplify else goal)
                        with self.assertRaisesRegex(
                            UPProblemDefinitionError, "not been instantiated: i"
                        ):
                            compiler.compile(p)
        p.clear_goals()
        action = InstantaneousAction("mark")
        action.add_effect(self.marked(j), True, forall=(j, self.i))
        self.assertEqual(action.effects[0].forall, (j,))
        p.add_action(action)
        with self.assertRaisesRegex(
            UPProblemDefinitionError, "not been instantiated: i"
        ):
            compiler.compile(p)

        # Exercise cycle detection without mutating the variables' identities.
        ranges = {self.i: (Int(0), j + 0), j: (Int(0), self.i + 0)}
        with self.assertRaisesRegex(UPProblemDefinitionError, "Circular dependencies"):
            list(compiler._get_int_var_instantiations(p, p, ranges, {}, ()))
