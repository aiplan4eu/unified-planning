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
"""This module defines the KS0 conformant-to-classical compiler skeleton."""

from typing import Iterable, Optional, Tuple

import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.exceptions import UPUsageError
from unified_planning.model import Problem, ProblemKind, State
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION


class Ks0Compiler(engines.engine.Engine, CompilerMixin):
    """
    Skeleton compiler for the KS0 conformant-planning compilation.

    The compiler expects a regular ``Problem`` plus an explicit, non-empty collection
    of possible initial states. Since the compiler API receives only the problem in the
    ``compile`` call, the possible states are provided at construction time.
    """

    def __init__(self, possible_initial_states: Optional[Iterable[State]] = None):
        engines.engine.Engine.__init__(self)
        CompilerMixin.__init__(self, CompilationKind.CONFORMANT_TO_CLASSICAL_KS0)
        self._possible_initial_states = self._normalize_possible_initial_states(
            possible_initial_states
        )

    @property
    def name(self) -> str:
        return "ks0_compiler"

    @property
    def possible_initial_states(self) -> Optional[Tuple[State, ...]]:
        return self._possible_initial_states

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_parameters("BOOL_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOOL_ACTION_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("UNBOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("REAL_ACTION_PARAMETERS")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITIES")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        supported_kind.set_effects_kind("FORALL_EFFECTS")
        supported_kind.set_initial_state("UNDEFINED_INITIAL_SYMBOLIC")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("TEMPORAL_OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("MAKESPAN")
        supported_kind.set_quality_metrics("FINAL_VALUE")
        supported_kind.set_actions_cost_kind("STATIC_FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("INT_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("REAL_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_oversubscription_kind("INT_NUMBERS_IN_OVERSUBSCRIPTION")
        supported_kind.set_oversubscription_kind("REAL_NUMBERS_IN_OVERSUBSCRIPTION")
        return supported_kind

    @staticmethod
    def supports(problem_kind: ProblemKind) -> bool:
        return problem_kind <= Ks0Compiler.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == CompilationKind.CONFORMANT_TO_CLASSICAL_KS0

    @staticmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: Optional[CompilationKind] = None
    ) -> ProblemKind:
        new_kind = problem_kind.clone()
        new_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        new_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        new_kind.unset_initial_state("UNDEFINED_INITIAL_SYMBOLIC")
        return new_kind

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        assert isinstance(problem, Problem)
        possible_initial_states = self._get_possible_initial_states()
        self._validate_possible_initial_states(problem, possible_initial_states)
        
        raise NotImplementedError(
            "Ks0Compiler skeleton only: the KS0 compilation is not implemented yet."
        )

    @staticmethod
    def _normalize_possible_initial_states(
        possible_initial_states: Optional[Iterable[State]],
    ) -> Optional[Tuple[State, ...]]:
        if possible_initial_states is None:
            return None
        return tuple(possible_initial_states)

    def _get_possible_initial_states(self) -> Tuple[State, ...]:
        possible_initial_states = self._possible_initial_states
        if possible_initial_states is None:
            raise UPUsageError(
                "Ks0Compiler requires `possible_initial_states` to be provided at construction time."
            )
        if len(possible_initial_states) == 0:
            raise UPUsageError(
                "Ks0Compiler requires `possible_initial_states` to be non-empty."
            )
        return possible_initial_states

    @staticmethod
    def _validate_possible_initial_states(
        problem: Problem, possible_initial_states: Tuple[State, ...]
    ) -> None:
        for index, state in enumerate(possible_initial_states):
            if not isinstance(state, State):
                raise UPUsageError(
                    "Every element of `possible_initial_states` must be a "
                    f"`unified_planning.model.State`; found {type(state)} at index {index}."
                )
            
            #TODO assert state is compatible with the problem, i.e., 
            # the state is defined over the same fluents as the probllem,
            # and that the fluents have the same types and parameters as in the problem.
            # Also verify that they are under the same environment as the problem.
