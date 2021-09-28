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
        plan_a = self.client(problem)
        with OneshotPlanner(name='tamer', params={'weight': 0.8}) as planner:
            plan_b = planner.solve(problem)

        self.assertEqual(str(plan_a), str(plan_b)) # TODO: Should this work without str()?

    def test_robot(self):
        problem = self.ps['robot'].problem
        plan_a = self.client(problem)
        with OneshotPlanner(name='tamer', params={'weight': 0.8}) as planner:
            plan_b = planner.solve(problem)

        assert(str(plan_a) == str(plan_b)) # TODO: Should this work without str()?

    def test_robot_loader(self):
        problem = self.ps['robot_loader'].problem
        plan_a = self.client(problem)
        with OneshotPlanner(name='tamer', params={'weight': 0.8}) as planner:
            plan_b = planner.solve(problem)

        assert(str(plan_a) == str(plan_b)) # TODO: Should this work without str()?

    def test_robot_loader_adv(self):
        problem = self.ps['robot_loader_adv'].problem
        plan_a = self.client(problem)
        with OneshotPlanner(name='tamer', params={'weight': 0.8}) as planner:
            plan_b = planner.solve(problem)

        assert(str(plan_a) == str(plan_b)) # TODO: Should this work without str()?


