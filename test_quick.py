#!/usr/bin/env python

from unified_planning.shortcuts import *

up.shortcuts.get_environment().credits_stream = None

from unified_planning.plans.ttp_to_stn import *
from unified_planning.test.examples import get_example_problems


if __name__ == "__main__":

    problems = get_example_problems()
    problem = problems["matchcellar"].problem
    with OneshotPlanner(problem_kind=problem.kind) as planner:
        plan = planner.solve(problem).plan
    ttp_to_stn = TTP_to_STN(plan, problem)
    # ttp_to_stn.get_table_event()
    ttp_to_stn.run()
    print("Done...")
