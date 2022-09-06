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


from unified_planning.engines.compilers.trajectory_constraints_remover import TrajectoryConstraintsRemover
from unified_planning.shortcuts import *
from unified_planning.walkers import Simplifier
from unified_planning.test import TestCase

class TestTrajectoryConstraintsRemoverCase(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        problem, fluents, actions = self.get_problem()
        self.simplifier = Simplifier(problem.env)
        self.problem = problem 
        self.fluents = fluents
        self.actions = actions

    def get_problem (self):
        problem = Problem('test_traj_constr_remover')
        a = Fluent('a')
        b = Fluent('b')
        c = Fluent('c')
        d = Fluent('d')
        e = Fluent('e')
        fluents = [a, b, c, d, e]
        for f in fluents:
            problem.add_fluent(f)
        act_1 = InstantaneousAction('act_1')
        act_1.add_precondition(a)
        act_2 = InstantaneousAction('act_2')
        act_2.add_precondition(a)
        act_3 = InstantaneousAction('act_3')
        act_3.add_precondition(a)
        condition = Or(Or((And(b, Not(c))), d), Or(Not(a), And(e, Not(d))))
        condition_2 = And(Not(e), Or(Or((And(b, Not(c))), d), Or(Not(a), And(e, Not(d)))))
        act_1.add_effect(condition=condition, fluent=a, value=True)
        act_2.add_effect(condition=condition, fluent=a, value=True)
        act_2.add_effect(condition=condition, fluent=b, value=False)
        act_2.add_effect(condition=condition, fluent=c, value=True)
        act_3.add_effect(condition=condition, fluent=e, value=False)
        act_3.add_effect(condition=condition_2, fluent=d, value=False)
        problem.add_action(act_1)
        problem.add_action(act_2)
        problem.add_action(act_3)
        problem.set_initial_value(a, True)
        problem.add_goal(e)
        acts = [act_1, act_2, act_3]
        return problem, fluents, acts

    def test_regression_1(self):
        traj_remover = TrajectoryConstraintsRemover()
        a_phi = FluentExp(self.fluents[0])
        b_phi = FluentExp(self.fluents[1])
        c_phi = FluentExp(self.fluents[2])
        d_phi = FluentExp(self.fluents[3])
        e_phi = FluentExp(self.fluents[4])
        act_1 = self.actions[0]
        R_a = self.simplifier.simplify(traj_remover._regression(a_phi, act_1))
        R_b = self.simplifier.simplify(traj_remover._regression(b_phi, act_1))
        R_c = self.simplifier.simplify(traj_remover._regression(c_phi, act_1))
        R_d = self.simplifier.simplify(traj_remover._regression(d_phi, act_1))
        R_e = self.simplifier.simplify(traj_remover._regression(e_phi, act_1))
        self.assertTrue(R_a.is_true() and R_b == b_phi and R_c == c_phi 
             and R_d == d_phi and R_e == e_phi)

    def test_regression_2(self):
        traj_remover = TrajectoryConstraintsRemover()
        a_phi = FluentExp(self.fluents[0])
        b_phi = FluentExp(self.fluents[1])
        c_phi = FluentExp(self.fluents[2])
        d_phi = FluentExp(self.fluents[3])
        e_phi = FluentExp(self.fluents[4])
        act_2 = self.actions[1]
        R_a = self.simplifier.simplify(traj_remover._regression(a_phi, act_2))
        R_b = self.simplifier.simplify(traj_remover._regression(b_phi, act_2))
        R_c = self.simplifier.simplify(traj_remover._regression(c_phi, act_2))
        R_d = self.simplifier.simplify(traj_remover._regression(d_phi, act_2))
        R_e = self.simplifier.simplify(traj_remover._regression(e_phi, act_2))
        self.assertTrue(R_a.is_true() and R_b != b_phi and R_c != c_phi 
             and R_d == d_phi and R_e == e_phi)

    def test_regression_3(self):
        traj_remover = TrajectoryConstraintsRemover()
        a_phi = FluentExp(self.fluents[0])
        b_phi = FluentExp(self.fluents[1])
        c_phi = FluentExp(self.fluents[2])
        d_phi = FluentExp(self.fluents[3])
        e_phi = FluentExp(self.fluents[4])
        act_3 = self.actions[2]
        R_a = self.simplifier.simplify(traj_remover._regression(a_phi, act_3))
        R_b = self.simplifier.simplify(traj_remover._regression(b_phi, act_3))
        R_c = self.simplifier.simplify(traj_remover._regression(c_phi, act_3))
        R_d = self.simplifier.simplify(traj_remover._regression(d_phi, act_3))
        R_e = self.simplifier.simplify(traj_remover._regression(e_phi, act_3))
        self.assertTrue(R_a == a_phi and R_b == b_phi and R_c == c_phi 
             and R_d != d_phi and R_e != e_phi)