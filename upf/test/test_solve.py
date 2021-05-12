import upf
from upf.test import TestCase, main
from upf.test import generate_simple_problem


class TestSolve(TestCase):
    def setUp(self):
        self.size = 14
        self.problem = generate_simple_problem(self.size)

    def test_cppyplanner(self):
        with upf.Planner('upf_cppplanner') as p:
            plan = p.solve(self.problem)
            self.assertEqual(len(plan), self.size*3-1)

    def test_pyplanner(self):
        with upf.Planner('upf_pyplanner') as p:
            plan = p.solve(self.problem)
            self.assertEqual(len(plan), self.size*3-1)


if __name__ == "__main__":
    main()
