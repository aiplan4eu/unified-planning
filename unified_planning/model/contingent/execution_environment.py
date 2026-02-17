# Copyright 2023 AIPlan4EU project
# Copyright 2024-2026 Unified Planning library and its maintainers
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

from collections import OrderedDict
import random
import unified_planning as up
from unified_planning.exceptions import UPUsageError
from typing import Dict, Optional


class ExecutionEnvironment:
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


class SimulatedExecutionEnvironment(ExecutionEnvironment):
    """
    Simulates the effects of actions on a given contingent planning problem.

    This class creates a deterministic version of a contingent problem by randomly
    resolving hidden fluent values (respecting oneof/or constraints), then uses a
    sequential simulator to apply actions and return observations.

    :param problem: A :class:`~unified_planning.model.ContingentProblem` object representing the planning problem to simulate.
    """

    def __init__(
        self,
        problem: "up.model.contingent.contingent_problem.ContingentProblem",
        max_constraints: Optional[int] = None,
    ):
        super().__init__(problem)
        self._deterministic_problem = self._get_stateless_deterministic_problem_clone(
            problem
        )
        self._max_constraints = max_constraints or float("inf")
        self._randomly_set_full_initial_state(problem)
        self._simulator = up.engines.UPSequentialSimulator(
            self._deterministic_problem, False
        )
        self._state = self._simulator.get_initial_state()

    def _get_stateless_deterministic_problem_clone(
        self, problem: "up.model.contingent.contingent_problem.ContingentProblem"
    ) -> "up.model.Problem":
        """Convert a ContingentProblem to a regular Problem."""
        # Create a new Problem with the same name and environment
        deterministic_problem = up.model.Problem(problem.name, problem.environment)

        for fluent in problem.fluents:
            default_value = problem.initial_defaults.get(fluent.type, False)
            deterministic_problem.add_fluent(
                fluent, default_initial_value=default_value
            )

        deterministic_problem.add_objects(problem.all_objects)

        for action in problem.actions:
            if isinstance(action, up.model.contingent.sensing_action.SensingAction):
                # Create a dummy action with no effects instead of a sensing action
                params = OrderedDict({p.name: p.type for p in action.parameters})
                dummy = up.model.InstantaneousAction(
                    action.name,
                    _parameters=params,
                    _env=problem.environment,
                )
                for precond in action.preconditions:
                    dummy.add_precondition(precond)
                deterministic_problem.add_action(dummy)
            else:
                deterministic_problem.add_action(action.clone())

        for g in problem.goals:
            deterministic_problem.add_goal(g)

        # Copy metrics
        for metric in problem.quality_metrics:
            deterministic_problem.add_quality_metric(metric)

        return deterministic_problem

    def _randomly_set_full_initial_state(
        self, problem: "up.model.contingent.contingent_problem.ContingentProblem"
    ):
        # import pysmt here to avoid making it a hard dependency for the whole contingent module
        from pysmt.shortcuts import Not, And, Symbol, Or, ExactlyOne

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

            if len(constraints) >= self._max_constraints:
                break

        res = random.choice(list(all_smt(And(constraints), symbol_to_fnode.keys())))

        for k, v in res.items():
            f = symbol_to_fnode[k]
            assert v.is_bool_constant()
            self._deterministic_problem.set_initial_value(f, v.is_true())

    def apply(
        self, action: "up.plans.ActionInstance"
    ) -> Dict["up.model.FNode", "up.model.FNode"]:
        """
        Applies the given action to the current state and returns the resulting observation.

        :param action: A :class:`~unified_planning.plans.ActionInstance` object representing the action to apply.
        :return: A dictionary mapping the fluent expressions observed by the sensing action to their corresponding values.
        """
        if isinstance(action.action, up.model.contingent.sensing_action.SensingAction):
            # Convert the sensing action instance to the corresponding dummy action instance
            # in the deterministic problem
            dummy_action = self._deterministic_problem.action(action.action.name)
            applied_action = dummy_action(*action.actual_parameters)
        else:
            applied_action = action

        new_state = self._simulator.apply(
            self._state, applied_action.action, action.actual_parameters
        )
        if new_state is None:
            raise UPUsageError("The given action is not applicable!")
        self._state = new_state
        res = {}
        subs: Dict["up.model.Expression", "up.model.Expression"] = dict(
            zip(action.action.parameters, action.actual_parameters)
        )
        if isinstance(action.action, up.model.contingent.sensing_action.SensingAction):
            for f in action.action.observed_fluents:
                f_exp = f.substitute(subs)
                res[f_exp] = self._state.get_value(f_exp)
        return res

    def is_goal_reached(self) -> bool:
        """
        Determines whether the goal of the planning problem has been reached in the current state.

        :return: A boolean value indicating whether the goal has been reached.
        """
        return self._simulator.is_goal(self._state)


def all_smt(formula, keys):
    # import pysmt here to avoid making it a hard dependency for the whole contingent module
    from pysmt.shortcuts import Solver, Not, And, EqualsOrIff
    from pysmt.oracles import get_logic

    target_logic = get_logic(formula)
    with Solver(logic=target_logic) as solver:
        solver.add_assertion(formula)
        while solver.solve():
            res = {k: solver.get_value(k) for k in keys}
            yield res
            partial_model = [EqualsOrIff(k, v) for k, v in res.items()]
            solver.add_assertion(Not(And(partial_model)))
