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
from unified_planning.model import problem, problem_kind
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

    @pytest.mark.skip(reason="Not implemented")
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

        # TODO: tests for AtomExpression and sublist expressions

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

    def test_problem(self):
        problem = self.problems["robot"].problem

        problem_pb = self.pb_writer.convert(problem)
        problem_up = self.pb_reader.convert(problem_pb, problem)

        self.assertTrue(problem == problem_up)

    def test_action(self):
        problem = self.problems["robot"].problem
        action = problem.action("move")

        action_pb = self.pb_writer.convert(action)
        action_up = self.pb_reader.convert(action_pb, problem)

        self.assertTrue(action == action_up)

    def test_action_instance(self):
        problem = self.problems["robot"].problem
        plan = self.problems["robot"].plan
        action_instance = plan.actions()[0]

        action_instance_pb = self.pb_writer.convert(action_instance)
        action_instance_up = self.pb_reader.convert(action_instance_pb, problem)

        self.assertTrue(action_instance == action_instance_up)


class TestProblems:
    problems = get_example_problems()
    pb_writer = ProtobufWriter()
    pb_reader = ProtobufReader()

    @pytest.mark.parametrize("problem_name", list(get_example_problems().keys()))
    def test_all_problems(self, problem_name):
        problem = self.problems[problem_name].problem
        problem_pb = self.pb_writer.convert(problem)
        problem_up = self.pb_reader.convert(problem_pb, problem)

        assert problem == problem_up
