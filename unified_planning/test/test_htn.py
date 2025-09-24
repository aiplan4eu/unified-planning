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
# limitations under the License.

import os
import tempfile

import unified_planning as up
from unified_planning.io import PDDLReader, PDDLWriter
from unified_planning.model.htn import TaskNetwork, Task
from unified_planning.model.htn.ordering import PartialOrder, TotalOrder
from unified_planning.shortcuts import *
from unified_planning.test import unittest_TestCase, main, examples
from unified_planning.test.examples import get_example_problems


FILE_PATH = os.path.dirname(os.path.abspath(__file__))


class TestProblem(unittest_TestCase):
    def setUp(self):
        unittest_TestCase.setUp(self)
        self.problems = get_example_problems()

    def test_htn_problem_creation(self):
        problems = examples.hierarchical.get_example_problems()
        problem = problems["htn-go"].problem
        self.assertTrue(isinstance(problem, up.model.htn.HierarchicalProblem))
        self.assertTrue(problem.kind.has_hierarchical())
        self.assertEqual(2, len(problem.fluents))
        self.assertEqual(1, len(problem.actions))
        self.assertEqual(["go"], [task.name for task in problem.tasks])
        self.assertEqual(
            ["go-noop", "go-recursive"], [method.name for method in problem.methods]
        )

        go_direct = problem.method("go-noop")
        self.assertEqual(0, len(go_direct.subtasks))
        self.assertEqual(1, len(go_direct.preconditions))
        self.assertEqual(0, len(go_direct.constraints))

        go_indirect = problem.method("go-recursive")
        self.assertEqual(2, len(go_indirect.subtasks))
        self.assertEqual(2, len(go_indirect.preconditions))
        self.assertEqual(1, len(go_indirect.constraints))

        self.assertEqual(2, len(problem.task_network.subtasks))

        # temporal HTN
        assert (
            "TASK_ORDER_TEMPORAL"
            in self.problems["htn-go-temporal"].problem.kind.features
        )

    def test_ordering(self):
        """Checks that we detect the right orderings in task networks"""

        def assert_po(tn):
            assert tn.partial_order() is not None
            assert tn.total_order() is None

        def assert_to(tn):
            assert tn.partial_order() is not None
            assert tn.total_order() is not None

        def assert_temporal(tn):
            assert tn.partial_order() is None
            assert tn.total_order() is None
            assert len(tn.temporal_constraints()) > 0

        tn = TaskNetwork()
        a = Task("a")
        assert_to(tn)
        a1 = tn.add_subtask(a, ident="a1")
        assert_to(tn)
        assert tn.total_order() == ["a1"]
        a2 = tn.add_subtask(a, ident="a2")
        assert_po(tn)
        assert tn.partial_order() == []
        tn.set_strictly_before(a1, a2)
        assert_to(tn)
        assert tn.total_order() == ["a1", "a2"]
        a3 = tn.add_subtask(a, ident="a3")
        assert_po(tn)
        assert tn.partial_order() == [("a1", "a2")]
        tn.set_strictly_before(a1.end + 0, a3.start)
        assert_po(tn)
        assert set(tn.partial_order()) == {("a1", "a2"), ("a1", "a3")}  # type: ignore
        tn.set_strictly_before(a2, a3)
        assert_to(tn)
        assert tn.total_order() == ["a1", "a2", "a3"]

        a4 = tn.add_subtask(a, ident="a4")
        assert_po(tn)
        tn_base = tn.clone()

        tn.set_strictly_before(a2.end + 3, a4.start)
        assert_temporal(tn)
        env = get_environment()

        # a set of constraints that cannot be interpreted as precedences and should make the task network "temporal"
        temporal_constraints = [
            # simple temporal constraint
            env.expression_manager.LT(a1.end + 1, a2.start - 3),
            # lesser equal prevents this from being interpreted as a precedence
            # note: low level API only handles Timing (+0, transforms a Timepoint into a Timing
            env.expression_manager.LE(a1.end + 0, a2.start + 0),
            # disjunction of precedence constraints, should be detected as temporal as well
            env.expression_manager.Or(
                env.expression_manager.LT(a1.end + 0, a2.start + 0),
                env.expression_manager.LT(a1.end + 0, a3.start + 0),
            ),
        ]
        for c in temporal_constraints:
            tn = tn_base.clone()
            assert_po(tn)
            tn.add_constraint(c)
            assert_temporal(tn)

    def test_hddl_parsing(self):
        """Tests that all HDDL benchmarks are successfully parsed."""
        hddl_dir = os.path.join(FILE_PATH, "hddl")
        subfolders = [f.path for f in os.scandir(hddl_dir) if f.is_dir()]
        for id, domain in enumerate(subfolders[:]):
            name = os.path.basename(domain)
            print(f"=== [{id}] {name} ===")
            domain_filename = os.path.join(domain, "domain.hddl")
            problem_filename = os.path.join(domain, "instance.1.pb.hddl")
            reader = PDDLReader()
            problem = reader.parse_problem(domain_filename, problem_filename)

            assert isinstance(problem, up.model.htn.HierarchicalProblem)
            if name.startswith("2020-to-"):
                # a totally ordered domain
                constraints = problem.task_network._ordering()
                assert isinstance(constraints, TotalOrder)
                assert "TASK_ORDER_TOTAL" in problem.kind.features
            elif name.startswith("2020-po-"):
                # a partially ordered domain
                constraints = problem.task_network._ordering()
                assert isinstance(constraints, PartialOrder)
                TO_instances = [
                    "2020-po-Satellite"
                ]  # these problems allow non-ordered goal tasks but have only one initial task in our test instance
                assert (
                    "TASK_ORDER_PARTIAL" in problem.kind.features
                    or name in TO_instances
                )

    def test_hddl_writing(self):
        """Tests that all HDDL benchmarks can be written to HDDL and reparsed."""
        hddl_dir = os.path.join(FILE_PATH, "hddl")
        subfolders = [f.path for f in os.scandir(hddl_dir) if f.is_dir()]
        for id, domain in enumerate(subfolders[:]):
            name = os.path.basename(domain)
            print(f"=== [{id}] {name} ===")
            domain_filename = os.path.join(domain, "domain.hddl")
            problem_filename = os.path.join(domain, "instance.1.pb.hddl")
            reader = PDDLReader()
            problem = reader.parse_problem(domain_filename, problem_filename)

            # print(problem)
            w = PDDLWriter(problem)
            with tempfile.TemporaryDirectory() as tempdir:
                domain_filename = os.path.join(tempdir, "domain.pddl")
                problem_filename = os.path.join(tempdir, "problem.pddl")
                w.write_domain(domain_filename)
                w.write_problem(problem_filename)

                reader = PDDLReader()
                parsed_problem = reader.parse_problem(domain_filename, problem_filename)
                self.assertEqual(parsed_problem.kind, problem.kind)
