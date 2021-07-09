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
from upf.test.examples import get_example_problems


class TestPddlIO(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_basic_writer(self):
        problem = self.problems['basic'].problem

        w = PDDLWriter(problem)

        pddl_domain = w.get_domain()
        self.assertTrue('(:requirements :strips :negative-preconditions)' in pddl_domain)
        self.assertTrue('(:predicates (x))' in pddl_domain)
        self.assertTrue('(:action a' in pddl_domain)
        self.assertTrue(':parameters()')
        self.assertTrue(':precondition (and (not (x)))' in pddl_domain)
        self.assertTrue(':effect (and (x))' in pddl_domain)

        pddl_problem = w.get_problem()
        self.assertTrue('(:domain basic-domain)' in pddl_problem)
        self.assertTrue('(:init)' in pddl_problem)
        self.assertTrue('(:goal (and (x)))' in pddl_problem)

    def test_robot_writer(self):
        problem = self.problems['robot'].problem

        w = PDDLWriter(problem)

        pddl_domain = w.get_domain()
        self.assertTrue('(:requirements :strips :typing :negative-preconditions :equality :numeric-fluents)' in pddl_domain)
        self.assertTrue('(:types Location)' in pddl_domain)
        self.assertTrue('(:predicates (robot_at ?p0 - Location))' in pddl_domain)
        self.assertTrue('(:functions (battery_charge))' in pddl_domain)
        self.assertTrue('(:action move' in pddl_domain)
        self.assertTrue(':parameters ( ?l_from - Location ?l_to - Location)' in pddl_domain)
        self.assertTrue(':precondition (and (<= 10 (battery_charge)) (not (= ?l_from ?l_to)) (robot_at ?l_from) (not (robot_at ?l_to)))' in pddl_domain)
        self.assertTrue(':effect (and (not (robot_at ?l_from)) (robot_at ?l_to) (assign (battery_charge) (- (battery_charge) 10)))' in pddl_domain)

        pddl_problem = w.get_problem()
        self.assertTrue('(:domain robot-domain)' in pddl_problem)
        self.assertTrue('(:objects' in pddl_problem)
        self.assertTrue('l1 l2 - Location' in pddl_problem)
        self.assertTrue('(:init (robot_at l1) (= (battery_charge) 100))' in pddl_problem)
        self.assertTrue('(:goal (and (robot_at l2)))' in pddl_problem)

    def test_robot_loader(self):
        problem = self.problems['robot_loader'].problem

        w = PDDLWriter(problem)

        pddl_domain = w.get_domain()
        self.assertTrue('(:requirements :strips :typing :negative-preconditions :equality)' in pddl_domain)
        self.assertTrue('(:types Location)' in pddl_domain)
        self.assertTrue('(:predicates (robot_at ?p0 - Location) (cargo_at ?p0 - Location) (cargo_mounted))' in pddl_domain)
        self.assertTrue('(:action move' in pddl_domain)
        self.assertTrue(':parameters ( ?l_from - Location ?l_to - Location)' in pddl_domain)
        self.assertTrue(':precondition (and (not (= ?l_from ?l_to)) (robot_at ?l_from) (not (robot_at ?l_to)))' in pddl_domain)
        self.assertTrue(':effect (and (not (robot_at ?l_from)) (robot_at ?l_to))' in pddl_domain)
        self.assertTrue('(:action load' in pddl_domain)
        self.assertTrue(':parameters ( ?loc - Location)' in pddl_domain)
        self.assertTrue(':precondition (and (cargo_at ?loc) (robot_at ?loc) (not (cargo_mounted)))' in pddl_domain)
        self.assertTrue(':effect (and (not (cargo_at ?loc)) (cargo_mounted))' in pddl_domain)
        self.assertTrue('(:action unload' in pddl_domain)
        self.assertTrue(':parameters ( ?loc - Location)' in pddl_domain)
        self.assertTrue(':precondition (and (not (cargo_at ?loc)) (robot_at ?loc) (cargo_mounted))' in pddl_domain)
        self.assertTrue(':effect (and (cargo_at ?loc) (not (cargo_mounted)))' in pddl_domain)

        pddl_problem = w.get_problem()
        self.assertTrue('(:domain robot_loader-domain)' in pddl_problem)
        self.assertTrue('(:objects' in pddl_problem)
        self.assertTrue('l1 l2 - Location' in pddl_problem)
        self.assertTrue('(:init (robot_at l1) (cargo_at l2))' in pddl_problem)
        self.assertTrue('(:goal (and (cargo_at l1)))' in pddl_problem)

    def test_robot_loader_adv(self):
        problem = self.problems['robot_loader_adv'].problem

        w = PDDLWriter(problem)

        pddl_domain = w.get_domain()
        self.assertTrue('(:requirements :strips :typing :negative-preconditions :equality)' in pddl_domain)
        self.assertTrue('(:types Robot Location Container)' in pddl_domain)
        self.assertTrue('(:predicates (robot_at ?p0 - Robot ?p1 - Location) (cargo_at ?p0 - Container ?p1 - Location) (cargo_mounted ?p0 - Container ?p1 - Robot))' in pddl_domain)
        self.assertTrue('(:action move' in pddl_domain)
        self.assertTrue(':parameters ( ?l_from - Location ?l_to - Location ?r - Robot)' in pddl_domain)
        self.assertTrue(':precondition (and (not (= ?l_from ?l_to)) (robot_at ?r ?l_from) (not (robot_at ?r ?l_to)))' in pddl_domain)
        self.assertTrue(':effect (and (not (robot_at ?r ?l_from)) (robot_at ?r ?l_to))' in pddl_domain)
        self.assertTrue('(:action load' in pddl_domain)
        self.assertTrue(':parameters ( ?loc - Location ?r - Robot ?c - Container)' in pddl_domain)
        self.assertTrue(':precondition (and (cargo_at ?c ?loc) (robot_at ?r ?loc) (not (cargo_mounted ?c ?r)))' in pddl_domain)
        self.assertTrue(':effect (and (not (cargo_at ?c ?loc)) (cargo_mounted ?c ?r))' in pddl_domain)
        self.assertTrue('(:action unload' in pddl_domain)
        self.assertTrue(':parameters ( ?loc - Location ?r - Robot ?c - Container)' in pddl_domain)
        self.assertTrue(':precondition (and (not (cargo_at ?c ?loc)) (robot_at ?r ?loc) (cargo_mounted ?c ?r))' in pddl_domain)
        self.assertTrue(':effect (and (cargo_at ?c ?loc) (not (cargo_mounted ?c ?r)))' in pddl_domain)

        pddl_problem = w.get_problem()
        self.assertTrue('(:domain robot_loader_adv-domain)' in pddl_problem)
        self.assertTrue('(:objects' in pddl_problem)
        self.assertTrue('r1 - Robot' in pddl_problem)
        self.assertTrue('l1 l2 l3 - Location' in pddl_problem)
        self.assertTrue('c1 - Container' in pddl_problem)
        self.assertTrue('(:init (robot_at r1 l1) (cargo_at c1 l2))' in pddl_problem)
        self.assertTrue('(:goal (and (cargo_at c1 l3) (robot_at r1 l1)))' in pddl_problem)
