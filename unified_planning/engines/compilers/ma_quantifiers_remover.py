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
"""This module defines the quantifiers remover class."""


from itertools import product
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
    TemporalOversubscription,
    Object,
    Variable,
    Expression,
    Effect,
)
from unified_planning.model.walkers import ExpressionQuantifiersRemover
from unified_planning.engines.compilers.utils import (
    get_fresh_name,
    replace_action,
    updated_minimize_action_costs,
)
from unified_planning.engines.compilers.quantifiers_remover import (
    QuantifiersRemover,
)
from unified_planning.model.multi_agent.ma_problem import MultiAgentProblem
from typing import Dict, List, Optional, Tuple
from functools import partial
import copy

class MAQuantifiersRemover(engines.engine.Engine, CompilerMixin):
    """
    Quantifiers remover class: this class offers the capability
    to transform a problem with quantifiers into a problem without.
    Every quantifier is compiled away by it's respective logic formula
    instantiated on object.

    For example the formula:
        ``Forall (s-sempahore) is_green(s)``

    in a problem with 3 objects of type ``semaphores {s1, s2, s3}`` is compiled in:
        ``And(is_green(s1), is_green(s2), is_green(s3))``

    While the respective formula on the same problem:
        ``Exists (s-semaphore) is_green(s)``

    becomes:
        ``Or(is_green(s1), is_green(s2), is_green(s3))``
    """

    def __init__(self):
        engines.engine.Engine.__init__(self)
        CompilerMixin.__init__(self, CompilationKind.QUANTIFIERS_REMOVING)

    @property
    def name(self):
        return "ma_qurm"

    @staticmethod
    def supported_kind() -> ProblemKind:
        supported_kind = QuantifiersRemover.supported_kind()
        supported_kind.unset_problem_class("ACTION_BASED")
        supported_kind.set_problem_class("ACTION_BASED_MULTI_AGENT")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= MAQuantifiersRemover.supported_kind()

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
        new_kind.unset_effects_kind("FORALL_EFFECTS")
        if problem_kind.has_existential_conditions():
            new_kind.set_conditions("DISJUNCTIVE_CONDITIONS")
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
        assert isinstance(problem, MultiAgentProblem)

        expression_quantifier_remover = ExpressionQuantifiersRemover(
            problem.environment
        )
        new_to_old: Dict[Action, Action] = {}
        new_problem = problem.clone()
        new_problem.name = f"{self.name}_{problem.name}"
        new_problem.clear_goals()
        for ag in problem.agents:
            new_problem.agent(ag.name).clear_actions()
            new_ag = new_problem.agent(ag.name)
            for a in ag.actions:
                if isinstance(a, InstantaneousAction):
                    original_action = InstantaneousAction(a.name)
                    for p in a.preconditions:
                        original_action.add_precondition(p)
                    for effect in a.effects:
                        original_action.add_effect(effect.fluent, effect.value, effect.condition, effect.forall)
                    #original_action = ag.action(a.name)
                    assert isinstance(original_action, InstantaneousAction)
                    a.clear_preconditions()
                    for p in original_action.preconditions:
                        a.add_precondition(
                            expression_quantifier_remover.remove_quantifiers(p, problem)
                        )
                    original_effects = original_action.effects
                    a.clear_effects()
                    for effect in original_effects:
                        for e in effect.expand_effect(new_ag):
                            if e.is_conditional():
                                e.set_condition(
                                    expression_quantifier_remover.remove_quantifiers(
                                        e.condition, problem
                                    ).simplify()
                                )
                            e.set_value(
                                expression_quantifier_remover.remove_quantifiers(
                                    e.value, problem
                                )
                            )
                            if not e.condition.is_false():
                                a._add_effect_instance(e)
                    new_to_old[a] = original_action
                    new_ag.add_action(a)
            new_problem.add_agent(new_ag)
        for g in problem.goals:
            ng = expression_quantifier_remover.remove_quantifiers(g, problem)
            new_problem.add_goal(ng)

        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old), self.name
        )


"""elif isinstance(a, DurativeAction):
    original_action = ag.action(a.name)
    assert isinstance(original_action, DurativeAction)
    a.clear_conditions()
    for i, cl in original_action.conditions.items():
        for c in cl:
            a.add_condition(
                i,
                expression_quantifier_remover.remove_quantifiers(
                    c, problem
                ),
            )
    original_durative_effects = a.effects
    a.clear_effects()
    for t, el in original_durative_effects.items():
        for effect in el:
            for e in effect.expand_effect(new_problem):
                if e.is_conditional():
                    e.set_condition(
                        expression_quantifier_remover.remove_quantifiers(
                            e.condition, problem
                        ).simplify()
                    )
                e.set_value(
                    expression_quantifier_remover.remove_quantifiers(
                        e.value, problem
                    )
                )
                if not e.condition.is_false():
                    a._add_effect_instance(t, e)
    new_to_old[a] = original_action
else:
    raise NotImplementedError"""