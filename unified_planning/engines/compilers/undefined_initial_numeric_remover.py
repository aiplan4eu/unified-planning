# Copyright 2026 Unified Planning library and its maintainers
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
"""This module defines the UndefinedInitialNumericRemover class."""


import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.model import (
    Problem,
    ProblemKind,
    Fluent,
    FNode,
    Action,
    InstantaneousAction,
    DurativeAction,
    MinimizeActionCosts,
    Timing,
    TimePointInterval,
    StartTiming,
)
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.model.walkers.free_vars import FreeVarsExtractor
from unified_planning.engines.compilers.utils import replace_action
from fractions import Fraction
from typing import Optional, Union, List, Dict, Set
from functools import partial
from collections import defaultdict


class UndefinedInitialNumericRemover(engines.engine.Engine, CompilerMixin):
    """
    Undefined initial numeric remover class: this class offers the capability
    to transform a :class:`~unified_planning.model.Problem` containing numeric
    fluents without an initial value into an equivalent problem where all numeric
    fluents are properly initialized and handled.
    This capability is offered by the :meth:`~unified_planning.engines.compilers.UndefinedInitialNumericRemover.compile`
    method, that returns a :class:`~unified_planning.engines.CompilerResult` in which
    the :meth:`problem <unified_planning.engines.CompilerResult.problem>` field
    is the compiled Problem.

    Compilation details:
    - For each numeric fluent with an undefined initial value, a corresponding
      boolean fluent is introduced and initialized to ``False``.
    - This boolean fluent tracks whether the numeric fluent has been assigned a value.
    - Whenever an action assigns a value to the numeric fluent, the boolean fluent
      is set to ``True``.
    - The boolean fluent is added to an action's conditions whenever the numeric fluent is used:
        * in any precondition of the action, or
        * in any expression used to compute the value of an effect of the action.

    This `Compiler` supports only the the `UNDEFINED_INITIAL_NUMERIC_REMOVING` :class:`~unified_planning.engines.CompilationKind`.
    """

    def __init__(self):
        engines.engine.Engine.__init__(self)
        CompilerMixin.__init__(self, CompilationKind.UNDEFINED_INITIAL_NUMERIC_REMOVING)
        self._fve = FreeVarsExtractor()

    @property
    def name(self):
        return "undefined_initial_numeric_remover"

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_problem_class("TAMP")
        supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
        supported_kind.set_time("CONTINUOUS_TIME")
        supported_kind.set_time("DISCRETE_TIME")
        supported_kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("EXTERNAL_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("TIMED_EFFECTS")
        supported_kind.set_time("TIMED_GOALS")
        supported_kind.set_time("DURATION_INEQUALITIES")
        supported_kind.set_time("SELF_OVERLAPPING")
        supported_kind.set_expression_duration("STATIC_FLUENTS_IN_DURATIONS")
        supported_kind.set_expression_duration("FLUENTS_IN_DURATIONS")
        supported_kind.set_expression_duration("INT_TYPE_DURATIONS")
        supported_kind.set_expression_duration("REAL_TYPE_DURATIONS")
        supported_kind.set_numbers("BOUNDED_TYPES")
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
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_parameters("BOOL_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOOL_ACTION_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("UNBOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_parameters("REAL_ACTION_PARAMETERS")
        supported_kind.set_fluents_type("INT_FLUENTS")
        supported_kind.set_fluents_type("REAL_FLUENTS")
        supported_kind.set_fluents_type("OBJECT_FLUENTS")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_quality_metrics("FINAL_VALUE")
        supported_kind.set_quality_metrics("MAKESPAN")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        supported_kind.set_actions_cost_kind("STATIC_FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("INT_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("REAL_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_initial_state("UNDEFINED_INITIAL_NUMERIC")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= UndefinedInitialNumericRemover.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == CompilationKind.UNDEFINED_INITIAL_NUMERIC_REMOVING

    @staticmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: Optional[CompilationKind] = None
    ) -> ProblemKind:
        new_kind = problem_kind.clone()
        if new_kind.has_undefined_initial_numeric():
            new_kind.unset_initial_state("UNDEFINED_INITIAL_NUMERIC")
        return new_kind

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        """
        Compiles the given problem by removing undefined initial numeric fluents.

        This method takes a :class:`~unified_planning.model.Problem` and applies the
        ``UNDEFINED_INITIAL_NUMERIC_REMOVING`` compilation. The resulting problem
        ensures that all numeric fluents have a well-defined initial value and are
        properly handled through auxiliary boolean fluents.

        :param problem: The instance of the `Problem` that may contain numeric
            fluents with undefined initial values.
        :param compilation_kind: The `CompilationKind` that specifies the requested
            compilation. Only `UNDEFINED_INITIAL_NUMERIC_REMOVING` is supported.
        :return: The resulting `CompilerResult` data structure, where the `problem`
            field contains the compiled problem without undefined initial numeric
            fluents.

        Notes:
            The compilation introduces additional boolean fluents to track whether
            numeric fluents have been assigned a value, and augments action
            conditions and effects accordingly.
        """

        assert isinstance(problem, Problem)
        if not problem.kind.has_undefined_initial_numeric():
            return CompilerResult(problem, lambda ai: ai, self.name)

        new_problem = problem.clone()
        new_problem.name = f"{problem.name}_{self.name}"
        env = new_problem.environment

        undef_fluents = new_problem._fluents_with_undefined_values()
        default_initial_value = get_default_initial_values(new_problem, undef_fluents)
        is_value_defined_fluents = {}
        for fluent in undef_fluents:
            (v_exp,) = env.expression_manager.auto_promote(
                default_initial_value[fluent]
            )
            new_problem.fluents_defaults[fluent] = v_exp

            name = new_fluent_name(new_problem, f"is_value_defined_{fluent.name}")
            is_value_defined = Fluent(
                name, env.type_manager.BoolType(), _signature=fluent.signature
            )
            new_problem.add_fluent(is_value_defined, default_initial_value=False)
            is_value_defined_fluents[fluent] = is_value_defined

        for fluent_exp in dict(new_problem.explicit_initial_values):
            fluent = fluent_exp.fluent()
            if fluent in is_value_defined_fluents:
                is_value_defined = is_value_defined_fluents[fluent]
                new_problem.set_initial_value(is_value_defined(*fluent_exp.args), True)

        self._compile_actions(new_problem, is_value_defined_fluents)
        self._compile_goals(new_problem, is_value_defined_fluents)
        self._compile_timed_effects_and_timed_goals(
            new_problem, is_value_defined_fluents
        )
        self._compile_quality_metrics(new_problem, is_value_defined_fluents)

        new_to_old_action_map: Dict[Action, Optional[Action]] = {
            a: problem.action(a.name) for a in new_problem.actions
        }
        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old_action_map), self.name
        )

    def _compile_actions(
        self, problem: Problem, is_value_defined_fluents: Dict[Fluent, Fluent]
    ):
        for action in problem.actions:
            if isinstance(action, InstantaneousAction):
                expressions = (
                    list(action.preconditions)
                    + [eff.value for eff in action.effects]
                    + [
                        eff.fluent
                        for eff in action.effects
                        if eff.is_increase() or eff.is_decrease()
                    ]
                    + [eff.condition for eff in action.effects]
                )
                undef_fluent_exps = set()
                for exp in expressions:
                    for fluent_exp in self._fve.get(exp):
                        if fluent_exp.fluent() in is_value_defined_fluents:
                            undef_fluent_exps.add(fluent_exp)

                affected_undef_fluent_exps = set()
                for eff in action.effects:
                    if eff.fluent.fluent() in is_value_defined_fluents:
                        affected_undef_fluent_exps.add(eff.fluent)

                for fluent_exp in undef_fluent_exps:
                    action.add_precondition(
                        is_value_defined_fluents[fluent_exp.fluent()](*fluent_exp.args)
                    )

                for fluent_exp in affected_undef_fluent_exps:
                    if fluent_exp not in undef_fluent_exps:
                        action.add_effect(
                            is_value_defined_fluents[fluent_exp.fluent()](
                                *fluent_exp.args
                            ),
                            True,
                        )

            elif isinstance(action, DurativeAction):
                timing_to_expressions: Dict[Timing, List[FNode]] = defaultdict(list)
                for timeinterval, conditions in action.conditions.items():
                    timing_to_expressions[timeinterval.lower] += conditions

                affected_undef_fluent_exps_map: Dict[Timing, Set[FNode]] = defaultdict(
                    set
                )
                for timing, effects in action.effects.items():
                    timing_to_expressions[timing] += [eff.value for eff in effects]
                    timing_to_expressions[timing] += [
                        eff.fluent
                        for eff in effects
                        if eff.is_increase() or eff.is_decrease()
                    ]
                    timing_to_expressions[timing] += [eff.condition for eff in effects]
                    affected_undef_fluent_exps_map[timing].update(
                        eff.fluent
                        for eff in effects
                        if eff.fluent.fluent() in is_value_defined_fluents
                    )

                for fluent_exp in self._fve.get(action.duration.lower) | self._fve.get(
                    action.duration.upper
                ):
                    timing_to_expressions[StartTiming()].append(fluent_exp)

                timing_to_undef_fluent_exps: Dict[Timing, Set[FNode]] = defaultdict(set)
                for timing, expressions in timing_to_expressions.items():
                    for exp in expressions:
                        for fluent_exp in self._fve.get(exp):
                            if fluent_exp.fluent() in is_value_defined_fluents:
                                timing_to_undef_fluent_exps[timing].add(fluent_exp)

                    timeinterval = TimePointInterval(timing)
                    for fluent_exp in timing_to_undef_fluent_exps[timing]:
                        action.add_condition(
                            timeinterval,
                            is_value_defined_fluents[fluent_exp.fluent()](
                                *fluent_exp.args
                            ),
                        )

                for timing, fluent_exps in affected_undef_fluent_exps_map.items():
                    for fluent_exp in fluent_exps:
                        if fluent_exp not in timing_to_undef_fluent_exps.get(
                            timing, set()
                        ):
                            action.add_effect(
                                timing,
                                is_value_defined_fluents[fluent_exp.fluent()](
                                    *fluent_exp.args
                                ),
                                True,
                            )

    def _compile_goals(
        self, problem: Problem, is_value_defined_fluents: Dict[Fluent, Fluent]
    ):
        undef_fluent_exps = set()
        for exp in problem.goals:
            for fluent_exp in self._fve.get(exp):
                if fluent_exp.fluent() in is_value_defined_fluents:
                    undef_fluent_exps.add(fluent_exp)

        for fluent_exp in undef_fluent_exps:
            problem.add_goal(
                is_value_defined_fluents[fluent_exp.fluent()](*fluent_exp.args)
            )

    def _compile_timed_effects_and_timed_goals(
        self, problem: Problem, is_value_defined_fluents: Dict[Fluent, Fluent]
    ):
        timing_to_expressions: Dict[Timing, List[FNode]] = defaultdict(list)
        for timeinterval, goals in problem.timed_goals.items():
            timing_to_expressions[timeinterval.lower].extend(goals)

        affected_undef_fluent_exps: Dict[Timing, Set[FNode]] = defaultdict(set)
        for timing, effects in problem.timed_effects.items():
            for eff in effects:
                timing_to_expressions[timing].append(eff.value)
                timing_to_expressions[timing].append(eff.condition)
                if eff.is_increase() or eff.is_decrease():
                    timing_to_expressions[timing].append(eff.fluent)

                affected_undef_fluent_exps[timing].update(
                    eff.fluent
                    for eff in effects
                    if eff.fluent.fluent() in is_value_defined_fluents
                )

        timing_to_undef_fluent_exps: Dict[Timing, Set[FNode]] = defaultdict(set)
        for timing, expressions in timing_to_expressions.items():
            for exp in expressions:
                for fluent_exp in self._fve.get(exp):
                    if fluent_exp.fluent() in is_value_defined_fluents:
                        timing_to_undef_fluent_exps[timing].add(fluent_exp)

            timeinterval = TimePointInterval(timing)
            for fluent_exp in timing_to_undef_fluent_exps[timing]:
                problem.add_timed_goal(
                    timeinterval,
                    is_value_defined_fluents[fluent_exp.fluent()](*fluent_exp.args),
                )

        for timing, fluent_exps in affected_undef_fluent_exps.items():
            for fluent_exp in fluent_exps:
                if fluent_exp not in timing_to_undef_fluent_exps.get(timing, set()):
                    problem.add_timed_effect(
                        timing,
                        is_value_defined_fluents[fluent_exp.fluent()](*fluent_exp.args),
                        True,
                    )

    def _compile_quality_metrics(
        self, problem: Problem, is_value_defined_fluents: Dict[Fluent, Fluent]
    ):
        for metric in problem.quality_metrics:
            if metric.is_minimize_action_costs():
                assert isinstance(metric, MinimizeActionCosts)
                for action, cost_exp in metric.costs.items():
                    undef_fluent_exps = set()
                    for fluent_exp in self._fve.get(cost_exp):
                        if fluent_exp.fluent() in is_value_defined_fluents:
                            undef_fluent_exps.add(fluent_exp)

                    if isinstance(action, InstantaneousAction):
                        for fluent_exp in undef_fluent_exps:
                            action.add_precondition(
                                is_value_defined_fluents[fluent_exp.fluent()](
                                    *fluent_exp.args
                                )
                            )
                    elif isinstance(action, DurativeAction):
                        timeinterval = TimePointInterval(StartTiming())
                        for fluent_exp in undef_fluent_exps:
                            action.add_condition(
                                timeinterval,
                                is_value_defined_fluents[fluent_exp.fluent()](
                                    *fluent_exp.args
                                ),
                            )


def get_default_initial_values(
    problem: Problem, undef_fluents: List[Fluent]
) -> Dict[Fluent, Union[int, Fraction]]:
    undef_fluents_set = set(undef_fluents)
    default_initial_value = {}
    for action in problem.actions:
        if isinstance(action, InstantaneousAction):
            effects = action.effects
        elif isinstance(action, DurativeAction):
            effects = [e for effs in action.effects.values() for e in effs]

        for eff in effects:
            fluent = eff.fluent.fluent()
            if (
                fluent in undef_fluents_set
                and eff.is_assignment()
                and eff.value.is_constant()
            ):
                v = eff.value.constant_value()
                if fluent not in default_initial_value:
                    default_initial_value[fluent] = v
                else:
                    default_initial_value[fluent] = min(
                        default_initial_value[fluent], v
                    )

    for fluent in undef_fluents_set:
        assert (
            fluent.type.is_int_type() or fluent.type.is_real_type()
        ), f"Fluent '{fluent}' has type '{fluent.type}', expected int or real."

        if fluent not in default_initial_value:
            if fluent.type.is_int_type():
                default_initial_value[fluent] = 0
            elif fluent.type.is_real_type():
                default_initial_value[fluent] = Fraction(0)

    return default_initial_value


def new_fluent_name(problem: Problem, name: str) -> str:
    new_name = name
    i = 0
    while problem.has_fluent(new_name):
        new_name = f"{name}_{i}"
        i += 1
    return new_name
