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
from unified_planning.io import PDDLWriter, PDDLReader
from unified_planning.test.examples import get_example_problems
from unified_planning.model.types import _UserType


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
        self.assertIn('(:predicates (x) (y ?semaphore - Semaphore))', pddl_domain)
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
        self.assertIn('(:predicates (robot_at ?position - Location))', pddl_domain)
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
        self.assertIn('(:predicates (robot_at ?position - Location))', pddl_domain)
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
        self.assertIn('(:predicates (robot_at ?position - Location) (cargo_at ?position - Location) (cargo_mounted))', pddl_domain)
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
        self.assertIn('(:predicates (robot_at ?robot - Robot ?position - Location) (cargo_at ?cargo - Container ?position - Location) (cargo_mounted ?cargo - Container ?robot - Robot))', pddl_domain)
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

    def test_matchcellar_writer(self):
        problem = self.problems['matchcellar'].problem

        w = PDDLWriter(problem)

        pddl_domain = w.get_domain()
        self.assertIn('(define (domain MatchCellar-domain)', pddl_domain)
        self.assertIn('(:requirements :strips :typing :negative-preconditions :durative-actions)', pddl_domain)
        self.assertIn('(:types Match Fuse)', pddl_domain)
        self.assertIn('(:predicates (handfree) (light) (match_used ?match - Match) (fuse_mended ?fuse - Fuse))', pddl_domain)
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

    def test_depot_reader(self):
        reader = PDDLReader()

        domain_filename = os.path.join(PDDL_DOMAINS_PATH, 'depot', 'domain.pddl')
        problem_filename = os.path.join(PDDL_DOMAINS_PATH, 'depot', 'problem.pddl')
        problem = reader.parse_problem(domain_filename, problem_filename)

        self.assertTrue(problem is not None)
        self.assertEqual(len(problem.fluents), 15)
        self.assertEqual(len(problem.actions), 5)
        self.assertEqual(len(list(problem.objects(problem.user_type('object')))), 13)

    def test_counters_reader(self):
        reader = PDDLReader()

        domain_filename = os.path.join(PDDL_DOMAINS_PATH, 'counters', 'domain.pddl')
        problem_filename = os.path.join(PDDL_DOMAINS_PATH, 'counters', 'problem.pddl')
        problem = reader.parse_problem(domain_filename, problem_filename)

        self.assertTrue(problem is not None)
        self.assertEqual(len(problem.fluents), 2)
        self.assertEqual(len(problem.actions), 2)
        self.assertEqual(len(list(problem.objects(problem.user_type('counter')))), 4)

    def test_sailing_reader(self):
        reader = PDDLReader()

        domain_filename = os.path.join(PDDL_DOMAINS_PATH, 'sailing', 'domain.pddl')
        problem_filename = os.path.join(PDDL_DOMAINS_PATH, 'sailing', 'problem.pddl')
        problem = reader.parse_problem(domain_filename, problem_filename)

        self.assertTrue(problem is not None)
        self.assertEqual(len(problem.fluents), 4)
        self.assertEqual(len(problem.actions), 8)
        self.assertEqual(len(list(problem.objects(problem.user_type('boat')))), 2)
        self.assertEqual(len(list(problem.objects(problem.user_type('person')))), 2)

    def test_matchcellar_reader(self):
        reader = PDDLReader()

        domain_filename = os.path.join(PDDL_DOMAINS_PATH, 'matchcellar', 'domain.pddl')
        problem_filename = os.path.join(PDDL_DOMAINS_PATH, 'matchcellar', 'problem.pddl')
        problem = reader.parse_problem(domain_filename, problem_filename)

        self.assertTrue(problem is not None)
        self.assertEqual(len(problem.fluents), 4)
        self.assertEqual(len(problem.actions), 2)
        self.assertEqual(len(list(problem.objects(problem.user_type('match')))), 3)
        self.assertEqual(len(list(problem.objects(problem.user_type('fuse')))), 3)

    def test_htn_transport_reader(self):
        reader = PDDLReader()

        domain_filename = os.path.join(PDDL_DOMAINS_PATH, 'htn-transport', 'domain.hddl')
        problem_filename = os.path.join(PDDL_DOMAINS_PATH, 'htn-transport', 'problem.hddl')
        problem = reader.parse_problem(domain_filename, problem_filename)

        assert isinstance(problem, up.model.htn.HierarchicalProblem)
        self.assertEqual(5, len(problem.fluents))
        self.assertEqual(4, len(problem.actions))
        self.assertEqual(["deliver", "get-to", "load", "unload"],
                         [task.name for task in problem.tasks])
        self.assertEqual(["m-deliver", "m-unload", "m-load", "m-drive-to", "m-drive-to-via", "m-i-am-there"],
                         [method.name for method in problem.methods])
        self.assertEqual(1, len(problem.method("m-drive-to").subtasks))
        self.assertEqual(2, len(problem.method("m-drive-to-via").subtasks))
        self.assertEqual(2, len(problem.task_network.subtasks))

    def test_examples_io(self):
        for example in self.problems.values():
            problem = example.problem
            kind = problem.kind
            if kind.has_intermediate_conditions_and_effects() or \
                kind.has_object_fluents():
                continue
            with tempfile.TemporaryDirectory() as tempdir:
                domain_filename = os.path.join(tempdir, 'domain.pddl')
                problem_filename = os.path.join(tempdir, 'problem.pddl')

                w = PDDLWriter(problem)
                w.write_domain(domain_filename)
                w.write_problem(problem_filename)

                reader = PDDLReader()
                parsed_problem = reader.parse_problem(domain_filename, problem_filename)

                if problem.has_type('object') and problem.kind.has_hierarchical_typing():
                    object_rename: str = 'object'
                    while problem.has_type(object_rename):
                        object_rename = f'{object_rename}_'
                    self.assertEqual(len(problem.fluents), len(parsed_problem.fluents))
                    self.assertTrue(_have_same_user_types_considering_object_renaming(problem, parsed_problem, object_rename))
                    self.assertEqual(len(problem.actions), len(parsed_problem.actions))
                    for a in problem.actions:
                        parsed_a = parsed_problem.action(a.name)
                        self.assertEqual(a.name, parsed_a.name)
                        for param, parsed_param in zip(a.parameters, parsed_a.parameters):
                            self.assertEqual(param.name, parsed_param.name)
                            self.assertTrue(_is_same_user_type_considering_object_renaming(param.type, parsed_param.type, object_rename))
                        if isinstance(a, unified_planning.model.InstantaneousAction):
                            self.assertEqual(len(a.effects), len(parsed_a.effects))
                        elif isinstance(a, unified_planning.model.DurativeAction):
                            self.assertEqual(a.duration, parsed_a.duration)
                            for t, e in a.effects.items():
                                self.assertEqual(len(e), len(parsed_a.effects[t]))
                else:
                    self.assertEqual(len(problem.fluents), len(parsed_problem.fluents))
                    self.assertEqual(set(problem.user_types), set(parsed_problem.user_types))
                    self.assertEqual(len(problem.actions), len(parsed_problem.actions))
                    for a in problem.actions:
                        parsed_a = parsed_problem.action(a.name)
                        self.assertEqual(a.name, parsed_a.name)
                        self.assertEqual(a.parameters, parsed_a.parameters)
                        if isinstance(a, unified_planning.model.InstantaneousAction):
                            self.assertEqual(len(a.effects), len(parsed_a.effects))
                        elif isinstance(a, unified_planning.model.DurativeAction):
                            self.assertEqual(a.duration, parsed_a.duration)
                            for t, e in a.effects.items():
                                self.assertEqual(len(e), len(parsed_a.effects[t]))

                    self.assertEqual(set(problem.all_objects), set(parsed_problem.all_objects))
                    self.assertEqual(len(problem.initial_values), len(parsed_problem.initial_values))

    def test_rationals(self):
        problem = self.problems['robot_decrease'].problem.clone()

        # Check perfect conversion
        battery = problem.fluent('battery_charge')
        problem.set_initial_value(battery, Fraction(5, 2))
        w = PDDLWriter(problem)
        pddl_txt = w.get_problem()
        self.assertNotIn('5/2', pddl_txt)
        self.assertIn('2.5', pddl_txt)

        # Check imperfect conversion
        with pytest.warns(UserWarning, match="cannot exactly represent") as warns:
            battery = problem.fluent('battery_charge')
            problem.set_initial_value(battery, Fraction(10, 3))
            w = PDDLWriter(problem)
            pddl_txt = w.get_problem()
            self.assertNotIn('10/3', pddl_txt)
            self.assertIn('3.333333333', pddl_txt)

def _is_same_user_type_considering_object_renaming(original_type: unified_planning.model.Type,
                                                    tested_type: unified_planning.model.Type,
                                                    object_rename: str) -> bool:
    assert isinstance(original_type, _UserType) and isinstance(tested_type, _UserType)
    if original_type.father is None: # case where original_type has no father
        if tested_type.father is not None:
            return False # original_type has a father, tested_type does not.
        if original_type.name != 'object': # fathers are both None, now we have to check the name
            return original_type.name == tested_type.name # original_type name is not object, so it should not be renamed
        else:
            return object_rename == tested_type.name # original_type name is object, so we expect it to be renamed
    else: # case where original_type has a father
        if tested_type.father is None:
            return False # and tested_type has no father
        if original_type.name != 'object': # original_type name is not object, so it should not be renamed, and both father's types are the same type
            return original_type.name == tested_type.name and _is_same_user_type_considering_object_renaming(original_type.father, tested_type.father, object_rename)
        else: # original_type name is object, so we expect it to be renamed, and both father's types are the same type
            return object_rename == tested_type.name and _is_same_user_type_considering_object_renaming(original_type.father, tested_type.father, object_rename)

def _have_same_user_types_considering_object_renaming(original_problem: unified_planning.model.Problem, tested_problem: unified_planning.model.Problem, object_rename: str) -> bool:
    for original_type in original_problem.user_types:
        if cast(_UserType, original_type).name != 'object':
            if not _is_same_user_type_considering_object_renaming(original_type, tested_problem.user_type(cast(_UserType, original_type).name), object_rename):
                return False
        else:
            if not _is_same_user_type_considering_object_renaming(original_type, tested_problem.user_type(object_rename), object_rename):
                return False
    return True
