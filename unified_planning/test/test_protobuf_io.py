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
# limitations under the License

import os
import tempfile
from typing import cast
import pytest
import unified_planning
from unified_planning.shortcuts import *
from unified_planning.test import TestCase, main
from unified_planning.grpc.proto_reader import ProtobufReader
from unified_planning.grpc.proto_writer import ProtobufWriter
from unified_planning.test.examples import get_example_problems
from unified_planning.model.types import _UserType
import unified_planning.grpc.generated.unified_planning_pb2 as up_pb2


class TestProtobufIO(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()
        self.pb_writer = ProtobufWriter()
        self.pb_reader = ProtobufReader()


    def test_fluent(self):
        problem = Problem("test")
        x = Fluent("x")

        x_pb = self.pb_writer.convert(x)

        self.assertTrue(x_pb.name == "x")
        self.assertTrue(x_pb.value_type == "bool")

        x_up = self.pb_reader.convert(x_pb, problem)

        self.assertTrue(x_up.name() == "x")
        self.assertTrue(str(x_up.type()) == "bool")

    def test_expression(self):
        problem = Problem("test")
        ex = problem.env.expression_manager.true_expression

        ex_pb = self.pb_writer.convert(ex)
        self.assertTrue(ex_pb.type == "BOOL_CONSTANT")
        self.assertTrue(ex_pb.kind == up_pb2.ExpressionKind.Value("CONSTANT"))

        ex_up = self.pb_reader.convert(ex_pb, problem, {})
        self.assertTrue(ex == ex_up)

        ex = problem.env.expression_manager.Int(10)

        ex_pb = self.pb_writer.convert(ex)
        self.assertTrue(ex_pb.type == "INT_CONSTANT")
        self.assertTrue(ex_pb.kind == up_pb2.ExpressionKind.Value("CONSTANT"))

        ex_up = self.pb_reader.convert(ex_pb, problem, {})
        self.assertTrue(ex == ex_up)

    def test_type_declaration(self):
        problem = Problem("test")
        ex = BoolType()
        ex_pb = self.pb_writer.convert(ex)
        ex_up = self.pb_reader.convert(ex_pb)
        self.assertTrue(ex == ex_up)

        ex = UserType("location", UserType("object"))
        ex_pb = self.pb_writer.convert(ex)
        ex_up = self.pb_reader.convert(ex_pb)
        self.assertTrue(ex == ex_up)

    def test_object_declaration(self):
        problem = Problem("test")

        loc_type = UserType("location")
        obj = Object("l1", loc_type)
        obj_pb = self.pb_writer.convert(obj)
        obj_up = self.pb_reader.convert(obj_pb, problem)
        self.assertTrue(obj == obj_up)

    # TODO: Next convert back with reader

    # def test_basic_writer(self):
    #     problem = self.problems['basic'].problem
    #
    #     w = PDDLWriter(problem)
    #
    #
    #
    # def test_basic_conditional_writer(self):
    #     problem = self.problems['basic_conditional'].problem
    #
    #     w = PDDLWriter(problem)
    #
    #
    # def test_basic_exists_writer(self):
    #     problem = self.problems['basic_exists'].problem
    #
    #     w = PDDLWriter(problem)
    #
    #
    #
    # def test_robot_writer(self):
    #     problem = self.problems['robot'].problem
    #
    #     w = PDDLWriter(problem)
    #
    #
    #
    # def test_robot_decrease_writer(self):
    #     problem = self.problems['robot_decrease'].problem
    #
    #     w = PDDLWriter(problem)
    #
    #
    # def test_robot_loader_writer(self):
    #     problem = self.problems['robot_loader'].problem
    #
    #     w = PDDLWriter(problem)
    #
    #
    # def test_robot_loader_adv_writer(self):
    #     problem = self.problems['robot_loader_adv'].problem
    #
    #     w = PDDLWriter(problem)
    #
    #
    #
    # def test_matchcellar_writer(self):
    #     problem = self.problems['matchcellar'].problem
    #
    #     w = PDDLWriter(problem)

