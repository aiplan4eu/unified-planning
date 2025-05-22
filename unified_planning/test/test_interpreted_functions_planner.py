# Copyright 2024 Unified Planning library and its maintainers
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
from unified_planning.test import skipIfEngineNotAvailable, unittest_TestCase
from unified_planning.test.examples import get_example_problems


class TestInterpretedFunctionsPlanner(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_interpreted_functions_in_preconditions_planner_always_impossible(self):
        problem = self.problems[
            "interpreted_functions_in_conditions_always_impossible"
        ].problem
        self.assertTrue(problem.kind.has_interpreted_functions_in_conditions())
        self.assertFalse(problem.kind.has_simple_numeric_planning())

        with OneshotPlanner(
            name="interpreted_functions_planning[opt-pddl-planner]"
        ) as planner:
            planner.skip_checks = True  # enhsp does not like bounded fluents but it does not make any difference here
            result = planner.solve(problem)

        self.assertFalse(result.status in up.engines.results.POSITIVE_OUTCOMES)

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_interpreted_functions_planner_int_assignment(self):
        problem = self.problems["interpreted_functions_in_numeric_assignment"].problem
        self.assertTrue(problem.kind.has_interpreted_functions_in_numeric_assignments())

        with OneshotPlanner(
            name="interpreted_functions_planning[opt-pddl-planner]"
        ) as planner:
            planner.skip_checks = True  # enhsp does not like bounded fluents but it does not make any difference here

            result = planner.solve(problem)

        self.assertTrue(result.status in up.engines.results.POSITIVE_OUTCOMES)

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_interpreted_functions_in_preconditions(self):
        testproblem = self.problems["interpreted_functions_in_conditions"]
        problem = testproblem.problem
        with OneshotPlanner(
            name="interpreted_functions_planning[opt-pddl-planner]"
        ) as planner:
            planner.skip_checks = True  # enhsp does not like bounded fluents but it does not make any difference here
            result = planner.solve(problem)
        self.assertEqual(len(result.plan.actions), 2)
        self.assertEqual(result.plan.actions[0].action, problem.actions[0])
        self.assertEqual(result.plan.actions[1].action, problem.actions[1])
        self.assertTrue(result.status in up.engines.results.POSITIVE_OUTCOMES)

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_interpreted_functions_assignment_chain_minimal(self):
        testproblem = self.problems[
            "interpreted_functions_minimal_chain_of_assignments"
        ]
        problem = testproblem.problem
        with OneshotPlanner(
            name="interpreted_functions_planning[opt-pddl-planner]"
        ) as planner:
            planner.skip_checks = True  # enhsp does not like bounded fluents but it does not make any difference here
            result = planner.solve(problem)
        self.assertTrue(result.status in up.engines.results.POSITIVE_OUTCOMES)
        self.assertEqual(len(result.plan.actions), 3)
        self.assertEqual(result.plan.actions[0].action, problem.actions[0])
        self.assertEqual(result.plan.actions[1].action, problem.actions[1])
        self.assertEqual(result.plan.actions[2].action, problem.actions[2])

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_interpreted_functions_in_preconditions_planner_complex(self):
        testproblem = self.problems["IF_in_conditions_complex_1"]
        problem = testproblem.problem
        self.assertTrue(problem.kind.has_interpreted_functions_in_conditions())
        self.assertFalse(problem.kind.has_simple_numeric_planning())

        with OneshotPlanner(
            name="interpreted_functions_planning[opt-pddl-planner]"
        ) as planner:
            planner.skip_checks = True  # enhsp does not like bounded fluents but it does not make any difference here
            result = planner.solve(problem)
        self.assertTrue(result.status in up.engines.results.POSITIVE_OUTCOMES)
        self.assertEqual(
            len(result.plan.actions), len(testproblem.valid_plans[0].actions)
        )
        i = 0
        while i < len(testproblem.valid_plans[0].actions):
            self.assertEqual(
                result.plan.actions[i].action,
                testproblem.valid_plans[0].actions[i].action,
            )

            i = i + 1

    @skipIfEngineNotAvailable("opt-pddl-planner")
    def test_interpreted_functions_reals(self):
        testproblem = self.problems["if_reals_condition_effect_pizza"]
        problem = testproblem.problem
        with OneshotPlanner(
            name="interpreted_functions_planning[opt-pddl-planner]"
        ) as planner:
            planner.skip_checks = True  # enhsp does not like bounded fluents but it does not make any difference here
            result = planner.solve(problem)
        self.assertTrue(result.status in up.engines.results.POSITIVE_OUTCOMES)
        self.assertEqual(
            len(result.plan.actions), len(testproblem.valid_plans[0].actions)
        )

    @skipIfEngineNotAvailable("tamer")
    def test_interpreted_functions_in_durations_planner(self):
        testproblem = self.problems["go_home_with_rain_and_interpreted_functions"]
        problem = testproblem.problem

        with OneshotPlanner(name="interpreted_functions_planning[tamer]") as planner:
            result = planner.solve(problem)

        self.assertTrue(result.status in up.engines.results.POSITIVE_OUTCOMES)
        self.assertEqual(len(result.plan._actions), 2)
        i = 0
        while i < len(testproblem.valid_plans[0].timed_actions):
            j = 0
            while j < 3:
                # the result tuple has 3 values: start time, action, duration
                if j != 1:
                    self.assertEqual(
                        result.plan.timed_actions[i][j],
                        testproblem.valid_plans[0].timed_actions[i][j],
                    )
                else:
                    # when checking for the action it needs a different syntax
                    self.assertEqual(
                        result.plan.timed_actions[i][j].action,
                        testproblem.valid_plans[0].timed_actions[i][j].action,
                    )
                j = j + 1
            i = i + 1

    @skipIfEngineNotAvailable("tamer")
    def test_interpreted_functions_usertype(self):
        testproblem = self.problems["treasure_hunting_robot_simple"]
        problem = testproblem.problem
        with OneshotPlanner(name="interpreted_functions_planning[tamer]") as planner:
            planner.skip_checks = True  # enhsp does not like bounded fluents but it does not make any difference here
            result = planner.solve(problem)
        self.assertTrue(result.status in up.engines.results.POSITIVE_OUTCOMES)
        self.assertEqual(
            len(result.plan.actions), len(testproblem.valid_plans[0].actions)
        )
        valid_plan = testproblem.valid_plans[0].actions
        found_plan = result.plan.actions
        for v, f in zip(valid_plan, found_plan):
            self.assertEqual(v.action, f.action)
