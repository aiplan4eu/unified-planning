from itertools import chain
from unified_planning.shortcuts import *

from unified_planning.plans.ttp_to_stn import *
from unified_planning.test.examples import get_example_problems
from unified_planning.test import unittest_TestCase

up.shortcuts.get_environment().credits_stream = None


class TestTTPToSTN(unittest_TestCase):
    def setUp(self) -> None:
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_matchcellar_to_stn(self):
        self.ttp_to_stn = TTP_to_STN(self.plan, self.problem)

        self.ttp_to_stn.run()

        # Each actions has start and end in the stn plus Start and End's nodes
        self.assertTrue(
            len(self.ttp_to_stn.stn) == len(self.plan.timed_actions) * 2 + 2
        )

    def test_matchcellar_to_stn(self):
        problem = self.problems["matchcellar"].problem
        with OneshotPlanner(problem_kind=problem.kind) as planner:
            plan = planner.solve(problem).plan
        stn_plan = plan.convert_to(PlanKind.STN_PLAN, problem)
        self.assertTrue(stn_plan.is_consistent())

        stn_constraints = stn_plan.get_constraints()
        total_stn_nodes = set(
            chain(
                stn_constraints.keys(),
                map(lambda x: x[2], chain(*stn_constraints.values())),
            )
        )
        self.assertEqual(len(total_stn_nodes), len(plan.timed_actions) * 2 + 2)

        ## TEST of the old version:
        ttp_to_stn = TTP_to_STN(plan, problem)

        ttp_to_stn.run()

        # Each actions has start and end in the stn plus Start and End's nodes
        self.assertTrue(len(ttp_to_stn.stn) == len(plan.timed_actions) * 2 + 2)

    def test_all_valid(self):
        for name, tc in self.problems.items():
            for valid_plan in tc.valid_plans:
                if valid_plan.kind == PlanKind.TIME_TRIGGERED_PLAN:
                    stn_plan = valid_plan.convert_to(PlanKind.STN_PLAN, tc.problem)
                    tt_plan = stn_plan.convert_to(
                        PlanKind.TIME_TRIGGERED_PLAN, tc.problem
                    )
                    try:
                        with PlanValidator(
                            problem_kind=tc.problem.kind, plan_kind=tt_plan.kind
                        ) as validator:
                            val_res = validator.validate(tc.problem, tt_plan)
                            self.assertTrue(val_res)
                    except up.exceptions.UPNoSuitableEngineAvailableException as e:
                        pass
