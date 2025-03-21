# Copyright 2021-2023 AIPlan4EU project
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
import pytest
from typing import cast
import unified_planning
from unified_planning.shortcuts import *
from unified_planning.test import (
    unittest_TestCase,
    main,
    skipIfNoOneshotPlannerForProblemKind,
)
from unified_planning.io import (
    PDDLWriter,
    UPPDDLReader,
    PDDLReader,
    extract_pddl_requirements,
)
from unified_planning.test.examples import get_example_problems
from unified_planning.exceptions import (
    UPProblemDefinitionError,
    UPUnsupportedProblemTypeError,
)
from unified_planning.model.metrics import MinimizeSequentialPlanLength
from unified_planning.plans import SequentialPlan
from unified_planning.model.problem_kind import simple_numeric_kind
from unified_planning.model.types import _UserType
from unified_planning.interop import (
    check_ai_pddl_requirements,
    convert_problem_from_ai_pddl,
)

from pddl import parse_domain, parse_problem  # type: ignore


FILE_PATH = os.path.dirname(os.path.abspath(__file__))
PDDL_DOMAINS_PATH = os.path.join(FILE_PATH, "pddl")


class TestPddlIO(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    def _normalized_pddl_str(self, w):
        return " ".join(w.split()).replace("( ", "(").replace(" )", ")")

    def test_basic_writer(self):
        problem = self.problems["basic"].problem

        w = PDDLWriter(problem)

        pddl_domain = self._normalized_pddl_str(w.get_domain())
        self.assertIn("(:requirements :strips :negative-preconditions)", pddl_domain)
        self.assertIn("(:predicates (x))", pddl_domain)
        self.assertIn("(:action a", pddl_domain)
        self.assertIn(":parameters ()", pddl_domain)
        self.assertIn(":precondition (and (not (x)))", pddl_domain)
        self.assertIn(":effect (and (x))", pddl_domain)

        pddl_problem = self._normalized_pddl_str(w.get_problem())
        self.assertIn("(:domain basic-domain)", pddl_problem)
        self.assertIn("(:init)", pddl_problem)
        self.assertIn("(:goal (and (x)))", pddl_problem)

    def test_basic_non_constant_boolean_assignment(self):
        problem = self.problems["basic"].problem.clone()
        x = problem.fluent("x")
        y = problem.add_fluent("y", default_initial_value=True)
        a = problem.action("a")
        a.clear_effects()
        a.add_effect(x, y)

        w = PDDLWriter(problem)
        with self.assertRaises(UPProblemDefinitionError) as e:
            _ = w.get_domain()

        w = PDDLWriter(problem, rewrite_bool_assignments=True)
        pddl_domain = self._normalized_pddl_str(w.get_domain())
        self.assertIn("(:requirements :strips :negative-preconditions)", pddl_domain)
        self.assertIn("(:predicates (x) (y))", pddl_domain)
        self.assertIn("(:action a", pddl_domain)
        self.assertIn(":parameters ()", pddl_domain)
        self.assertIn(":precondition (and (not (x)))", pddl_domain)
        self.assertIn(
            ":effect (and (when (y) (x)) (when (not (y)) (not (x)))))", pddl_domain
        )

        pddl_problem = self._normalized_pddl_str(w.get_problem())
        self.assertIn("(:domain basic-domain)", pddl_problem)
        self.assertIn("(:init (y))", pddl_problem)
        self.assertIn("(:goal (and (x)))", pddl_problem)

    def test_basic_conditional_writer(self):
        problem = self.problems["basic_conditional"].problem

        self.assertTrue(problem.action("a_x").is_conditional())
        self.assertFalse(problem.action("a_y").is_conditional())

        w = PDDLWriter(problem)

        pddl_domain = self._normalized_pddl_str(w.get_domain())
        self.assertIn(
            "(:requirements :strips :negative-preconditions :conditional-effects)",
            pddl_domain,
        )
        self.assertIn("(:predicates (x) (y))", pddl_domain)
        self.assertIn("(:action a_x", pddl_domain)
        self.assertIn(":parameters ()", pddl_domain)
        self.assertIn(":precondition (and (not (x)))", pddl_domain)
        self.assertIn(":effect (and (when (y) (x)))", pddl_domain)
        self.assertIn("(:action a_y", pddl_domain)
        self.assertIn(":parameters ()", pddl_domain)
        self.assertIn(":precondition (and (not (y)))", pddl_domain)
        self.assertIn(":effect (and (y))", pddl_domain)

        pddl_problem = self._normalized_pddl_str(w.get_problem())
        self.assertIn("(:domain basic_conditional-domain)", pddl_problem)
        self.assertIn("(:init)", pddl_problem)
        self.assertIn("(:goal (and (x)))", pddl_problem)

    def test_processes_writer(self):
        problem = self.problems["1d_movement"].problem
        w = PDDLWriter(problem)
        pddl_domain = self._normalized_pddl_str(w.get_domain())
        self.assertIn("(:process moving", pddl_domain)
        self.assertIn("#t", pddl_domain)

    def test_basic_exists_writer(self):
        problem = self.problems["basic_exists"].problem

        w = PDDLWriter(problem)

        pddl_domain = self._normalized_pddl_str(w.get_domain())
        self.assertIn(
            "(:requirements :strips :typing :existential-preconditions)", pddl_domain
        )
        self.assertIn("(:predicates (x) (y ?semaphore - semaphore))", pddl_domain)
        self.assertIn("(:action a", pddl_domain)
        self.assertIn(":parameters ()", pddl_domain)
        self.assertIn(
            ":precondition (and (exists (?s - semaphore) (y ?s)))", pddl_domain
        )
        self.assertIn(":effect (and (x))", pddl_domain)

        pddl_problem = self._normalized_pddl_str(w.get_problem())
        self.assertIn("(:domain basic_exists-domain)", pddl_problem)
        self.assertIn("(:objects o1 o2 - semaphore)", pddl_problem)
        self.assertIn("(:init (y o1))", pddl_problem)
        self.assertIn("(:goal (and (x)))", pddl_problem)

    def test_basic_tils_writer(self):
        problem = self.problems["basic_tils"].problem

        w = PDDLWriter(problem)

        pddl_domain = self._normalized_pddl_str(w.get_domain())
        self.assertIn(
            "(:requirements :strips :durative-actions :timed-initial-literals)",
            pddl_domain,
        )
        self.assertIn("(:predicates (x) (y))", pddl_domain)
        self.assertIn("(:durative-action a", pddl_domain)
        self.assertIn(":parameters ()", pddl_domain)
        self.assertIn(":duration (= ?duration 1)", pddl_domain)
        self.assertIn(
            ":condition (and (at start (y))(over all (y))(at end (y)))",
            pddl_domain,
        )
        self.assertIn(":effect (and (at end (x)))", pddl_domain)

        norm_pddl_problem = self._normalized_pddl_str(w.get_problem())
        self.assertIn("(:domain basic_tils-domain)", norm_pddl_problem)
        self.assertIn(
            "(:init (at 5.0 (not (x))) (at 2.0 (y)) (at 8.0 (not (y))))",
            norm_pddl_problem,
        )
        self.assertIn("(:goal (and (x)))", norm_pddl_problem)

        pddl_problem = w.get_problem()
        self.assertIn("(at 5.0 (not (x)))", pddl_problem)
        self.assertIn("(at 2.0 (y))", pddl_problem)
        self.assertIn("(at 8.0 (not (y)))", pddl_problem)

    def test_robot_writer(self):
        problem = self.problems["robot"].problem

        w = PDDLWriter(problem)

        pddl_domain = self._normalized_pddl_str(w.get_domain())
        self.assertIn(
            "(:requirements :strips :typing :negative-preconditions :equality :numeric-fluents)",
            pddl_domain,
        )
        self.assertIn("(:types location)", pddl_domain)
        self.assertIn("(:predicates (robot_at ?position - location))", pddl_domain)
        self.assertIn("(:functions (battery_charge))", pddl_domain)
        self.assertIn("(:action move", pddl_domain)
        self.assertIn(":parameters (?l_from - location ?l_to - location)", pddl_domain)
        self.assertIn(
            ":precondition (and (<= 10 (battery_charge)) (not (= ?l_from ?l_to)) (robot_at ?l_from) (not (robot_at ?l_to)))",
            pddl_domain,
        )
        self.assertIn(
            ":effect (and (not (robot_at ?l_from)) (robot_at ?l_to) (assign (battery_charge) (- (battery_charge) 10)))",
            pddl_domain,
        )

        pddl_problem = self._normalized_pddl_str(w.get_problem())
        self.assertIn("(:domain robot-domain)", pddl_problem)
        self.assertIn("(:objects", pddl_problem)
        self.assertIn("l1 l2 - location", pddl_problem)
        self.assertIn("(:init (robot_at l1) (= (battery_charge) 100))", pddl_problem)
        self.assertIn("(:goal (and (robot_at l2)))", pddl_problem)

    def test_robot_decrease_writer(self):
        problem = self.problems["robot_decrease"].problem

        w = PDDLWriter(problem)

        pddl_domain = self._normalized_pddl_str(w.get_domain())
        self.assertIn(
            "(:requirements :strips :typing :negative-preconditions :equality :numeric-fluents)",
            pddl_domain,
        )
        self.assertIn("(:types location)", pddl_domain)
        self.assertIn("(:predicates (robot_at ?position - location))", pddl_domain)
        self.assertIn("(:functions (battery_charge))", pddl_domain)
        self.assertIn("(:action move", pddl_domain)
        self.assertIn(":parameters (?l_from - location ?l_to - location)", pddl_domain)
        self.assertIn(
            ":precondition (and (<= 10 (battery_charge)) (not (= ?l_from ?l_to)) (robot_at ?l_from) (not (robot_at ?l_to)))",
            pddl_domain,
        )
        self.assertIn(
            ":effect (and (not (robot_at ?l_from)) (robot_at ?l_to) (decrease (battery_charge) 10))",
            pddl_domain,
        )

        pddl_problem = self._normalized_pddl_str(w.get_problem())
        self.assertIn("(:domain robot_decrease-domain)", pddl_problem)
        self.assertIn("(:objects", pddl_problem)
        self.assertIn("l1 l2 - location", pddl_problem)
        self.assertIn("(:init (robot_at l1) (= (battery_charge) 100))", pddl_problem)
        self.assertIn("(:goal (and (robot_at l2)))", pddl_problem)

    def test_robot_loader_writer(self):
        problem = self.problems["robot_loader"].problem

        w = PDDLWriter(problem)

        pddl_domain = self._normalized_pddl_str(w.get_domain())
        self.assertIn(
            "(:requirements :strips :typing :negative-preconditions :equality)",
            pddl_domain,
        )
        self.assertIn("(:types location)", pddl_domain)
        self.assertIn(
            "(:predicates (robot_at ?position - location) (cargo_at ?position - location) (cargo_mounted))",
            pddl_domain,
        )
        self.assertIn("(:action move", pddl_domain)
        self.assertIn(":parameters (?l_from - location ?l_to - location)", pddl_domain)
        self.assertIn(
            ":precondition (and (not (= ?l_from ?l_to)) (robot_at ?l_from) (not (robot_at ?l_to)))",
            pddl_domain,
        )
        self.assertIn(
            ":effect (and (not (robot_at ?l_from)) (robot_at ?l_to))", pddl_domain
        )
        self.assertIn("(:action load", pddl_domain)
        self.assertIn(":parameters (?loc - location)", pddl_domain)
        self.assertIn(
            ":precondition (and (cargo_at ?loc) (robot_at ?loc) (not (cargo_mounted)))",
            pddl_domain,
        )
        self.assertIn(
            ":effect (and (not (cargo_at ?loc)) (cargo_mounted))", pddl_domain
        )
        self.assertIn("(:action unload", pddl_domain)
        self.assertIn(":parameters (?loc - location)", pddl_domain)
        self.assertIn(
            ":precondition (and (not (cargo_at ?loc)) (robot_at ?loc) (cargo_mounted))",
            pddl_domain,
        )
        self.assertIn(
            ":effect (and (cargo_at ?loc) (not (cargo_mounted)))", pddl_domain
        )

        pddl_problem = self._normalized_pddl_str(w.get_problem())
        self.assertIn("(:domain robot_loader-domain)", pddl_problem)
        self.assertIn("(:objects", pddl_problem)
        self.assertIn("l1 l2 - location", pddl_problem)
        self.assertIn("(:init (robot_at l1) (cargo_at l2))", pddl_problem)
        self.assertIn("(:goal (and (cargo_at l1)))", pddl_problem)

    def test_robot_loader_adv_writer(self):
        problem = self.problems["robot_loader_adv"].problem

        w = PDDLWriter(problem)

        pddl_domain = self._normalized_pddl_str(w.get_domain())
        self.assertIn(
            "(:requirements :strips :typing :negative-preconditions :equality)",
            pddl_domain,
        )
        self.assertIn("(:types robot location container)", pddl_domain)
        self.assertIn(
            "(:predicates (robot_at ?robot - robot ?position - location) (cargo_at ?cargo - container ?position - location) (cargo_mounted ?cargo - container ?robot - robot))",
            pddl_domain,
        )
        self.assertIn("(:action move", pddl_domain)
        self.assertIn(
            ":parameters (?l_from - location ?l_to - location ?r - robot)", pddl_domain
        )
        self.assertIn(
            ":precondition (and (not (= ?l_from ?l_to)) (robot_at ?r ?l_from) (not (robot_at ?r ?l_to)))",
            pddl_domain,
        )
        self.assertIn(
            ":effect (and (not (robot_at ?r ?l_from)) (robot_at ?r ?l_to))", pddl_domain
        )
        self.assertIn("(:action load", pddl_domain)
        self.assertIn(
            ":parameters (?loc - location ?r - robot ?c - container)", pddl_domain
        )
        self.assertIn(
            ":precondition (and (cargo_at ?c ?loc) (robot_at ?r ?loc) (not (cargo_mounted ?c ?r)))",
            pddl_domain,
        )
        self.assertIn(
            ":effect (and (not (cargo_at ?c ?loc)) (cargo_mounted ?c ?r))", pddl_domain
        )
        self.assertIn("(:action unload", pddl_domain)
        self.assertIn(
            ":parameters (?loc - location ?r - robot ?c - container)", pddl_domain
        )
        self.assertIn(
            ":precondition (and (not (cargo_at ?c ?loc)) (robot_at ?r ?loc) (cargo_mounted ?c ?r))",
            pddl_domain,
        )
        self.assertIn(
            ":effect (and (cargo_at ?c ?loc) (not (cargo_mounted ?c ?r)))", pddl_domain
        )

        pddl_problem = self._normalized_pddl_str(w.get_problem())
        self.assertIn("(:domain robot_loader_adv-domain)", pddl_problem)
        self.assertIn("(:objects", pddl_problem)
        self.assertIn("r1 - robot", pddl_problem)
        self.assertIn("l1 l2 l3 - location", pddl_problem)
        self.assertIn("c1 - container", pddl_problem)
        self.assertIn("(:init (robot_at r1 l1) (cargo_at c1 l2))", pddl_problem)
        self.assertIn("(:goal (and (cargo_at c1 l3) (robot_at r1 l1)))", pddl_problem)

    def test_matchcellar_writer(self):
        problem = self.problems["matchcellar"].problem

        w = PDDLWriter(problem)

        pddl_domain = self._normalized_pddl_str(w.get_domain())
        self.assertIn("(define (domain matchcellar-domain)", pddl_domain)
        self.assertIn(
            "(:requirements :strips :typing :negative-preconditions :durative-actions)",
            pddl_domain,
        )
        self.assertIn("(:types match fuse)", pddl_domain)
        self.assertIn(
            "(:predicates (handfree) (light) (match_used ?match - match) (fuse_mended ?fuse - fuse))",
            pddl_domain,
        )
        self.assertIn("(:durative-action light_match", pddl_domain)
        self.assertIn(":parameters (?m - match)", pddl_domain)
        self.assertIn(":duration (= ?duration 6)", pddl_domain)
        self.assertIn(":condition (and (at start (not (match_used ?m))))", pddl_domain)
        self.assertIn(
            ":effect (and (at start (match_used ?m)) (at start (light)) (at end (not (light)))))",
            pddl_domain,
        )
        self.assertIn("(:durative-action mend_fuse", pddl_domain)
        self.assertIn(":parameters (?f - fuse)", pddl_domain)
        self.assertIn(":duration (= ?duration 5)", pddl_domain)
        self.assertIn(
            ":condition (and (at start (handfree)) (at start (light))(over all (light))(at end (light)))",
            pddl_domain,
        )
        self.assertIn(
            ":effect (and (at start (not (handfree))) (at end (fuse_mended ?f)) (at end (handfree))))",
            pddl_domain,
        )

    def test_renamings(self):
        problem = self.problems["hierarchical_blocks_world"].problem
        problem = problem.clone()
        move = problem.action("move")
        move.name = "move-move"

        Block = problem.user_type("Block")
        block_4 = Object("block-4", Block)
        problem.add_object(block_4)

        w = PDDLWriter(problem)
        plan = SequentialPlan(
            [move(block_4, problem.object("block_3"), problem.object("block_2"))]
        )
        plan_str = w.get_plan(plan)

        r = UPPDDLReader()
        test_plan = r.parse_plan_string(problem, plan_str, w.get_item_named)

        self.assertEqual(plan, test_plan)

    def test_depot_reader(self):
        reader = UPPDDLReader()

        domain_filename = os.path.join(PDDL_DOMAINS_PATH, "depot", "domain.pddl")
        problem_filename = os.path.join(PDDL_DOMAINS_PATH, "depot", "problem.pddl")
        problem = reader.parse_problem(domain_filename, problem_filename)

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 15)
        self.assertEqual(len(problem.actions), 5)
        self.assertEqual(len(list(problem.objects(problem.user_type("object")))), 13)

        with open(domain_filename, "r", encoding="utf-8") as file:
            domain_str = file.read()
        with open(problem_filename, "r", encoding="utf-8") as file:
            problem_str = file.read()

        problem_2 = reader.parse_problem_string(domain_str, problem_str)
        self.assertEqual(problem, problem_2)

    def test_counters_reader(self):
        reader = UPPDDLReader()

        domain_filename = os.path.join(PDDL_DOMAINS_PATH, "counters", "domain.pddl")
        problem_filename = os.path.join(PDDL_DOMAINS_PATH, "counters", "problem.pddl")
        problem = reader.parse_problem(domain_filename, problem_filename)

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 2)
        self.assertEqual(len(problem.actions), 2)
        self.assertEqual(len(list(problem.objects(problem.user_type("counter")))), 4)

        with open(domain_filename, "r", encoding="utf-8") as file:
            domain_str = file.read()
        with open(problem_filename, "r", encoding="utf-8") as file:
            problem_str = file.read()

        problem_2 = reader.parse_problem_string(domain_str, problem_str)
        self.assertEqual(problem, problem_2)

    def test_sailing_reader(self):
        reader = UPPDDLReader()

        domain_filename = os.path.join(PDDL_DOMAINS_PATH, "sailing", "domain.pddl")
        problem_filename = os.path.join(PDDL_DOMAINS_PATH, "sailing", "problem.pddl")
        problem = reader.parse_problem(domain_filename, problem_filename)

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 4)
        self.assertEqual(len(problem.actions), 8)
        self.assertEqual(len(list(problem.objects(problem.user_type("boat")))), 2)
        self.assertEqual(len(list(problem.objects(problem.user_type("person")))), 2)

        with open(domain_filename, "r", encoding="utf-8") as file:
            domain_str = file.read()
        with open(problem_filename, "r", encoding="utf-8") as file:
            problem_str = file.read()

        problem_2 = reader.parse_problem_string(domain_str, problem_str)
        self.assertEqual(problem, problem_2)

    def test_non_linear_car(self):
        reader = UPPDDLReader()

        domain_filename = os.path.join(PDDL_DOMAINS_PATH, "car_nl", "d.pddl")
        problem_filename = os.path.join(PDDL_DOMAINS_PATH, "car_nl", "p.pddl")
        problem = reader.parse_problem(domain_filename, problem_filename)

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 8)
        n_proc = len(list([el for el in problem.processes if isinstance(el, Process)]))
        n_eve = len(list([el for el in problem.events if isinstance(el, Event)]))
        self.assertEqual(n_proc, 3)
        self.assertEqual(n_eve, 1)
        found_drag_ahead = False
        for ele in problem.processes:
            if isinstance(ele, Process):
                for e in ele.effects:
                    self.assertTrue(
                        (e.kind == EffectKind.CONTINUOUS_INCREASE)
                        or (e.kind == EffectKind.CONTINUOUS_DECREASE)
                    )
                if ele.name == "drag_ahead":
                    found_drag_ahead = True
                    self.assertTrue("engine_running" in str(ele))
                    self.assertTrue("drag_coefficient" in str(ele))
        self.assertTrue(found_drag_ahead)

    def test_matchcellar_reader(self):
        reader = UPPDDLReader()

        domain_filename = os.path.join(PDDL_DOMAINS_PATH, "matchcellar", "domain.pddl")
        problem_filename = os.path.join(
            PDDL_DOMAINS_PATH, "matchcellar", "problem.pddl"
        )
        problem = reader.parse_problem(domain_filename, problem_filename)

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 4)
        self.assertEqual(len(problem.actions), 2)
        self.assertEqual(len(list(problem.objects(problem.user_type("match")))), 3)
        self.assertEqual(len(list(problem.objects(problem.user_type("fuse")))), 3)

        with open(domain_filename, "r", encoding="utf-8") as file:
            domain_str = file.read()
        with open(problem_filename, "r", encoding="utf-8") as file:
            problem_str = file.read()

        problem_2 = reader.parse_problem_string(domain_str, problem_str)
        self.assertEqual(problem, problem_2)

    def test_parking_reader(self):
        reader = UPPDDLReader()

        domain_filename = os.path.join(
            PDDL_DOMAINS_PATH, "parking_action_cost", "domain.pddl"
        )
        problem_filename = os.path.join(
            PDDL_DOMAINS_PATH, "parking_action_cost", "problem.pddl"
        )
        problem = reader.parse_problem(domain_filename, problem_filename)

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 5)
        self.assertEqual(len(problem.actions), 4)
        self.assertEqual(len(list(problem.objects(problem.user_type("car")))), 2)
        self.assertEqual(len(list(problem.objects(problem.user_type("curb")))), 4)
        self.assertEqual(len(problem.quality_metrics), 1)
        self.assertTrue(problem.quality_metrics[0].is_minimize_action_costs())

        with open(domain_filename, "r", encoding="utf-8") as file:
            domain_str = file.read()
        with open(problem_filename, "r", encoding="utf-8") as file:
            problem_str = file.read()

        problem_2 = reader.parse_problem_string(domain_str, problem_str)
        self.assertEqual(problem, problem_2)

    def _test_htn_transport_reader(self, problem):
        assert isinstance(problem, up.model.htn.HierarchicalProblem)
        self.assertEqual(5, len(problem.fluents))
        self.assertEqual(4, len(problem.actions))
        self.assertEqual(
            ["deliver", "get-to", "load", "unload"],
            [task.name for task in problem.tasks],
        )
        self.assertEqual(
            [
                "m-deliver",
                "m-unload",
                "m-load",
                "m-drive-to",
                "m-drive-to-via",
                "m-i-am-there",
            ],
            [method.name for method in problem.methods],
        )
        self.assertEqual(1, len(problem.method("m-drive-to").subtasks))
        self.assertEqual(2, len(problem.method("m-drive-to-via").subtasks))
        self.assertEqual(2, len(problem.task_network.subtasks))

    def test_htn_transport_reader(self):
        reader = UPPDDLReader()

        domain_filename = os.path.join(
            PDDL_DOMAINS_PATH, "htn-transport", "domain.hddl"
        )
        problem_filename = os.path.join(
            PDDL_DOMAINS_PATH, "htn-transport", "problem.hddl"
        )
        problem = reader.parse_problem(domain_filename, problem_filename)
        self._test_htn_transport_reader(problem)

        with open(domain_filename, "r", encoding="utf-8") as file:
            domain_str = file.read()
        with open(problem_filename, "r", encoding="utf-8") as file:
            problem_str = file.read()

        problem_2 = reader.parse_problem_string(domain_str, problem_str)
        self._test_htn_transport_reader(problem_2)

    def test_examples_io(self):
        for example in self.problems.values():
            problem = example.problem
            kind = problem.kind
            if (
                kind.has_intermediate_conditions_and_effects()
                or kind.has_object_fluents()
                or kind.has_oversubscription()
                or kind.has_timed_goals()
                or kind.has_bool_fluent_parameters()
                or kind.has_bounded_int_fluent_parameters()
                or kind.has_bool_action_parameters()
                or kind.has_bounded_int_action_parameters()
                or kind.has_unbounded_int_action_parameters()
                or kind.has_real_action_parameters()
                or kind.has_scheduling()
            ):
                continue
            with tempfile.TemporaryDirectory() as tempdir:
                domain_filename = os.path.join(tempdir, "domain.pddl")
                problem_filename = os.path.join(tempdir, "problem.pddl")

                w = PDDLWriter(problem)
                w.write_domain(domain_filename)
                w.write_problem(problem_filename)

                # if problem.kind.has_final_value():
                #     with open(domain_filename, "r") as domain_file:
                #         print(domain_file.read())
                #     with open(problem_filename, "r") as problem_file:
                #         print(problem_file.read())
                #     print(problem.name)
                #     assert False

                with open(domain_filename, "r") as domain_file:
                    domain_str = domain_file.read()

                general_reader = PDDLReader(disable_warnings=True)

                for i in range(3):
                    if i == 0:
                        parsed_problem = general_reader.parse_problem(
                            domain_filename, problem_filename
                        )
                    elif i == 1:
                        reader = UPPDDLReader()
                        parsed_problem = reader.parse_problem(
                            domain_filename, problem_filename
                        )
                    elif not check_ai_pddl_requirements(
                        extract_pddl_requirements(domain_str)
                    ):  # skip problems with ai_pddl that do not respect the requirements
                        assert i == 2
                        continue
                    else:
                        assert i == 2
                        try:
                            ai_problem = parse_domain(domain_filename)
                            ai_domain = parse_problem(problem_filename)
                        except Exception as _:
                            # skip problems where ai_pddl parsing fails; they are out of the scope of this testing
                            continue
                        parsed_problem = convert_problem_from_ai_pddl(
                            ai_problem, ai_domain
                        )

                    # Case where the reader does not convert the final_value back to actions_cost.
                    if (
                        kind.has_actions_cost()
                        and parsed_problem.kind.has_final_value()
                    ):
                        self.assertEqual(
                            len(problem.fluents) + 1, len(parsed_problem.fluents)
                        )
                    else:
                        self.assertEqual(
                            len(problem.fluents), len(parsed_problem.fluents)
                        )

                    self.assertTrue(
                        _have_same_user_types_considering_renamings(
                            problem, parsed_problem, w.get_item_named
                        )
                    )
                    self.assertEqual(len(problem.actions), len(parsed_problem.actions))
                    self.assertEqual(
                        len(problem.processes),
                        len(parsed_problem.processes),
                    )
                    self.assertEqual(
                        len(problem.events),
                        len(parsed_problem.events),
                    )
                    for a in problem.actions:
                        parsed_a = parsed_problem.action(w.get_pddl_name(a))
                        self.assertEqual(a, w.get_item_named(parsed_a.name))

                        for param, parsed_param in zip(
                            a.parameters, parsed_a.parameters
                        ):
                            self.assertEqual(
                                param.type,
                                w.get_item_named(
                                    cast(_UserType, parsed_param.type).name
                                ),
                            )
                        if isinstance(a, InstantaneousAction):
                            assert isinstance(parsed_a, InstantaneousAction)
                            if (
                                kind.has_actions_cost()
                                and parsed_problem.kind.has_final_value()
                            ):
                                self.assertEqual(
                                    len(a.effects) + 1, len(parsed_a.effects)
                                )
                            else:
                                self.assertEqual(len(a.effects), len(parsed_a.effects))
                        elif isinstance(a, DurativeAction):
                            assert isinstance(parsed_a, DurativeAction)
                            self.assertEqual(str(a.duration), str(parsed_a.duration))
                            for t, e in a.effects.items():
                                self.assertEqual(len(e), len(parsed_a.effects[t]))
                            for i, ce in a.continuous_effects.items():
                                self.assertEqual(
                                    len(ce), len(parsed_a.continuous_effects[i])
                                )
                    self.assertEqual(
                        len(problem.trajectory_constraints),
                        len(parsed_problem.trajectory_constraints),
                    )
                    self.assertEqual(
                        set(map(str, problem.trajectory_constraints)),
                        set(map(str, parsed_problem.trajectory_constraints)),
                    )
                    if problem.quality_metrics:
                        self.assertTrue(
                            parsed_problem.quality_metrics, f"{problem.name}, {i}"
                        )
                        self.assertEqual(
                            type(problem.quality_metrics[0]),
                            type(parsed_problem.quality_metrics[0]),
                        )

    def test_basic_with_object_constant(self):
        problem = self.problems["basic_with_object_constant"].problem

        w = PDDLWriter(problem)

        pddl_domain = self._normalized_pddl_str(w.get_domain())
        self.assertIn("(define (domain basic_with_object_constant-domain)", pddl_domain)
        self.assertIn(
            "(:requirements :strips :typing :negative-preconditions)",
            pddl_domain,
        )
        self.assertIn("(:constants", pddl_domain)
        self.assertIn("l1 - location)", pddl_domain)
        self.assertIn("(:types location)", pddl_domain)
        self.assertIn(
            "(:predicates (is_at ?loc - location))",
            pddl_domain,
        )
        self.assertIn("(:action move", pddl_domain)
        self.assertIn(":parameters (?l_from - location ?l_to - location)", pddl_domain)
        self.assertIn(
            ":precondition (and (is_at ?l_from) (not (is_at ?l_to)))", pddl_domain
        )
        self.assertIn(
            ":effect (and (not (is_at ?l_from)) (is_at ?l_to)))",
            pddl_domain,
        )
        self.assertIn("(:action move_to_l1", pddl_domain)
        self.assertIn(":parameters (?l_from - location)", pddl_domain)
        self.assertIn(
            ":precondition (and (is_at ?l_from) (not (is_at l1)))", pddl_domain
        )
        self.assertIn(
            ":effect (and (not (is_at ?l_from)) (is_at l1)))",
            pddl_domain,
        )

        pddl_problem = self._normalized_pddl_str(w.get_problem())
        self.assertIn("(:domain basic_with_object_constant-domain)", pddl_problem)
        self.assertIn("(:objects", pddl_problem)
        self.assertIn("l2 - location)", pddl_problem)
        self.assertIn("(:init (is_at l1))", pddl_problem)
        self.assertIn("(:goal (and (is_at l2))))", pddl_problem)

        expected_domain = """(define (domain basic_with_object_constant-domain)
 (:requirements :strips :typing :negative-preconditions)
 (:types location)
 (:constants
   l1 - location
 )
 (:predicates (is_at ?loc - location))
 (:action move
  :parameters ( ?l_from - location ?l_to - location)
  :precondition (and (is_at ?l_from) (not (is_at ?l_to)))
  :effect (and (not (is_at ?l_from)) (is_at ?l_to)))
 (:action move_to_l1
  :parameters ( ?l_from - location)
  :precondition (and (is_at ?l_from) (not (is_at l1)))
  :effect (and (not (is_at ?l_from)) (is_at l1)))
)
"""
        expected_problem = """(define (problem basic_with_object_constant-problem)
 (:domain basic_with_object_constant-domain)
 (:objects
   l2 - location
 )
 (:init (is_at l1))
 (:goal (and (is_at l2)))
)
"""

    def test_rationals(self):
        problem = self.problems["robot_decrease"].problem.clone()

        # Check perfect conversion
        battery = problem.fluent("battery_charge")
        problem.set_initial_value(battery, Fraction(5, 2))
        w = PDDLWriter(problem)
        pddl_txt = w.get_problem()
        self.assertNotIn("5/2", pddl_txt)
        self.assertIn("2.5", pddl_txt)

        # Check imperfect conversion
        with pytest.warns(UserWarning, match="cannot exactly represent") as warns:
            battery = problem.fluent("battery_charge")
            problem.set_initial_value(battery, Fraction(10, 3))
            w = PDDLWriter(problem)
            pddl_txt = w.get_problem()
            self.assertNotIn("10/3", pddl_txt)
            self.assertIn("3.333333333", pddl_txt)

    def test_ad_hoc_1(self):
        when = UserType("when")
        fl = Fluent("4ction")
        obj_1 = Object("obj_1", when)
        obj_2 = Object("OBJ_1", when)
        act = InstantaneousAction("forall", AND=when)
        fluent = act.parameter("AND")
        act.add_effect(fl, True, Equals(fluent, obj_1))
        problem = Problem("ad_hoc")
        problem.add_fluent(fl)
        problem.add_action(act)
        problem.add_object(obj_1)
        problem.add_object(obj_2)
        problem.set_initial_value(fl, False)
        w = PDDLWriter(problem)
        pddl_domain = self._normalized_pddl_str(w.get_domain())
        self.assertIn("(define (domain ad_hoc-domain)", pddl_domain)
        self.assertIn(
            "(:requirements :strips :typing :equality :conditional-effects)",
            pddl_domain,
        )
        self.assertIn("(:types when_)", pddl_domain)
        self.assertIn("(:constants obj_1 - when_)", pddl_domain)
        self.assertIn("(:predicates (f_4ction))", pddl_domain)
        self.assertIn("(:action forall_", pddl_domain)
        self.assertIn(":parameters (?and_ - when_)", pddl_domain)
        self.assertIn(":effect (and (when (= ?and_ obj_1) (f_4ction)))))", pddl_domain)

        pddl_problem = self._normalized_pddl_str(w.get_problem())
        self.assertIn("(define (problem ad_hoc-problem)", pddl_problem)
        self.assertIn("(:domain ad_hoc-domain)", pddl_problem)
        self.assertIn("(:objects obj_1_0 - when_)", pddl_problem)
        self.assertIn("(:init)", pddl_problem)
        self.assertIn("(:goal (and)))", pddl_problem)
        expected_domain = """(define (domain ad_hoc-domain)
 (:requirements :strips :typing :equality :conditional-effects)
 (:types when_)
 (:constants
   obj_1 - when_
 )
 (:predicates (f_4ction))
 (:action forall_
  :parameters ( ?and_ - when_)
  :effect (and (when (= ?and_ obj_1) (f_4ction))))
)
"""
        expected_problem = """(define (problem ad_hoc-problem)
 (:domain ad_hoc-domain)
 (:objects
   obj_1_0 - when_
 )
 (:init)
 (:goal (and ))
)
"""

    def test_miconic_reader(self):
        reader = UPPDDLReader()

        domain_filename = os.path.join(PDDL_DOMAINS_PATH, "miconic", "domain.pddl")
        problem_filename = os.path.join(PDDL_DOMAINS_PATH, "miconic", "problem.pddl")
        problem = reader.parse_problem(domain_filename, problem_filename)
        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 15)
        self.assertEqual(len(problem.actions), 3)
        self.assertEqual(len(list(problem.objects(problem.user_type("passenger")))), 2)
        self.assertEqual(len(list(problem.objects(problem.user_type("floor")))), 4)

    def test_citycar_reader(self):
        reader = UPPDDLReader()

        domain_filename = os.path.join(PDDL_DOMAINS_PATH, "citycar", "domain.pddl")
        problem_filename = os.path.join(PDDL_DOMAINS_PATH, "citycar", "problem.pddl")
        problems = [
            reader.parse_problem(domain_filename, problem_filename),
            PDDLReader(force_ai_planning_reader=True).parse_problem(
                domain_filename, problem_filename
            ),
        ]

        for problem in problems:
            em = problem.environment.expression_manager
            self.assertIsNotNone(problem)
            self.assertEqual(len(problem.fluents), 10)
            self.assertEqual(len(problem.actions), 7)
            self.assertEqual(
                len(list(problem.objects(problem.user_type("junction")))), 9
            )
            self.assertEqual(len(list(problem.objects(problem.user_type("car")))), 2)
            self.assertEqual(len(list(problem.objects(problem.user_type("garage")))), 3)
            self.assertEqual(len(list(problem.objects(problem.user_type("road")))), 5)
            metric = problem.quality_metrics[0]
            self.assertTrue(metric.is_minimize_action_costs())
            assert isinstance(metric, MinimizeActionCosts)
            action_costs = {
                problem.action("move_car_in_road"): em.Int(1),
                problem.action("move_car_out_road"): em.Int(1),
                problem.action("build_diagonal_oneway"): em.Int(30),
                problem.action("build_straight_oneway"): em.Int(20),
                problem.action("destroy_road"): em.Int(10),
            }
            for action, cost in action_costs.items():
                parsed_action = problem.action(action.name)
                self.assertEqual(action, parsed_action)
                parsed_cost = metric.costs[parsed_action]
                self.assertEqual(cost, parsed_cost)

    def test_visit_precedence_reader(self):
        reader = UPPDDLReader()

        domain_filename = os.path.join(
            PDDL_DOMAINS_PATH, "visit_precedence", "domain.pddl"
        )
        problem_filename = os.path.join(
            PDDL_DOMAINS_PATH, "visit_precedence", "problem.pddl"
        )
        problem = reader.parse_problem(domain_filename, problem_filename)
        em = problem.environment.expression_manager

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 2)
        self.assertEqual(len(problem.actions), 1)
        self.assertEqual(len(list(problem.objects(problem.user_type("location")))), 3)
        self.assertEqual(len(problem.goals), 1)
        self.assertEqual(len(problem.timed_goals), 0)
        self.assertEqual(len(problem.timed_effects), 0)

        visit = problem.action("visit")
        assert isinstance(visit, DurativeAction)
        to_visit = visit.parameter("to_visit")
        location = problem.user_type("location")
        precedes = problem.fluent("precedes")
        visited = problem.fluent("visited")
        p = Variable("p", location, problem.environment)
        cond_test = em.Forall(
            em.And(
                em.Or(em.Not(precedes(p, to_visit)), visited(p)),
                em.Not(visited(to_visit)),
            ),
            p,
        )
        l = Variable("l_0", location, problem.environment)
        l2 = Variable("l2", location, problem.environment)
        goal_test = em.Forall(
            em.And(
                visited(l), em.Forall(em.Or(em.Not(precedes(l2, l)), visited(l2)), l2)
            ),
            l,
        )
        self.assertEqual(
            visit.duration,
            FixedDuration(em.Int(3)),
        )
        for interval, cond_list in visit.conditions.items():
            self.assertEqual(interval, TimePointInterval(StartTiming()))
            self.assertEqual(len(cond_list), 1)
            self.assertEqual(cond_test, cond_list[0])
        for timing, effect_list in visit.effects.items():
            if timing == EndTiming():
                self.assertEqual(len(effect_list), 1)
            else:
                self.assertTrue(False)
        for g in problem.goals:
            self.assertEqual(g, goal_test)

    def test_robot_fastener_reader(self):
        reader = UPPDDLReader()

        domain_filename = os.path.join(
            PDDL_DOMAINS_PATH, "robot_fastener", "domain.pddl"
        )
        problem_filename = os.path.join(
            PDDL_DOMAINS_PATH, "robot_fastener", "problem.pddl"
        )
        problem = reader.parse_problem(domain_filename, problem_filename)

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 5)
        self.assertEqual(len(problem.actions), 1)
        self.assertEqual(len(list(problem.objects(problem.user_type("robot")))), 3)
        self.assertEqual(len(list(problem.objects(problem.user_type("fastener")))), 3)

    def test_safe_road_reader(self):
        reader = UPPDDLReader()

        domain_filename = os.path.join(PDDL_DOMAINS_PATH, "safe_road", "domain.pddl")
        problem_filename = os.path.join(PDDL_DOMAINS_PATH, "safe_road", "problem.pddl")
        problem = reader.parse_problem(domain_filename, problem_filename)

        self.assertIsNotNone(problem)
        self.assertEqual(len(problem.fluents), 1)
        self.assertEqual(len(problem.actions), 2)
        natural_disaster = problem.action("natural_disaster")
        assert isinstance(natural_disaster, InstantaneousAction)
        self.assertEqual(len(natural_disaster.effects), 1)
        self.assertTrue(natural_disaster.effects[0].is_forall())
        self.assertEqual(len(list(problem.objects(problem.user_type("location")))), 3)

    @skipIfNoOneshotPlannerForProblemKind(
        simple_numeric_kind, OptimalityGuarantee.SOLVED_OPTIMALLY
    )
    def test_reading_domain_only(self):
        reader = UPPDDLReader()

        domain_filename = os.path.join(PDDL_DOMAINS_PATH, "counters", "domain.pddl")
        domain = reader.parse_problem(domain_filename)
        counter_type = domain.user_type("counter")
        domain.set_initial_value(domain.fluent("max_int"), 10)
        value_fluent = domain.fluent("value")
        expected_plan_length = 0
        for i in range(5):
            expected_plan_length += i
            problem = (
                domain.clone()
            )  # Clone the parsed domain, then populate it and solve
            for j in range(i + 1):
                object_j = Object(f"c{str(j)}", counter_type)
                problem.add_object(object_j)
                problem.set_initial_value(value_fluent(object_j), 0)
                if j > 0:
                    previous_object = problem.object(f"c{str(j-1)}")
                    problem.add_goal(
                        LE(
                            Plus(value_fluent(previous_object), 1),
                            value_fluent(object_j),
                        )
                    )
            problem.add_quality_metric(MinimizeSequentialPlanLength())
            with OneshotPlanner(
                problem_kind=problem.kind, optimality_guarantee="SOLVED_OPTIMALLY"
            ) as planner:
                plan = planner.solve(problem).plan
                self.assertEqual(len(plan.actions), expected_plan_length)

    def test_writer_nested_and(self):
        x, y, z = Fluent("x"), Fluent("y"), Fluent("z")
        goals: List[FNode] = [
            And(x, y),
            And(x, And(y, z)),
            And(Or(x, y), And(y, z)),
        ]
        expected_goals: List[str] = [
            "(:goal (and (x) (y)))",
            "(:goal (and (x) (y) (z)))",
            "(:goal (and (or (x) (y)) (y) (z)))",
        ]
        assert len(goals) == len(
            expected_goals
        ), "goals and expected_goals must have the same length"
        for i, (goal, expected_goal) in enumerate(zip(goals, expected_goals)):
            problem = Problem(f"test_{i}")
            problem.add_fluent(x, default_initial_value=False)
            problem.add_fluent(y, default_initial_value=False)
            problem.add_fluent(z, default_initial_value=False)
            problem.add_goal(goal)
            writer = PDDLWriter(problem)
            pddl_problem = self._normalized_pddl_str(writer.get_problem())
            self.assertIn(expected_goal, pddl_problem)

    def test_grounding_tpp_metric(self):
        reader = UPPDDLReader()

        domain_filename = os.path.join(PDDL_DOMAINS_PATH, "tpp_metric", "domain.pddl")
        problem_filename = os.path.join(PDDL_DOMAINS_PATH, "tpp_metric", "problem.pddl")
        problem = reader.parse_problem(domain_filename, problem_filename)

        self.assertIsNotNone(problem)

        with Compiler(
            name="up_grounder", compilation_kind=CompilationKind.GROUNDING
        ) as grounder:
            grounded_problem = grounder.compile(
                problem, compilation_kind=CompilationKind.GROUNDING
            ).problem
        self.assertEqual(40, len(grounded_problem.actions))
        self.assertEqual(3, len(problem.actions))

    def test_robot_continuous(self):
        problem = self.problems["robot_continuous"].problem

        w = PDDLWriter(problem)

        pddl_domain = self._normalized_pddl_str(w.get_domain())
        self.assertIn(
            "(:requirements :strips :typing :equality :numeric-fluents :durative-actions :continuous-effects)",
            pddl_domain,
        )
        self.assertIn("(decrease (battery_charge) (* #t 1))", pddl_domain)

    def test_robot_conditional_effects(self):
        problem = self.problems["robot_conditional_effects"].problem

        # NOTE conditional effects not fully supported for continuous change

        w = PDDLWriter(problem)

        pddl_domain = self._normalized_pddl_str(w.get_domain())
        self.assertIn(
            "(when (at end (<= 10 (battery_charge))) (at end (robot_at ?l_to)))",
            pddl_domain,
        )
        # self.assertIn(
        #    "(when (at start (<= 10 (battery_charge))) (decrease (battery_charge) (* #t 1)))",
        #    pddl_domain,
        # )

    def test_continuous_forall(self):
        process_domain = """
(define
    (domain continuous_forall)
    (:types car)

    (:functions
        (distance_traveled ?car - car)
    )

    (:process all_cars_travel
        :parameters ()
        :effect (forall (?c - car)
        (increase (distance_traveled(?c)) (* #t (1.0))))
    )
)
"""
        durative_act_domain = """
(define
    (domain continuous_forall)
    (:types car)

    (:functions
        (distance_traveled ?car - car)
    )

    (:durative-action all_cars_travel
        :parameters ()
        :duration (and (>= ?duration 4) (<= ?duration 4))
        :effect (
            forall (?c - car)
            (increase (distance_traveled(?c)) (* #t (1.0)))
        )
    )
)
"""
        for domain in [process_domain, durative_act_domain]:
            reader = PDDLReader()
            with self.assertRaises(UPUnsupportedProblemTypeError) as e:
                reader.parse_problem_string(domain)
            self.assertEqual(
                str(e.exception),
                "Continuous change with forall effects is not supported",
            )

    def test_type_self_subtype(self):
        domain = """
(define (domain shape-stacking)
    (:requirements :strips :typing)
    (:types
        shape
        square triangle - shape
    )
)
"""
        reader = PDDLReader()
        with self.assertRaises(SyntaxError) as e:
            reader.parse_problem_string(
                domain,
            )
        self.assertEqual(
            str(e.exception),
            "Type 'shape' is defined as a subtype of itself",
        )


def _have_same_user_types_considering_renamings(
    original_problem: unified_planning.model.Problem,
    tested_problem: unified_planning.model.Problem,
    get_item_named,
) -> bool:
    for tested_type in tested_problem.user_types:
        if (
            get_item_named(cast(_UserType, tested_type).name)
            not in original_problem.user_types
        ):
            return False
    return True
