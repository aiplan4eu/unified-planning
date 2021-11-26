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
import upf
from upf.shortcuts import *
from upf.test import TestCase, main
from upf.io.pddl_writer import PDDLWriter
from upf.io.pddl_reader import PDDLReader
from upf.test.examples import get_example_problems


FILE_PATH = os.path.dirname(os.path.abspath(__file__))
PDDL_DOMAINS_PATH = os.path.join(FILE_PATH, 'pddl')


class TestPddlIO(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_basic_writer(self):
        problem = self.problems['basic'].problem

        w = PDDLWriter(problem)

        pddl_domain = w.get_domain()
        self.assertIn('(:requirements :strips :negative-preconditions)', pddl_domain)
        self.assertIn('(:predicates (x))', pddl_domain)
        self.assertIn('(:action a', pddl_domain)
        self.assertIn(':parameters ()', pddl_domain)
        self.assertIn(':precondition (and (not (x)))', pddl_domain)
        self.assertIn(':effect (and (x))', pddl_domain)

        pddl_problem = w.get_problem()
        self.assertIn('(:domain basic-domain)', pddl_problem)
        self.assertIn('(:init)', pddl_problem)
        self.assertIn('(:goal (and (x)))', pddl_problem)


    def test_basic_conditional_writer(self):
        problem = self.problems['basic_conditional'].problem

        self.assertTrue(problem.action('a_x').is_conditional())
        self.assertFalse(problem.action('a_y').is_conditional())

        w = PDDLWriter(problem)

        pddl_domain = w.get_domain()
        self.assertIn('(:requirements :strips :negative-preconditions :conditional-effects)', pddl_domain)
        self.assertIn('(:predicates (x) (y))', pddl_domain)
        self.assertIn('(:action a_x', pddl_domain)
        self.assertIn(':parameters ()', pddl_domain)
        self.assertIn(':precondition (and (not (x)))', pddl_domain)
        self.assertIn(':effect (and (when (y) (x)))', pddl_domain)
        self.assertIn('(:action a_y', pddl_domain)
        self.assertIn(':parameters ()', pddl_domain)
        self.assertIn(':precondition (and (not (y)))', pddl_domain)
        self.assertIn(':effect (and (y))', pddl_domain)

        pddl_problem = w.get_problem()
        self.assertIn('(:domain basic_conditional-domain)', pddl_problem)
        self.assertIn('(:init)', pddl_problem)
        self.assertIn('(:goal (and (x)))', pddl_problem)

    def test_basic_exists_writer(self):
        problem = self.problems['basic_exists'].problem

        w = PDDLWriter(problem)

        pddl_domain = w.get_domain()
        self.assertIn('(:requirements :strips :typing :existential-preconditions)', pddl_domain)
        self.assertIn('(:predicates (x) (y ?p0 - Semaphore))', pddl_domain)
        self.assertIn('(:action a', pddl_domain)
        self.assertIn(':parameters ()', pddl_domain)
        self.assertIn(':precondition (and (exists (?s - Semaphore)\n (y ?s)))', pddl_domain)
        self.assertIn(':effect (and (x))', pddl_domain)

        pddl_problem = w.get_problem()
        self.assertIn('(:domain basic_exists-domain)', pddl_problem)
        self.assertIn('(:objects \n   o1 o2 - Semaphore\n )', pddl_problem)
        self.assertIn('(:init (y o1))', pddl_problem)
        self.assertIn('(:goal (and (x)))', pddl_problem)

    def test_robot_writer(self):
        problem = self.problems['robot'].problem

        w = PDDLWriter(problem)

        pddl_domain = w.get_domain()
        self.assertIn('(:requirements :strips :typing :negative-preconditions :equality :numeric-fluents)', pddl_domain)
        self.assertIn('(:types Location)', pddl_domain)
        self.assertIn('(:predicates (robot_at ?p0 - Location))', pddl_domain)
        self.assertIn('(:functions (battery_charge))', pddl_domain)
        self.assertIn('(:action move', pddl_domain)
        self.assertIn(':parameters ( ?l_from - Location ?l_to - Location)', pddl_domain)
        self.assertIn(':precondition (and (<= 10 (battery_charge)) (not (= ?l_from ?l_to)) (robot_at ?l_from) (not (robot_at ?l_to)))', pddl_domain)
        self.assertIn(':effect (and (not (robot_at ?l_from)) (robot_at ?l_to) (assign (battery_charge) (- (battery_charge) 10)))', pddl_domain)

        pddl_problem = w.get_problem()
        self.assertIn('(:domain robot-domain)', pddl_problem)
        self.assertIn('(:objects', pddl_problem)
        self.assertIn('l1 l2 - Location', pddl_problem)
        self.assertIn('(:init (robot_at l1) (= (battery_charge) 100))', pddl_problem)
        self.assertIn('(:goal (and (robot_at l2)))', pddl_problem)

    def test_robot_decrease_writer(self):
        problem = self.problems['robot_decrease'].problem

        w = PDDLWriter(problem)

        pddl_domain = w.get_domain()
        self.assertIn('(:requirements :strips :typing :negative-preconditions :equality :numeric-fluents)', pddl_domain)
        self.assertIn('(:types Location)', pddl_domain)
        self.assertIn('(:predicates (robot_at ?p0 - Location))', pddl_domain)
        self.assertIn('(:functions (battery_charge))', pddl_domain)
        self.assertIn('(:action move', pddl_domain)
        self.assertIn(':parameters ( ?l_from - Location ?l_to - Location)', pddl_domain)
        self.assertIn(':precondition (and (<= 10 (battery_charge)) (not (= ?l_from ?l_to)) (robot_at ?l_from) (not (robot_at ?l_to)))', pddl_domain)
        self.assertIn(':effect (and (not (robot_at ?l_from)) (robot_at ?l_to) (decrease (battery_charge) 10))', pddl_domain)

        pddl_problem = w.get_problem()
        self.assertIn('(:domain robot_decrease-domain)', pddl_problem)
        self.assertIn('(:objects', pddl_problem)
        self.assertIn('l1 l2 - Location', pddl_problem)
        self.assertIn('(:init (robot_at l1) (= (battery_charge) 100))', pddl_problem)
        self.assertIn('(:goal (and (robot_at l2)))', pddl_problem)

    def test_robot_loader_writer(self):
        problem = self.problems['robot_loader'].problem

        w = PDDLWriter(problem)

        pddl_domain = w.get_domain()
        self.assertIn('(:requirements :strips :typing :negative-preconditions :equality)', pddl_domain)
        self.assertIn('(:types Location)', pddl_domain)
        self.assertIn('(:predicates (robot_at ?p0 - Location) (cargo_at ?p0 - Location) (cargo_mounted))', pddl_domain)
        self.assertIn('(:action move', pddl_domain)
        self.assertIn(':parameters ( ?l_from - Location ?l_to - Location)', pddl_domain)
        self.assertIn(':precondition (and (not (= ?l_from ?l_to)) (robot_at ?l_from) (not (robot_at ?l_to)))', pddl_domain)
        self.assertIn(':effect (and (not (robot_at ?l_from)) (robot_at ?l_to))', pddl_domain)
        self.assertIn('(:action load', pddl_domain)
        self.assertIn(':parameters ( ?loc - Location)', pddl_domain)
        self.assertIn(':precondition (and (cargo_at ?loc) (robot_at ?loc) (not (cargo_mounted)))', pddl_domain)
        self.assertIn(':effect (and (not (cargo_at ?loc)) (cargo_mounted))', pddl_domain)
        self.assertIn('(:action unload', pddl_domain)
        self.assertIn(':parameters ( ?loc - Location)', pddl_domain)
        self.assertIn(':precondition (and (not (cargo_at ?loc)) (robot_at ?loc) (cargo_mounted))', pddl_domain)
        self.assertIn(':effect (and (cargo_at ?loc) (not (cargo_mounted)))', pddl_domain)

        pddl_problem = w.get_problem()
        self.assertIn('(:domain robot_loader-domain)', pddl_problem)
        self.assertIn('(:objects', pddl_problem)
        self.assertIn('l1 l2 - Location', pddl_problem)
        self.assertIn('(:init (robot_at l1) (cargo_at l2))', pddl_problem)
        self.assertIn('(:goal (and (cargo_at l1)))', pddl_problem)

    def test_robot_loader_adv_writer(self):
        problem = self.problems['robot_loader_adv'].problem

        w = PDDLWriter(problem)

        pddl_domain = w.get_domain()
        self.assertIn('(:requirements :strips :typing :negative-preconditions :equality)', pddl_domain)
        self.assertIn('(:types Robot Location Container)', pddl_domain)
        self.assertIn('(:predicates (robot_at ?p0 - Robot ?p1 - Location) (cargo_at ?p0 - Container ?p1 - Location) (cargo_mounted ?p0 - Container ?p1 - Robot))', pddl_domain)
        self.assertIn('(:action move', pddl_domain)
        self.assertIn(':parameters ( ?l_from - Location ?l_to - Location ?r - Robot)', pddl_domain)
        self.assertIn(':precondition (and (not (= ?l_from ?l_to)) (robot_at ?r ?l_from) (not (robot_at ?r ?l_to)))', pddl_domain)
        self.assertIn(':effect (and (not (robot_at ?r ?l_from)) (robot_at ?r ?l_to))', pddl_domain)
        self.assertIn('(:action load', pddl_domain)
        self.assertIn(':parameters ( ?loc - Location ?r - Robot ?c - Container)', pddl_domain)
        self.assertIn(':precondition (and (cargo_at ?c ?loc) (robot_at ?r ?loc) (not (cargo_mounted ?c ?r)))', pddl_domain)
        self.assertIn(':effect (and (not (cargo_at ?c ?loc)) (cargo_mounted ?c ?r))', pddl_domain)
        self.assertIn('(:action unload', pddl_domain)
        self.assertIn(':parameters ( ?loc - Location ?r - Robot ?c - Container)', pddl_domain)
        self.assertIn(':precondition (and (not (cargo_at ?c ?loc)) (robot_at ?r ?loc) (cargo_mounted ?c ?r))', pddl_domain)
        self.assertIn(':effect (and (cargo_at ?c ?loc) (not (cargo_mounted ?c ?r)))', pddl_domain)

        pddl_problem = w.get_problem()
        self.assertIn('(:domain robot_loader_adv-domain)', pddl_problem)
        self.assertIn('(:objects', pddl_problem)
        self.assertIn('r1 - Robot', pddl_problem)
        self.assertIn('l1 l2 l3 - Location', pddl_problem)
        self.assertIn('c1 - Container', pddl_problem)
        self.assertIn('(:init (robot_at r1 l1) (cargo_at c1 l2))', pddl_problem)
        self.assertIn('(:goal (and (cargo_at c1 l3) (robot_at r1 l1)))', pddl_problem)

    def test_depot_reader(self):
        reader = PDDLReader()

        domain_filename = os.path.join(PDDL_DOMAINS_PATH, 'depot', 'domain.pddl')
        problem_filename = os.path.join(PDDL_DOMAINS_PATH, 'depot', 'problem.pddl')
        problem = reader.parse_problem(domain_filename, problem_filename)

        self.assertTrue(problem is not None)
        self.assertEqual(len(problem.fluents()), 15)
        self.assertEqual(len(problem.actions_list()), 5)
        self.assertEqual(len(problem.objects(problem.user_type('object'))), 13)

    def test_counters_reader(self):
        reader = PDDLReader()

        domain_filename = os.path.join(PDDL_DOMAINS_PATH, 'counters', 'domain.pddl')
        problem_filename = os.path.join(PDDL_DOMAINS_PATH, 'counters', 'problem.pddl')
        problem = reader.parse_problem(domain_filename, problem_filename)

        self.assertTrue(problem is not None)
        self.assertEqual(len(problem.fluents()), 2)
        self.assertEqual(len(problem.actions_list()), 2)
        self.assertEqual(len(problem.objects(problem.user_type('counter'))), 4)

    def test_sailing_reader(self):
        reader = PDDLReader()

        domain_filename = os.path.join(PDDL_DOMAINS_PATH, 'sailing', 'domain.pddl')
        problem_filename = os.path.join(PDDL_DOMAINS_PATH, 'sailing', 'problem.pddl')
        problem = reader.parse_problem(domain_filename, problem_filename)

        self.assertTrue(problem is not None)
        self.assertEqual(len(problem.fluents()), 4)
        self.assertEqual(len(problem.actions_list()), 8)
        self.assertEqual(len(problem.objects(problem.user_type('boat'))), 2)
        self.assertEqual(len(problem.objects(problem.user_type('person'))), 2)

    def test_matchcellar_writer(self):
        problem = self.problems['matchcellar'].problem

        w = PDDLWriter(problem)

        pddl_domain = w.get_domain()
        self.assertIn('(define (domain MatchCellar-domain)', pddl_domain)
        self.assertIn('(:requirements :strips :typing :negative-preconditions :durative-actions)', pddl_domain)
        self.assertIn('(:types Match Fuse)', pddl_domain)
        self.assertIn('(:predicates (handfree) (light) (match_used ?p0 - Match) (fuse_mended ?p0 - Fuse))', pddl_domain)
        self.assertIn('(:durative-action light_match', pddl_domain)
        self.assertIn(':parameters ( ?m - Match)', pddl_domain)
        self.assertIn(':duration (= ?duration 6)', pddl_domain)
        self.assertIn(':condition (and (at start (not (match_used ?m))))', pddl_domain)
        self.assertIn(':effect (and (at start (match_used ?m)) (at start (light)) (at end (not (light)))))', pddl_domain)
        self.assertIn('(:durative-action mend_fuse', pddl_domain)
        self.assertIn(':parameters ( ?f - Fuse)', pddl_domain)
        self.assertIn(':duration (= ?duration 5)', pddl_domain)
        self.assertIn(':condition (and (at start (handfree))(at start (light))(over all (light))(at end (light)))', pddl_domain)
        self.assertIn(':effect (and (at start (not (handfree))) (at end (fuse_mended ?f)) (at end (handfree))))', pddl_domain)
