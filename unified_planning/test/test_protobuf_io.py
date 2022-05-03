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
import unified_planning.grpc.generated.unified_planning_pb2 as up_pb2
from unified_planning.grpc.proto_reader import ProtobufReader # type: ignore[attr-defined]
from unified_planning.grpc.proto_writer import ProtobufWriter # type: ignore[attr-defined]
from unified_planning.model.metrics import *
from unified_planning.shortcuts import *
from unified_planning.solvers import LogMessage
from unified_planning.solvers.results import LogLevel, PlanGenerationResultStatus
from unified_planning.test import TestCase, skipIfSolverNotAvailable
from unified_planning.test.examples import get_example_problems


class TestProtobufIO(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()
        self.pb_writer = ProtobufWriter()
        self.pb_reader = ProtobufReader()

    def test_fluent(self):
        problem = Problem("test")
        x = Fluent("x")

        x_pb = self.pb_writer.convert(x, problem)

        self.assertEqual(x_pb.name, "x")
        self.assertEqual(x_pb.value_type, "bool")

        x_up = self.pb_reader.convert(x_pb, problem)

        self.assertEqual(x_up.name, "x")
        self.assertEqual(str(x_up.type), "bool")

    def test_fluent_2(self):
        problem = self.problems["robot"].problem

        for f in problem.fluents:
            f_pb = self.pb_writer.convert(f, problem)
            f_up = self.pb_reader.convert(f_pb, problem)
            self.assertEqual(f, f_up)

    def test_fluent_3(self):
        """Test to handle subtypes of usertypes of Fluent Expression"""
        problem = self.problems["hierarchical_blocks_world"].problem

        for f in problem.fluents:
            f_pb = self.pb_writer.convert(f, problem)
            f_up = self.pb_reader.convert(f_pb, problem)
            self.assertEqual(f, f_up)

    def test_objects(self):
        """Test to handle subtypes of usertypes of Fluent Expression"""
        problem = self.problems["hierarchical_blocks_world"].problem

        for o in problem.all_objects:
            o_pb = self.pb_writer.convert(o)
            o_up = self.pb_reader.convert(o_pb, problem)

            self.assertEqual(o, o_up)

    def test_expression(self):
        problem = Problem("test")
        ex = problem.env.expression_manager.true_expression

        ex_pb = self.pb_writer.convert(ex)
        ex_up = self.pb_reader.convert(ex_pb, problem)
        self.assertEqual(ex, ex_up)

        ex = problem.env.expression_manager.Int(10)

        ex_pb = self.pb_writer.convert(ex)
        ex_up = self.pb_reader.convert(ex_pb, problem)
        self.assertEqual(ex, ex_up)

    def test_fluent_expressions(self):
        problem = self.problems["hierarchical_blocks_world"].problem

        problem_pb = self.pb_writer.convert(problem)
        problem_up = self.pb_reader.convert(problem_pb)

        self.assertEqual(problem, problem_up)

    def test_type_declaration(self):
        problem = Problem("test")
        ex = UserType("object")
        ex_pb = self.pb_writer.convert(ex)
        ex_up = self.pb_reader.convert(ex_pb, problem)
        self.assertEqual(ex, ex_up)

        o = Object('o', ex)
        problem.add_object(o)

        ex = UserType("location", ex)
        ex_pb = self.pb_writer.convert(ex)
        ex_up = self.pb_reader.convert(ex_pb, problem)
        self.assertEqual(ex, ex_up)

    def test_object_declaration(self):
        problem = Problem("test")

        loc_type = UserType("location")
        obj = Object("l1", loc_type)
        obj_pb = self.pb_writer.convert(obj)
        obj_up = self.pb_reader.convert(obj_pb, problem)
        self.assertEqual(obj, obj_up)

    def test_problem(self):
        problem = self.problems["robot"].problem

        problem_pb = self.pb_writer.convert(problem)
        problem_up = self.pb_reader.convert(problem_pb)

        pb_features = set(
            [up_pb2.Feature.Name(feature) for feature in problem_pb.features]
        )
        self.assertEqual(set(problem.kind.features), pb_features)
        self.assertEqual(problem, problem_up)

    def test_action(self):
        problem = self.problems["robot"].problem
        action = problem.action("move")

        action_pb = self.pb_writer.convert(action)
        action_up = self.pb_reader.convert(action_pb, problem)

        self.assertEqual(action, action_up)

    def test_durative_action(self):
        problem = self.problems["matchcellar"].problem
        action = problem.action("mend_fuse")

        action_pb = self.pb_writer.convert(action)
        action_up = self.pb_reader.convert(action_pb, problem)

        self.assertEqual(action, action_up)

    def test_action_instance(self):
        problem = self.problems["robot"].problem
        plan = self.problems["robot"].plan
        action_instance = plan.actions[0]

        action_instance_pb = self.pb_writer.convert(action_instance)
        action_instance_up = self.pb_reader.convert(action_instance_pb, problem)

        self.assertEqual(action_instance, action_instance_up)

    def test_plan(self):
        problem = self.problems["robot"].problem
        plan = self.problems["robot"].plan

        plan_pb = self.pb_writer.convert(plan)
        plan_up = self.pb_reader.convert(plan_pb, problem)

        self.assertEqual(plan, plan_up)

    def test_time_triggered_plan(self):
        problem = self.problems["temporal_conditional"].problem
        plan = self.problems["temporal_conditional"].plan

        plan_pb = self.pb_writer.convert(plan)
        plan_up = self.pb_reader.convert(plan_pb, problem)

        self.assertEqual(plan, plan_up)

    def test_metric(self):
        problem = Problem("test")
        problem.add_quality_metric(metric=MinimizeSequentialPlanLength())
        problem.add_quality_metric(metric=MinimizeMakespan())
        problem.add_quality_metric(
            metric=MinimizeExpressionOnFinalState(
                problem.env.expression_manager.true_expression
            )
        )
        problem.add_quality_metric(
            metric=MaximizeExpressionOnFinalState(
                problem.env.expression_manager.true_expression
            )
        )

        for metric in problem.quality_metrics:
            metric_pb = self.pb_writer.convert(metric)
            metric_up = self.pb_reader.convert(metric_pb, problem)

            self.assertEqual(str(metric), str(metric_up))

    def test_log_message(self):
        def assert_log(log):
            logger_pb = self.pb_writer.convert(log)
            logger_up = self.pb_reader.convert(logger_pb)
            self.assertEqual(log, logger_up)

        log = LogMessage(LogLevel.DEBUG, "test message")
        assert_log(log)
        log = LogMessage(LogLevel.INFO, "test message")
        assert_log(log)
        log = LogMessage(LogLevel.WARNING, "test message")
        assert_log(log)
        log = LogMessage(LogLevel.ERROR, "test message")
        assert_log(log)

    @skipIfSolverNotAvailable("tamer")
    def test_plan_generation(self):
        problem = self.problems["robot"].problem

        with OneshotPlanner(name="tamer", params={"weight": 0.8}) as planner:
            self.assertNotEqual(planner, None)
            final_report = planner.solve(problem)

            final_report_pb = self.pb_writer.convert(final_report)
            final_report_up = self.pb_reader.convert(final_report_pb, problem)

            self.assertEqual(final_report, final_report_up)

    @skipIfSolverNotAvailable('tarski_grounder')
    def test_grounding_result(self):
        problem, _ = self.problems['hierarchical_blocks_world']
        with Grounder(name='tarski_grounder') as grounder:
            ground_result = grounder.ground(problem)

            ground_result_pb = self.pb_writer.convert(ground_result)
            ground_result_up = self.pb_reader.convert(ground_result_pb)

            self.assertEqual(ground_result, ground_result_up)



class TestProtobufProblems(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()
        self.pb_writer = ProtobufWriter()
        self.pb_reader = ProtobufReader()

    def test_all_problems(self):
        for name, example in self.problems.items():
            problem = example.problem
            problem_pb = self.pb_writer.convert(problem)
            problem_up = self.pb_reader.convert(problem_pb)

            self.assertEqual(problem, problem_up)

    def test_all_plans(self):
        for name, example in self.problems.items():
            problem = example.problem
            plan = example.plan
            plan_pb = self.pb_writer.convert(plan)
            plan_up = self.pb_reader.convert(plan_pb, problem)

            self.assertEqual(plan, plan_up)

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
        for name in problems:
            problem = self.problems[name].problem

            with OneshotPlanner(name='tamer') as planner:
                self.assertNotEqual(planner, None)
                final_report = planner.solve(problem)

                final_report_pb = self.pb_writer.convert(final_report)
                final_report_up = self.pb_reader.convert(final_report_pb, problem)

                self.assertEqual(final_report.status, final_report_up.status)
                self.assertEqual(final_report.plan, final_report_up.plan)
                self.assertEqual(final_report.planner_name, final_report_up.planner_name)
