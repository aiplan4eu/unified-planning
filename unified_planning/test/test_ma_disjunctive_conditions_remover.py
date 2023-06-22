import unified_planning
from unified_planning.model.multi_agent import *
from collections import namedtuple
from unified_planning.shortcuts import *
from unified_planning.model.problem_kind import (
    basic_classical_kind,
    classical_kind,
    simple_numeric_kind,
    bounded_types_kind,
    full_classical_kind,
    basic_temporal_kind,
)
from unified_planning.test import (
    TestCase,
    skipIfNoPlanValidatorForProblemKind,
    skipIfNoOneshotPlannerForProblemKind,
)
from unified_planning.test.examples import get_example_problems
from unified_planning.engines import CompilationKind
from unified_planning.engines.compilers.ma_disjunctive_conditions_remover import (
    MADisjunctiveConditionsRemover,
)


class TestMADisjunctiveConditionsRemover(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.problems = get_example_problems()

    @skipIfNoOneshotPlannerForProblemKind(
        classical_kind.union(simple_numeric_kind).union(bounded_types_kind)
    )
    @skipIfNoPlanValidatorForProblemKind(
        full_classical_kind.union(simple_numeric_kind).union(bounded_types_kind)
    )
    def test_ad_hoc_1(self):
        # mockup problem
        problem: MultiAgentProblem = MultiAgentProblem("simple_test")
        a1 = Agent("a1", problem)
        a2 = Agent("a2", problem)
        a = Fluent("a")
        b = Fluent("b")
        c = Fluent("c")
        d = Fluent("d")
        act = InstantaneousAction("act")
        # (a <-> (b -> c)) -> (a & d)
        # In Dnf:
        # (!a & !b) | (!a & c) | (a & b & !c) | (a & d)
        cond = Implies(Iff(a, Implies(b, c)), And(a, d))
        possible_conditions = [
            {Not(a), Not(b)},
            {Not(a), FluentExp(c)},
            {FluentExp(b), Not(c), FluentExp(a)},
            {FluentExp(a), FluentExp(d)},
        ]
        act.add_precondition(cond)
        act.add_effect(a, TRUE(), cond)
        # problem = Problem("mockup")
        a1.add_fluent(a)
        a1.add_fluent(b)
        a1.add_fluent(c)
        a1.add_fluent(d)
        a2.add_fluent(a)
        a2.add_fluent(b)
        a2.add_fluent(c)
        a2.add_fluent(d)
        a1.add_action(act)
        a2.add_action(act)
        problem.add_agent(a1)
        problem.add_agent(a2)

        # problem.add_action(act)
        problem.set_initial_value(a, True)
        problem.set_initial_value(b, False)
        problem.set_initial_value(c, True)
        problem.set_initial_value(d, False)
        problem.add_goal(a)
        dnfr = MADisjunctiveConditionsRemover()
        res = dnfr.compile(problem, CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING)
        dnf_problem = res.problem
        assert isinstance(dnf_problem, MultiAgentProblem)

        self.assertEqual(len(dnf_problem.agent("a1").actions), 4)
        self.assertEqual(len(dnf_problem.agent("a2").actions), 4)
        # Cycle over all actions. For every new action assume that the precondition is equivalent
        # to one in the possible_preconditions and that no other action has the same precondition.
        for i, new_action in enumerate(dnf_problem.agent("a1").actions):
            assert isinstance(new_action, InstantaneousAction)
            preconditions = set(new_action.preconditions)
            self.assertIn(preconditions, possible_conditions)
            for j, new_action_oth_acts in enumerate(dnf_problem.agent("a1").actions):
                assert isinstance(new_action_oth_acts, InstantaneousAction)
                preconditions_oth_acts = set(new_action_oth_acts.preconditions)
                if i != j:
                    self.assertNotEqual(preconditions, preconditions_oth_acts)
            self.assertEqual(len(new_action.effects), 4)
            self.assertEqual(len(new_action.conditional_effects), 4)

    def test_ad_hoc_2(self):
        # mockup problem
        problem: MultiAgentProblem = MultiAgentProblem("mockup")
        a1 = Agent("a1", problem)
        a2 = Agent("a2", problem)
        a = Fluent("a")
        act = InstantaneousAction("act")
        cond = And(a, a)
        act.add_precondition(cond)
        act.add_effect(a, TRUE())
        a1.add_fluent(a)
        a2.add_fluent(a)
        a1.add_action(act)
        a2.add_action(act)
        problem.add_agent(a1)
        problem.add_agent(a2)
        problem.set_initial_value(a, True)
        problem.add_goal(a)
        dnfr = MADisjunctiveConditionsRemover()
        res = dnfr.compile(problem, CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING)
        dnf_problem = res.problem
        assert isinstance(dnf_problem, MultiAgentProblem)

        self.assertEqual(len(dnf_problem.agent("a1").actions), 1)
        self.assertEqual(len(dnf_problem.agent("a2").actions), 1)

    @skipIfNoOneshotPlannerForProblemKind(basic_classical_kind)
    def test_ad_hoc_3(self):
        # mockup problem
        problem: MultiAgentProblem = MultiAgentProblem("mockup")
        a1 = Agent("a1", problem)
        a2 = Agent("a2", problem)
        a = Fluent("a")
        b = Fluent("b")
        c = Fluent("c")
        act_a = InstantaneousAction("act_a")
        act_a.add_effect(a, TRUE())
        act_b = InstantaneousAction("act_b")
        act_b.add_effect(b, TRUE())
        act_c = InstantaneousAction("act_c")
        act_c.add_effect(c, TRUE())
        a1.add_fluent(a)
        a1.add_fluent(b)
        a1.add_fluent(c)
        a2.add_fluent(a)
        a2.add_fluent(b)
        a2.add_fluent(c)
        a1.add_action(act_a)
        a1.add_action(act_b)
        a1.add_action(act_c)
        a2.add_action(act_a)
        a2.add_action(act_b)
        a2.add_action(act_c)
        problem.add_agent(a1)
        problem.add_agent(a2)
        problem.set_initial_value(a, True)
        problem.set_initial_value(b, False)
        problem.set_initial_value(c, False)
        problem.add_goal(And(a, Or(b, c)))
        dnfr = MADisjunctiveConditionsRemover()
        res = dnfr.compile(problem, CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING)
        dnf_problem = res.problem
        assert isinstance(dnf_problem, MultiAgentProblem)
        self.assertEqual(len(dnf_problem.agent("a1").actions), 5)
        self.assertEqual(len(dnf_problem.agent("a2").actions), 5)
        self.assertEqual(len(dnf_problem.goals), 2)
        self.assertTrue(dnf_problem.goals[0].is_fluent_exp())
        breakpoint()
        with OneshotPlanner(problem_kind=dnf_problem.kind) as planner:
            os_res = planner.solve(dnf_problem)


o = TestMADisjunctiveConditionsRemover()
o.setUp()
o.test_ad_hoc_1()
o.test_ad_hoc_2()
o.test_ad_hoc_3()
