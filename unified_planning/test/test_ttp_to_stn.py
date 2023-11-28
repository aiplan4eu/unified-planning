from unified_planning.shortcuts import *

from unified_planning.plans.ttp_to_stn import *
from unified_planning.test.examples import get_example_problems
from unified_planning.test import unittest_TestCase


class TestTTPToSTN(unittest_TestCase):
    def setUp(self) -> None:
        unittest_TestCase.setUp(self)
        problems = get_example_problems()
        self.problem = problems["matchcellar"].problem
        with OneshotPlanner(problem_kind=self.problem.kind) as planner:
            self.plan = planner.solve(self.problem).plan
        print("PLAN :", self.plan)

    def test_matchcellar_to_stn(self):
        self.ttp_to_stn = TTP_to_STN(self.plan, self.problem)

        self.ttp_to_stn.run()

        # Each actions has start and end in the stn plus Start and End's nodes
        self.assertTrue(
            len(self.ttp_to_stn.stn) == len(self.plan.timed_actions) * 2 + 2
        )
