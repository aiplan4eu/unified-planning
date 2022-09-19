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


import unified_planning
from unified_planning.engines.compilers.trajectory_constraints_remover import (
    TrajectoryConstraintsRemover,
)
from unified_planning.model.walkers import Simplifier, ExpressionQuantifiersRemover
from unified_planning.shortcuts import *
from unified_planning.test import TestCase


class TestRemoveQuantifierInTrajConstraint(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        problem = self.define_problem()
        self.simplifier = Simplifier(problem.env)
        self.problem = problem
        self.traj_remover = TrajectoryConstraintsRemover()
        self.traj_remover._expression_quantifier_remover = ExpressionQuantifiersRemover(
            problem.env
        )
        self.traj_remover._problem = self.problem

    def get_all_variable_by_type(self, vars, type):
        vars_to_return = []
        for var in vars:
            if var.type == type:
                vars_to_return.append(var)
        return vars_to_return

    def define_problem(self):
        Location = UserType("Location")
        Robot = UserType("Robot")
        robot_at = unified_planning.model.Fluent("robot_at", BoolType(), l=Location)
        connected = unified_planning.model.Fluent(
            "connected", BoolType(), l_from=Location, l_to=Location
        )
        problem = unified_planning.model.Problem("robot")
        problem.add_fluent(robot_at, default_initial_value=False)
        problem.add_fluent(connected, default_initial_value=False)

        l1 = unified_planning.model.Object("l1", Location)
        l2 = unified_planning.model.Object("l2", Location)
        l3 = unified_planning.model.Object("l3", Location)
        l4 = unified_planning.model.Object("l4", Location)
        r1 = unified_planning.model.Object("r1", Robot)
        r2 = unified_planning.model.Object("r2", Robot)
        problem.add_objects([l1, l2, l3, l4, r1, r2])

        problem.set_initial_value(robot_at(l1), True)
        problem.set_initial_value(connected(l1, l2), True)
        problem.set_initial_value(connected(l2, l3), True)
        problem.set_initial_value(connected(l3, l4), True)
        return problem

    def test_remove_external_forall(self):
        problem = self.problem
        Location = UserType("Location")
        robot_at = unified_planning.model.Fluent("robot_at", BoolType(), l=Location)
        s_loc = Variable("l", Location)
        test_forall = Forall(At_Most_Once(FluentExp(robot_at, [s_loc])), s_loc)
        problem.add_trajectory_constraint(test_forall)
        new_constrs = self.simplifier.simplify(
            And(self.traj_remover._remove_quantifire(problem.trajectory_constraints))
        )
        self.assertTrue(new_constrs.is_and())
        self.assertTrue(
            len(new_constrs.args)
            == len(self.get_all_variable_by_type(problem.all_objects, s_loc.type))
        )
        for const in new_constrs.args:
            self.assertTrue(new_constrs.args.count(const) == 1)
            self.assertTrue(const.is_at_most_once())

    def test_remove_internal_forall(self):
        problem = self.problem
        Location = UserType("Location")
        robot_at = unified_planning.model.Fluent("robot_at", BoolType(), l=Location)
        s_loc = Variable("l", Location)
        test_forall = At_Most_Once(Forall(FluentExp(robot_at, [s_loc]), s_loc))
        problem.add_trajectory_constraint(test_forall)
        new_constrs = self.simplifier.simplify(
            And(self.traj_remover._remove_quantifire(problem.trajectory_constraints))
        )
        self.assertTrue(new_constrs.is_at_most_once())
        self.assertTrue(new_constrs.args[0].is_and())
        self.assertTrue(
            len(new_constrs.args[0].args)
            == len(self.get_all_variable_by_type(problem.all_objects, s_loc.type))
        )
        for const in new_constrs.args[0].args:
            self.assertTrue(new_constrs.args[0].args.count(const) == 1)
            self.assertTrue(const.is_fluent_exp())

    def test_remove_external_exists(self):
        problem = self.problem
        Location = UserType("Location")
        robot_at = unified_planning.model.Fluent("robot_at", BoolType(), l=Location)
        s_loc = Variable("l", Location)
        test_forall = Exists(At_Most_Once(FluentExp(robot_at, [s_loc])), s_loc)
        problem.add_trajectory_constraint(test_forall)
        new_constrs = self.simplifier.simplify(
            And(self.traj_remover._remove_quantifire(problem.trajectory_constraints))
        )
        self.assertTrue(new_constrs.is_or())
        self.assertTrue(
            len(new_constrs.args)
            == len(self.get_all_variable_by_type(problem.all_objects, s_loc.type))
        )
        for const in new_constrs.args:
            self.assertTrue(new_constrs.args.count(const) == 1)
            self.assertTrue(const.is_at_most_once())

    def test_remove_internal_exists(self):
        problem = self.problem
        Location = UserType("Location")
        robot_at = unified_planning.model.Fluent("robot_at", BoolType(), l=Location)
        s_loc = Variable("l", Location)
        test_forall = At_Most_Once(Exists(FluentExp(robot_at, [s_loc]), s_loc))
        problem.add_trajectory_constraint(test_forall)
        new_constrs = self.simplifier.simplify(
            And(self.traj_remover._remove_quantifire(problem.trajectory_constraints))
        )
        self.assertTrue(new_constrs.is_at_most_once())
        self.assertTrue(new_constrs.args[0].is_or())
        self.assertTrue(
            len(new_constrs.args[0].args)
            == len(self.get_all_variable_by_type(problem.all_objects, s_loc.type))
        )
        for const in new_constrs.args[0].args:
            self.assertTrue(new_constrs.args[0].args.count(const) == 1)
            self.assertTrue(const.is_fluent_exp())
