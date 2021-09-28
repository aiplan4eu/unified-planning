from upf.test import TestCase

from upf.test.examples import get_example_problems

from upf.grpc.factory import ProtoFactory

class TestProtobufFactory(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.ps = get_example_problems()
        self.factory = ProtoFactory()

    def test_basic(self):
        problem = self.ps['basic'].problem
        msg = self.factory .problem2message(problem)
        problem_ret = self.factory .message2problem(msg)
        assert(str(problem) == str(problem_ret))
        
    def test_robot(self):
        problem = self.ps['robot'].problem
        msg = self.factory.problem2message(problem)
        problem_ret = self.factory.message2problem(msg)
        assert(str(problem) == str(problem_ret))
        
    def test_robot_loader(self):
        problem = self.ps['robot_loader'].problem
        msg = self.factory.problem2message(problem)
        problem_ret = self.factory.message2problem(msg)
        assert(str(problem) == str(problem_ret))

    def test_robot_loader_adv(self):
        problem = self.ps['robot_loader_adv'].problem
        msg = self.factory.problem2message(problem)
        problem_ret = self.factory.message2problem(msg)
        assert(str(problem) == str(problem_ret))
