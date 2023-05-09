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


import unified_planning
from unified_planning.shortcuts import *
from unified_planning.test import TestCase, main
from unified_planning.test.examples import get_example_problems
from unified_planning.engines import SequentialPlanValidator, ValidationResultStatus
from unified_planning.environment import get_environment


class TestProblem(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_all(self):
        pv = SequentialPlanValidator(environment=get_environment())
        for p in self.problems.values():
            if not pv.supports(p.problem.kind):
                continue
            problem, plan = p.problem, p.plan
            if SequentialPlanValidator.supports(problem.kind):
                validation_result = pv.validate(problem, plan)
                self.assertEqual(validation_result.status, ValidationResultStatus.VALID)

    def test_all_from_factory(self):
        with PlanValidator(name="sequential_plan_validator") as pv:
            self.assertEqual(pv.name, "sequential_plan_validator")
            for p in self.problems.values():
                if not pv.supports(p.problem.kind):
                    continue
                problem, plan = p.problem, p.plan
                validation_result = pv.validate(problem, plan)
                self.assertEqual(validation_result.status, ValidationResultStatus.VALID)

    def test_all_from_factory_with_problem_kind(self):
        for p in self.problems.values():
            problem, plan = p.problem, p.plan
            pk = problem.kind
            if SequentialPlanValidator.supports(pk):
                environment = unified_planning.environment.Environment()
                environment.factory.preference_list = [
                    e for e in environment.factory.preference_list if e != "tamer"
                ]
                with environment.factory.PlanValidator(
                    problem_kind=pk, plan_kind=plan.kind
                ) as pv:
                    self.assertEqual(pv.name, "sequential_plan_validator")
                    validation_result = pv.validate(problem, plan)
                    self.assertEqual(
                        validation_result.status, ValidationResultStatus.VALID
                    )

    def test_quality_metric(self):
        pv = SequentialPlanValidator()
        problem, plan = self.problems["basic"]
        problem = problem.clone()
        problem.add_quality_metric(MinimizeSequentialPlanLength())
        res = pv.validate(problem, plan)
        me = res.metric_evaluations
        assert me is not None
        self.assertEqual(len(me), 1)
        for qm, val in me.items():
            self.assertIsInstance(qm, MinimizeSequentialPlanLength)
            self.assertEqual(val, 1)

        problem, plan = self.problems["locations_connected_visited_oversubscription"]
        res = pv.validate(problem, plan)
        me = res.metric_evaluations
        assert me is not None
        self.assertEqual(len(me), 1)
        for qm, val in me.items():
            self.assertIsInstance(qm, Oversubscription)
            self.assertEqual(val, 15)

        problem, plan = self.problems["locations_connected_cost_minimize"]
        res = pv.validate(problem, plan)
        me = res.metric_evaluations
        assert me is not None
        self.assertEqual(len(me), 1)
        for qm, val in me.items():
            self.assertIsInstance(qm, MinimizeActionCosts)
            self.assertEqual(val, 10)

    def test_global_constraints(self):
        problem = self.problems["robot_loader_weak_bridge"].problem
        move = problem.action("move")
        load = problem.action("load")
        unload = problem.action("unload")
        l1, l2, l3 = [problem.object(f"l{i}") for i in range(1, 4)]
        # the plan is bad because going loaded from l3 to l1 violates a global constraint
        bad_plan = up.plans.SequentialPlan(
            [
                up.plans.ActionInstance(move, (ObjectExp(l1), ObjectExp(l3))),
                up.plans.ActionInstance(load, (ObjectExp(l3),)),
                up.plans.ActionInstance(move, (ObjectExp(l3), ObjectExp(l1))),
                up.plans.ActionInstance(unload, (ObjectExp(l1),)),
            ]
        )
        with PlanValidator(name="sequential_plan_validator") as pv:
            self.assertEqual(pv.name, "sequential_plan_validator")
            self.assertTrue(pv.supports(problem.kind))
            validation_result = pv.validate(problem, bad_plan)
            self.assertEqual(validation_result.status, ValidationResultStatus.INVALID)
            self.assertIn("violates global constraints.", str(validation_result))
            # when removing the global constraints, the bad plan should become valid
            problem = problem.clone()
            problem.clear_trajectory_constraints()
            validation_result = pv.validate(problem, bad_plan)
            self.assertEqual(validation_result.status, ValidationResultStatus.VALID)
