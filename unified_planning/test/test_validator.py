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

import unified_planning as up
from unified_planning.shortcuts import *
from unified_planning.engines import SequentialPlanValidator, FailedValidationReason
from unified_planning.plans import SequentialPlan, ActionInstance
from unified_planning.model.problem_kind import (
    classical_kind,
    general_numeric_kind,
    bounded_types_kind,
)
from unified_planning.test import (
    unittest_TestCase,
    main,
    skipIfNoPlanValidatorForProblemKind,
)
from unified_planning.test.examples import get_example_problems


class TestPlanValidator(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfNoPlanValidatorForProblemKind(classical_kind)
    def test_basic(self):
        example = self.problems["basic"]
        problem, plan = example.problem, example.valid_plans[0]

        with PlanValidator(problem_kind=problem.kind, plan_kind=plan.kind) as validator:
            self.assertNotEqual(validator, None)

            res = validator.validate(problem, plan)
            self.assertEqual(res.status, up.engines.ValidationResultStatus.VALID)

            plan = up.plans.SequentialPlan([])
            res = validator.validate(problem, plan)
            self.assertEqual(res.status, up.engines.ValidationResultStatus.INVALID)

    @skipIfNoPlanValidatorForProblemKind(
        classical_kind.union(general_numeric_kind).union(bounded_types_kind)
    )
    def test_robot(self):
        example = self.problems["robot"]
        problem, plan = example.problem, example.valid_plans[0]

        with PlanValidator(problem_kind=problem.kind, plan_kind=plan.kind) as validator:
            self.assertNotEqual(validator, None)

            res = validator.validate(problem, plan)
            self.assertEqual(res.status, up.engines.ValidationResultStatus.VALID)

            plan = up.plans.SequentialPlan([])
            res = validator.validate(problem, plan)
            self.assertEqual(res.status, up.engines.ValidationResultStatus.INVALID)

    @skipIfNoPlanValidatorForProblemKind(classical_kind)
    def test_robot_loader(self):
        example = self.problems["robot_loader"]
        problem, plan = example.problem, example.valid_plans[0]

        with PlanValidator(problem_kind=problem.kind, plan_kind=plan.kind) as validator:
            self.assertNotEqual(validator, None)

            res = validator.validate(problem, plan)
            self.assertEqual(res.status, up.engines.ValidationResultStatus.VALID)

            plan = up.plans.SequentialPlan([])
            res = validator.validate(problem, plan)
            self.assertEqual(res.status, up.engines.ValidationResultStatus.INVALID)

    @skipIfNoPlanValidatorForProblemKind(classical_kind)
    def test_robot_loader_adv(self):
        example = self.problems["robot_loader_adv"]
        problem, plan = example.problem, example.valid_plans[0]

        with PlanValidator(problem_kind=problem.kind, plan_kind=plan.kind) as validator:
            self.assertNotEqual(validator, None)

            res = validator.validate(problem, plan)
            self.assertEqual(res.status, up.engines.ValidationResultStatus.VALID)

            plan = up.plans.SequentialPlan([])
            res = validator.validate(problem, plan)
            self.assertEqual(res.status, up.engines.ValidationResultStatus.INVALID)

    def test_invalid_report(self):
        example = self.problems["travel"]
        problem, plan = example.problem, example.valid_plans[0]
        up_validator = SequentialPlanValidator()

        # without the last action the goal fails.
        failed_goal_plan = SequentialPlan([*plan.actions[:-1]])
        res = up_validator.validate(problem, failed_goal_plan)
        self.assertEqual(res.reason, FailedValidationReason.UNSATISFIED_GOALS)

        # add an invalid action to the plan
        move = problem.action("move")
        l1 = problem.object("l1")
        l2 = problem.object("l2")
        invalid_action = ActionInstance(move, (ObjectExp(l2), ObjectExp(l1)))
        actions = [*plan.actions]
        actions.append(invalid_action)
        invalid_action_plan = SequentialPlan(actions)
        res = up_validator.validate(problem, invalid_action_plan)
        self.assertEqual(res.reason, FailedValidationReason.INAPPLICABLE_ACTION)
        self.assertEqual(res.inapplicable_action, invalid_action)


if __name__ == "__main__":
    main()
