# In this problem, one can either apply a single action for high cost
# or instead 3 actions for overall lower cost.

import unified_planning
from unified_planning.shortcuts import *
from unified_planning.model.metrics import (
    MinimizeActionCosts,
    MinimizeSequentialPlanLength,
)
from unified_planning.test import TestCase


def get_test_cases():
    res = {}

    # base problem, metrics added later
    x = Fluent("x")
    y = Fluent("y")
    g = Fluent("g")
    a_exp = InstantaneousAction("o_expensive")
    a_exp.add_effect(g, True)
    a_cheap_1 = InstantaneousAction("o_cheap_1")
    a_cheap_1.add_effect(x, True)
    a_cheap_2 = InstantaneousAction("o_cheap_2")
    a_cheap_2.add_precondition(x)
    a_cheap_2.add_effect(y, True)
    a_cheap_3 = InstantaneousAction("o_cheap_3")
    a_cheap_3.add_precondition(y)
    a_cheap_3.add_effect(g, True)
    base_problem = Problem("metric_impact")
    base_problem.add_fluent(x)
    base_problem.add_fluent(y)
    base_problem.add_fluent(g)
    base_problem.add_action(a_exp)
    base_problem.add_action(a_cheap_1)
    base_problem.add_action(a_cheap_2)
    base_problem.add_action(a_cheap_3)
    base_problem.set_initial_value(g, False)
    base_problem.set_initial_value(x, False)
    base_problem.set_initial_value(y, False)
    base_problem.add_goal(g)

    # cheap expensive action_costs
    action_costs_problem = base_problem.clone()
    action_costs_problem.name = "cheap expensive action_costs"
    costs: Dict[Action, Expression] = {
        a_exp: Int(5),
        a_cheap_1: Int(1),
        a_cheap_2: Int(1),
        a_cheap_3: Int(2),
    }
    action_costs_problem.add_quality_metric(MinimizeActionCosts(costs, 1))

    # TODO add plans
    res[action_costs_problem.name] = TestCase(
        problem=action_costs_problem, solvable=True, optimum=4
    )

    # cheap expensive plan_length
    plan_length_problem = base_problem.clone()
    plan_length_problem.name = "cheap expensive plan_length"
    plan_length_problem.add_quality_metric(MinimizeSequentialPlanLength())

    # TODO add plans
    res[plan_length_problem.name] = TestCase(
        problem=plan_length_problem, solvable=True, optimum=1
    )
    return res
