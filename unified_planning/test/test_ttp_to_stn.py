from unified_planning.shortcuts import *

from unified_planning.plans.ttp_to_stn import *
from unified_planning.test.examples import get_example_problems
import pylab
import matplotlib.pyplot as plt
from unified_planning.test import TestCase


class TestTTPToSTN(TestCase):
    def setUp(self) -> None:
        TestCase.setUp(self)
        problems = get_example_problems()
        self.problem = problems["matchcellar"].problem
        with OneshotPlanner(problem_kind=self.problem.kind) as planner:
            self.plan = planner.solve(self.problem).plan
        print("PLAN :", self.plan)

    def test_matchcellar_to_stn(self):
        self.ttp_to_stn = TTP_to_STN(self.plan, self.problem)

        self.ttp_to_stn.run()

        options = {
            "node_color": "blue",
            "node_size": 1000,
            "width": 3,
        }
        pos = nx.spring_layout(self.ttp_to_stn.stn)
        edge_labels = dict(
            [
                (
                    (
                        u,
                        v,
                    ),
                    [float(d["interval"][0]), float(d["interval"][1])],
                )
                for u, v, d in self.ttp_to_stn.stn.edges(data=True)
            ]
        )
        nx.draw_networkx_edge_labels(self.ttp_to_stn.stn, pos, edge_labels=edge_labels)
        nx.draw_networkx(
            self.ttp_to_stn.stn,
            pos,
            with_labels=True,
            arrows=True,
            **options,
            edge_cmap=plt.cm.Reds
        )
        # pylab.show()
        # Each actions has start and end in the stn plus Start and End's nodes
        self.assertTrue(
            len(self.ttp_to_stn.stn) == len(self.plan.timed_actions) * 2 + 2
        )
