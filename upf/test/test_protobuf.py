from upf.test import TestCase

from upf.test.examples import get_example_problems

from upf.grpc.pb_factory import problem2message
from upf.grpc.pb_factory import message2problem


class TestProtobufFactory(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.ps = get_example_problems()

    def test_basic(self):
        problem = self.ps['basic'].problem
        msg = problem2message(problem)
        problem_ret = message2problem(msg)
        assert(str(problem) == str(problem_ret))
        
    def test_robot(self):
        problem = self.ps['robot'].problem
        msg = problem2message(problem)
        problem_ret = message2problem(msg)

        print(problem_ret)
        assert(str(problem) == str(problem_ret))
        
    def test_robot_loader(self):
        problem = self.ps['robot_loader'].problem
        msg = problem2message(problem)
        problem_ret = message2problem(msg)

        print(problem_ret)
        assert(str(problem) == str(problem_ret))

    def test_robot_loader_adv(self):
        problem = self.ps['robot_loader_adv'].problem
        msg = problem2message(problem)
        problem_ret = message2problem(msg)

        print(problem_ret)
        assert(str(problem) == str(problem_ret))
