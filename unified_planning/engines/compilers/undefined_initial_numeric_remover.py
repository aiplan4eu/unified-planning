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
"""This module defines the UndefinedInitialNumericRemover class."""


import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.model import (
    Problem,
    ProblemKind,
    Fluent,
    InstantaneousAction,
    DurativeAction,
    FNode,
    OperatorKind,
    TimePointInterval,
)
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.engines.compilers.utils import replace_action
from typing import Optional, Iterable
from functools import partial
from collections import defaultdict


class UndefinedInitialNumericRemover(engines.engine.Engine, CompilerMixin):
    # TODO: doc

    def __init__(self):
        engines.engine.Engine.__init__(self)
        CompilerMixin.__init__(self, CompilationKind.UNDEFINED_INITIAL_NUMERIC_REMOVING)

    @property
    def name(self):
        return "undefined_initial_numeric_remover"

    @staticmethod
    def supported_kind() -> ProblemKind:
        # TODO
        supported_kind = ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_time("CONTINUOUS_TIME")
        supported_kind.set_time("INTERMEDIATE_CONDITIONS_AND_EFFECTS")
        supported_kind.set_time("DURATION_INEQUALITIES")
        supported_kind.set_expression_duration("STATIC_FLUENTS_IN_DURATIONS")
        supported_kind.set_expression_duration("FLUENTS_IN_DURATIONS")
        supported_kind.set_expression_duration("INT_TYPE_DURATIONS")
        supported_kind.set_numbers("DISCRETE_NUMBERS")
        supported_kind.set_numbers("CONTINUOUS_NUMBERS")
        supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_parameters("BOOL_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOOL_ACTION_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_ACTION_PARAMETERS")
        supported_kind.set_effects_kind("INCREASE_EFFECTS")
        supported_kind.set_effects_kind("DECREASE_EFFECTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_conditions_kind("NEGATIVE_CONDITIONS")
        supported_kind.set_conditions_kind("DISJUNCTIVE_CONDITIONS")
        supported_kind.set_conditions_kind("EQUALITIES")
        supported_kind.set_fluents_type("NUMERIC_FLUENTS")
        supported_kind.set_fluents_type("OBJECT_FLUENTS")
        supported_kind.set_fluents_type("INT_FLUENTS")
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
        # TODO: doc

        assert isinstance(problem, Problem)
        if not problem.kind.has_undefined_initial_numeric():
            return CompilerResult(problem, lambda ai: ai, self.name)

        new_problem = problem.clone()
        new_problem.name = f"{problem.name}_{self.name}"
        env = new_problem.environment

        undef_fluents = new_problem._fluents_with_undefined_values()
        is_value_defined_fluents = {}
        for fluent in undef_fluents:
            if fluent.type.is_int_type():
                default_initial_value = 0
            elif fluent.type.is_real_type():
                default_initial_value = 0.0
            else:
                raise Exception(
                    f"Fluent '{fluent}' has type '{fluent.type}', expected int or real."
                )
            (v_exp,) = env.expression_manager.auto_promote(default_initial_value)
            new_problem.fluents_defaults[fluent] = v_exp

            name = new_fluent_name(new_problem, f"is_value_defined_{fluent.name}")
            is_value_defined = Fluent(
                name, env.type_manager.BoolType(), _signature=fluent.signature
            )
            new_problem.add_fluent(is_value_defined, default_initial_value=False)
            is_value_defined_fluents[fluent] = is_value_defined

        for fluent_exp in dict(new_problem.explicit_initial_values):
            if fluent_exp.fluent() in is_value_defined_fluents:
                new_problem.set_initial_value(
                    is_value_defined_fluents[fluent_exp.fluent()](*fluent_exp.args),
                    True,
                )

        for action in new_problem.actions:
            if isinstance(action, InstantaneousAction):
                undef_fluent_exps = set()
                for exp in (
                    list(action.preconditions)
                    + [eff.value for eff in action.effects]
                    + [eff.condition for eff in action.effects]
                ):
                    for fluent_exp in get_fluents_from_expression(exp):
                        if fluent_exp.fluent() in is_value_defined_fluents:
                            undef_fluent_exps.add(fluent_exp)

                for fluent_exp in undef_fluent_exps:
                    action.add_precondition(
                        is_value_defined_fluents[fluent_exp.fluent()](*fluent_exp.args)
                    )

            elif isinstance(action, DurativeAction):
                expressions = defaultdict(list)
                for timeinterval, conditions in action.conditions.items():
                    expressions[timeinterval] += conditions

                for timing, effects in action.effects:
                    timeinterval = TimePointInterval(timing)
                    expressions[timeinterval] += [eff.value for eff in effects]
                    expressions[timeinterval] += [eff.condition for eff in effects]

                for timeinterval, exps in expressions.items():
                    undef_fluent_exps = set()
                    for exp in exps:
                        for fluent_exp in get_fluents_from_expression(exp):
                            if fluent_exp.fluent() in is_value_defined_fluents:
                                undef_fluent_exps.add(fluent_exp)

                    for fluent_exp in undef_fluent_exps:
                        action.add_condition(
                            timeinterval,
                            is_value_defined_fluents[fluent_exp.fluent()](
                                *fluent_exp.args
                            ),
                        )

        new_to_old_action_map = {a: problem.action(a.name) for a in new_problem.actions}
        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old_action_map), self.name
        )


def new_fluent_name(problem: Problem, name: str) -> str:
    new_name = name
    i = 0
    while problem.has_fluent(new_name):
        new_name = f"{name}_{i}"
        i += 1
    return new_name


def get_fluents_from_expression(expression: FNode) -> Iterable[FNode]:
    stack = [expression]
    while len(stack) > 0:
        exp = stack.pop()

        if exp.node_type in {
            OperatorKind.BOOL_CONSTANT,
            OperatorKind.INT_CONSTANT,
            OperatorKind.REAL_CONSTANT,
            OperatorKind.DOT,
            OperatorKind.PARAM_EXP,
            OperatorKind.VARIABLE_EXP,
            OperatorKind.OBJECT_EXP,
            OperatorKind.TIMING_EXP,
            OperatorKind.PRESENT_EXP,
        }:
            pass

        elif exp.node_type == OperatorKind.FLUENT_EXP:
            yield exp

        elif exp.node_type in {
            OperatorKind.AND,
            OperatorKind.OR,
            OperatorKind.NOT,
            OperatorKind.IMPLIES,
            OperatorKind.IFF,
            OperatorKind.PLUS,
            OperatorKind.MINUS,
            OperatorKind.TIMES,
            OperatorKind.DIV,
            OperatorKind.LE,
            OperatorKind.LT,
            OperatorKind.EQUALS,
        }:
            stack.extend(exp.args)

        elif exp.node_type in {
            OperatorKind.EXISTS,
            OperatorKind.FORALL,
            OperatorKind.ALWAYS,
            OperatorKind.SOMETIME,
            OperatorKind.SOMETIME_BEFORE,
            OperatorKind.SOMETIME_AFTER,
            OperatorKind.AT_MOST_ONCE,
        }:
            # TODO
            pass
