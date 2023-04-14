# Copyright 2023 AIPlan4EU project
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
#

import random
import unified_planning as up
from unified_planning.exceptions import UPUsageError
from pysmt.shortcuts import Solver, Not, And, Symbol, Or, ExactlyOne, EqualsOrIff
from pysmt.oracles import get_logic
from typing import Dict


class Environment:
    """
    A base class that defines the interface for an environment in the planning domain.
    """

    def __init__(
        self, problem: "up.model.contingent.contingent_problem.ContingentProblem"
    ):
        self._problem = problem

    def apply(
        self, action: "up.plans.ActionInstance"
    ) -> Dict["up.model.FNode", "up.model.FNode"]:
        """
        Applies the given action to the current state of the environment and returns the resulting observation.

        :param action: A :class:`~unified_planning.plans.ActionInstance` object representing the action to apply.
        :return: A dictionary mapping the fluent expressions observed by the sensing action to their corresponding values.
        """
        raise NotImplementedError

    def is_goal_reached(self) -> bool:
        """
        Determines whether the goal of the planning problem has been reached in the current state of the environment.

        :return: A boolean value indicating whether the goal has been reached.
        """
        raise NotImplementedError


class SimulatedEnvironment(Environment):
    """
    An implementation of an environment that simulates the effects of actions on a given contingent planning problem.

    :param problem: A :class:`~unified_planning.model.ContingentProblem` object representing the planning problem to simulate.
    """

    def __init__(
        self, problem: "up.model.contingent.contingent_problem.ContingentProblem"
    ):
        super().__init__(problem)
        self._deterministic_problem = problem.clone()
        self._randomly_set_full_initial_state(self._deterministic_problem)
        self._simulator = up.engines.UPSequentialSimulator(
            self._deterministic_problem, False
        )
        self._state = self._simulator.get_initial_state()

    def _randomly_set_full_initial_state(
        self, problem: "up.model.contingent.contingent_problem.ContingentProblem"
    ):
        fnode_to_symbol = {}
        symbol_to_fnode = {}
        cnt = 0
        for hf in problem.hidden_fluents:
            if not hf.is_not():
                s = Symbol(f"v_{cnt}")
                fnode_to_symbol[hf] = s
                symbol_to_fnode[s] = hf
                cnt += 1

        constraints = []
        for c in problem.oneof_constraints:
            args = []
            for x in c:
                if x.is_not():
                    args.append(Not(fnode_to_symbol[x.arg(0)]))
                else:
                    args.append(fnode_to_symbol[x])
            constraints.append(ExactlyOne(args))
        for c in problem.or_constraints:
            args = []
            for x in c:
                if x.is_not():
                    args.append(Not(fnode_to_symbol[x.arg(0)]))
                else:
                    args.append(fnode_to_symbol[x])
            constraints.append(Or(args))

        res = random.choice(list(all_smt(And(constraints), symbol_to_fnode.keys())))

        for k, v in res.items():
            f = symbol_to_fnode[k]
            assert v.is_bool_constant()
            problem.set_initial_value(f, v.is_true())

    def apply(
        self, action: "up.plans.ActionInstance"
    ) -> Dict["up.model.FNode", "up.model.FNode"]:
        """
        Applies the given action to the current state of the environment and returns the resulting observation.

        :param action: A :class:`~unified_planning.plans.ActionInstance` object representing the action to apply.
        :return: A dictionary mapping the fluent expressions observed by the sensing action to their corresponding values.
        """
        new_state = self._simulator.apply(
            self._state, action.action, action.actual_parameters
        )
        if new_state is None:
            raise UPUsageError("The given action is not applicable!")
        self._state = new_state
        res = {}
        if isinstance(action, up.model.contingent.sensing_action.SensingAction):
            for f in action.observed_fluents:
                res[f] = self._state.get_value(f)
        return res

    def is_goal_reached(self) -> bool:
        """
        Determines whether the goal of the planning problem has been reached in the current state of the environment.

        :return: A boolean value indicating whether the goal has been reached.
        """
        return self._simulator.is_goal(self._state)


def all_smt(formula, keys):
    target_logic = get_logic(formula)
    with Solver(logic=target_logic) as solver:
        solver.add_assertion(formula)
        while solver.solve():
            res = {k: solver.get_value(k) for k in keys}
            yield res
            partial_model = [EqualsOrIff(k, v) for k, v in res.items()]
            solver.add_assertion(Not(And(partial_model)))
