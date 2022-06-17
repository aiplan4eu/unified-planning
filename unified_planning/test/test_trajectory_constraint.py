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
from unified_planning.walkers import Dnf, Nnf, Simplifier, Substituter

class TestTrajectoryConstraint(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        
    def define_problem(self):
        Location = UserType('Location')
        robot_at = unified_planning.model.Fluent('robot_at', BoolType(), l=Location)
        connected = unified_planning.model.Fluent('connected', BoolType(), l_from=Location, l_to=Location)
        problem = unified_planning.model.Problem('robot')
        problem.add_fluent(robot_at, default_initial_value=False)
        problem.add_fluent(connected, default_initial_value=False)

        l1 = unified_planning.model.Object('l1', Location)
        l2 = unified_planning.model.Object('l2', Location)
        l3 = unified_planning.model.Object('l3', Location)
        l4 = unified_planning.model.Object('l4', Location)
        problem.add_objects([l1, l2, l3, l4])

        problem.set_initial_value(robot_at(l1), True)
        problem.set_initial_value(connected(l1, l2), True)
        problem.set_initial_value(connected(l2, l3), True)
        problem.set_initial_value(connected(l3, l4), True)
        return problem, [robot_at, connected], [l1, l2, l3, l4]

    def test_create_always_constraint(self):
        problem, fluents, objects= self.define_problem()
        robot_at = fluents[0]
        always = Always(robot_at(objects[0]))
        always_not = Always(Not(robot_at(objects[1])))
        self.assertTrue(always.is_always() and always_not.is_always())
        self.assertTrue(always.node_type == OperatorKind.ALWAYS and always_not.node_type == OperatorKind.ALWAYS)
        self.assertTrue(len(always.args) == 1 and
                        always.args[0].node_type == OperatorKind.FLUENT_EXP
                        )
        self.assertTrue(len(always_not.args) == 1 and
                        always_not.args[0].node_type == OperatorKind.NOT and
                        len(always_not.args[0].args) == 1 and
                        always_not.args[0].args[0].node_type == OperatorKind.FLUENT_EXP
                        )
        problem.add_trajectory_constraint(always)
        problem.add_trajectory_constraint(always_not)
        self.assertTrue(str(problem.trajectory_constraints) == 
                        '[Always(robot_at(l1)), Always((not robot_at(l2)))]')

    def test_create_sometime_constraint(self):
        problem, fluents, objects= self.define_problem()
        robot_at = fluents[0]
        sometime = Sometime(robot_at(objects[0]))
        sometime_not = Sometime(Not(robot_at(objects[1])))
        self.assertTrue(sometime.is_sometime() and sometime_not.is_sometime())
        self.assertTrue(sometime.node_type == OperatorKind.SOMETIME and sometime_not.node_type == OperatorKind.SOMETIME)
        self.assertTrue(len(sometime.args) == 1 and
                        sometime.args[0].node_type == OperatorKind.FLUENT_EXP
                        )
        self.assertTrue(len(sometime_not.args) == 1 and
                        sometime_not.args[0].node_type == OperatorKind.NOT and
                        len(sometime_not.args[0].args) == 1 and
                        sometime_not.args[0].args[0].node_type == OperatorKind.FLUENT_EXP
                        )
        problem.add_trajectory_constraint(sometime)
        problem.add_trajectory_constraint(sometime_not)
        self.assertTrue(str(problem.trajectory_constraints) == 
                        '[Sometime(robot_at(l1)), Sometime((not robot_at(l2)))]')

    def test_create_at_most_once_constraint(self):
        problem, fluents, objects= self.define_problem()
        robot_at = fluents[0]
        at_most_once = At_Most_Once(robot_at(objects[0]))
        at_most_once_not = At_Most_Once(Not(robot_at(objects[1])))
        self.assertTrue(at_most_once.is_at_most_once() and at_most_once_not.is_at_most_once())
        self.assertTrue(at_most_once.node_type == OperatorKind.AT_MOST_ONCE and at_most_once_not.node_type == OperatorKind.AT_MOST_ONCE)
        self.assertTrue(len(at_most_once.args) == 1 and
                        at_most_once.args[0].node_type == OperatorKind.FLUENT_EXP
                        )
        self.assertTrue(len(at_most_once_not.args) == 1 and
                        at_most_once_not.args[0].node_type == OperatorKind.NOT and
                        len(at_most_once_not.args[0].args) == 1 and
                        at_most_once_not.args[0].args[0].node_type == OperatorKind.FLUENT_EXP
                        )
        problem.add_trajectory_constraint(at_most_once)
        problem.add_trajectory_constraint(at_most_once_not)
        self.assertTrue(str(problem.trajectory_constraints) == 
                        '[At-Most-Once(robot_at(l1)), At-Most-Once((not robot_at(l2)))]')

    def test_create_sometime_before_constraint(self):
        problem, fluents, objects= self.define_problem()
        robot_at = fluents[0]
        sometime_before = Sometime_Before(robot_at(objects[0]), robot_at(objects[1]))
        sometime_before_not = Sometime_Before(Not(robot_at(objects[0])), robot_at(objects[1]))
        self.assertTrue(sometime_before.is_sometime_before() and sometime_before_not.is_sometime_before())
        self.assertTrue(sometime_before.node_type == OperatorKind.SOMETIME_BEFORE and sometime_before_not.node_type == OperatorKind.SOMETIME_BEFORE)
        self.assertTrue(len(sometime_before.args) == 2 and
                        sometime_before.args[0].node_type == OperatorKind.FLUENT_EXP and
                        sometime_before.args[1].node_type == OperatorKind.FLUENT_EXP
                        )
        self.assertTrue(len(sometime_before_not.args) == 2 and
                        sometime_before_not.args[0].node_type == OperatorKind.NOT and
                        len(sometime_before_not.args[0].args) == 1 and
                        sometime_before_not.args[0].args[0].node_type == OperatorKind.FLUENT_EXP and
                        sometime_before_not.args[1].node_type == OperatorKind.FLUENT_EXP
                        )
        problem.add_trajectory_constraint(sometime_before)
        problem.add_trajectory_constraint(sometime_before_not)
        self.assertTrue(str(problem.trajectory_constraints) == 
                        '[Sometime-Before(robot_at(l1), robot_at(l2)), Sometime-Before((not robot_at(l1)), robot_at(l2))]')

    def test_create_sometime_before_constraint(self):
        problem, fluents, objects= self.define_problem()
        robot_at = fluents[0]
        sometime_before = Sometime_Before(robot_at(objects[0]), robot_at(objects[1]))
        sometime_before_not = Sometime_Before(Not(robot_at(objects[0])), robot_at(objects[1]))
        self.assertTrue(sometime_before.is_sometime_before() and sometime_before_not.is_sometime_before())
        self.assertTrue(sometime_before.node_type == OperatorKind.SOMETIME_BEFORE and sometime_before_not.node_type == OperatorKind.SOMETIME_BEFORE)
        self.assertTrue(len(sometime_before.args) == 2 and
                        sometime_before.args[0].node_type == OperatorKind.FLUENT_EXP and
                        sometime_before.args[1].node_type == OperatorKind.FLUENT_EXP
                        )
        self.assertTrue(len(sometime_before_not.args) == 2 and
                        sometime_before_not.args[0].node_type == OperatorKind.NOT and
                        len(sometime_before_not.args[0].args) == 1 and
                        sometime_before_not.args[0].args[0].node_type == OperatorKind.FLUENT_EXP and
                        sometime_before_not.args[1].node_type == OperatorKind.FLUENT_EXP
                        )
        problem.add_trajectory_constraint(sometime_before)
        problem.add_trajectory_constraint(sometime_before_not)
        self.assertTrue(str(problem.trajectory_constraints) == 
                        '[Sometime-Before(robot_at(l1), robot_at(l2)), Sometime-Before((not robot_at(l1)), robot_at(l2))]')

    def test_create_sometime_after_constraint(self):
        problem, fluents, objects= self.define_problem()
        robot_at = fluents[0]
        sometime_after = Sometime_After(robot_at(objects[0]), robot_at(objects[1]))
        sometime_after_not = Sometime_After(Not(robot_at(objects[0])), robot_at(objects[1]))
        self.assertTrue(sometime_after.is_sometime_after() and sometime_after_not.is_sometime_after())
        self.assertTrue(sometime_after.node_type == OperatorKind.SOMETIME_AFTER and sometime_after_not.node_type == OperatorKind.SOMETIME_AFTER)
        self.assertTrue(len(sometime_after.args) == 2 and
                        sometime_after.args[0].node_type == OperatorKind.FLUENT_EXP and
                        sometime_after.args[1].node_type == OperatorKind.FLUENT_EXP
                        )
        self.assertTrue(len(sometime_after_not.args) == 2 and
                        sometime_after_not.args[0].node_type == OperatorKind.NOT and
                        len(sometime_after_not.args[0].args) == 1 and
                        sometime_after_not.args[0].args[0].node_type == OperatorKind.FLUENT_EXP and
                        sometime_after_not.args[1].node_type == OperatorKind.FLUENT_EXP
                        )
        problem.add_trajectory_constraint(sometime_after)
        problem.add_trajectory_constraint(sometime_after_not)
        self.assertTrue(str(problem.trajectory_constraints) == 
                        '[Sometime-After(robot_at(l1), robot_at(l2)), Sometime-After((not robot_at(l1)), robot_at(l2))]')