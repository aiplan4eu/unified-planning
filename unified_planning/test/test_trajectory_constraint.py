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
from unified_planning.io.pddl_reader import PDDLReader
from unified_planning.test.examples import get_example_problems
from unified_planning.shortcuts import *
from unified_planning.test import TestCase, main
from unified_planning.environment import get_env
from unified_planning.engines.compilers.trajectory_constraints_remover import (
    TrajectoryConstraintsRemover,
)


class TestTrajectoryConstraint(TestCase):
    def setUp(self):
        TestCase.setUp(self)

    def define_problem(self):
        Location = UserType('Location')
        robot_at = unified_planning.model.Fluent('robot_at', BoolType(), l=Location)
        connected = unified_planning.model.Fluent('connected', BoolType(), l_from=Location, l_to=Location)

        move = unified_planning.model.InstantaneousAction('move', l_from=Location, l_to=Location)
        l_from = move.parameter('l_from')
        l_to = move.parameter('l_to')
        move.add_precondition(connected(l_from, l_to))
        move.add_precondition(robot_at(l_from))
        move.add_effect(robot_at(l_from), False)
        move.add_effect(robot_at(l_to), True)

        problem = unified_planning.model.Problem('robot', 
            initial_defaults={BoolType(): FALSE()}
            )
        problem.add_fluent(robot_at, default_initial_value=False) 
        problem.add_fluent(connected, default_initial_value=False)
        problem.add_action(move)

        NLOC = 5
        locations = [unified_planning.model.Object('l%s' % i, Location) for i in range(NLOC)]
        problem.add_objects(locations)
        problem.set_initial_value(robot_at(locations[0]), True)
        for i in range(NLOC - 1):
            problem.set_initial_value(connected(locations[i], locations[i+1]), True)

        problem.add_goal(robot_at(locations[-1]))
        return problem

    def test_create_always_constraint(self):
        problem = self.define_problem()
        Location = UserType('Location')
        l1 = unified_planning.model.Object('l1', Location)
        l2 = unified_planning.model.Object('l2', Location)
        robot_at = unified_planning.model.Fluent('robot_at', BoolType(), l=Location)
        always = Always(robot_at(l1))
        always_not = Always(Not(robot_at(l2)))
        self.assertTrue(always.is_always() and always_not.is_always())
        self.assertTrue(
            always.node_type == OperatorKind.ALWAYS
            and always_not.node_type == OperatorKind.ALWAYS
        )
        self.assertTrue(
            len(always.args) == 1
            and always.args[0].node_type == OperatorKind.FLUENT_EXP
        )
        self.assertTrue(
            len(always_not.args) == 1
            and always_not.args[0].node_type == OperatorKind.NOT
            and len(always_not.args[0].args) == 1
            and always_not.args[0].args[0].node_type == OperatorKind.FLUENT_EXP
        )
        problem.add_trajectory_constraint(always)
        problem.add_trajectory_constraint(always_not)
        self.assertTrue(
            str(problem.trajectory_constraints)
            == "[(Always((not robot_at(l2))) and Always(robot_at(l1)))]"
        )

    def test_create_sometime_constraint(self):
        problem = self.define_problem()
        Location = UserType('Location')
        l1 = unified_planning.model.Object('l1', Location)
        l2 = unified_planning.model.Object('l2', Location)
        robot_at = unified_planning.model.Fluent('robot_at', BoolType(), l=Location)
        sometime = Sometime(robot_at(l1))
        sometime_not = Sometime(Not(robot_at(l2)))
        self.assertTrue(sometime.is_sometime() and sometime_not.is_sometime())
        self.assertTrue(
            sometime.node_type == OperatorKind.SOMETIME
            and sometime_not.node_type == OperatorKind.SOMETIME
        )
        self.assertTrue(
            len(sometime.args) == 1
            and sometime.args[0].node_type == OperatorKind.FLUENT_EXP
        )
        self.assertTrue(
            len(sometime_not.args) == 1
            and sometime_not.args[0].node_type == OperatorKind.NOT
            and len(sometime_not.args[0].args) == 1
            and sometime_not.args[0].args[0].node_type == OperatorKind.FLUENT_EXP
        )
        problem.add_trajectory_constraint(sometime)
        problem.add_trajectory_constraint(sometime_not)
        self.assertTrue(
            str(problem.trajectory_constraints)
            == "[(Sometime((not robot_at(l2))) and Sometime(robot_at(l1)))]"
        )

    def test_create_at_most_once_constraint(self):
        problem = self.define_problem()
        Location = UserType('Location')
        l1 = unified_planning.model.Object('l1', Location)
        l2 = unified_planning.model.Object('l2', Location)
        robot_at = unified_planning.model.Fluent('robot_at', BoolType(), l=Location)
        at_most_once = AtMostOnce(robot_at(l1))
        at_most_once_not = AtMostOnce(Not(robot_at(l2)))
        self.assertTrue(
            at_most_once.is_at_most_once() and at_most_once_not.is_at_most_once()
        )
        self.assertTrue(
            at_most_once.node_type == OperatorKind.AT_MOST_ONCE
            and at_most_once_not.node_type == OperatorKind.AT_MOST_ONCE
        )
        self.assertTrue(
            len(at_most_once.args) == 1
            and at_most_once.args[0].node_type == OperatorKind.FLUENT_EXP
        )
        self.assertTrue(
            len(at_most_once_not.args) == 1
            and at_most_once_not.args[0].node_type == OperatorKind.NOT
            and len(at_most_once_not.args[0].args) == 1
            and at_most_once_not.args[0].args[0].node_type == OperatorKind.FLUENT_EXP
        )
        problem.add_trajectory_constraint(at_most_once)
        problem.add_trajectory_constraint(at_most_once_not)
        self.assertTrue(
            str(problem.trajectory_constraints)
            == "[(At-Most-Once((not robot_at(l2))) and At-Most-Once(robot_at(l1)))]"
        )

    def test_create_sometime_before_constraint(self):
        problem = self.define_problem()
        Location = UserType('Location')
        l1 = unified_planning.model.Object('l1', Location)
        l2 = unified_planning.model.Object('l2', Location)
        robot_at = unified_planning.model.Fluent('robot_at', BoolType(), l=Location)
        sometime_before = SometimeBefore(robot_at(l1), robot_at(l2))
        sometime_before_not = SometimeBefore(
            Not(robot_at(l1)), robot_at(l2)
        )
        self.assertTrue(
            sometime_before.is_sometime_before()
            and sometime_before_not.is_sometime_before()
        )
        self.assertTrue(
            sometime_before.node_type == OperatorKind.SOMETIME_BEFORE
            and sometime_before_not.node_type == OperatorKind.SOMETIME_BEFORE
        )
        self.assertTrue(
            len(sometime_before.args) == 2
            and sometime_before.args[0].node_type == OperatorKind.FLUENT_EXP
            and sometime_before.args[1].node_type == OperatorKind.FLUENT_EXP
        )
        self.assertTrue(
            len(sometime_before_not.args) == 2
            and sometime_before_not.args[0].node_type == OperatorKind.NOT
            and len(sometime_before_not.args[0].args) == 1
            and sometime_before_not.args[0].args[0].node_type == OperatorKind.FLUENT_EXP
            and sometime_before_not.args[1].node_type == OperatorKind.FLUENT_EXP
        )
        problem.add_trajectory_constraint(sometime_before)
        problem.add_trajectory_constraint(sometime_before_not)
        self.assertTrue(
            str(problem.trajectory_constraints)
            == "[(Sometime-Before((not robot_at(l1)), robot_at(l2)) and Sometime-Before(robot_at(l1), robot_at(l2)))]"
        )

    def test_create_sometime_after_constraint(self):
        problem = self.define_problem()
        Location = UserType('Location')
        l1 = unified_planning.model.Object('l1', Location)
        l2 = unified_planning.model.Object('l2', Location)
        robot_at = unified_planning.model.Fluent('robot_at', BoolType(), l=Location)
        sometime_after = SometimeAfter(robot_at(l1), robot_at(l2))
        sometime_after_not = SometimeAfter(
            Not(robot_at(l1)), robot_at(l2)
        )
        self.assertTrue(
            sometime_after.is_sometime_after()
            and sometime_after_not.is_sometime_after()
        )
        self.assertTrue(
            sometime_after.node_type == OperatorKind.SOMETIME_AFTER
            and sometime_after_not.node_type == OperatorKind.SOMETIME_AFTER
        )
        self.assertTrue(
            len(sometime_after.args) == 2
            and sometime_after.args[0].node_type == OperatorKind.FLUENT_EXP
            and sometime_after.args[1].node_type == OperatorKind.FLUENT_EXP
        )
        self.assertTrue(
            len(sometime_after_not.args) == 2
            and sometime_after_not.args[0].node_type == OperatorKind.NOT
            and len(sometime_after_not.args[0].args) == 1
            and sometime_after_not.args[0].args[0].node_type == OperatorKind.FLUENT_EXP
            and sometime_after_not.args[1].node_type == OperatorKind.FLUENT_EXP
        )
        problem.add_trajectory_constraint(sometime_after)
        problem.add_trajectory_constraint(sometime_after_not)
        self.assertTrue(
            str(problem.trajectory_constraints)
            == "[(Sometime-After((not robot_at(l1)), robot_at(l2)) and Sometime-After(robot_at(l1), robot_at(l2)))]"
        )

    def test_remove_external_forall(self):
        problem = self.define_problem()
        Location = UserType('Location')
        l0 = unified_planning.model.Object('l0', Location)
        l1 = unified_planning.model.Object('l1', Location)
        l2 = unified_planning.model.Object('l2', Location)
        l3 = unified_planning.model.Object('l3', Location)
        l4 = unified_planning.model.Object('l4', Location)
        s_loc = Variable("l", Location)
        robot_at = unified_planning.model.Fluent('robot_at', BoolType(), l=Location)
        test_forall = Forall(AtMostOnce(FluentExp(robot_at, [s_loc])), s_loc)
        problem_with_forall = problem.clone()
        problem_with_forall.add_trajectory_constraint(test_forall)
        problem_without_forall = problem.clone()
        for loc in [l4, l3, l2, l1, l0]:
            problem_without_forall.add_trajectory_constraint(AtMostOnce(robot_at(loc)))

        problem_with_forall_comp = TrajectoryConstraintsRemover().compile(
                problem_with_forall, CompilationKind.TRAJECTORY_CONSTRAINTS_REMOVING
                ).problem
        problem_without_forall_comp = TrajectoryConstraintsRemover().compile(
                problem_without_forall, CompilationKind.TRAJECTORY_CONSTRAINTS_REMOVING
        ).problem
        self.assertTrue(problem_with_forall_comp == problem_without_forall_comp)

    def test_remove_internal_forall(self):
        problem = self.define_problem()
        Location = UserType('Location')
        l0 = unified_planning.model.Object('l0', Location)
        l1 = unified_planning.model.Object('l1', Location)
        l2 = unified_planning.model.Object('l2', Location)
        l3 = unified_planning.model.Object('l3', Location)
        l4 = unified_planning.model.Object('l4', Location)
        s_loc = Variable("l", Location)
        robot_at = unified_planning.model.Fluent('robot_at', BoolType(), l=Location)
        test_forall = AtMostOnce(Forall(FluentExp(robot_at, [s_loc]), s_loc))
        problem_with_forall = problem.clone()
        problem_with_forall.add_trajectory_constraint(test_forall)
        problem_without_forall = problem.clone()
        problem_without_forall.add_trajectory_constraint(AtMostOnce(
                And(robot_at(l0), robot_at(l1), robot_at(l2), robot_at(l3), robot_at(l4)))
                )
        problem_with_forall_comp = TrajectoryConstraintsRemover().compile(
                problem_with_forall, CompilationKind.TRAJECTORY_CONSTRAINTS_REMOVING
                ).problem
        problem_without_forall_comp = TrajectoryConstraintsRemover().compile(
                problem_without_forall, CompilationKind.TRAJECTORY_CONSTRAINTS_REMOVING
        ).problem
        self.assertTrue(problem_with_forall_comp == problem_without_forall_comp)

    def test_remove_internal_exists(self):
        problem = self.define_problem()
        Location = UserType('Location')
        l0 = unified_planning.model.Object('l0', Location)
        l1 = unified_planning.model.Object('l1', Location)
        l2 = unified_planning.model.Object('l2', Location)
        l3 = unified_planning.model.Object('l3', Location)
        l4 = unified_planning.model.Object('l4', Location)
        s_loc = Variable("l", Location)
        robot_at = unified_planning.model.Fluent('robot_at', BoolType(), l=Location)
        test_exixst = AtMostOnce(Exists(FluentExp(robot_at, [s_loc]), s_loc))
        problem_with_forall = problem.clone()
        problem_with_forall.add_trajectory_constraint(test_exixst)
        problem_without_forall = problem.clone()
        problem_without_forall.add_trajectory_constraint(AtMostOnce(
                Or(robot_at(l0), robot_at(l1), robot_at(l2), robot_at(l3), robot_at(l4)))
                )
        problem_with_forall_comp = TrajectoryConstraintsRemover().compile(
                problem_with_forall, CompilationKind.TRAJECTORY_CONSTRAINTS_REMOVING
                ).problem
        problem_without_forall_comp = TrajectoryConstraintsRemover().compile(
                problem_without_forall, CompilationKind.TRAJECTORY_CONSTRAINTS_REMOVING
        ).problem
        self.assertTrue(problem_with_forall_comp == problem_without_forall_comp)