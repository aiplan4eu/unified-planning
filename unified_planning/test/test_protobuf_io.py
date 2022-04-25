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

import pytest
from unified_planning.model.metrics import *
from unified_planning.shortcuts import *
from unified_planning.solvers.results import PlanGenerationResultStatus
from unified_planning.test import TestCase, skipIfSolverNotAvailable
from unified_planning.grpc.proto_reader import ProtobufReader
from unified_planning.grpc.proto_writer import ProtobufWriter
from unified_planning.test.examples import get_example_problems
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

        self.assertTrue(x_up.name == "x")
        self.assertTrue(str(x_up.type) == "bool")

    def test_fluent_2(self):
        problem = self.problems["robot"].problem

        for f in problem.fluents:
            f_pb = self.pb_writer.convert(f)
            f_up = self.pb_reader.convert(f_pb, problem)
            self.assertTrue(f == f_up)

    def test_expression(self):
        problem = Problem("test")
        ex = problem.env.expression_manager.true_expression

        ex_pb = self.pb_writer.convert(ex)
        ex_up = self.pb_reader.convert(ex_pb, problem, {})
        self.assertTrue(ex == ex_up)

        ex = problem.env.expression_manager.Int(10)

        ex_pb = self.pb_writer.convert(ex)
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

    def test_durative_action(self):
        problem = self.problems["matchcellar"].problem
        action = problem.action("mend_fuse")

        action_pb = self.pb_writer.convert(action)
        action_up = self.pb_reader.convert(action_pb, problem)

        self.assertTrue(action == action_up)

    def test_action_instance(self):
        problem = self.problems["robot"].problem
        plan = self.problems["robot"].plan
        action_instance = plan.actions[0]

        action_instance_pb = self.pb_writer.convert(action_instance)
        action_instance_up = self.pb_reader.convert(action_instance_pb, problem)

        self.assertTrue(action_instance == action_instance_up)

    def test_plan(self):
        problem = self.problems["robot"].problem
        plan = self.problems["robot"].plan

        plan_pb = self.pb_writer.convert(plan)
        plan_up = self.pb_reader.convert(plan_pb, problem)

        self.assertTrue(plan == plan_up)

    def test_time_triggered_plan(self):
        problem = self.problems["temporal_conditional"].problem
        plan = self.problems["temporal_conditional"].plan

        plan_pb = self.pb_writer.convert(plan)
        plan_up = self.pb_reader.convert(plan_pb, problem)

        self.assertTrue(plan == plan_up)

    def test_metric(self):
        problem = Problem("test")
        problem.add_quality_metric(metric=MinimizeSequentialPlanLength())
        problem.add_quality_metric(metric=MinimizeMakespan())

        for metric in problem.quality_metrics:
            metric_pb = self.pb_writer.convert(metric)
            metric_up = self.pb_reader.convert(metric_pb, problem, [])

            self.assertTrue(str(metric) == str(metric_up))  # FIXME: compare metrics

    @pytest.mark.skip("Metrics and logs in result object are not supported yet")
    @skipIfSolverNotAvailable("tamer")
    def test_plan_generation(self):
        problem = self.problems["robot"].problem

        with OneshotPlanner(name="tamer", params={"weight": 0.8}) as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)

            final_report_pb = self.pb_writer.convert(final_report)
            final_report_up = self.pb_reader.convert(final_report_pb, problem)

            self.assertTrue(final_report == final_report_up)


class TestProtobufProblems:
    problems = get_example_problems()
    pb_writer = ProtobufWriter()
    pb_reader = ProtobufReader()

    @pytest.mark.parametrize("problem_name", list(get_example_problems().keys()))
    def test_all_problems(self, problem_name):
        # FIXME: Int types are not added to user types in the base problem
        # Unable to handle variable expressions
        # HACK: skip the test for now
        if problem_name in [
            "robot_int_battery",
            "robot_fluent_of_user_type_with_int_id",
            "basic_exists",
            "basic_forall",
            "robot_locations_connected",
            "robot_locations_visited",
            "timed_connected_locations",
            "hierarchical_blocks_world",
            "robot_locations_connected_without_battery",
            "hierarchical_blocks_world_exists",
            "hierarchical_blocks_world_object_as_root",
            "hierarchical_blocks_world_with_object",
        ]:
            pytest.skip("Internal problem")

        problem = self.problems[problem_name].problem
        problem_pb = self.pb_writer.convert(problem)
        problem_up = self.pb_reader.convert(problem_pb, problem)

        assert problem == problem_up

    @pytest.mark.parametrize("problem_name", list(get_example_problems().keys()))
    def test_all_plans(self, problem_name):
        if problem_name in [
            "robot_fluent_of_user_type_with_int_id",
        ]:
            pytest.skip("Internal problem")
        problem = self.problems[problem_name].problem
        plan = self.problems[problem_name].plan
        plan_pb = self.pb_writer.convert(plan)
        plan_up = self.pb_reader.convert(plan_pb, problem)

        assert plan == plan_up

    @pytest.mark.skip("Metrics and logs in result object are not supported yet")
    @skipIfSolverNotAvailable("tamer")
    def test_some_plan_generations(self):
        problems = [
            "basic",
            "basic_without_negative_preconditions",
            "basic_nested_conjunctions",
            "robot_loader",
            "robot_loader_mod",
            "robot_loader_adv",
            "robot_real_constants",
            "robot_int_battery",
            "robot",
        ]
        for p in problems:
            problem = self.problems[p].problem

            with OneshotPlanner(name="tamer", params={"weight": 0.8}) as planner:
                self.assertNotEqual(planner, None)
                final_report = planner.solve(problem)

                final_report_pb = self.pb_writer.convert(final_report)
                final_report_up = self.pb_reader.convert(final_report_pb, problem)

                self.assertTrue(final_report == final_report_up)
