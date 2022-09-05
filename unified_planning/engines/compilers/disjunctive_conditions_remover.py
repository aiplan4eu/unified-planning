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
#
"""This module defines the dnf remover class."""

import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.compilers.utils import get_fresh_name, replace_action
from unified_planning.engines.results import CompilerResult
from unified_planning.exceptions import UPProblemDefinitionError
from unified_planning.model import (
    FNode,
    Problem,
    InstantaneousAction,
    DurativeAction,
    TimeInterval,
    Timing,
    Action,
    ProblemKind,
)
from unified_planning.model.walkers import Dnf
from typing import List, Tuple, Dict, cast
from itertools import product
from functools import partial


class DisjunctiveConditionsRemover(engines.engine.Engine, CompilerMixin):
    """DisjunctiveConditions remover class: this class offers the capability
    to transform a problem with preconditions not in the DNF form
    into one with all the preconditions in DNF form (an OR of AND);
    Then this OR is decomposed into subactions, therefore after this
    remover is called, every action condition or precondition will be
    an AND of leaf nodes.
    """

    @property
    def name(self):
        return "dcrm"

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind()
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_numbers("CONTINUOUS_NUMBERS")
        supported_kind.set_numbers("DISCRETE_NUMBERS")
        supported_kind.set_fluents_type("NUMERIC_FLUENTS")
        supported_kind.set_fluents_type("OBJECT_FLUENTS")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITY")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        supported_kind.set_effects_kind("INCREASE_EFFECTS")
        supported_kind.set_effects_kind("DECREASE_EFFECTS")
        supported_kind.set_time("CONTINUOUS_TIME")
        supported_kind.set_time("DISCRETE_TIME")
        supported_kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("TIMED_EFFECT")
        supported_kind.set_time("TIMED_GOALS")
        supported_kind.set_time("DURATION_INEQUALITIES")
        supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= DisjunctiveConditionsRemover.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        assert isinstance(problem, Problem)

        env = problem.env

        new_to_old: Dict[Action, Action] = {}

        new_problem = problem.clone()
        new_problem.name = f"{self.name}_{problem.name}"
        new_problem.clear_actions()

        dnf = Dnf(env)
        for a in problem.actions:
            if isinstance(a, InstantaneousAction):
                new_precond = dnf.get_dnf_expression(
                    env.expression_manager.And(a.preconditions)
                )
                if new_precond.is_or():
                    for and_exp in new_precond.args:
                        na = self._create_new_action_with_given_precond(
                            new_problem, and_exp, a
                        )
                        new_to_old[na] = a
                        new_problem.add_action(na)
                else:
                    na = self._create_new_action_with_given_precond(
                        new_problem, new_precond, a
                    )
                    new_to_old[na] = a
                    new_problem.add_action(na)
            elif isinstance(a, DurativeAction):
                interval_list: List[TimeInterval] = []
                conditions: List[List[FNode]] = []
                # save the timing, calculate the dnf of the and of all the conditions at the same time
                # and then save it in conditions.
                # conditions contains lists of Fnodes, where [a,b,c] means a or b or c
                for i, cl in a.conditions.items():
                    interval_list.append(i)
                    new_cond = dnf.get_dnf_expression(env.expression_manager.And(cl))
                    if new_cond.is_or():
                        conditions.append(new_cond.args)
                    else:
                        conditions.append([new_cond])
                conditions_tuple = cast(Tuple[List[FNode], ...], product(*conditions))
                for cond_list in conditions_tuple:
                    nda = self._create_new_durative_action_with_given_conds_at_given_times(
                        new_problem, interval_list, cond_list, a
                    )
                    new_to_old[nda] = a
                    new_problem.add_action(nda)
            else:
                raise NotImplementedError

        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old), self.name
        )

    def _create_new_durative_action_with_given_conds_at_given_times(
        self,
        new_problem,
        interval_list: List[TimeInterval],
        cond_list: List[FNode],
        original_action: DurativeAction,
    ) -> DurativeAction:
        new_action = original_action.clone()
        new_action.name = get_fresh_name(new_problem, original_action.name)
        new_action.clear_conditions()
        for i, c in zip(interval_list, cond_list):
            if c.is_and():
                for co in c.args:
                    new_action.add_condition(i, co)
            else:
                new_action.add_condition(i, c)
        return new_action

    def _create_new_action_with_given_precond(
        self, new_problem, precond: FNode, original_action: InstantaneousAction
    ) -> InstantaneousAction:
        new_action = original_action.clone()
        new_action.name = get_fresh_name(new_problem, original_action.name)
        new_action.clear_preconditions()
        if precond.is_and():
            for leaf in precond.args:
                new_action.add_precondition(leaf)
        else:
            new_action.add_precondition(precond)
        return new_action
