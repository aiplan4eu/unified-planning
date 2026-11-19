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


from itertools import product
from typing import cast
import unified_planning
from unified_planning.shortcuts import *
from unified_planning.model.problem_kind import full_classical_kind
from unified_planning.test import unittest_TestCase, main
from unified_planning.test import (
    skipIfNoPlanValidatorForProblemKind,
    skipIfNoOneshotPlannerForProblemKind,
)
from unified_planning.test.examples import get_example_problems
from unified_planning.engines import CompilationKind, ValidationResultStatus
from unified_planning.model.fluent import get_all_fluent_exp
from unified_planning.model.types import domain_item, domain_size
from unified_planning.model.walkers import QuantifierSimplifier
from unified_planning.engines.compilers.usertype_fluents_remover import (
    UsertypeFluentsRemover,
)


class TestUsertypeFLuentsRemover(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfNoOneshotPlannerForProblemKind(full_classical_kind)
    @skipIfNoPlanValidatorForProblemKind(full_classical_kind)
    def test_robot_fluent_of_user_type(self):
        problem = self.problems["robot_fluent_of_user_type"].problem

        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.USERTYPE_FLUENTS_REMOVING,
        ) as utfr:
            res = utfr.compile(problem)
        compiled_problem = res.problem

        self.assertTrue(problem.kind.has_object_fluents())
        self.assertFalse(compiled_problem.kind.has_object_fluents())

        with OneshotPlanner(problem_kind=compiled_problem.kind) as planner:
            self.assertNotEqual(planner, None)
            solve_res = planner.solve(compiled_problem)
            compiled_plan = solve_res.plan
            new_plan = compiled_plan.replace_action_instances(
                res.map_back_action_instance
            )
            with PlanValidator(
                problem_kind=problem.kind, plan_kind=new_plan.kind
            ) as pv:
                self.assertTrue(pv.validate(problem, new_plan))

    def test_robot_fluent_of_user_type_with_int_id(self):
        example = self.problems["robot_fluent_of_user_type_with_int_id"]
        problem, plan = example.problem, example.valid_plans[0]

        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.USERTYPE_FLUENTS_REMOVING,
        ) as utfr:
            res = utfr.compile(problem)
        compiled_problem = res.problem
        original_kind = problem.kind
        compiled_kind = compiled_problem.kind

        self.assertTrue(original_kind.has_object_fluents())
        self.assertFalse(compiled_kind.has_object_fluents())

        self.assertFalse(
            original_kind.has_conditional_effects()
            or original_kind.has_existential_conditions()
        )
        self.assertTrue(compiled_kind.has_conditional_effects())

        original_is_at = problem.fluent("is_at")
        compiled_is_at = compiled_problem.fluent("is_at")
        self.assertFalse(original_is_at.type.is_bool_type())
        self.assertTrue(compiled_is_at.type.is_bool_type())
        self.assertEqual(
            len(original_is_at.signature) + 1, len(compiled_is_at.signature)
        )

        compiled_plan = compiled_problem.normalize_plan(plan)

        with PlanValidator(
            problem_kind=compiled_kind, plan_kind=compiled_plan.kind
        ) as validator:
            val_res = validator.validate(compiled_problem, compiled_plan)
            self.assertEqual(val_res.status, ValidationResultStatus.VALID)

    def test_single_expressions(self):
        # create a mockup problem, with some ad-hoc conditions, compile it, and check
        # that with the same fluent assignments, the every condition is equivalent to
        # his compiled counterpart.
        problem = Problem("test")
        ut1 = UserType("UT1")
        f1 = Fluent("f1", ut1)
        g1 = Fluent("g1", ut1)
        f1_r = Fluent("f1_r", ut1, param_ut1=ut1)
        b1 = Fluent("b1", BoolType(), param_1=ut1)
        b1_1 = Fluent("b1_1", BoolType(), param_1=ut1, param_2=ut1)
        f1_b_ut1 = Fluent("f1_b_ut1", ut1, param_bool=BoolType(), param_ut1=ut1)
        int1 = Fluent("int1", IntType(1, 3), param_1=ut1)

        obj_1 = Object("o_1", ut1)
        obj_2 = Object("o_2", ut1)
        conds = [
            f1.Equals(obj_1),
            f1.Equals(g1),
            b1(f1),
            b1_1(f1, g1),
            int1(f1) < 1.5,
            int1(g1) + int1(f1) + 5 - 3 > 4.5,
            b1(f1_r(f1_r(f1_r(f1)))),
        ]
        a = InstantaneousAction("a")
        for condition in conds:
            a.add_precondition(condition)
        a.add_effect(f1, g1)

        b = InstantaneousAction("b")
        b.add_effect(f1_r(obj_1), g1)

        c = InstantaneousAction("c")
        c.add_effect(f1, g1, b1(g1))

        d = InstantaneousAction("d")
        d.add_effect(f1_b_ut1(True, obj_1), g1)

        problem.add_fluents([f1, g1, f1_r, b1, b1_1, f1_b_ut1, int1])
        problem.add_objects([obj_1, obj_2])
        problem.add_actions([a, b, c, d])

        init: Dict[FNode, Union[Object, int, bool]] = {
            f1(): obj_1,
            g1(): obj_2,
            f1_r(obj_1): obj_2,
            f1_r(obj_2): obj_1,
            b1(obj_1): True,
            b1(obj_2): False,
            b1_1(obj_1, obj_1): True,
            b1_1(obj_2, obj_1): False,
            b1_1(obj_1, obj_2): True,
            b1_1(obj_2, obj_2): False,
            f1_b_ut1(True, obj_1): obj_1,
            f1_b_ut1(False, obj_1): obj_2,
            f1_b_ut1(True, obj_2): obj_2,
            f1_b_ut1(False, obj_2): obj_1,
            int1(obj_1): 1,
            int1(obj_2): 2,
        }

        for k, v in init.items():
            problem.set_initial_value(k, v)

        with Compiler(
            problem_kind=problem.kind,
            compilation_kind=CompilationKind.USERTYPE_FLUENTS_REMOVING,
        ) as utfr:
            res = utfr.compile(problem)
        compiled_problem = res.problem

        new_f1 = compiled_problem.fluent(f1.name)
        new_g1 = compiled_problem.fluent(g1.name)
        new_f1_r = compiled_problem.fluent(f1_r.name)
        new_f1_b_ut1 = compiled_problem.fluent(f1_b_ut1.name)
        g1_var = Variable("g1_ut1", g1.type)
        expected_effects = {}

        # a effect -> f1 := g1
        expected_effects[a.name] = {
            Effect(
                new_f1(obj_1),
                TRUE(),
                new_g1(obj_1),
            ),
            Effect(
                new_f1(obj_1),
                FALSE(),
                Not(new_g1(obj_1)),
            ),
            Effect(
                new_f1(obj_2),
                TRUE(),
                new_g1(obj_2),
            ),
            Effect(
                new_f1(obj_2),
                FALSE(),
                Not(new_g1(obj_2)),
            ),
        }

        # b effect -> f1_r(obj_1):= g1
        expected_effects[b.name] = {
            Effect(
                new_f1_r(obj_1, obj_1),
                TRUE(),
                new_g1(obj_1),
            ),
            Effect(
                new_f1_r(obj_1, obj_1),
                FALSE(),
                Not(new_g1(obj_1)),
            ),
            Effect(
                new_f1_r(obj_1, obj_2),
                TRUE(),
                new_g1(obj_2),
            ),
            Effect(
                new_f1_r(obj_1, obj_2),
                FALSE(),
                Not(new_g1(obj_2)),
            ),
        }

        # c effect -> if  b1(g1) then f1 := g1
        expected_effects[c.name] = {
            Effect(
                new_f1(obj_1),
                TRUE(),
                And(Exists(And(b1(g1_var), new_g1(g1_var)), g1_var), new_g1(obj_1)),
            ),
            Effect(
                new_f1(obj_1),
                FALSE(),
                And(
                    Exists(And(b1(g1_var), new_g1(g1_var)), g1_var), Not(new_g1(obj_1))
                ),
            ),
            Effect(
                new_f1(obj_2),
                TRUE(),
                And(Exists(And(b1(g1_var), new_g1(g1_var)), g1_var), new_g1(obj_2)),
            ),
            Effect(
                new_f1(obj_2),
                FALSE(),
                And(
                    Exists(And(b1(g1_var), new_g1(g1_var)), g1_var), Not(new_g1(obj_2))
                ),
            ),
        }

        # d effect -> f1_b_ut1(True, obj_1) := g1
        expected_effects[d.name] = {
            Effect(
                new_f1_b_ut1(True, obj_1, obj_1),
                TRUE(),
                new_g1(obj_1),
            ),
            Effect(
                new_f1_b_ut1(True, obj_1, obj_1),
                FALSE(),
                Not(new_g1(obj_1)),
            ),
            Effect(
                new_f1_b_ut1(True, obj_1, obj_2),
                TRUE(),
                new_g1(obj_2),
            ),
            Effect(
                new_f1_b_ut1(True, obj_1, obj_2),
                FALSE(),
                Not(new_g1(obj_2)),
            ),
        }
        simplifier = QuantifierSimplifier(problem.environment, problem)
        compiled_simplifier = QuantifierSimplifier(
            compiled_problem.environment, compiled_problem
        )

        for condition, compiled_condition in zip(
            cast(InstantaneousAction, problem.action("a")).preconditions,
            cast(InstantaneousAction, compiled_problem.action("a")).preconditions,
        ):
            all_fluent_exp = [
                f
                for k in problem.environment.free_vars_extractor.get(condition)
                for f in get_all_fluent_exp(problem, k.fluent())
            ]
            gen = [
                [
                    domain_item(problem, k.fluent().type, i)
                    for i in range(domain_size(problem, k.fluent().type))
                ]
                for k in all_fluent_exp
            ]
            for values in product(*gen):
                assert len(all_fluent_exp) == len(values)
                original_assignments: Dict[Expression, Expression] = dict(
                    zip(all_fluent_exp, values)
                )
                compiled_assignments: Dict[Expression, Expression] = {}
                for fluent, val in original_assignments.items():
                    assert isinstance(fluent, FNode)
                    assert fluent.is_fluent_exp()
                    if fluent.fluent().type.is_user_type():
                        compiled_fluent = compiled_problem.fluent(fluent.fluent().name)
                        compiled_args = fluent.args[:]
                        for i in range(domain_size(problem, fluent.fluent().type)):
                            obj = domain_item(problem, fluent.fluent().type, i)
                            compiled_assignments[
                                compiled_fluent(*compiled_args, obj)
                            ] = obj == val
                    else:
                        compiled_assignments[fluent] = val
                sc = simplifier.qsimplify(condition, original_assignments, {})
                scc = compiled_simplifier.qsimplify(
                    compiled_condition, compiled_assignments, {}
                )
                self.assertEqual(sc, scc)

        for action in compiled_problem.actions:
            assert isinstance(action, InstantaneousAction)
            action_expected_effects = expected_effects[action.name]
            action_effects = action.effects
            self.assertEqual(len(action_expected_effects), len(action_effects))
            for effect in action_effects:
                self.assertIn(effect, action_expected_effects)

    def _check_same_applicability(self, problem, action_name, parameters_list):
        compiled = (
            UsertypeFluentsRemover()
            .compile(problem, CompilationKind.USERTYPE_FLUENTS_REMOVING)
            .problem
        )
        original_action = problem.action(action_name)
        compiled_action = compiled.action(action_name)
        c1, c2 = problem.fluent("c1"), problem.fluent("c2")
        results = []
        for v1, v2 in product([True, False], repeat=2):
            original_problem = problem.clone()
            original_problem.set_initial_value(c1, v1)
            original_problem.set_initial_value(c2, v2)
            compiled_problem = compiled.clone()
            compiled_problem.set_initial_value(c1, v1)
            compiled_problem.set_initial_value(c2, v2)
            for params in parameters_list:
                with SequentialSimulator(problem=original_problem) as simulator:
                    expected = simulator.is_applicable(
                        simulator.get_initial_state(), original_action, params
                    )
                with SequentialSimulator(problem=compiled_problem) as simulator:
                    actual = simulator.is_applicable(
                        simulator.get_initial_state(), compiled_action, params
                    )
                self.assertEqual(expected, actual, (v1, v2, params))
                results.append(expected)
        return results

    def _conflict_problem(self):
        T = UserType("T")
        objects = [Object(f"o{i}", T) for i in range(1, 4)]
        x = Fluent("x", T)
        problem = Problem("conflict")
        problem.add_objects(objects)
        problem.add_fluent(x, default_initial_value=objects[0])
        problem.add_fluent("c1", default_initial_value=True)
        problem.add_fluent("c2", default_initial_value=True)
        problem.add_goal(Equals(x, objects[1]))
        return problem, T, objects, x

    def test_conflicting_conditional_assignments(self):
        problem, T, (o1, o2, o3), x = self._conflict_problem()
        c1, c2 = problem.fluent("c1"), problem.fluent("c2")
        a = InstantaneousAction("a")
        a.add_effect(x, o2, c1)
        a.add_effect(x, o3, c2)
        problem.add_action(a)
        # both effects fire only in the first state, so only there is the action not applicable
        results = self._check_same_applicability(problem, "a", [()])
        self.assertEqual(results, [False, True, True, True])

        # equal values do not conflict
        same = problem.clone()
        same.clear_actions()
        b = InstantaneousAction("a")
        b.add_effect(x, o2, c1)
        b.add_effect(x, o2, c2)
        same.add_action(b)
        self.assertEqual(self._check_same_applicability(same, "a", [()]), [True] * 4)

    def test_conflicting_parametric_assignments(self):
        problem, T, objects, x = self._conflict_problem()
        c1, c2 = problem.fluent("c1"), problem.fluent("c2")
        a = InstantaneousAction("a", p=T, q=T)
        a.add_effect(x, a.parameter("p"), c1)
        a.add_effect(x, a.parameter("q"), c2)
        problem.add_action(a)
        # the compiled action stays applicable when p = q
        params = list(product(objects, repeat=2))
        self._check_same_applicability(problem, "a", params)

    def test_conflicting_forall_assignments(self):
        problem, T, (o1, o2, o3), x = self._conflict_problem()
        c1, c2 = problem.fluent("c1"), problem.fluent("c2")
        y = Fluent("y", T, t=T)
        problem.add_fluent(y, default_initial_value=o1)
        problem.set_initial_value(y(o2), o2)
        problem.set_initial_value(y(o3), o3)
        v = Variable("v", T)
        w = Variable("w", T)
        # forall v: x := v if c1 and y(v) == v, which writes x once per v that matches
        a = InstantaneousAction("a")
        a.add_effect(x, v, And(c1, Equals(y(v), v)), forall=[v])
        problem.add_action(a)
        self._check_same_applicability(problem, "a", [()])

        # a forall effect on y(w) and a plain effect on y(o2) write the same atom for w = o2
        other = problem.clone()
        other.clear_actions()
        b = InstantaneousAction("a")
        b.add_effect(y(w), o3, c1, forall=[w])
        b.add_effect(y(o2), o1, c2)
        other.add_action(b)
        results = self._check_same_applicability(other, "a", [()])
        self.assertEqual(results, [False, True, True, True])

    def test_conflicting_durative_assignments(self):
        problem, T, (o1, o2, o3), x = self._conflict_problem()
        c1, c2 = problem.fluent("c1"), problem.fluent("c2")
        a = DurativeAction("a")
        a.set_fixed_duration(1)
        a.add_effect(EndTiming(), x, o2, c1)
        a.add_effect(EndTiming(), x, o3, c2)
        a.add_effect(StartTiming(), x, o3, c2)
        problem.add_action(a)
        compiled = (
            UsertypeFluentsRemover()
            .compile(problem, CompilationKind.USERTYPE_FLUENTS_REMOVING)
            .problem
        )
        conditions = compiled.action("a").conditions
        self.assertEqual(
            conditions,
            {TimePointInterval(EndTiming()): [Not(And(c1, c2))]},
        )
