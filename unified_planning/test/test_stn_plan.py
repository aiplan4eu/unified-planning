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


from typing import Set, cast, List, Tuple, Dict
from numbers import Real as RealNumbers
import unified_planning as up
from unified_planning.shortcuts import *
from unified_planning.test import unittest_TestCase
from unified_planning.plans import *
from unified_planning.test.examples import get_example_problems


class TestSTNPlan(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_constraints(self):
        action_1 = DurativeAction("1")
        action_2 = DurativeAction("2")
        action_3 = DurativeAction("3")

        ai_1 = ActionInstance(action_1)
        ai_2 = ActionInstance(action_2)
        ai_3 = ActionInstance(action_3)

        start_plan = STNPlanNode(TimepointKind.GLOBAL_START)
        end_plan = STNPlanNode(TimepointKind.GLOBAL_END)
        ai_1_s = STNPlanNode(TimepointKind.START, ai_1)
        ai_1_e = STNPlanNode(TimepointKind.END, ai_1)
        ai_2_s = STNPlanNode(TimepointKind.START, ai_2)
        ai_2_e = STNPlanNode(TimepointKind.END, ai_2)
        ai_3_s = STNPlanNode(TimepointKind.START, ai_3)
        ai_3_e = STNPlanNode(TimepointKind.END, ai_3)

        constraints: Dict[
            STNPlanNode, List[Tuple[Optional[int], Optional[int], STNPlanNode]]
        ] = {}
        constraints[start_plan] = [(None, 1, ai_1_s)]
        constraints[ai_1_s] = [(None, 2, ai_2_s), (5, None, ai_3_s)]
        constraints[ai_2_s] = [(3, 3, ai_1_e), (None, 4, ai_2_e), (None, 5, ai_3_s)]
        constraints[ai_1_e] = [(None, 2, end_plan)]
        constraints[ai_2_e] = [(None, 6, ai_3_e)]
        constraints[ai_3_s] = [(None, 6, ai_3_e)]
        constraints[ai_3_e] = [(None, 7, end_plan)]

        plan = STNPlan(
            cast(
                Dict[
                    STNPlanNode,
                    List[
                        Tuple[Optional[RealNumbers], Optional[RealNumbers], STNPlanNode]
                    ],
                ],
                constraints,
            )
        )

        self.assertTrue(plan.is_consistent())
        # start_plan is linked to every node in it's constraints (the 8), every node is
        # linked to end_plan in it's constraints (the +1), unless it was already in it's
        # constraints (ai_1_e and ai_3_e), end_plan is linked to himself in it's
        # constraints (the 1)
        expected_len: Dict[STNPlanNode, int] = {
            start_plan: 7,
            ai_1_s: len(constraints[ai_1_s]) + 1,
            ai_2_s: len(constraints[ai_2_s]) + 1,
            ai_3_s: len(constraints[ai_3_s]) + 1,
            ai_1_e: len(constraints[ai_1_e]),
            ai_2_e: len(constraints[ai_2_e]) + 1,
            ai_3_e: len(constraints[ai_3_e]),
            end_plan: 1,
        }
        plan_constraints = plan.get_constraints()
        # seen_couples is used to prove that there are no duplicates in the constraints
        seen_couples: Set[Tuple[STNPlanNode, STNPlanNode]] = set()
        for left_node, cl in plan_constraints.items():
            self.assertEqual(len(cl), expected_len[left_node])
            for _, _, right_node in cl:
                test_1 = (left_node, right_node)
                test_2 = (right_node, left_node)
                self.assertFalse(test_1 in seen_couples or test_2 in seen_couples)
                seen_couples.add(test_1)
                seen_couples.add(test_2)

        # remove ai_1
        def replace_function(
            action_instance: ActionInstance,
        ) -> Optional[ActionInstance]:
            if action_instance.is_semantically_equivalent(ai_1):
                return None
            return action_instance

        new_plan = plan.replace_action_instances(replace_function)
        assert isinstance(new_plan, STNPlan)
        self.assertTrue(new_plan.is_consistent())
        # new constraints considering ai_1 is removed
        # only constraints that are not in the original map are commented,
        # considering that the original map has added constraints where
        # low(start_plan, ANY) = 0 and low(ANY, end_plan) = 0, meaning that nothing
        # comes before start_plan or after end_plan
        expected_new_constraints: Dict[
            Tuple[STNPlanNode, STNPlanNode], Tuple[Optional[int], Optional[int]]
        ] = {
            (start_plan, ai_2_s): (
                0,
                3,
            ),  # 3 = 1+2 = up(start_plan, ai_1_s) + up(ai_1_s, ai_2_s)
            (start_plan, ai_3_s): (
                5,
                None,
            ),  # 5 = 0+5 = low(start_plan, ai_1_s) + low(ai_1_s, ai_3_s)
            (start_plan, ai_2_e): (0, None),
            (start_plan, ai_3_e): (0, None),
            (start_plan, end_plan): (0, None),
            (ai_2_s, ai_3_s): (
                3,
                5,
            ),  # 3 = 5-2 = low(ai_1_s, ai_3_s) - up(ai_1_s, ai_2_s)
            (ai_2_s, ai_2_e): (None, 4),
            (ai_2_s, end_plan): (
                3,
                5,
            ),  # 3 = 3+0 = low(ai_2_s, ai_3_e) + low(ai_1_e, end_plan)
            # 5 = 3+2 = up(ai_2_s, ai_3_e) + up(ai_1_e, end_plan)
            (ai_3_s, ai_3_e): (None, 6),
            (ai_3_s, end_plan): (0, None),
            (ai_2_e, ai_3_e): (None, 6),
            (ai_2_e, end_plan): (0, None),
            (ai_3_e, end_plan): (0, 7),
        }
        counter = 0
        for left_node, cl in new_plan.get_constraints().items():
            for low, up, right_node in cl:
                if left_node == right_node:
                    continue
                self.assertEqual(
                    (low, up), expected_new_constraints[left_node, right_node]
                )
                counter += 1
        self.assertEqual(counter, len(expected_new_constraints))
