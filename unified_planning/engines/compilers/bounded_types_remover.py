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
from unified_planning.engines.results import CompilerResult
from unified_planning.exceptions import (
    UPProblemDefinitionError,
    UPConflictingEffectsException,
)
from unified_planning.model import Problem, ProblemKind, Fluent, FNode
from unified_planning.model.fluent import get_all_fluent_exp
from unified_planning.model.types import _RealType
from unified_planning.model.walkers import FluentsSubstituter
from unified_planning.engines.compilers.utils import (
    add_condition_to_all_problem,
    replace_action,
)
from typing import List, Dict, OrderedDict, Optional, cast
from functools import partial


class BoundedTypesRemover(engines.engine.Engine, CompilerMixin):
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
        CompilerMixin.__init__(self, CompilationKind.BOUNDED_TYPES_REMOVING)

    @property
    def name(self):
        return "btrm"

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
        return problem_kind <= BoundedTypesRemover.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == CompilationKind.BOUNDED_TYPES_REMOVING

    @staticmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: Optional[CompilationKind] = None
    ) -> ProblemKind:
        new_kind = ProblemKind(problem_kind.features)
        if new_kind.has_bounded_types():
            new_kind.unset_numbers("BOUNDED_TYPES")
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
        em = env.expression_manager
        tm = env.type_manager
        new_problem = Problem(f"{problem.name}_{self.name}", env)
        new_problem.add_objects(problem.all_objects)

        int_type = tm.IntType()
        real_type = tm.RealType()
        conditions: List[FNode] = []

        new_fluents: Dict[Fluent, Fluent] = {}
        for old_fluent in problem.fluents:
            old_fluent_type = cast(_RealType, old_fluent.type)

            new_fluent = None
            if old_fluent_type.is_int_type() and old_fluent_type != int_type:
                assert (
                    old_fluent_type.lower_bound is not None
                    or old_fluent_type.upper_bound is not None
                ), "Error, old_fluent_type should equal int_type"
                signature = OrderedDict(
                    ((p.name, p.type) for p in old_fluent.signature)
                )
                new_fluent = Fluent(old_fluent.name, int_type, signature, env)
            elif old_fluent_type.is_real_type() and old_fluent_type != real_type:
                assert (
                    old_fluent_type.lower_bound is not None
                    or old_fluent_type.upper_bound is not None
                ), "Error, old_fluent_type should equal int_type"
                signature = OrderedDict(
                    ((p.name, p.type) for p in old_fluent.signature)
                )
                new_fluent = Fluent(old_fluent.name, real_type, signature, env)

            if new_fluent is not None:
                new_problem.add_fluent(new_fluent)
                new_fluents[old_fluent] = new_fluent
                for fluent_exp in get_all_fluent_exp(new_problem, new_fluent):
                    if old_fluent_type.lower_bound is not None:
                        conditions.append(
                            em.LE(old_fluent_type.lower_bound, fluent_exp)
                        )
                    if old_fluent_type.upper_bound is not None:
                        conditions.append(
                            em.LE(fluent_exp, old_fluent_type.upper_bound)
                        )
            else:
                new_problem.add_fluent(old_fluent)

        fluents_substituter = FluentsSubstituter(new_fluents, env)
        new_to_old = add_condition_to_all_problem(
            problem,
            new_problem,
            em.And(conditions),
            fluents_substituter.substitute_fluents,
        )

        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old), self.name
        )
