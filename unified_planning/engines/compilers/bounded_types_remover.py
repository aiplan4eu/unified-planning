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
#
"""This module defines the bounded types remover class."""


import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.model import Problem, ProblemKind, Fluent, FNode
from unified_planning.model.fluent import get_all_fluent_exp
from unified_planning.model.types import _RealType, _IntType
from unified_planning.model.walkers import FluentsSubstituter
from unified_planning.engines.compilers.utils import (
    add_invariant_condition_apply_function_to_problem_expressions,
    replace_action,
)
from typing import List, Dict, OrderedDict, Optional, Union, cast
from functools import partial


class BoundedTypesRemover(engines.engine.Engine, CompilerMixin):
    """
    Bounded types remover class: this class offers the capability
    to transform a :class:`~unified_planning.model.Problem` with Bounded :class:`Types <unified_planning.model.Type>`
    into a `Problem` without bounded `Types` (only IntType and RealType can be bounded).
    This capability is offered by the :meth:`~unified_planning.engines.compilers.BoundedTypesRemover.compile`
    method, that returns a :class:`~unified_planning.engines.CompilerResult` in which the :meth:`problem <unified_planning.engines.CompilerResult.problem>` field
    is the compiled Problem.

    This is done by changing the type of the fluents to unbounded types, and adding to every action's condition and
    every goal of the problem the artificial condition that emulates the typing bound.

    For example, if we have a fluent `F` of type `int[0, 5]`, the added condition would be `0 <= F <= 5`.

    This `Compiler` supports only the the `BOUNDED_TYPES_REMOVING` :class:`~unified_planning.engines.CompilationKind`.
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
        supported_kind.set_parameters("BOOL_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOOL_ACTION_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("UNBOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("REAL_ACTION_PARAMETERS")
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
        supported_kind.set_constraints_kind("STATE_INVARIANTS")
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
        and returns a :class:`~unified_planning.engines.results.CompilerResult` where the :meth:`problem<unified_planning.engines.results.CompilerResult.problem>`
        field does not have bounded types.

        :param problem: The instance of the :class:`~unified_planning.model.Problem` that must be returned without bounded types.
        :param compilation_kind: The :class:`~unified_planning.engines.CompilationKind` that must be applied on the given problem;
            only :class:`~unified_planning.engines.CompilationKind.BOUNDED_TYPES_REMOVING` is supported by this compiler
        :return: The resulting :class:`~unified_planning.engines.results.CompilerResult` data structure.
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

            new_fluent = None
            # old_fluent.type != int_type is used to check if the type of the old_fluent
            # has lower or upper bound
            if old_fluent.type.is_int_type() and old_fluent.type != int_type:
                old_fluent_type: Union[_IntType, _RealType] = cast(
                    _IntType, old_fluent.type
                )
                assert (
                    old_fluent_type.lower_bound is not None
                    or old_fluent_type.upper_bound is not None
                ), "Error, old_fluent_type should equal int_type"
                signature = OrderedDict(
                    ((p.name, p.type) for p in old_fluent.signature)
                )
                new_fluent = Fluent(old_fluent.name, int_type, signature, env)

            # old_fluent.type != real_type is used to check if the type of the old_fluent
            # has lower or upper bound
            elif old_fluent.type.is_real_type() and old_fluent.type != real_type:
                old_fluent_type = cast(_RealType, old_fluent.type)
                assert (
                    old_fluent_type.lower_bound is not None
                    or old_fluent_type.upper_bound is not None
                ), "Error, old_fluent_type should equal real_type"
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
        new_to_old = add_invariant_condition_apply_function_to_problem_expressions(
            problem,
            new_problem,
            em.And(conditions),
            fluents_substituter.substitute_fluents,
        )

        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old), self.name
        )
