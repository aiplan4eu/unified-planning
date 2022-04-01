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
        ex_up = self.pb_reader.convert(ex_pb, problem)
        self.assertTrue(ex == ex_up)

        ex = problem.env.expression_manager.Int(10)
        ex_pb = self.pb_writer.convert(ex)
        ex_up = self.pb_reader.convert(ex_pb, problem)
        self.assertTrue(ex == ex_up)

    def test_not_expression(self):
        x = Fluent('x')
        problem = Problem('basic')
        problem.add_fluent(x)

        ex = Not(x)
        ex_pb = self.pb_writer.convert(ex)
        print(ex_pb)
        ex_up = self.pb_reader.convert(ex_pb, problem)
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

    def test_basic_action(self):
        problem = self.problems['basic'].problem
        a = problem.action('a')
        a_pb = self.pb_writer.convert(a)
        a_up = self.pb_reader.convert(a_pb, problem)
        self.assertEqual(a, a_up)

    def test_simple_problem(self):
        x = Fluent('x')
        a = InstantaneousAction('a')
        a.add_precondition(Not(x))
        a.add_effect(x, True)
        problem = Problem('basic')
        problem.add_fluent(x)
        problem.add_action(a)
        problem.set_initial_value(x, False)
        problem.add_goal(x)

        p_pb = self.pb_writer.convert(problem)
        p_up = self.pb_reader.convert(p_pb)

        print(problem)
        print("---------------") # TODO: Precondition comes back without "not"
        print(p_up)

        self.assertEqual(problem, p_up)

    def test_durative_action(self):
        match_cellar = self.problems['matchcellar'].problem
        mend_fuse = match_cellar.action('mend_fuse')
        eff = mend_fuse.effects()[EndTiming()][0]
        eff_fluent = eff.fluent()
        eff_fluent_pb = self.pb_writer.convert(eff_fluent)
        self.pb_reader.current_action = mend_fuse
        eff_fluent_up = self.pb_reader.convert(eff_fluent_pb, match_cellar)
        self.assertEqual(eff_fluent, eff_fluent_up)
        a_pb = self.pb_writer.convert(mend_fuse)
        a_up = self.pb_reader.convert(a_pb, match_cellar)
        self.assertEqual(mend_fuse, a_up)


    def test_durative_problem(self):
        match_cellar = self.problems['matchcellar'].problem
        p_pb = self.pb_writer.convert(match_cellar)
        p_up = self.pb_reader.convert(p_pb)
        self.assertEqual(match_cellar, p_up)


