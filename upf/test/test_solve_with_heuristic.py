import upf
from upf.test import TestCase, main
from upf.test import generate_simple_problem


class GoalCounterHeuristic:
    def __init__(self, size, problem):
        self.size = size
        self.problem = problem

    def __call__(self, state):
        return self.size - len(state & self.problem.goal)


class TestSolveWithHeuristic(TestCase):
    def setUp(self):
        self.size = 14
        self.problem = generate_simple_problem(self.size)

    def test_cppyplanner(self):
        with upf.Planner('upf_cppplanner') as p:
            plan = p.solve(self.problem, GoalCounterHeuristic(self.size, self.problem))
            self.assertEqual(len(plan), self.size*3-1)

    def test_pyplanner(self):
        with upf.Planner('upf_pyplanner') as p:
            plan = p.solve(self.problem, GoalCounterHeuristic(self.size, self.problem))
            self.assertEqual(len(plan), self.size*3-1)


if __name__ == "__main__":
    main()
