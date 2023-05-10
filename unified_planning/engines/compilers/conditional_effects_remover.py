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
"""This module defines the conditional effects remover class."""


import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.compilers.utils import updated_minimize_action_costs
from unified_planning.engines.results import CompilerResult
from unified_planning.exceptions import (
    UPProblemDefinitionError,
    UPConflictingEffectsException,
)
from unified_planning.model import Problem, ProblemKind
from unified_planning.engines.compilers.utils import (
    get_fresh_name,
    check_and_simplify_preconditions,
    check_and_simplify_conditions,
    replace_action,
)
from unified_planning.utils import powerset
from typing import List, Dict, Tuple, Optional
from functools import partial


class ConditionalEffectsRemover(engines.engine.Engine, CompilerMixin):
    """
    Conditional effects remover class: this class offers the capability
    to transform a :class:`~unified_planning.model.Problem` with conditional :class:`Effects <unified_planning.model.Effect>`
    into a `Problem` without conditional `Effects`. This capability is offered by the :meth:`~unified_planning.engines.compilers.ConditionalEffectsRemover.compile`
    method, that returns a :class:`~unified_planning.engines.CompilerResult` in which the :meth:`problem <unified_planning.engines.CompilerResult.problem>` field
    is the compiled Problem.

    This is done by substituting every conditional :class:`~unified_planning.model.Action` with different
    actions representing every possible branch of the original action.

    Also the conditional :meth:`timed_effects <unified_planning.model.Problem.timed_effects>` are removed maintaining the same
    semantics.

    When it is not possible to remove a conditional Effect without changing the semantic of the resulting Problem,
    an :exc:`~unified_planning.exceptions.UPProblemDefinitionError` is raised.

    This `Compiler` supports only the the `CONDITIONAL_EFFECTS_REMOVING` :class:`~unified_planning.engines.CompilationKind`.
    """

    def __init__(self):
        engines.engine.Engine.__init__(self)
        CompilerMixin.__init__(self, CompilationKind.CONDITIONAL_EFFECTS_REMOVING)

    @property
    def name(self):
        return "cerm"

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind()
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_numbers("CONTINUOUS_NUMBERS")
        supported_kind.set_numbers("DISCRETE_NUMBERS")
        supported_kind.set_numbers("BOUNDED_TYPES")
        supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
        supported_kind.set_fluents_type("NUMERIC_FLUENTS")
        supported_kind.set_fluents_type("OBJECT_FLUENTS")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITIES")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        supported_kind.set_effects_kind("INCREASE_EFFECTS")
        supported_kind.set_effects_kind("DECREASE_EFFECTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_time("CONTINUOUS_TIME")
        supported_kind.set_time("DISCRETE_TIME")
        supported_kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("EXTERNAL_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("TIMED_EFFECTS")
        supported_kind.set_time("TIMED_GOALS")
        supported_kind.set_time("DURATION_INEQUALITIES")
        supported_kind.set_time("SELF_OVERLAPPING")
        supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_actions_cost_kind("STATIC_FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("TEMPORAL_OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("MAKESPAN")
        supported_kind.set_quality_metrics("FINAL_VALUE")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= ConditionalEffectsRemover.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == CompilationKind.CONDITIONAL_EFFECTS_REMOVING

    @staticmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: Optional[CompilationKind] = None
    ) -> ProblemKind:
        new_kind = ProblemKind(problem_kind.features)
        if new_kind.has_conditional_effects():
            new_kind.unset_effects_kind("CONDITIONAL_EFFECTS")
            new_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        return new_kind

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        """
        Takes an instance of a :class:`~unified_planning.model.Problem` and the wanted :class:`~unified_planning.engines.CompilationKind`
        and returns a :class:`~unified_planning.engines.results.CompilerResult` where the :meth:`problem<unified_planning.engines.results.CompilerResult.problem>` field does not have conditional effects.

        :param problem: The instance of the :class:`~unified_planning.model.Problem` that must be returned without conditional effects.
        :param compilation_kind: The :class:`~unified_planning.engines.CompilationKind` that must be applied on the given problem;
            only :class:`~unified_planning.engines.CompilationKind.CONDITIONAL_EFFECTS_REMOVING` is supported by this compiler
        :return: The resulting :class:`~unified_planning.engines.results.CompilerResult` data structure.
        :raises: :exc:`~unified_planning.exceptions.UPProblemDefinitionError` when the :meth:`condition<unified_planning.model.Effect.condition>` of an
            :class:`~unified_planning.model.Effect` can't be removed without changing the :class:`~unified_planning.model.Problem` semantic.
        """
        assert isinstance(problem, Problem)
        env = problem.environment
        simplifier = env.simplifier

        new_to_old = {}

        new_problem = problem.clone()
        new_problem.name = f"{self.name}_{problem.name}"
        new_problem.clear_timed_effects()
        for t, el in problem.timed_effects.items():
            for e in el:
                if e.is_conditional():
                    f, v = e.fluent.fluent(), e.value
                    if not f.type.is_bool_type():
                        raise UPProblemDefinitionError(
                            f"The condition of effect: {e}\ncould not be removed without changing the problem."
                        )
                    else:
                        em = env.expression_manager
                        c = e.condition
                        nv = simplifier.simplify(
                            em.Or(em.And(c, v), em.And(em.Not(c), f))
                        )
                        new_problem.add_timed_effect(t, e.fluent, nv)
                else:
                    new_problem._add_effect_instance(t, e.clone())
        new_problem.clear_actions()
        for ua in problem.unconditional_actions:
            new_uncond_action = ua.clone()
            new_problem.add_action(new_uncond_action)
            new_to_old[new_uncond_action] = ua
        for action in problem.conditional_actions:
            if isinstance(action, up.model.InstantaneousAction):
                cond_effects = action.conditional_effects
                for p in powerset(range(len(cond_effects))):
                    new_action = action.clone()
                    new_action.name = get_fresh_name(new_problem, action.name)
                    new_action.clear_effects()
                    for e in action.unconditional_effects:
                        new_action._add_effect_instance(e.clone())
                    for i, e in enumerate(cond_effects):
                        if i in p:
                            # positive precondition
                            new_action.add_precondition(e.condition)
                            ne = up.model.Effect(
                                e.fluent,
                                e.value,
                                env.expression_manager.TRUE(),
                                e.kind,
                            )
                            # We try to add the new effect, but it might be in conflict with exising effects,
                            # so the action is not added to the problem
                            try:
                                new_action._add_effect_instance(ne)
                            except UPConflictingEffectsException:
                                continue
                        else:
                            # negative precondition
                            new_action.add_precondition(
                                env.expression_manager.Not(e.condition)
                            )
                    # new action is created, then is checked if it has any impact and if it can be simplified
                    if len(new_action.effects) > 0:
                        (
                            action_is_feasible,
                            simplified_preconditions,
                        ) = check_and_simplify_preconditions(
                            new_problem, new_action, simplifier
                        )
                        if action_is_feasible:
                            new_action._set_preconditions(simplified_preconditions)
                            new_to_old[new_action] = action
                            new_problem.add_action(new_action)
            elif isinstance(action, up.model.DurativeAction):
                timing_cond_effects: Dict[
                    "up.model.Timing", List["up.model.Effect"]
                ] = action.conditional_effects
                cond_effects_timing: List[
                    Tuple["up.model.Effect", "up.model.Timing"]
                ] = [(e, t) for t, el in timing_cond_effects.items() for e in el]
                for p in powerset(range(len(cond_effects_timing))):
                    new_action = action.clone()
                    new_action.name = get_fresh_name(new_problem, action.name)
                    new_action.clear_effects()
                    for t, el in action.unconditional_effects.items():
                        for e in el:
                            new_action._add_effect_instance(t, e.clone())
                    for i, (e, t) in enumerate(cond_effects_timing):
                        if i in p:
                            # positive precondition
                            new_action.add_condition(t, e.condition)
                            ne = up.model.Effect(
                                e.fluent,
                                e.value,
                                env.expression_manager.TRUE(),
                                e.kind,
                            )
                            # We try to add the new effect, but it might be in conflict with exising effects,
                            # so the action is not added to the problem
                            try:
                                new_action._add_effect_instance(t, ne)
                            except UPConflictingEffectsException:
                                continue
                        else:
                            # negative precondition
                            new_action.add_condition(
                                t, env.expression_manager.Not(e.condition)
                            )
                    # new action is created, then is checked if it has any impact and if it can be simplified
                    if len(new_action.effects) > 0:
                        (
                            action_is_feasible,
                            simplified_conditions,
                        ) = check_and_simplify_conditions(
                            new_problem, new_action, simplifier
                        )
                        if action_is_feasible:
                            new_action.clear_conditions()
                            for interval, c in simplified_conditions:
                                new_action.add_condition(interval, c)
                            new_to_old[new_action] = action
                            new_problem.add_action(new_action)
            else:
                raise NotImplementedError

        new_problem.clear_quality_metrics()
        for qm in problem.quality_metrics:
            if qm.is_minimize_action_costs():
                new_problem.add_quality_metric(
                    updated_minimize_action_costs(
                        qm, new_to_old, new_problem.environment
                    )
                )
            else:
                new_problem.add_quality_metric(qm)

        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old), self.name
        )
