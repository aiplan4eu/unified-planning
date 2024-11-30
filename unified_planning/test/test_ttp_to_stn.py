from itertools import chain
from unified_planning.shortcuts import *
from unified_planning.model.problem_kind import (
    temporal_kind,
    classical_kind,
    int_duration_kind,
)
from unified_planning.plans import TimeTriggeredPlan
from unified_planning.test.examples import get_example_problems
from unified_planning.test import unittest_TestCase
from unified_planning.test import (
    skipIfNoPlanValidatorForProblemKind,
    skipIfNoOneshotPlannerForProblemKind,
)


up.shortcuts.get_environment().credits_stream = None


def simultaneity_problem() -> Problem:
    problem = Problem("test_simultaneity")
    x = problem.add_fluent("x", default_initial_value=True)
    y = problem.add_fluent("y", default_initial_value=True)
    z = problem.add_fluent("z", default_initial_value=True)
    k = problem.add_fluent("k", default_initial_value=False)

    problem.add_timed_effect(GlobalStartTiming(5), k, True)

    a = DurativeAction("a")
    a.add_condition(ClosedTimeInterval(StartTiming(), EndTiming()), y)
    a.add_condition(TimePointInterval(StartTiming()), k)
    a.add_effect(EndTiming(), x, False)
    a.set_fixed_duration(1)
    problem.add_action(a)

    b = DurativeAction("b")
    b.add_condition(ClosedTimeInterval(StartTiming(), EndTiming()), x)
    b.add_effect(EndTiming(), y, False)
    b.set_fixed_duration(1)
    problem.add_action(b)

    c = DurativeAction("c")
    c.add_condition(ClosedTimeInterval(StartTiming(), EndTiming()), z)
    c.add_effect(EndTiming(), z, False)
    c.set_fixed_duration(1)
    problem.add_action(c)

    problem.add_goal(Not(x))
    problem.add_goal(Not(y))
    problem.add_goal(Not(z))
    problem.add_goal(k)

    return problem


sim_problem = simultaneity_problem()


class TestTTPToSTN(unittest_TestCase):
    def setUp(self) -> None:
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfNoOneshotPlannerForProblemKind(
        classical_kind.union(temporal_kind).union(int_duration_kind)
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

    @skipIfNoPlanValidatorForProblemKind(sim_problem.kind)
    def test_simultaneity(self):
        a = sim_problem.action("a")
        b = sim_problem.action("b")
        c = sim_problem.action("c")

        st = Fraction(6)
        dur = Fraction(1)
        action_instances = (a(), b(), c())
        valid_plan = TimeTriggeredPlan([(st, act, dur) for act in action_instances])
        stn_plan = valid_plan.convert_to(PlanKind.STN_PLAN, sim_problem)
        tt_plan = stn_plan.convert_to(PlanKind.TIME_TRIGGERED_PLAN, sim_problem)
        with PlanValidator(
            problem_kind=sim_problem.kind, plan_kind=tt_plan.kind
        ) as validator:
            val_res = validator.validate(sim_problem, tt_plan)
            self.assertTrue(val_res)
