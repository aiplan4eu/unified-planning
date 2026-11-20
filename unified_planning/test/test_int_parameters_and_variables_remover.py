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

from collections import OrderedDict
from itertools import product
from unified_planning.plans import Plan

from unified_planning.shortcuts import *
from unified_planning.environment import Environment
from unified_planning.exceptions import UPProblemDefinitionError
from unified_planning.engines.compilers import IntParametersAndVariablesRemover
from unified_planning.engines.plan_validator import (
    SequentialPlanValidator,
    TimeTriggeredPlanValidator,
)
from unified_planning.engines.results import ValidationResultStatus as Status
from unified_planning.plans import ActionInstance, SequentialPlan, TimeTriggeredPlan
from unified_planning.test import unittest_TestCase


class TestIntParametersAndVariablesRemover(unittest_TestCase):
    def setUp(self):
        super().setUp()
        self.problem = Problem("ipavr")
        self.compiler = IntParametersAndVariablesRemover()
        self.marked = Fluent("marked", index=IntType(0, 2))
        self.cell = Fluent("cell", index=IntType(1, 2))
        self.enabled, self.done = Fluent("enabled"), Fluent("done")
        for fluent in (self.marked, self.cell, self.enabled, self.done):
            self.problem.add_fluent(fluent, default_initial_value=False)

    def compile_action(self, action, mode="pddl"):
        self.problem.clear_actions()
        self.problem.add_action(action)
        if mode == "pddl":
            return self.compiler.compile(self.problem)
        return IntParametersAndVariablesRemover(mode).compile(self.problem)

    def integer_instances(self, result):
        return {
            result.map_back_action_instance(ActionInstance(a)).actual_parameters: a
            for a in result.problem.actions
        }

    def test_parameter_order_and_retained_types(self):
        location = UserType("location")
        home = Object("home", location)
        self.problem.add_object(home)
        action = InstantaneousAction(
            "finish",
            n=IntType(1, 2),
            site=location,
            flag=BoolType(),
            m=IntType(3, 4),
            ratio=RealType(),
        )
        result = self.compile_action(action)
        combinations = set()
        for compiled in result.problem.actions:
            instance = ActionInstance(compiled, (home, True, Fraction(3, 2)))
            lifted = result.map_back_action_instance(instance)
            n, site, flag, m, ratio = lifted.actual_parameters
            self.assertIs(lifted.action, action)
            self.assertEqual(
                (site.object(), flag.bool_constant_value(), ratio.constant_value()),
                (home, True, Fraction(3, 2)),
            )
            combinations.add((n.constant_value(), m.constant_value()))
        self.assertEqual(combinations, {(1, 3), (1, 4), (2, 3), (2, 4)})

    def test_parameter_dependent_quantifiers_and_effects(self):
        for quantifier, combine in [(Forall, And), (Exists, Or)]:
            with self.subTest(quantifier=quantifier.__name__):
                action = InstantaneousAction("mark", n=IntType(0, 2))
                i = Variable(
                    "i", IntType(), lower_bound=1, upper_bound=action.parameter("n")
                )
                action.add_precondition(quantifier(self.marked(i), i))
                action.add_effect(self.marked(i), True, forall=(i,))
                result = self.compile_action(action)
                self.assertTrue(self.problem.kind.has_int_variables_in_conditions())
                self.assertTrue(self.problem.kind.has_int_variables_in_effects())
                actions = self.integer_instances(result)
                self.assertEqual(
                    set(actions),
                    {
                        (Int(n),)
                        for n in (range(3) if quantifier is Forall else range(1, 3))
                    },
                )
                for (n,), compiled in actions.items():
                    marks = [self.marked(j) for j in range(1, n.constant_value() + 1)]
                    expected = combine(marks).simplify()
                    self.assertEqual(
                        compiled.preconditions, [] if expected.is_true() else [expected]
                    )
                    self.assertEqual({e.fluent for e in compiled.effects}, set(marks))
                    self.assertTrue(all(not e.forall for e in compiled.effects))
                self.assertFalse(result.problem.kind.has_int_variables_in_conditions())
                self.assertFalse(result.problem.kind.has_int_variables_in_effects())

    def test_nested_ranges_and_variable_scope(self):
        i = Variable("i", IntType(1, 2))
        j = Variable("j", IntType(), lower_bound=1, upper_bound=i + 0)
        self.problem.add_goal(Forall(Forall(And(self.marked(i), self.marked(j)), j), i))
        action = InstantaneousAction("mark", i=IntType(0, 0))
        action.add_precondition(
            Forall(And(self.marked(i), self.marked(action.parameter("i"))), i)
        )
        compiled = self.compile_action(action).problem
        self.assertEqual(compiled.goals, [And(self.marked(1), self.marked(2))])
        expected = And(self.marked(1), self.marked(0), self.marked(2))
        self.assertEqual(compiled.actions[0].preconditions, [expected])

    def test_nonconstant_range_is_rejected(self):
        for i, message in (
            (Variable("i", IntType()), "finite bounds for integer variable i"),
            (
                Variable("i", IntType(), lower_bound=0),
                "finite bounds for integer variable i",
            ),
            (
                Variable("i", IntType(), upper_bound=2),
                "finite bounds for integer variable i",
            ),
        ):
            with self.subTest(variable=i):
                self.problem.clear_goals()
                self.problem.add_goal(Forall(self.marked(i), i))
                with self.assertRaisesRegex(UPProblemDefinitionError, message):
                    self.compiler.compile(self.problem)

    def test_type_and_variable_bounds_are_intersected(self):
        for i, values in (
            (Variable("i", IntType(0, 2)), (0, 1, 2)),
            (Variable("i", IntType(), lower_bound=0, upper_bound=2), (0, 1, 2)),
            (Variable("i", IntType(1, 2), lower_bound=0, upper_bound=3), (1, 2)),
            (Variable("i", IntType(0, 2), upper_bound=1), (0, 1)),
            (Variable("i", IntType(0, 2), lower_bound=1), (1, 2)),
            (Variable("i", IntType(0, None), upper_bound=2), (0, 1, 2)),
            (Variable("i", IntType(None, 2), lower_bound=0), (0, 1, 2)),
            (Variable("i", IntType(0, 2), lower_bound=3), ()),
        ):
            for quantifier, combine in ((Forall, And), (Exists, Or)):
                with self.subTest(variable=i, quantifier=quantifier.__name__):
                    self.problem.clear_goals()
                    self.problem.add_goal(quantifier(self.marked(i), i))
                    action = InstantaneousAction("mark")
                    action.add_effect(self.marked(i), True, forall=(i,))
                    compiled = self.compile_action(action).problem
                    assert isinstance(compiled, Problem)
                    assert isinstance(compiled.actions[0], InstantaneousAction)
                    expected = combine(
                        *(self.marked(value) for value in values)
                    ).simplify()
                    self.assertEqual(
                        compiled.goals, [] if expected.is_true() else [expected]
                    )
                    self.assertEqual(
                        {effect.fluent for effect in compiled.actions[0].effects},
                        {self.marked(value) for value in values},
                    )

    def test_mixed_quantifiers_in_custom_environment(self):
        env = Environment()
        em, tm = env.expression_manager, env.type_manager
        location = tm.UserType("location")
        p = Problem("custom", environment=env)
        marked = Fluent(
            "marked",
            tm.BoolType(),
            _signature=OrderedDict(site=location, index=tm.IntType(1, 2)),
            environment=env,
        )
        p.add_fluent(marked, default_initial_value=False)
        p.add_object(Object("home", location, env))
        site, i = (
            Variable("site", location, env),
            Variable("i", env.type_manager.IntType(1, 2), env),
        )
        for quantifier, combine in [(em.Forall, em.And), (em.Exists, em.Or)]:
            with self.subTest(quantifier=quantifier.__name__):
                p.clear_goals()
                p.add_goal(quantifier(marked(site, i), site, i).simplify())
                self.assertTrue(p.kind.has_int_variables_in_conditions())
                self.assertFalse(p.kind.has_int_variables_in_effects())
                compiled = self.compiler.compile(p).problem
                assert isinstance(compiled, Problem)
                self.assertEqual(
                    compiled.goals,
                    [quantifier(combine(marked(site, 1), marked(site, 2)), site)],
                )
                self.assertIs(compiled.environment, env)
                self.assertFalse(compiled.kind.has_int_variables_in_conditions())
                self.assertFalse(compiled.kind.has_int_variables_in_effects())

    def test_empty_object_domains(self):
        robot_type = UserType("robot")
        robot = Variable("robot", robot_type)
        available = Fluent("available", robot=robot_type)
        self.problem.add_fluent(available, default_initial_value=True)
        i = Variable("i", IntType(0, 1))
        body = And(available(robot), self.cell(i))
        for quantifier in (Forall, Exists):
            goals = [
                quantifier(body, robot, i),
                quantifier(quantifier(body, i), robot),
                quantifier(quantifier(body, robot), i),
            ]
            for goal in goals:
                with self.subTest(goal=goal):
                    self.problem.clear_goals()
                    self.problem.add_goal(goal)
                    compiled = self.compiler.compile(self.problem).problem
                    assert isinstance(compiled, Problem)
                    expected = [] if quantifier is Forall else [Bool(False)]
                    self.assertEqual(compiled.goals, expected)
        self.problem.clear_goals()
        self.problem.add_object(Object("drone1", UserType("drone", robot_type)))
        self.problem.add_goal(Forall(body, robot, i))
        compiled = self.compiler.compile(self.problem).problem
        assert isinstance(compiled, Problem)
        self.assertEqual(compiled.goals, [Bool(False)])
        with self.assertRaisesRegex(UPProblemDefinitionError, "Undefined final goal"):
            IntParametersAndVariablesRemover("permissive").compile(self.problem)

    def test_undefined_quantifiers(self):
        i = Variable("i", IntType(0, 1))
        for mode, quantifier, negate in product(
            ("pddl", "permissive"), (Forall, Exists), (False, True)
        ):
            with self.subTest(mode=mode, quantifier=quantifier.__name__, negate=negate):
                goal = quantifier(self.cell(i), i)
                self.problem.clear_goals()
                self.problem.add_goal(Not(goal) if negate else goal)
                compiler = IntParametersAndVariablesRemover(mode)
                if mode == "permissive" and quantifier is Forall:
                    with self.assertRaisesRegex(
                        UPProblemDefinitionError, "Undefined final goal"
                    ):
                        compiler.compile(self.problem)
                    continue
                compiled = compiler.compile(self.problem).problem
                assert isinstance(compiled, Problem)
                if mode == "pddl":
                    expected = Bool(False)
                else:
                    expected = Not(self.cell(1)) if negate else self.cell(1)
                self.assertEqual(compiled.goals, [expected])

    def test_goals_report_undefined_but_preserve_defined_alternatives(self):
        i = Variable("i", IntType(0, 1))
        undefined = Exists(self.cell(i - i), i)
        interval = ClosedTimeInterval(GlobalStartTiming(2), GlobalStartTiming(4))
        for mode, timed, goal in product(
            ("pddl", "permissive"),
            (False, True),
            (undefined, Not(undefined), Or(undefined, self.enabled), Bool(False)),
        ):
            with self.subTest(mode=mode, timed=timed, goal=goal):
                self.problem.clear_goals()
                self.problem.clear_timed_goals()
                if timed:
                    self.problem.add_timed_goal(interval, goal)
                else:
                    self.problem.add_goal(goal)
                compiler = IntParametersAndVariablesRemover(mode)
                if mode == "permissive" and goal in (undefined, Not(undefined)):
                    with self.assertRaisesRegex(
                        UPProblemDefinitionError, "Undefined .*goal"
                    ) as error:
                        compiler.compile(self.problem)
                    self.assertIn(str(goal), str(error.exception))
                    if timed:
                        self.assertIn(str(interval), str(error.exception))
                    continue
                compiled = compiler.compile(self.problem).problem
                assert isinstance(compiled, Problem)
                goals = compiled.timed_goals[interval] if timed else compiled.goals
                if mode == "permissive" and goal.is_or():
                    self.assertEqual(goals, [self.enabled()])
                else:
                    self.assertEqual(goals, [Bool(False)])

    def test_undefined_preconditions(self):
        for mode, quantifier in product(("pddl", "permissive"), (Forall, Exists)):
            with self.subTest(mode=mode, quantifier=quantifier.__name__):
                action = InstantaneousAction("finish", n=IntType(0, 1))
                i = Variable("i", IntType(0, 1))
                action.add_precondition(
                    quantifier(self.cell(i + action.parameter("n")), i)
                )
                actions = self.integer_instances(self.compile_action(action, mode))
                self.assertEqual(
                    set(actions),
                    (
                        {(Int(0),), (Int(1),)}
                        if mode == "permissive" and quantifier is Exists
                        else {(Int(1),)}
                    ),
                )

    def test_out_of_range_fluent_index(self):
        f = Fluent("f", index=IntType(0, 5))
        self.problem.add_fluent(f, default_initial_value=False)
        effect = InstantaneousAction("effect", x=IntType(0, 5))
        effect.add_effect(f(effect.parameter("x") + 1), True)
        precondition = InstantaneousAction("precondition", x=IntType(0, 5))
        x = precondition.parameter("x")
        precondition.add_precondition(Or(Equals(x, 5), f(x + 1)))
        conditional = InstantaneousAction("conditional", x=IntType(0, 5))
        conditional.add_effect(f(conditional.parameter("x") + 1), True, self.enabled)
        # In strict mode, the guard x < 5 does not prevent the error.
        guarded = InstantaneousAction("guarded", x=IntType(0, 5))
        x = guarded.parameter("x")
        guarded.add_precondition(x < 5)
        guarded.add_effect(f(x + 1), True)
        for mode, action in product(
            ("pddl", "permissive"), (effect, precondition, conditional, guarded)
        ):
            with self.subTest(mode=mode, action=action.name):
                instances = self.integer_instances(self.compile_action(action, mode))
                kept = mode == "permissive" and action in (precondition, conditional)
                self.assertEqual(len(instances), 6 if kept else 5)
                if kept:
                    last = instances[(Int(5),)]
                    self.assertEqual(last.effects, [])
                    self.assertEqual(
                        last.preconditions,
                        [] if action is precondition else [Not(self.enabled)],
                    )
        for action in (effect, precondition, conditional, guarded):
            with self.subTest(mode="strict", action=action.name):
                with self.assertRaisesRegex(
                    UPProblemDefinitionError, "with x = 5: 6 is outside"
                ):
                    self.compile_action(action, "strict")
        # Simulated effects only accept parameters as indices.
        simulated = InstantaneousAction("simulated", x=IntType(0, 6))
        with self.assertWarns(DeprecationWarning):
            target = f(simulated.parameter("x"))
            simulated.set_simulated_effect(SimulatedEffect([target], lambda *_: [True]))
        for mode in ("pddl", "permissive"):
            with self.subTest(mode=mode, action=simulated.name):
                instances = self.integer_instances(self.compile_action(simulated, mode))
                self.assertEqual(set(instances), {(Int(x),) for x in range(6)})

    def test_invalid_conditional_effects(self):
        x = Fluent("x", IntType(0, 1))
        self.problem.add_fluent(x, default_initial_value=0)
        for mode, action_type, invalid in product(
            ("pddl", "permissive"),
            (InstantaneousAction, DurativeAction),
            ("bounds", "undefined"),
        ):
            with self.subTest(
                mode=mode, action_type=action_type.__name__, invalid=invalid
            ):
                action = action_type("update", n=IntType(0, 2))
                assert isinstance(action, (InstantaneousAction, DurativeAction))
                n = action.parameter("n")
                target, value = (x, n) if invalid == "bounds" else (self.cell(n), True)
                if isinstance(action, DurativeAction):
                    action.set_fixed_duration(1)
                    action.add_effect(EndTiming(), target, value, self.enabled)
                    action.add_effect(EndTiming(), self.done, True)
                else:
                    action.add_effect(target, value, self.enabled)
                    action.add_effect(self.done, True)
                result = self.compile_action(action, mode)
                instances = self.integer_instances(result)
                if mode == "pddl" and invalid == "undefined":
                    self.assertNotIn((Int(0),), instances)
                    continue
                compiled = instances[(Int(2 if invalid == "bounds" else 0),)]
                plan: Plan
                validator: Union[TimeTriggeredPlanValidator, SequentialPlanValidator]
                if isinstance(compiled, DurativeAction):
                    self.assertEqual(
                        compiled.conditions,
                        {
                            ClosedTimeInterval(EndTiming(), EndTiming()): [
                                Not(self.enabled)
                            ]
                        },
                    )
                    plan = TimeTriggeredPlan(
                        [(Fraction(0), ActionInstance(compiled), Fraction(1))]
                    )
                    validator = TimeTriggeredPlanValidator()
                else:
                    self.assertEqual(compiled.preconditions, [Not(self.enabled)])
                    plan = SequentialPlan([ActionInstance(compiled)])
                    validator = SequentialPlanValidator()
                result.problem.add_goal(self.done)
                with validator:
                    for enabled, expected in [
                        (False, Status.VALID),
                        (True, Status.INVALID),
                    ]:
                        result.problem.set_initial_value(self.enabled, enabled)
                        self.assertEqual(
                            validator.validate(result.problem, plan).status, expected
                        )

    def test_invalid_effect_with_constant_condition(self):
        for mode, target_undefined, condition_kind in product(
            ("pddl", "permissive"), (False, True), ("true", "false", "undefined")
        ):
            with self.subTest(
                mode=mode, target=target_undefined, condition=condition_kind
            ):
                action = InstantaneousAction("update", n=IntType(0, 1))
                n = action.parameter("n")
                condition = {
                    "true": Equals(n, 0),
                    "false": GT(n, 0),
                    "undefined": self.cell(n),
                }[condition_kind]
                if target_undefined:
                    action.add_effect(self.cell(n), True, condition)
                else:
                    action.add_effect(self.done, self.cell(n), condition)
                actions = self.integer_instances(self.compile_action(action, mode))
                # In pddl mode only an undefined target that is never written keeps the instance
                if mode == "pddl":
                    kept = target_undefined and condition_kind == "false"
                else:
                    kept = condition_kind != "true"
                if kept:
                    self.assertEqual(actions[(Int(0),)].effects, [])
                    self.assertEqual(actions[(Int(0),)].preconditions, [])
                else:
                    self.assertNotIn((Int(0),), actions)

    def test_quantified_invalid_effect(self):
        location = UserType("location")
        self.problem.add_object(Object("home", location))
        site, i = Variable("site", location), Variable("i", IntType(0, 1))
        x = Fluent("x", site=location, index=IntType(1, 1))
        enabled = Fluent("site_enabled", site=location)
        self.problem.add_fluent(x, default_initial_value=False)
        self.problem.add_fluent(enabled, default_initial_value=False)
        action = InstantaneousAction("update")
        action.add_effect(x(site, i), True, enabled(site), forall=(site, i))
        self.assertEqual(self.compile_action(action, "pddl").problem.actions, [])
        compiled = self.compile_action(action, "permissive").problem.actions[0]
        self.assertEqual(compiled.preconditions, [Forall(Not(enabled(site)), site)])
        self.assertEqual([e.fluent for e in compiled.effects], [x(site, 1)])
        self.assertEqual(compiled.effects[0].forall, (site,))

    def test_partial_bounds_and_numeric_effects(self):
        for bounds in [(None, None), (0, None), (None, 3)]:
            with self.subTest(bounds=bounds):
                p = Problem("bounds")
                x = Fluent("x", IntType(*bounds))
                p.add_fluent(x, default_initial_value=0)
                action = InstantaneousAction("update", n=IntType(1, 2))
                action.add_effect(x, action.parameter("n"))
                p.add_action(action)
                compiled = self.compiler.compile(p).problem
                assert isinstance(compiled, Problem)
                self.assertEqual(len(compiled.actions), 2)
        x = Fluent("counter", IntType(0, 20))
        self.problem.add_fluent(x, default_initial_value=15)
        for method, kind in [
            ("add_increase_effect", "is_increase"),
            ("add_decrease_effect", "is_decrease"),
        ]:
            action = InstantaneousAction("update", n=IntType(1, 2))
            getattr(action, method)(x, action.parameter("n"))
            result = self.compile_action(action)
            self.assertEqual(len(result.problem.actions), 2)
            self.assertTrue(
                all(getattr(a.effects[0], kind)() for a in result.problem.actions)
            )

    def test_durative_quantifiers_and_plan_mapping(self):
        action = DurativeAction("mark", n=IntType(1, 2))
        n = action.parameter("n")
        i = Variable("i", IntType(), lower_bound=1, upper_bound=n)
        action.set_fixed_duration(ParameterExp(n))
        interval = OpenTimeInterval(StartTiming(), EndTiming())
        action.add_condition(interval, Not(self.enabled))
        action.add_condition(StartTiming(), Forall(Not(self.marked(i)), i))
        action.add_effect(EndTiming(), self.marked(i), True, forall=(i,))
        self.problem.add_goal(self.marked(2))
        result = self.compile_action(action)
        compiled = self.integer_instances(result)[(Int(2),)]
        self.assertEqual(compiled.duration.lower, Int(2))
        self.assertEqual(compiled.conditions[interval], [Not(self.enabled)])
        self.assertEqual(
            {e.fluent for e in compiled.effects[EndTiming()]},
            {self.marked(1), self.marked(2)},
        )
        plan = TimeTriggeredPlan([(Fraction(1), ActionInstance(compiled), Fraction(2))])
        lifted = plan.replace_action_instances(result.map_back_action_instance)
        assert isinstance(lifted, TimeTriggeredPlan)
        self.assertEqual(lifted.timed_actions[0][1].actual_parameters, (Int(2),))
        self.assertEqual(lifted.timed_actions[0][2], Fraction(2))
        with TimeTriggeredPlanValidator() as validator:
            self.assertEqual(
                validator.validate(result.problem, plan).status, Status.VALID
            )

    def test_duration_limits(self):
        action = DurativeAction("wait", n=IntType(1, 2))
        action.set_left_open_duration_interval(action.parameter("n") - 1, 1)
        compiled = self.compile_action(action).problem
        self.assertEqual(len(compiled.actions), 1)
        self.assertEqual(
            compiled.actions[0].duration, LeftOpenDurationInterval(Int(0), Int(1))
        )
        x = Fluent("x", RealType())
        self.problem.add_fluent(x, default_initial_value=0)
        action.add_increase_continuous_effect(
            ClosedTimeInterval(StartTiming(), EndTiming()), x, 1
        )
        self.compiler.skip_checks = True
        with self.assertRaisesRegex(UPProblemDefinitionError, "continuous effects"):
            self.compile_action(action)

    def test_global_effects_and_quantified_constraints(self):
        x = Fluent("x", RealType(), index=IntType(1, 1))
        self.problem.add_fluent(x, default_initial_value=0)
        i = Variable("i", IntType(0, 1))
        timing = GlobalStartTiming(1)
        interval = ClosedTimeInterval(timing, timing)
        self.problem.add_timed_effect(timing, x(i), 1, self.enabled, forall=(i,))
        compiled = self.compiler.compile(self.problem).problem
        assert isinstance(compiled, Problem)
        self.assertEqual(compiled.timed_goals[interval], [Bool(False)])
        self.assertTrue(compiled.kind.has_timed_goals())
        with self.assertRaisesRegex(
            UPProblemDefinitionError, "global timed effect"
        ) as error:
            IntParametersAndVariablesRemover("permissive").compile(self.problem)
        self.assertIn(str(timing), str(error.exception))
        self.assertIn(str(x(i)), str(error.exception))
        with self.assertRaisesRegex(UPProblemDefinitionError, "with i = 0"):
            IntParametersAndVariablesRemover("strict").compile(self.problem)
        self.problem.clear_timed_effects()
        self.problem.add_timed_effect(
            timing, x(i), 1, And(self.enabled, i > 0), forall=(i,)
        )
        self.problem.add_increase_effect(GlobalStartTiming(2), x(1), 2)
        self.problem.add_decrease_effect(GlobalStartTiming(3), x(1), 1)
        self.problem.add_trajectory_constraint(Always(Forall(self.marked(i), i)))
        self.problem.add_timed_goal(GlobalStartTiming(4), Forall(self.marked(i), i))
        for mode in ("pddl", "permissive"):
            with self.subTest(mode=mode):
                compiled = (
                    IntParametersAndVariablesRemover(mode).compile(self.problem).problem
                )
                assert isinstance(compiled, Problem)
                self.assertNotIn(interval, compiled.timed_goals)
                self.assertEqual(
                    [e.fluent for e in compiled.timed_effects[timing]], [x(1)]
                )
                self.assertTrue(
                    compiled.timed_effects[GlobalStartTiming(2)][0].is_increase()
                )
                self.assertTrue(
                    compiled.timed_effects[GlobalStartTiming(3)][0].is_decrease()
                )
                expanded = And(self.marked(0), self.marked(1))
                self.assertEqual(compiled.trajectory_constraints, [Always(expanded)])
                self.assertEqual(
                    compiled.timed_goals[
                        ClosedTimeInterval(GlobalStartTiming(4), GlobalStartTiming(4))
                    ],
                    [expanded],
                )

    def test_simulated_effect_arguments_and_timing(self):
        location = UserType("location")
        home = Object("home", location)
        self.problem.add_object(home)
        x = Fluent("x", IntType(), site=location, index=IntType(1, 2))
        self.problem.add_fluent(x, default_initial_value=0)
        for action_type in (InstantaneousAction, DurativeAction):
            with self.subTest(action_type=action_type.__name__):
                action = action_type("update", n=IntType(1, 2), site=location)
                n, site = action.parameter("n"), action.parameter("site")

                def callback(problem, state, args):
                    self.assertEqual(args[site].object(), home)
                    return [args[n]]

                with self.assertWarns(DeprecationWarning):
                    effect = SimulatedEffect([x(site, n)], callback)
                if isinstance(action, DurativeAction):
                    action.set_fixed_duration(1)
                    action.set_simulated_effect(EndTiming(), effect)
                else:
                    action.set_simulated_effect(effect)
                result = self.compile_action(action)
                for compiled in result.problem.actions:
                    instance = ActionInstance(compiled, (home,))
                    integer = result.map_back_action_instance(
                        instance
                    ).actual_parameters[0]
                    effect = (
                        compiled.simulated_effects[EndTiming()]
                        if isinstance(compiled, DurativeAction)
                        else compiled.simulated_effect
                    )
                    self.assertEqual(
                        effect.fluents, [x(compiled.parameter("site"), integer)]
                    )
                    arguments = {compiled.parameter("site"): ObjectExp(home)}
                    self.assertEqual(
                        effect.function(
                            result.problem, UPState({}, result.problem), arguments
                        ),
                        [integer],
                    )

    def test_action_costs(self):
        action = InstantaneousAction("finish", n=IntType(0, 2))
        n = action.parameter("n")
        for cost in (None, n + 1):
            with self.subTest(cost=cost):
                self.problem.clear_quality_metrics()
                metric = MinimizeActionCosts({} if cost is None else {action: cost})
                self.problem.add_quality_metric(metric)
                result = self.compile_action(action)
                for (value,), compiled in self.integer_instances(result).items():
                    actual = result.problem.quality_metrics[0].get_action_cost(compiled)
                    expected = None if cost is None else Int(value.constant_value() + 1)
                    self.assertEqual(
                        None if actual is None else actual.simplify(), expected
                    )
        self.problem.clear_quality_metrics()
        action.add_precondition(n > 0)
        self.problem.add_quality_metric(
            MinimizeActionCosts({action: Div(1, n)}, default=7)
        )
        result = self.compile_action(action)
        metric = result.problem.quality_metrics[0]
        self.assertEqual(metric.default, Int(7))
        costs = {
            n: metric.get_action_cost(a).simplify()
            for (n,), a in self.integer_instances(result).items()
        }
        self.assertEqual(costs, {Int(1): Int(1), Int(2): Real(Fraction(1, 2))})

    def test_oversubscription_rewards(self):
        i = Variable("i", IntType(1, 1))
        goal = Forall(self.marked(i), i)
        interval = ClosedTimeInterval(GlobalStartTiming(1), GlobalStartTiming(2))
        for temporal in (False, True):
            key = (lambda g: (interval, g)) if temporal else (lambda g: g)
            self.problem.clear_quality_metrics()
            if temporal:
                self.problem.add_quality_metric(
                    TemporalOversubscription(
                        {(interval, goal): 10, (interval, self.marked(1)): 5}
                    )
                )
            else:
                self.problem.add_quality_metric(
                    Oversubscription({goal: 10, self.marked(1): 5})
                )
            compiled = self.compiler.compile(self.problem).problem
            assert isinstance(compiled, Problem)
            metric = compiled.quality_metrics[0]
            assert isinstance(metric, (Oversubscription, TemporalOversubscription))
            self.assertEqual(metric.goals, {key(self.marked(1)): 15})
