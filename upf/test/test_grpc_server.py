from upf.test import TestCase
from upf.shortcuts import *
from upf.test.examples import get_example_problems


class TestProtobufFactory(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        try:
            import grpc
        except ImportError:
            self.skipTest("grpc module not found")
        from upf.grpc.server import UpfGrpcServer
        from upf.grpc.client import UpfGrpcClient

        self.ps = get_example_problems()
        self.server = UpfGrpcServer(30000)
        self.server.start()
        self.client = UpfGrpcClient("localhost", 30000)

    def test_basic(self):
        problem = self.ps['basic'].problem
        plan = self.client(problem)
        with PlanValidator(problem_kind=problem.kind()) as validator:
            res = validator.validate(problem, plan)
            self.assertTrue(res)

    def test_robot(self):
        problem = self.ps['robot'].problem
        plan = self.client(problem)
        with PlanValidator(problem_kind=problem.kind()) as validator:
            res = validator.validate(problem, plan)
            self.assertTrue(res)

    def test_robot_loader(self):
        problem = self.ps['robot_loader'].problem
        plan = self.client(problem)
        with PlanValidator(problem_kind=problem.kind()) as validator:
            res = validator.validate(problem, plan)
            self.assertTrue(res)

    def test_robot_loader_adv(self):
        problem = self.ps['robot_loader_adv'].problem
        plan = self.client(problem)
        with PlanValidator(problem_kind=problem.kind()) as validator:
            res = validator.validate(problem, plan)
            self.assertTrue(res)

