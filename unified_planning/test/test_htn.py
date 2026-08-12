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
from fractions import Fraction

import unified_planning as up
from unified_planning.io import PDDLReader, PDDLWriter
from unified_planning.model.htn import HierarchicalProblem, Method, TaskNetwork, Task
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

    def test_hierarchical_problem_clone_preserves_fields(self):
        x = Fluent("x", BoolType())
        a = InstantaneousAction("a")
        a.add_effect(x, True)

        problem = HierarchicalProblem("p")
        problem.add_fluent(x, default_initial_value=False)
        problem.add_action(a)

        # TimeModelMixin state
        problem.epsilon = Fraction(1, 100)
        problem.discrete_time = True
        problem.self_overlapping = True

        # natural transitions
        event = Event("ev")
        event.add_effect(x, True)
        problem.add_event(event)
        process = Process("proc")
        y = Fluent("y", RealType())
        problem.add_fluent(y, default_initial_value=0)
        process.add_increase_continuous_effect(y, 1)
        problem.add_process(process)

        # quality metric default
        problem.add_quality_metric(MinimizeActionCosts({a: 5}, default=99))

        # trajectory constraint
        problem.add_trajectory_constraint(Always(x))

        # HTN-specific state
        go = problem.add_task("go")
        go_noop = Method("go-noop")
        go_noop.set_task(go)
        problem.add_method(go_noop)
        problem.task_network.add_subtask(go, ident="go1")

        clone = problem.clone()

        self.assertEqual(problem.epsilon, clone.epsilon)
        self.assertEqual(problem.discrete_time, clone.discrete_time)
        self.assertEqual(problem.self_overlapping, clone.self_overlapping)
        self.assertEqual(len(problem.events), len(clone.events))
        self.assertEqual(len(problem.processes), len(clone.processes))
        metric, clone_metric = problem.quality_metrics[0], clone.quality_metrics[0]
        assert isinstance(metric, MinimizeActionCosts) and isinstance(
            clone_metric, MinimizeActionCosts
        )
        self.assertEqual(metric.default, clone_metric.default)
        self.assertEqual(problem.trajectory_constraints, clone.trajectory_constraints)
        self.assertEqual(len(problem.tasks), len(clone.tasks))
        self.assertEqual(len(problem.methods), len(clone.methods))
        self.assertEqual(
            len(problem.task_network.subtasks), len(clone.task_network.subtasks)
        )
        self.assertEqual(problem, clone)
        self.assertEqual(clone, problem)

    def test_task_network_constraint_kind(self):
        Loc = UserType("Loc")
        l1 = Object("l1", Loc)
        l2 = Object("l2", Loc)

        problem = up.model.htn.HierarchicalProblem("p")
        problem.add_objects([l1, l2])
        v = problem.task_network.add_variable("v", Loc)
        problem.task_network.add_constraint(Or(Equals(v, l1), Equals(v, l2)))

        self.assertTrue(problem.kind.has_disjunctive_conditions())
        self.assertTrue(problem.kind.has_equalities())

    def test_method_constraint_kind(self):
        Loc = UserType("Loc")
        l1 = Object("l1", Loc)
        l2 = Object("l2", Loc)

        problem = up.model.htn.HierarchicalProblem("p")
        problem.add_objects([l1, l2])
        top_task = Task("top-task")
        problem.add_task(top_task)
        problem.task_network.add_subtask(top_task)

        m = up.model.htn.Method("m1", v=Loc)
        m.set_task(top_task)
        v = m.parameter("v")
        m.add_constraint(Or(Equals(v, l1), Equals(v, l2)))
        problem.add_method(m)

        self.assertTrue(problem.kind.has_disjunctive_conditions())
        self.assertTrue(problem.kind.has_equalities())

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
        assert set(tn.partial_order()) == {("a1", "a2"), ("a1", "a3")}  # type: ignore[arg-type]
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

    def test_method_instances_do_not_share_a_decomposition(self):
        # decomposition used to default to one shared Decomposition, so mutating one
        # instance's subtasks leaked into every other default-constructed one.
        from unified_planning.plans.hierarchical_plan import MethodInstance
        from unified_planning.plans.plan import ActionInstance

        top_task = Task("top-task")
        m = up.model.htn.Method("m1")
        m.set_task(top_task)

        a = InstantaneousAction("a")

        first = MethodInstance(m, ())
        second = MethodInstance(m, ())

        self.assertIsNot(first.decomposition, second.decomposition)
        self.assertEqual(first.decomposition.subtasks, {})
        self.assertEqual(second.decomposition.subtasks, {})

        first.decomposition.subtasks["s1"] = ActionInstance(a)

        self.assertEqual(list(first.decomposition.subtasks), ["s1"])
        self.assertEqual(second.decomposition.subtasks, {})

    def test_hddl_parsing(self):
        """Tests that all HDDL benchmarks are successfully parsed."""
        hddl_dir = os.path.join(FILE_PATH, "hddl")
        subfolders = [f.path for f in os.scandir(hddl_dir) if f.is_dir()]
        for id, domain in enumerate(subfolders[:]):
            name = os.path.basename(domain)
            print(f"=== [{id}] {name} ===")
            domain_filename = os.path.join(domain, "domain.hddl")
            problem_filename = os.path.join(domain, "instance.1.pb.hddl")
            reader = PDDLReader(disable_warnings=True)
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
            reader = PDDLReader(disable_warnings=True)
            problem = reader.parse_problem(domain_filename, problem_filename)

            # print(problem)
            w = PDDLWriter(problem)
            with tempfile.TemporaryDirectory() as tempdir:
                domain_filename = os.path.join(tempdir, "domain.pddl")
                problem_filename = os.path.join(tempdir, "problem.pddl")
                w.write_domain(domain_filename)
                w.write_problem(problem_filename)

                reader = PDDLReader(disable_warnings=True)
                parsed_problem = reader.parse_problem(domain_filename, problem_filename)
                self.assertEqual(parsed_problem.kind, problem.kind)
