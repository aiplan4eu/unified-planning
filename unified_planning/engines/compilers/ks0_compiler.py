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
"""This module defines the KS0 conformant-to-classical compiler."""

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.compilers.disjunctive_conditions_remover import (
    DisjunctiveConditionsRemover,
)
from unified_planning.engines.compilers.grounder import Grounder
from unified_planning.engines.compilers.quantifiers_remover import QuantifiersRemover
from unified_planning.engines.compilers.utils import split_all_ands
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.exceptions import UPUsageError
from unified_planning.model import (
    FNode,
    Fluent,
    InstantaneousAction,
    Problem,
    ProblemKind,
    State,
    UPState,
)
from unified_planning.model.fluent import get_all_fluent_exp
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.plans import ActionInstance, Plan


@dataclass(frozen=True)
class _Ks0Tag:
    name: str


@dataclass(frozen=True)
class _PreparedEffectRule:
    condition_literals: Tuple[FNode, ...]
    target_literal: FNode
    negated_target_literal: FNode


@dataclass(frozen=True)
class _PreparedAction:
    action: InstantaneousAction
    precondition_literals: Tuple[FNode, ...]
    effect_rules: Tuple[_PreparedEffectRule, ...]


@dataclass(frozen=True)
class _PreparedNormalizedProblem:
    ground_fluent_expressions: Tuple[FNode, ...]
    prepared_actions: Tuple[_PreparedAction, ...]
    goal_literals: Tuple[FNode, ...]
    merge_targets: Tuple[FNode, ...]


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
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITIES")
        supported_kind.set_conditions_kind("EXISTENTIAL_CONDITIONS")
        supported_kind.set_conditions_kind("UNIVERSAL_CONDITIONS")
        supported_kind.set_effects_kind("CONDITIONAL_EFFECTS")
        supported_kind.set_effects_kind("FORALL_EFFECTS")
        supported_kind.set_initial_state("UNDEFINED_INITIAL_SYMBOLIC")
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
        new_kind.unset_conditions_kind("DISJUNCTIVE_CONDITIONS")
        new_kind.unset_conditions_kind("EQUALITIES")
        new_kind.unset_conditions_kind("EXISTENTIAL_CONDITIONS")
        new_kind.unset_conditions_kind("UNIVERSAL_CONDITIONS")
        new_kind.unset_effects_kind("FORALL_EFFECTS")
        new_kind.unset_initial_state("UNDEFINED_INITIAL_SYMBOLIC")
        return new_kind

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        assert isinstance(problem, Problem)
        possible_initial_states = self._get_possible_initial_states()
        ground_fluent_expressions = self._get_ground_fluent_expressions(problem)
        self._validate_possible_initial_states(
            problem, ground_fluent_expressions, possible_initial_states
        )

        if len(problem.quality_metrics) > 0:
            raise UPUsageError(
                "Ks0Compiler does not support problems with plan quality metrics."
            )

        deduplicated_states = self._deduplicate_possible_initial_states(
            ground_fluent_expressions, possible_initial_states
        )
        normalized_problem, normalization_results = self._normalize_problem(problem)
        self._validate_normalized_problem(normalized_problem)
        prepared_problem = self._prepare_normalized_problem(normalized_problem)
        normalized_states = self._rebuild_possible_initial_states(
            problem, normalized_problem, prepared_problem, deduplicated_states
        )
        basis_states = self._reduce_possible_initial_states_to_basis(
            normalized_problem, prepared_problem, normalized_states
        )
        compiled_problem, new_to_old_action = self._compile_normalized_problem(
            normalized_problem, prepared_problem, basis_states, problem.name
        )
        plan_back_conversion = self._build_plan_back_conversion(
            new_to_old_action, normalization_results
        )

        return CompilerResult(
            problem=compiled_problem,
            map_back_action_instance=None,
            engine_name=self.name,
            plan_back_conversion=plan_back_conversion,
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
        problem: Problem,
        ground_fluent_expressions: Tuple[FNode, ...],
        possible_initial_states: Tuple[State, ...],
    ) -> None:
        for fluent in problem.fluents:
            if not fluent.type.is_bool_type():
                raise UPUsageError(
                    "Ks0Compiler supports only problems with Boolean fluents."
                )

        for index, state in enumerate(possible_initial_states):
            if not isinstance(state, State):
                raise UPUsageError(
                    "Every element of `possible_initial_states` must be a "
                    f"`unified_planning.model.State`; found {type(state)} at index {index}."
                )

            state_problem = getattr(state, "_fluent_set", None)
            state_environment = getattr(state_problem, "environment", None)
            if state_environment is None:
                state_values = getattr(state, "_values", None)
                if isinstance(state_values, dict) and len(state_values) > 0:
                    sample_exp = next(iter(state_values))
                    state_environment = sample_exp.environment

            if (
                state_environment is not None
                and state_environment is not problem.environment
            ):
                raise UPUsageError(
                    "Every element of `possible_initial_states` must be defined "
                    "in the same environment as the problem passed to `compile`; "
                    f"found a state from a different environment at index {index}."
                )

            if state_problem is not None and state_problem is not problem:
                raise UPUsageError(
                    "Every element of `possible_initial_states` must be defined "
                    "for the same problem passed to `compile`; found a state from a "
                    f"different problem at index {index}."
                )

            for fluent_exp in ground_fluent_expressions:
                try:
                    value = state.get_value(fluent_exp)
                except UPUsageError as err:
                    raise UPUsageError(
                        "Every element of `possible_initial_states` must define "
                        "a Boolean value for every grounded fluent of the problem; "
                        f"state at index {index} is missing a value for `{fluent_exp}`."
                    ) from err
                if not value.is_bool_constant():
                    raise UPUsageError(
                        "Every element of `possible_initial_states` must define "
                        "a Boolean value for every grounded fluent of the problem; "
                        f"state at index {index} assigns `{value}` to `{fluent_exp}`."
                    )

    @staticmethod
    def _deduplicate_possible_initial_states(
        ground_fluent_expressions: Tuple[FNode, ...],
        possible_initial_states: Tuple[State, ...],
    ) -> Tuple[State, ...]:
        unique_states: List[State] = []
        seen_signatures = set()
        for state in possible_initial_states:
            state_signature = tuple(
                state.get_value(fluent_exp).bool_constant_value()
                for fluent_exp in ground_fluent_expressions
            )
            if state_signature not in seen_signatures:
                seen_signatures.add(state_signature)
                unique_states.append(state)
        return tuple(unique_states)

    @staticmethod
    def _get_ground_fluent_expressions(problem: Problem) -> Tuple[FNode, ...]:
        ground_fluent_expressions: List[FNode] = []
        for fluent in problem.fluents:
            ground_fluent_expressions.extend(get_all_fluent_exp(problem, fluent))
        return tuple(ground_fluent_expressions)

    @staticmethod
    def _normalize_problem(
        problem: Problem,
    ) -> Tuple[Problem, Tuple[CompilerResult, ...]]:
        normalized_problem = problem
        normalization_results: List[CompilerResult] = []

        if (
            normalized_problem.kind.has_existential_conditions()
            or normalized_problem.kind.has_universal_conditions()
            or normalized_problem.kind.has_forall_effects()
        ):
            quantifiers_remover = QuantifiersRemover()
            quantifiers_remover.skip_checks = True
            quantifiers_result = quantifiers_remover.compile(
                normalized_problem, CompilationKind.QUANTIFIERS_REMOVING
            )
            assert isinstance(quantifiers_result.problem, Problem)
            normalized_problem = quantifiers_result.problem
            normalization_results.append(quantifiers_result)

        if normalized_problem.kind.has_disjunctive_conditions():
            disjunction_remover = DisjunctiveConditionsRemover()
            disjunction_remover.skip_checks = True
            disjunction_result = disjunction_remover.compile(
                normalized_problem, CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING
            )
            assert isinstance(disjunction_result.problem, Problem)
            normalized_problem = disjunction_result.problem
            normalization_results.append(disjunction_result)

        grounder = Grounder()
        grounder.skip_checks = True
        grounding_result = grounder.compile(
            normalized_problem, CompilationKind.GROUNDING
        )
        assert isinstance(grounding_result.problem, Problem)
        normalized_problem = grounding_result.problem
        normalization_results.append(grounding_result)

        return normalized_problem, tuple(normalization_results)

    @staticmethod
    def _rebuild_possible_initial_states(
        original_problem: Problem,
        normalized_problem: Problem,
        prepared_problem: _PreparedNormalizedProblem,
        possible_initial_states: Tuple[State, ...],
    ) -> Tuple[UPState, ...]:
        expression_manager = normalized_problem.environment.expression_manager
        true_exp = expression_manager.TRUE()
        false_exp = expression_manager.FALSE()
        value_sources: List[Tuple[FNode, Optional[FNode], Optional[bool]]] = []

        for fluent_exp in prepared_problem.ground_fluent_expressions:
            fluent = fluent_exp.fluent()
            if original_problem.has_fluent(fluent.name):
                original_fluent = original_problem.fluent(fluent.name)
                original_args = []
                for arg in fluent_exp.args:
                    if not arg.is_object_exp():
                        raise UPUsageError(
                            "Ks0Compiler requires all fluent arguments to be grounded "
                            "to objects after normalization."
                        )
                    original_args.append(original_problem.object(arg.object().name))
                value_sources.append(
                    (fluent_exp, original_fluent(*original_args), None)
                )
            else:
                value = normalized_problem.initial_value(fluent_exp)
                if value is None:
                    raise UPUsageError(
                        "Ks0Compiler normalization introduced a fluent with an "
                        f"undefined initial value: `{fluent_exp}`."
                    )
                if not value.is_bool_constant():
                    raise UPUsageError(
                        "Ks0Compiler supports only Boolean-valued possible initial "
                        f"states; found `{value}` for `{fluent_exp}`."
                    )
                value_sources.append((fluent_exp, None, value.bool_constant_value()))

        normalized_states: List[UPState] = []

        for state in possible_initial_states:
            values: Dict[FNode, FNode] = {}
            for fluent_exp, original_fluent_exp, default_value in value_sources:
                if original_fluent_exp is None:
                    values[fluent_exp] = true_exp if default_value else false_exp
                else:
                    value = state.get_value(original_fluent_exp)
                    if not value.is_bool_constant():
                        raise UPUsageError(
                            "Ks0Compiler supports only Boolean-valued possible initial "
                            "states; found "
                            f"`{value}` for `{original_fluent_exp}`."
                        )
                    values[fluent_exp] = (
                        true_exp if value.bool_constant_value() else false_exp
                    )
            normalized_states.append(UPState(values, normalized_problem))

        return tuple(normalized_states)

    def _compile_normalized_problem(
        self,
        problem: Problem,
        prepared_problem: _PreparedNormalizedProblem,
        possible_initial_states: Tuple[UPState, ...],
        original_problem_name: Optional[str],
    ) -> Tuple[Problem, Dict[up.model.Action, Optional[up.model.Action]]]:
        environment = problem.environment
        expression_manager = environment.expression_manager
        tags = tuple(
            [_Ks0Tag("empty")]
            + [_Ks0Tag(f"s{index}") for index, _ in enumerate(possible_initial_states)]
        )

        compiled_problem = Problem(
            f"ks0_{original_problem_name}", environment=environment
        )
        for obj in problem.all_objects:
            compiled_problem.add_object(obj)

        knowledge_fluents: Dict[Tuple[Fluent, bool, str], Fluent] = {}
        for fluent in problem.fluents:
            for is_negative in (False, True):
                for tag in tags:
                    knowledge_fluent = Fluent(
                        self._knowledge_fluent_name(fluent, is_negative, tag.name),
                        environment.type_manager.BoolType(),
                        fluent.signature,
                        environment=environment,
                    )
                    compiled_problem.add_fluent(
                        knowledge_fluent, default_initial_value=False
                    )
                    knowledge_fluents[
                        (fluent, is_negative, tag.name)
                    ] = knowledge_fluent

        empty_tag = tags[0]
        negated_ground_literals = {
            fluent_exp: expression_manager.Not(fluent_exp)
            for fluent_exp in prepared_problem.ground_fluent_expressions
        }
        knowledge_literal_cache: Dict[Tuple[FNode, str], FNode] = {}
        negated_knowledge_literal_cache: Dict[Tuple[FNode, str], FNode] = {}
        for tag in tags:
            for fluent_exp in prepared_problem.ground_fluent_expressions:
                positive_knowledge = knowledge_fluents[
                    (fluent_exp.fluent(), False, tag.name)
                ](*fluent_exp.args)
                negative_knowledge = knowledge_fluents[
                    (fluent_exp.fluent(), True, tag.name)
                ](*fluent_exp.args)
                knowledge_literal_cache[(fluent_exp, tag.name)] = positive_knowledge
                knowledge_literal_cache[
                    (negated_ground_literals[fluent_exp], tag.name)
                ] = negative_knowledge
                negated_knowledge_literal_cache[
                    (fluent_exp, tag.name)
                ] = expression_manager.Not(negative_knowledge)
                negated_knowledge_literal_cache[
                    (negated_ground_literals[fluent_exp], tag.name)
                ] = expression_manager.Not(positive_knowledge)

        for fluent_exp in prepared_problem.ground_fluent_expressions:
            state_values = tuple(
                state.get_value(fluent_exp).bool_constant_value()
                for state in possible_initial_states
            )
            if all(state_values):
                compiled_problem.set_initial_value(
                    knowledge_literal_cache[(fluent_exp, empty_tag.name)],
                    True,
                )
            elif not any(state_values):
                compiled_problem.set_initial_value(
                    knowledge_literal_cache[
                        (negated_ground_literals[fluent_exp], empty_tag.name)
                    ],
                    True,
                )

            for index, value in enumerate(state_values):
                tag_name = tags[index + 1].name
                compiled_problem.set_initial_value(
                    knowledge_literal_cache[
                        (
                            fluent_exp
                            if value
                            else negated_ground_literals[fluent_exp],
                            tag_name,
                        )
                    ],
                    True,
                )

        new_to_old_action: Dict[up.model.Action, Optional[up.model.Action]] = {}
        for prepared_action in prepared_problem.prepared_actions:
            action = prepared_action.action
            compiled_action = InstantaneousAction(action.name, _env=environment)
            for literal in prepared_action.precondition_literals:
                compiled_action.add_precondition(
                    knowledge_literal_cache[(literal, empty_tag.name)]
                )

            for tag in tags:
                for effect_rule in prepared_action.effect_rules:
                    support_condition = self._conjunction(
                        expression_manager,
                        [
                            knowledge_literal_cache[(literal, tag.name)]
                            for literal in effect_rule.condition_literals
                        ],
                    )
                    compiled_action.add_effect(
                        knowledge_literal_cache[(effect_rule.target_literal, tag.name)],
                        True,
                        support_condition,
                    )

                    cancellation_condition = self._conjunction(
                        expression_manager,
                        [
                            negated_knowledge_literal_cache[(literal, tag.name)]
                            for literal in effect_rule.condition_literals
                        ],
                    )
                    compiled_action.add_effect(
                        knowledge_literal_cache[
                            (effect_rule.negated_target_literal, tag.name)
                        ],
                        False,
                        cancellation_condition,
                    )

            compiled_problem.add_action(compiled_action)
            new_to_old_action[compiled_action] = action

        for goal_literal in prepared_problem.goal_literals:
            compiled_problem.add_goal(
                knowledge_literal_cache[(goal_literal, empty_tag.name)]
            )

        for literal in prepared_problem.merge_targets:
            merge_action = InstantaneousAction(
                f"merge_{self._literal_name(literal)}", _env=environment
            )
            for tag in tags[1:]:
                merge_action.add_precondition(
                    knowledge_literal_cache[(literal, tag.name)]
                )
            merge_action.add_effect(
                knowledge_literal_cache[(literal, empty_tag.name)],
                True,
            )
            compiled_problem.add_action(merge_action)
            new_to_old_action[merge_action] = None

        return compiled_problem, new_to_old_action

    @staticmethod
    def _validate_normalized_problem(problem: Problem) -> None:
        for fluent in problem.fluents:
            if not fluent.type.is_bool_type():
                raise UPUsageError(
                    "Ks0Compiler supports only Boolean fluents after normalization."
                )

        for action in problem.actions:
            if not isinstance(action, InstantaneousAction):
                raise UPUsageError(
                    "Ks0Compiler supports only instantaneous actions after "
                    "normalization."
                )

    @classmethod
    def _prepare_normalized_problem(
        cls, problem: Problem
    ) -> _PreparedNormalizedProblem:
        expression_manager = problem.environment.expression_manager
        prepared_actions: List[_PreparedAction] = []
        merge_targets: List[FNode] = []
        seen_merge_targets = set()

        for action in problem.actions:
            assert isinstance(action, InstantaneousAction)
            precondition_literals = cls._extract_literals(
                action.preconditions,
                f"the preconditions of action `{action.name}`",
            )
            for literal in precondition_literals:
                if literal not in seen_merge_targets:
                    seen_merge_targets.add(literal)
                    merge_targets.append(literal)

            effect_rules: List[_PreparedEffectRule] = []
            for effect in action.effects:
                for expanded_effect in effect.expand_effect(problem):
                    if expanded_effect.condition.is_false():
                        continue

                    if not expanded_effect.is_assignment():
                        raise UPUsageError(
                            "Ks0Compiler supports only Boolean assignment effects "
                            f"after normalization; found `{expanded_effect}` in "
                            f"action `{action.name}`."
                        )
                    if not expanded_effect.fluent.is_fluent_exp():
                        raise UPUsageError(
                            "Ks0Compiler supports only fluent assignment effects "
                            f"after normalization; found `{expanded_effect}` in "
                            f"action `{action.name}`."
                        )
                    if not expanded_effect.fluent.fluent().type.is_bool_type():
                        raise UPUsageError(
                            "Ks0Compiler supports only Boolean assignment effects "
                            f"after normalization; found `{expanded_effect}` in "
                            f"action `{action.name}`."
                        )
                    if not expanded_effect.value.is_bool_constant():
                        raise UPUsageError(
                            "Ks0Compiler supports only Boolean assignment effects "
                            f"after normalization; found `{expanded_effect}` in "
                            f"action `{action.name}`."
                        )

                    target_literal = (
                        expanded_effect.fluent
                        if expanded_effect.value.bool_constant_value()
                        else expression_manager.Not(expanded_effect.fluent)
                    )
                    effect_rules.append(
                        _PreparedEffectRule(
                            condition_literals=cls._extract_literals(
                                (expanded_effect.condition,),
                                f"the condition of effect `{expanded_effect}`",
                            ),
                            target_literal=target_literal,
                            negated_target_literal=cls._negate_literal(
                                target_literal, expression_manager
                            ),
                        )
                    )

            prepared_actions.append(
                _PreparedAction(
                    action=action,
                    precondition_literals=precondition_literals,
                    effect_rules=tuple(effect_rules),
                )
            )

        goal_literals = cls._extract_literals(problem.goals, "the goals")
        for goal_literal in goal_literals:
            if goal_literal not in seen_merge_targets:
                seen_merge_targets.add(goal_literal)
                merge_targets.append(goal_literal)

        return _PreparedNormalizedProblem(
            ground_fluent_expressions=cls._get_ground_fluent_expressions(problem),
            prepared_actions=tuple(prepared_actions),
            goal_literals=goal_literals,
            merge_targets=tuple(merge_targets),
        )

    @classmethod
    def _reduce_possible_initial_states_to_basis(
        cls,
        problem: Problem,
        prepared_problem: _PreparedNormalizedProblem,
        possible_initial_states: Tuple[UPState, ...],
    ) -> Tuple[UPState, ...]:
        if len(possible_initial_states) <= 1:
            return possible_initial_states

        target_literals = prepared_problem.merge_targets
        if len(target_literals) == 0:
            return possible_initial_states[:1]

        expression_manager = problem.environment.expression_manager
        negated_literals = {
            fluent_exp: expression_manager.Not(fluent_exp)
            for fluent_exp in prepared_problem.ground_fluent_expressions
        }
        complete_state_literals = []
        for state in possible_initial_states:
            complete_state_literals.append(
                frozenset(
                    fluent_exp
                    if state.get_value(fluent_exp).bool_constant_value()
                    else negated_literals[fluent_exp]
                    for fluent_exp in prepared_problem.ground_fluent_expressions
                )
            )

        relevance = cls._get_relevance_relation(prepared_problem, expression_manager)
        relevant_sources_by_target = {
            target_literal: frozenset(
                source_literal
                for source_literal, relevant_targets in relevance.items()
                if target_literal in relevant_targets
            )
            for target_literal in target_literals
        }

        selected_indices: set[int] = set()
        for target_literal in target_literals:
            relevant_sources = relevant_sources_by_target[target_literal]
            minimal_rel_sets: List[Tuple[int, frozenset[FNode]]] = []

            for index, state_literals in enumerate(complete_state_literals):
                relevant_state_literals = frozenset(
                    literal for literal in state_literals if literal in relevant_sources
                )

                dominated = False
                updated_minimals: List[Tuple[int, frozenset[FNode]]] = []
                for existing_index, existing_rel_set in minimal_rel_sets:
                    if existing_rel_set <= relevant_state_literals:
                        dominated = True
                        updated_minimals.append((existing_index, existing_rel_set))
                    elif relevant_state_literals < existing_rel_set:
                        continue
                    else:
                        updated_minimals.append((existing_index, existing_rel_set))

                if not dominated:
                    minimal_rel_sets = updated_minimals
                    minimal_rel_sets.append((index, relevant_state_literals))

            selected_indices.update(index for index, _ in minimal_rel_sets)

        if len(selected_indices) == len(possible_initial_states):
            return possible_initial_states
        return tuple(
            possible_initial_states[index] for index in sorted(selected_indices)
        )

    @staticmethod
    def _get_relevance_relation(
        prepared_problem: _PreparedNormalizedProblem, expression_manager
    ) -> Dict[FNode, frozenset[FNode]]:
        all_literals: List[FNode] = []
        negated_literals: Dict[FNode, FNode] = {}
        for fluent_exp in prepared_problem.ground_fluent_expressions:
            negated_literal = expression_manager.Not(fluent_exp)
            all_literals.append(fluent_exp)
            all_literals.append(negated_literal)
            negated_literals[fluent_exp] = negated_literal
            negated_literals[negated_literal] = fluent_exp

        relevance: Dict[FNode, set[FNode]] = {
            literal: {literal} for literal in all_literals
        }
        for prepared_action in prepared_problem.prepared_actions:
            for effect_rule in prepared_action.effect_rules:
                for condition_literal in effect_rule.condition_literals:
                    relevance[condition_literal].add(effect_rule.target_literal)

        changed = True
        while changed:
            changed = False

            for literal in all_literals:
                expanded_targets = set(relevance[literal])
                for intermediate_literal in tuple(relevance[literal]):
                    expanded_targets.update(relevance[intermediate_literal])
                if len(expanded_targets) > len(relevance[literal]):
                    relevance[literal] = expanded_targets
                    changed = True

            for literal in all_literals:
                complement_targets = relevance[negated_literals[literal]]
                expanded_targets = set(relevance[literal])
                for complement_target in complement_targets:
                    expanded_targets.add(negated_literals[complement_target])
                if len(expanded_targets) > len(relevance[literal]):
                    relevance[literal] = expanded_targets
                    changed = True

        return {literal: frozenset(targets) for literal, targets in relevance.items()}

    @staticmethod
    def _build_plan_back_conversion(
        new_to_old_action: Dict[up.model.Action, Optional[up.model.Action]],
        normalization_results: Sequence[CompilerResult],
    ) -> Callable[[Plan], Plan]:
        def convert(plan: Plan) -> Plan:
            current_plan = plan.replace_action_instances(
                lambda action_instance: Ks0Compiler._map_back_ks0_action_instance(
                    action_instance, new_to_old_action
                )
            )
            for normalization_result in reversed(normalization_results):
                current_plan = Ks0Compiler._compiler_result_plan_back_conversion(
                    normalization_result
                )(current_plan)
            return current_plan

        return convert

    @staticmethod
    def _compiler_result_plan_back_conversion(
        result: CompilerResult,
    ) -> Callable[[Plan], Plan]:
        if result.plan_back_conversion is not None:
            return result.plan_back_conversion
        if result.map_back_action_instance is not None:
            map_back = result.map_back_action_instance
            return lambda plan: plan.replace_action_instances(map_back)
        raise UPUsageError(
            "Ks0Compiler expected a compiler result with a plan-back conversion, "
            f"but `{result.engine_name}` did not provide one."
        )

    @staticmethod
    def _map_back_ks0_action_instance(
        action_instance: ActionInstance,
        new_to_old_action: Dict[up.model.Action, Optional[up.model.Action]],
    ) -> Optional[ActionInstance]:
        old_action = new_to_old_action[action_instance.action]
        if old_action is None:
            return None
        return ActionInstance(old_action, action_instance.actual_parameters)

    @staticmethod
    def _knowledge_fluent_name(fluent: Fluent, is_negative: bool, tag_name: str) -> str:
        return f"K_{'not_' if is_negative else ''}{fluent.name}_{tag_name}"

    @staticmethod
    def _knowledge_for_literal(
        knowledge_fluents: Dict[Tuple[Fluent, bool, str], Fluent],
        literal: FNode,
        tag: _Ks0Tag,
    ) -> FNode:
        fluent_exp, is_negative = Ks0Compiler._literal_parts(literal)
        return knowledge_fluents[(fluent_exp.fluent(), is_negative, tag.name)](
            *fluent_exp.args
        )

    @staticmethod
    def _literal_parts(literal: FNode) -> Tuple[FNode, bool]:
        if literal.is_fluent_exp():
            return literal, False
        if literal.is_not() and literal.arg(0).is_fluent_exp():
            return literal.arg(0), True
        raise UPUsageError(
            f"Ks0Compiler expected a fluent literal and found `{literal}` instead."
        )

    @staticmethod
    def _negate_literal(literal: FNode, expression_manager) -> FNode:
        fluent_exp, is_negative = Ks0Compiler._literal_parts(literal)
        return fluent_exp if is_negative else expression_manager.Not(fluent_exp)

    @staticmethod
    def _literal_name(literal: FNode) -> str:
        fluent_exp, is_negative = Ks0Compiler._literal_parts(literal)
        name_parts = [fluent_exp.fluent().name]
        for arg in fluent_exp.args:
            if arg.is_object_exp():
                name_parts.append(arg.object().name)
            else:
                name_parts.append(str(arg))
        prefix = "not_" if is_negative else ""
        return prefix + "_".join(name_parts)

    @staticmethod
    def _extract_literals(
        expressions: Sequence[FNode], context: str
    ) -> Tuple[FNode, ...]:
        literals: List[FNode] = []
        for expression in split_all_ands(list(expressions)):
            if expression.is_true():
                continue
            if expression.is_false():
                raise UPUsageError(
                    "Ks0Compiler requires conjunctions of fluent literals after "
                    f"normalization, but found `false` in {context}."
                )
            if expression.is_fluent_exp() or (
                expression.is_not() and expression.arg(0).is_fluent_exp()
            ):
                literals.append(expression)
            else:
                raise UPUsageError(
                    "Ks0Compiler requires conjunctions of fluent literals after "
                    f"normalization, but found `{expression}` in {context}."
                )
        return tuple(literals)

    @staticmethod
    def _conjunction(expression_manager, expressions: Sequence[FNode]) -> FNode:
        if len(expressions) == 0:
            return expression_manager.TRUE()
        if len(expressions) == 1:
            return expressions[0]
        return expression_manager.And(list(expressions))
