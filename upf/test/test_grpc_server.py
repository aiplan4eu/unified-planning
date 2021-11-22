# Copyright 2021 AIPlan4EU project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from upf.test import TestCase
from upf.shortcuts import *
from upf.test.examples import get_example_problems

from upf.grpc.server import UpfGrpcServer
from upf.grpc.client import UpfGrpcClient

class TestProtobufFactory(TestCase):
    def setUp(self):
        TestCase.setUp(self)
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
