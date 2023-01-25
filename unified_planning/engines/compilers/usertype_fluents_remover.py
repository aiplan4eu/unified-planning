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
from unified_planning.model import Problem, ProblemKind, Fluent, Parameter, Action
from unified_planning.engines.compilers.utils import (
    get_fresh_name,
    check_and_simplify_preconditions,
    check_and_simplify_conditions,
    replace_action,
)
from unified_planning.utils import powerset
from typing import List, Dict, Tuple, Optional
from functools import partial


class UserTypeFluentsRemover(engines.engine.Engine, CompilerMixin):
    """TODO
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
        CompilerMixin.__init__(self, CompilationKind.USERTYPE_FLUENTS_REMOVING)

    @property
    def name(self):
        return "utfr"

    @staticmethod
    def supported_kind() -> ProblemKind:  # TODO check
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
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= UserTypeFluentsRemover.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == CompilationKind.USERTYPE_FLUENTS_REMOVING

    @staticmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: Optional[CompilationKind] = None
    ) -> ProblemKind:
        new_kind = ProblemKind(problem_kind.features)
        if new_kind.has_conditional_effects():
            new_kind.unset_fluents_type("OBJECT_FLUENTS")
            new_kind.set_effects_kind("CONDITIONAL_EFFECTS")
            new_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        return new_kind

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        """# TODO
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
        env = problem.env
        simplifier = env.simplifier
        tm = env.type_manager

        new_to_old: Dict[Action, Action] = {}

        new_problem = problem.clone()
        new_problem.name = f"{self.name}_{problem.name}"
        fluents_map: Dict[Fluent, Fluent] = {}
        new_problem.clear_fluents()
        for fluent in problem.fluents:
            assert isinstance(fluent, Fluent)
            if fluent.type.is_user_type():
                new_signature = fluent.signature[:]
                base_name = str(fluent.type).lower()
                new_param_name = base_name
                count = 0
                while any(p.name == new_param_name for p in new_signature):
                    new_param_name = f"{base_name}_{count}"
                    count += 1
                new_signature.append(Parameter(new_param_name, fluent.type, env))
                new_fluent = Fluent(
                    fluent.name, tm.BoolType(), _signature=new_signature, env=env
                )
                fluents_map[fluent] = new_fluent
                new_problem.add_fluent(new_fluent)
            else:
                new_problem.add_fluent(fluent)

        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old), self.name
        )
