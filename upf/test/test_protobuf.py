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
