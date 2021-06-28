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

import upf
from upf.shortcuts import *
from upf.test import TestCase, main
from upf.io.pddl_writer import PDDLWriter


class TestPddlIO(TestCase):
    def test_basic_writer(self):
        x = upf.Fluent('x')
        a = upf.Action('a')
        a.add_precondition(Not(x))
        a.add_effect(x, True)
        problem = upf.Problem('basic')
        problem.add_fluent(x)
        problem.add_action(a)
        problem.set_initial_value(x, False)
        problem.add_goal(x)

        w = PDDLWriter(problem)

        pddl_domain = w.get_domain()
        self.assertTrue('(:requirements :strips :negative-preconditions)' in pddl_domain)
        self.assertTrue('(:predicates (x))' in pddl_domain)
        self.assertTrue('(:action a' in pddl_domain)
        self.assertTrue(':precondition (and (not (x)))' in pddl_domain)
        self.assertTrue(':effect (and (x))' in pddl_domain)

        pddl_problem = w.get_problem()
        self.assertTrue('(:domain basic-domain)' in pddl_problem)
        self.assertTrue('(:init)' in pddl_problem)
        self.assertTrue('(:goal (and (x)))' in pddl_problem)

    def test_robot_writer(self):
        Location = UserType('Location')
        robot_at = upf.Fluent('robot_at', BoolType(), [Location])
        battery_charge = upf.Fluent('battery_charge', RealType(0, 100))
        move = upf.Action('move', l_from=Location, l_to=Location)
        l_from = move.parameter('l_from')
        l_to = move.parameter('l_to')
        move.add_precondition(GE(battery_charge, 10))
        move.add_precondition(Not(Equals(l_from, l_to)))
        move.add_precondition(robot_at(l_from))
        move.add_precondition(Not(robot_at(l_to)))
        move.add_effect(robot_at(l_from), False)
        move.add_effect(robot_at(l_to), True)
        move.add_effect(battery_charge, Minus(battery_charge, 10))
        l1 = upf.Object('l1', Location)
        l2 = upf.Object('l2', Location)
        problem = upf.Problem('robot')
        problem.add_fluent(robot_at)
        problem.add_fluent(battery_charge)
        problem.add_action(move)
        problem.add_object(l1)
        problem.add_object(l2)
        problem.set_initial_value(robot_at(l1), True)
        problem.set_initial_value(robot_at(l2), False)
        problem.set_initial_value(battery_charge, 100)
        problem.add_goal(robot_at(l2))

        w = PDDLWriter(problem)

        pddl_domain = w.get_domain()
        self.assertTrue('(:requirements :strips :typing :negative-preconditions :equality :numeric-fluents)' in pddl_domain)
        self.assertTrue('(:predicates (robot_at ?p0 - Location))' in pddl_domain)
        self.assertTrue('(:functions (battery_charge))' in pddl_domain)
        self.assertTrue('(:types Location)' in pddl_domain)
        self.assertTrue('(:action move' in pddl_domain)
        self.assertTrue(':parameters ( ?l_from - Location ?l_to - Location)' in pddl_domain)
        self.assertTrue(':precondition (and (<= 10 (battery_charge)) (not (= ?l_from ?l_to)) (robot_at ?l_from) (not (robot_at ?l_to)))' in pddl_domain)
        self.assertTrue(':effect (and (not (robot_at ?l_from)) (robot_at ?l_to) (= (battery_charge) (- (battery_charge) 10)))' in pddl_domain)

        pddl_problem = w.get_problem()
        self.assertTrue('(:domain robot-domain)' in pddl_problem)
        self.assertTrue('(:objects' in pddl_problem)
        self.assertTrue('l1 l2 - Location' in pddl_problem)
        self.assertTrue('(:init (robot_at l1) (= (battery_charge) 100))' in pddl_problem)
        self.assertTrue('(:goal (and (robot_at l2)))' in pddl_problem)
