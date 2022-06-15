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

TRAJECTORY_CONSTRAINTS = ['always', 'sometime-before', 'sometime-after', 'at-most-once', 'sometime']

class TestTrajectoryConstraint(TestCase):
    def setUp(self):
        reader = PDDLReader()
        prob = '.venv/lib/python3.10/site-packages/unified_planning/test/examples/problem_test/p01.pddl'
        dom = '.venv/lib/python3.10/site-packages/unified_planning/test/examples/problem_test/domain.pddl'
        self.problem = reader.parse_problem(dom, prob)
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

    def control_number_parameters(self, trajectory_constraint):
        match trajectory_constraint.type:
            case 'always':
                return len(trajectory_constraint.parameters) == 1
            case 'sometime':
                return len(trajectory_constraint.parameters) == 1
            case 'at-most-once':
                return len(trajectory_constraint.parameters) == 1
            case 'sometime-after':
                return len(trajectory_constraint.parameters) == 2
            case 'sometime-before':
                return len(trajectory_constraint.parameters) == 2
            case _:
                return False
    
    def test_parse_problem_from_file(self):
        trajectory_constraints = self.problem.trajectory_constraints
        self.assertEqual(len(trajectory_constraints), 10) 
        for t in trajectory_constraints:
            self.assertTrue(isinstance(t, unified_planning.model.trajectory_constraint.TrajectoryConstraint))
            self.assertTrue(t.type in TRAJECTORY_CONSTRAINTS)
            self.assertFalse(t.type not in TRAJECTORY_CONSTRAINTS)
            self.assertTrue(self.control_number_parameters(t))
            for p in t.parameters:
                self.assertTrue(p.is_fluent_exp() or p.is_not())


    def test_create_always_constraint(self):
        problem, fluents, objects= self.define_problem()
        robot_at = fluents[0]
        always_short = Always(Not(robot_at(objects[1])))
        always_long = unified_planning.model.trajectory_constraint.TrajectoryConstraint('always', [robot_at(objects[0])])
        self.assertRaises(Exception,
            unified_planning.model.trajectory_constraint.TrajectoryConstraint, 
            'alw', [robot_at(objects[0])])
        self.assertRaises(Exception,
            Always, robot_at(objects[0]), robot_at(objects[1]))
        problem.add_trajectory_constraint(always_short) 
        problem.add_trajectory_constraint(always_long)
        trajectory_constraints = problem.trajectory_constraints
        self.assertEqual(len(trajectory_constraints), 2) 
        for t in trajectory_constraints:
            self.assertTrue(isinstance(t, unified_planning.model.trajectory_constraint.TrajectoryConstraint))
            self.assertTrue(t.type in TRAJECTORY_CONSTRAINTS)
            self.assertFalse(t.type not in TRAJECTORY_CONSTRAINTS)
            self.assertTrue(self.control_number_parameters(t))
            for p in t.parameters:
                self.assertTrue(p.is_fluent_exp() or p.is_not())

    def test_create_sometime_constraint(self):
        problem, fluents, objects= self.define_problem()
        robot_at = fluents[0]
        sometime_short = Sometime(Not(robot_at(objects[1])))
        sometime_long = unified_planning.model.trajectory_constraint.TrajectoryConstraint('sometime', [robot_at(objects[0])])
        self.assertRaises(Exception,
            unified_planning.model.trajectory_constraint.TrajectoryConstraint, 
            'sometttime', [robot_at(objects[0])])
        self.assertRaises(Exception,
            Sometime, robot_at(objects[0]), robot_at(objects[1]))
        problem.add_trajectory_constraint(sometime_short) 
        problem.add_trajectory_constraint(sometime_long)
        trajectory_constraints = problem.trajectory_constraints
        self.assertEqual(len(trajectory_constraints), 2) 
        for t in trajectory_constraints:
            self.assertTrue(isinstance(t, unified_planning.model.trajectory_constraint.TrajectoryConstraint))
            self.assertTrue(t.type in TRAJECTORY_CONSTRAINTS)
            self.assertFalse(t.type not in TRAJECTORY_CONSTRAINTS)
            self.assertTrue(self.control_number_parameters(t))
            for p in t.parameters:
                self.assertTrue(p.is_fluent_exp() or p.is_not())

    def test_create_at_most_once_constraint(self):
        problem, fluents, objects= self.define_problem()
        robot_at = fluents[0]
        at_most_once_short = At_Most_Once(robot_at(objects[1]))
        at_most_once_long = unified_planning.model.trajectory_constraint.TrajectoryConstraint('at-most-once', [robot_at(objects[0])])
        self.assertRaises(Exception,
            unified_planning.model.trajectory_constraint.TrajectoryConstraint, 
            'atmostonce', [robot_at(objects[0])])
        self.assertRaises(Exception,
            At_Most_Once, robot_at(objects[0]), robot_at(objects[1]))
        problem.add_trajectory_constraint(at_most_once_short) 
        problem.add_trajectory_constraint(at_most_once_long)
        trajectory_constraints = problem.trajectory_constraints
        self.assertEqual(len(trajectory_constraints), 2) 
        for t in trajectory_constraints:
            self.assertTrue(isinstance(t, unified_planning.model.trajectory_constraint.TrajectoryConstraint))
            self.assertTrue(t.type in TRAJECTORY_CONSTRAINTS)
            self.assertFalse(t.type not in TRAJECTORY_CONSTRAINTS)
            self.assertTrue(self.control_number_parameters(t))
            for p in t.parameters:
                self.assertTrue(p.is_fluent_exp() or p.is_not())

    def test_create_sometime_before_constraint(self):
        problem, fluents, objects= self.define_problem()
        connected = fluents[1]
        sometime_before_short = Sometime_Before(connected(objects[1], objects[2]), connected(objects[0], objects[1]))
        sometime_before_long = unified_planning.model.trajectory_constraint.TrajectoryConstraint(
            'sometime-before', [connected(objects[1], objects[2]), connected(objects[0], objects[1])])
        self.assertRaises(Exception,
            unified_planning.model.trajectory_constraint.TrajectoryConstraint, 
            'somebef', [connected(objects[1], objects[2]), connected(objects[0], objects[1])])
        self.assertRaises(Exception,
            Sometime_Before, connected(objects[1], objects[2]))
        problem.add_trajectory_constraint(sometime_before_short) 
        problem.add_trajectory_constraint(sometime_before_long)
        trajectory_constraints = problem.trajectory_constraints
        self.assertEqual(len(trajectory_constraints), 2) 
        for t in trajectory_constraints:
            self.assertTrue(isinstance(t, unified_planning.model.trajectory_constraint.TrajectoryConstraint))
            self.assertTrue(t.type in TRAJECTORY_CONSTRAINTS)
            self.assertFalse(t.type not in TRAJECTORY_CONSTRAINTS)
            self.assertTrue(self.control_number_parameters(t))
            for p in t.parameters:
                self.assertTrue(p.is_fluent_exp() or p.is_not())
        
    def test_create_sometime_after_constraint(self):
        problem, fluents, objects= self.define_problem()
        connected = fluents[1]
        sometime_after_short = Sometime_After(connected(objects[1], objects[2]), connected(objects[0], objects[1]))
        sometime_after_long = unified_planning.model.trajectory_constraint.TrajectoryConstraint(
            'sometime-after', [connected(objects[1], objects[2]), connected(objects[0], objects[1])])
        self.assertRaises(Exception,
            unified_planning.model.trajectory_constraint.TrajectoryConstraint, 
            'saftf', [connected(objects[1], objects[2]), connected(objects[0], objects[1])])
        self.assertRaises(Exception,
            Sometime_After, connected(objects[1], objects[2]), connected(objects[1], objects[2]), connected(objects[1], objects[2]))
        problem.add_trajectory_constraint(sometime_after_short) 
        problem.add_trajectory_constraint(sometime_after_long)
        trajectory_constraints = problem.trajectory_constraints
        self.assertEqual(len(trajectory_constraints), 2) 
        for t in trajectory_constraints:
            self.assertTrue(isinstance(t, unified_planning.model.trajectory_constraint.TrajectoryConstraint))
            self.assertTrue(t.type in TRAJECTORY_CONSTRAINTS)
            self.assertFalse(t.type not in TRAJECTORY_CONSTRAINTS)
            self.assertTrue(self.control_number_parameters(t))
            for p in t.parameters:
                self.assertTrue(p.is_fluent_exp() or p.is_not())





            