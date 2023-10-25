#!/usr/bin/env python

from unified_planning.shortcuts import *

up.shortcuts.get_environment().credits_stream = None

from unified_planning.plans.ttp_to_stn import *
from unified_planning.test.examples import get_example_problems
import pylab
import matplotlib.pyplot as plt


if __name__ == "__main__":

    problems = get_example_problems()
    problem = problems["matchcellar"].problem
    with OneshotPlanner(problem_kind=problem.kind) as planner:
        plan = planner.solve(problem).plan
    ttp_to_stn = TTP_to_STN(plan, problem)
    print("PLAN :", plan)
    graph = ttp_to_stn.run()

    options = {
    'node_color': 'blue',
    'node_size': 1000,
    'width': 3,
}
    pos=nx.spring_layout(ttp_to_stn.stn)   
    edge_labels=dict([((u,v,),[float(d['interval'][0]), float(d['interval'][0])])
                 for u,v,d in ttp_to_stn.stn.edges(data=True)])
    nx.draw_networkx_edge_labels(ttp_to_stn.stn, pos, edge_labels=edge_labels)
    nx.draw_networkx(ttp_to_stn.stn, pos, with_labels = True, arrows=True, **options, edge_cmap=plt.cm.Reds)
    pylab.show()

    print("Done...")
