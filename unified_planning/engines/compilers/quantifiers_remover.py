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
"""This module defines the quantifiers remover class."""


import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.model import (
    Problem,
    InstantaneousAction,
    DurativeAction,
    Action,
    ProblemKind,
    Oversubscription,
)
from unified_planning.model.walkers import ExpressionQuantifiersRemover
from unified_planning.engines.compilers.utils import get_fresh_name, replace_action
from typing import Dict, Optional
from functools import partial


class QuantifiersRemover(engines.engine.Engine, CompilerMixin):
    """Quantifiers remover class: this class offers the capability
    to transform a problem with quantifiers into a problem without.
    Every quantifier is compiled away by it's respective logic formula
    instantiated on object.
    For example the formula:
        Forall (s-sempahore) is_green(s)
    in a problem with 3 objects of type semaphores {s1, s2, s3} is compiled in:
        And(is_green(s1), is_green(s2), is_green(s3)).
    While the respective formula on the same problem:
        Exists (s-semaphore) is_green(s)
    becomes:
        Or(is_green(s1), is_green(s2), is_green(s3))."""

    def __init__(self):
        engines.engine.Engine.__init__(self)
        CompilerMixin.__init__(self, CompilationKind.QUANTIFIERS_REMOVING)

    @property
    def name(self):
        return "qurm"

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind()
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_numbers("CONTINUOUS_NUMBERS")
        supported_kind.set_numbers("DISCRETE_NUMBERS")
        supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
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
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("MAKESPAN")
        supported_kind.set_quality_metrics("FINAL_VALUE")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= QuantifiersRemover.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == CompilationKind.QUANTIFIERS_REMOVING

    @staticmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: Optional[CompilationKind] = None
    ) -> ProblemKind:
        new_kind = ProblemKind(problem_kind.features)
        new_kind.unset_conditions_kind("EXISTENTIAL_CONDITIONS")
        new_kind.unset_conditions_kind("UNIVERSAL_CONDITIONS")
        return new_kind

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        """
        Takes an instance of a up.model.Problem and the up.engines.CompilationKind.QUANTIFIERS_REMOVING
        and returns a CompilerResult where the problem does not have universal or existential (Forall or Exists)
        operands; The quantifiers are substituted with their grounded version by using the problem's objects.

        :param problem: The instance of the up.model.Problem that must be returned without quantifiers.
        :param compilation_kind: The up.engines.CompilationKind that must be applied on the given problem;
        only QUANTIFIERS_REMOVING is supported by this compiler
        :return: The resulting up.engines.results.CompilerResult data structure.
        """
        assert isinstance(problem, Problem)

        expression_quantifier_remover = ExpressionQuantifiersRemover(
            problem.environment
        )

        new_to_old: Dict[Action, Action] = {}

        new_problem = problem.clone()
        new_problem.name = f"{self.name}_{problem.name}"
        new_problem.clear_timed_goals()
        new_problem.clear_goals()
        new_problem.clear_quality_metrics()

        for action in new_problem.actions:
            if isinstance(action, InstantaneousAction):
                original_action = problem.action(action.name)
                assert isinstance(original_action, InstantaneousAction)
                action.name = get_fresh_name(new_problem, action.name)
                action.clear_preconditions()
                for p in original_action.preconditions:
                    action.add_precondition(
                        expression_quantifier_remover.remove_quantifiers(p, problem)
                    )
                for e in action.effects:
                    if e.is_conditional():
                        e.set_condition(
                            expression_quantifier_remover.remove_quantifiers(
                                e.condition, problem
                            )
                        )
                    e.set_value(
                        expression_quantifier_remover.remove_quantifiers(
                            e.value, problem
                        )
                    )
                new_to_old[action] = original_action
            elif isinstance(action, DurativeAction):
                original_action = problem.action(action.name)
                assert isinstance(original_action, DurativeAction)
                action.name = get_fresh_name(new_problem, action.name)
                action.clear_conditions()
                for i, cl in original_action.conditions.items():
                    for c in cl:
                        action.add_condition(
                            i,
                            expression_quantifier_remover.remove_quantifiers(
                                c, problem
                            ),
                        )
                for t, el in action.effects.items():
                    for e in el:
                        if e.is_conditional():
                            e.set_condition(
                                expression_quantifier_remover.remove_quantifiers(
                                    e.condition, problem
                                )
                            )
                        e.set_value(
                            expression_quantifier_remover.remove_quantifiers(
                                e.value, problem
                            )
                        )
                new_to_old[action] = original_action
            else:
                raise NotImplementedError
        for el in new_problem.timed_effects.values():
            for e in el:
                if e.is_conditional():
                    e.set_condition(
                        expression_quantifier_remover.remove_quantifiers(
                            e.condition, problem
                        )
                    )
                e.set_value(
                    expression_quantifier_remover.remove_quantifiers(e.value, problem)
                )
        for i, gl in problem.timed_goals.items():
            for g in gl:
                ng = expression_quantifier_remover.remove_quantifiers(g, problem)
                new_problem.add_timed_goal(i, ng)
        for g in problem.goals:
            ng = expression_quantifier_remover.remove_quantifiers(g, problem)
            new_problem.add_goal(ng)
        for qm in problem.quality_metrics:
            if isinstance(qm, Oversubscription):
                new_problem.add_quality_metric(
                    Oversubscription(
                        {
                            expression_quantifier_remover.remove_quantifiers(
                                g, problem
                            ): v
                            for g, v in qm.goals.items()
                        }
                    )
                )
            else:
                new_problem.add_quality_metric(qm)

        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old), self.name
        )
