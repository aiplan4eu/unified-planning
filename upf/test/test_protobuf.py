from upf.test import TestCase

from upf.test.examples import get_example_problems

from upf.grpc.factory import FromProtobufConverter, ToProtobufConverter


class TestProtobufFactory(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.ps = get_example_problems()
        self.from_protobuf = FromProtobufConverter()
        self.to_protobuf = ToProtobufConverter()

    def test_basic(self):
        problem = self.ps['basic'].problem
        msg = self.to_protobuf.convert(problem)
        problem_ret = self.from_protobuf.convert(msg)
        assert(str(problem) == str(problem_ret))

    def test_robot(self):
        problem = self.ps['robot'].problem
        msg = self.to_protobuf.convert(problem)
        problem_ret = self.from_protobuf.convert(msg)
        assert(str(problem) == str(problem_ret))

    def test_robot_loader(self):
        problem = self.ps['robot_loader'].problem
        msg = self.to_protobuf.convert(problem)
        problem_ret = self.from_protobuf.convert(msg)
        assert(str(problem) == str(problem_ret))

    def test_robot_loader_adv(self):
        problem = self.ps['robot_loader_adv'].problem
        msg = self.to_protobuf.convert(problem)
        problem_ret = self.from_protobuf.convert(msg)
        assert(str(problem) == str(problem_ret))
