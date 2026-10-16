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
        self.enabled, self.done = Fluent("enabled"), Fluent("done")
        for fluent in (self.marked, self.enabled, self.done):
            self.problem.add_fluent(fluent, default_initial_value=False)

    def compile_action(self, action):
        self.problem.clear_actions()
        self.problem.add_action(action)
        return self.compiler.compile(self.problem)

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
                i = IntVariable("i", 1, action.parameter("n"))
                action.add_precondition(quantifier(self.marked(i), i))
                action.add_effect(self.marked(i), True, forall=(i,))
                result = self.compile_action(action)
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
                self.assertFalse(result.problem.kind.has_int_variables())

    def test_nested_ranges_and_variable_scope(self):
        i = IntVariable("i", 1, 2)
        j = IntVariable("j", 1, i + 0)
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
        limit = Fluent("limit", IntType(0, 2))
        self.problem.add_fluent(limit, default_initial_value=1)
        i = IntVariable("i", 0, limit())
        self.problem.add_goal(Forall(self.marked(i), i))
        with self.assertRaisesRegex(
            UPProblemDefinitionError, "bounds of integer variable i"
        ):
            self.compiler.compile(self.problem)

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
        site, i = Variable("site", location, env), IntVariable("i", 1, 2, env)
        for quantifier, combine in [(em.Forall, em.And), (em.Exists, em.Or)]:
            with self.subTest(quantifier=quantifier.__name__):
                p.clear_goals()
                p.add_goal(quantifier(marked(site, i), site, i).simplify())
                self.assertTrue(p.kind.has_int_variables())
                compiled = self.compiler.compile(p).problem
                assert isinstance(compiled, Problem)
                self.assertEqual(
                    compiled.goals,
                    [quantifier(combine(marked(site, 1), marked(site, 2)), site)],
                )
                self.assertIs(compiled.environment, env)
                self.assertFalse(compiled.kind.has_int_variables())

    def test_empty_object_domains(self):
        robot_type = UserType("robot")
        robot = Variable("robot", robot_type)
        available = Fluent("available", robot=robot_type)
        self.problem.add_fluent(available, default_initial_value=True)
        i = IntVariable("i", 0, 1)
        body = And(available(robot), GT(Div(1, i), 0))
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
        with self.assertRaisesRegex(UPProblemDefinitionError, "Undefined final goal"):
            self.compiler.compile(self.problem)

    def test_undefined_quantifiers(self):
        i = IntVariable("i", 0, 1)
        for quantifier, defined, negate in product(
            (Forall, Exists), (False, True), (False, True)
        ):
            with self.subTest(
                quantifier=quantifier.__name__, defined=defined, negate=negate
            ):
                body = GT(Div(1, i), 0) if defined else LT(Div(1, i), 0)
                goal = quantifier(body, i)
                self.problem.clear_goals()
                self.problem.add_goal(Not(goal) if negate else goal)
                if quantifier is Forall:
                    with self.assertRaisesRegex(
                        UPProblemDefinitionError, "Undefined final goal"
                    ):
                        self.compiler.compile(self.problem)
                else:
                    compiled = self.compiler.compile(self.problem).problem
                    assert isinstance(compiled, Problem)
                    self.assertEqual(
                        compiled.goals, [] if defined != negate else [Bool(False)]
                    )

    def test_goals_report_undefined_but_preserve_defined_alternatives(self):
        i = IntVariable("i", 0, 1)
        undefined = Exists(GT(Div(1, i - i), 0), i)
        interval = ClosedTimeInterval(GlobalStartTiming(2), GlobalStartTiming(4))
        for timed, goal in product(
            (False, True),
            (undefined, Not(undefined), Or(undefined, self.enabled), Bool(False)),
        ):
            with self.subTest(timed=timed, goal=goal):
                self.problem.clear_goals()
                self.problem.clear_timed_goals()
                if timed:
                    self.problem.add_timed_goal(interval, goal)
                else:
                    self.problem.add_goal(goal)
                if goal in (undefined, Not(undefined)):
                    with self.assertRaisesRegex(
                        UPProblemDefinitionError, "Undefined .*goal"
                    ) as error:
                        self.compiler.compile(self.problem)
                    self.assertIn(str(goal), str(error.exception))
                    if timed:
                        self.assertIn(str(interval), str(error.exception))
                else:
                    compiled = self.compiler.compile(self.problem).problem
                    assert isinstance(compiled, Problem)
                    goals = compiled.timed_goals[interval] if timed else compiled.goals
                    self.assertEqual(
                        goals, [Bool(False) if goal.is_false() else self.enabled()]
                    )

    def test_undefined_preconditions(self):
        for quantifier in (Forall, Exists):
            action = InstantaneousAction("finish", n=IntType(0, 1))
            i = IntVariable("i", 0, 1)
            action.add_precondition(
                quantifier(GT(Div(1, i + action.parameter("n")), 0), i)
            )
            actions = self.integer_instances(self.compile_action(action))
            self.assertEqual(
                set(actions),
                {(Int(1),)} if quantifier is Forall else {(Int(0),), (Int(1),)},
            )

    def test_invalid_conditional_effects(self):
        x = Fluent("x", IntType(0, 1))
        self.problem.add_fluent(x, default_initial_value=0)
        real_x = Fluent("real_x", RealType())
        self.problem.add_fluent(real_x, default_initial_value=0)
        for action_type, invalid in product(
            (InstantaneousAction, DurativeAction), ("bounds", "division")
        ):
            with self.subTest(action_type=action_type.__name__, invalid=invalid):
                action = action_type("update", n=IntType(0, 2))
                assert isinstance(action, (InstantaneousAction, DurativeAction))
                n = action.parameter("n")
                value = n if invalid == "bounds" else Div(1, n)
                target = x if invalid == "bounds" else real_x
                if isinstance(action, DurativeAction):
                    action.set_fixed_duration(1)
                    action.add_effect(EndTiming(), target, value, self.enabled)
                    action.add_effect(EndTiming(), self.done, True)
                else:
                    action.add_effect(target, value, self.enabled)
                    action.add_effect(self.done, True)
                result = self.compile_action(action)
                compiled = self.integer_instances(result)[
                    (Int(2 if invalid == "bounds" else 0),)
                ]
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
        x = Fluent("x", RealType(), flag=BoolType())
        self.problem.add_fluent(x, default_initial_value=0)
        for target_undefined, condition_kind in product(
            (False, True), ("true", "false", "undefined")
        ):
            with self.subTest(target=target_undefined, condition=condition_kind):
                action = InstantaneousAction("update", n=IntType(0, 1))
                n = action.parameter("n")
                quotient = Div(1, n)
                condition = {
                    "true": Equals(n, 0),
                    "false": GT(n, 0),
                    "undefined": GT(quotient, 0),
                }[condition_kind]
                target = x(GT(quotient, 0)) if target_undefined else x(True)
                action.add_effect(
                    target, 1 if target_undefined else quotient, condition
                )
                actions = self.integer_instances(self.compile_action(action))
                if condition_kind == "true":
                    self.assertNotIn((Int(0),), actions)
                else:
                    self.assertEqual(actions[(Int(0),)].effects, [])
                    self.assertEqual(actions[(Int(0),)].preconditions, [])

    def test_quantified_invalid_effect(self):
        location = UserType("location")
        self.problem.add_object(Object("home", location))
        site, i = Variable("site", location), IntVariable("i", 0, 1)
        x = Fluent("x", RealType(), site=location, index=IntType(0, 1))
        enabled = Fluent("site_enabled", site=location)
        self.problem.add_fluent(x, default_initial_value=0)
        self.problem.add_fluent(enabled, default_initial_value=False)
        action = InstantaneousAction("update")
        action.add_effect(x(site, i), Div(1, i), enabled(site), forall=(site, i))
        compiled = self.compile_action(action).problem.actions[0]
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
        i = IntVariable("i", 1, n)
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
        x = Fluent("x", RealType(), index=IntType(0, 1))
        self.problem.add_fluent(x, default_initial_value=0)
        i = IntVariable("i", 0, 1)
        timing = GlobalStartTiming(1)
        interval = ClosedTimeInterval(timing, timing)
        self.problem.add_timed_effect(
            timing, x(i), Div(1, i), self.enabled, forall=(i,)
        )
        with self.assertRaisesRegex(
            UPProblemDefinitionError, "global timed effect"
        ) as error:
            self.compiler.compile(self.problem)
        self.assertIn(str(timing), str(error.exception))
        self.assertIn(str(Div(1, i)), str(error.exception))
        self.problem.clear_timed_effects()
        self.problem.add_timed_effect(
            timing, x(i), Div(1, i), And(self.enabled, i > 0), forall=(i,)
        )
        self.problem.add_increase_effect(GlobalStartTiming(2), x(1), 2)
        self.problem.add_decrease_effect(GlobalStartTiming(3), x(1), 1)
        self.problem.add_trajectory_constraint(Always(Forall(self.marked(i), i)))
        self.problem.add_timed_goal(GlobalStartTiming(4), Forall(self.marked(i), i))
        compiled = self.compiler.compile(self.problem).problem
        assert isinstance(compiled, Problem)
        self.assertNotIn(interval, compiled.timed_goals)
        self.assertEqual([e.fluent for e in compiled.timed_effects[timing]], [x(1)])
        self.assertTrue(compiled.timed_effects[GlobalStartTiming(2)][0].is_increase())
        self.assertTrue(compiled.timed_effects[GlobalStartTiming(3)][0].is_decrease())
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
        i = IntVariable("i", 1, 1)
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
