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


from itertools import product
import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.exceptions import (
    UPProblemDefinitionError,
    UPConflictingEffectsException,
)
from unified_planning.model import (
    Problem,
    ProblemKind,
    Fluent,
    Parameter,
    Action,
    InstantaneousAction,
    DurativeAction,
    Effect,
    FNode,
    ExpressionManager,
    MinimizeActionCosts,
    MinimizeSequentialPlanLength,
    MinimizeMakespan,
    MinimizeExpressionOnFinalState,
    MaximizeExpressionOnFinalState,
    Oversubscription,
    Object,
    Variable,
    Expression,
)
from unified_planning.model.walkers import UsertypeFluentsWalker, Substituter
from unified_planning.model.types import _UserType
from unified_planning.engines.compilers.utils import (
    get_fresh_name,
    check_and_simplify_preconditions,
    check_and_simplify_conditions,
    replace_action,
)
from unified_planning.utils import powerset
from typing import Iterator, List, Dict, Tuple, Optional, cast
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
        tm = env.type_manager
        em = env.expression_manager
        substituter = Substituter(env)

        new_to_old: Dict[Action, Action] = {}
        old_to_new: Dict[Action, Action] = {}

        new_problem = problem.clone()
        new_problem.name = f"{self.name}_{problem.name}"
        fluents_map: Dict[Fluent, Fluent] = {}
        new_problem.clear_fluents()
        for fluent in problem.fluents:
            assert isinstance(fluent, Fluent)
            if fluent.type.is_user_type():
                new_signature = fluent.signature[:]
                base_name = str(cast(_UserType, fluent.type).name).lower()
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

        used_names = problem.get_contained_names()
        utf_remover = UsertypeFluentsWalker(fluents_map, used_names, env)

        new_problem.clear_actions()
        for old_action in problem.actions:
            new_action = new_problem.action(old_action.name)
            if isinstance(new_action, InstantaneousAction):
                assert isinstance(old_action, InstantaneousAction)
                new_action.clear_preconditions()
                for p in old_action.preconditions:
                    new_action.add_precondition(
                        self._convert_to_value(p, em, utf_remover)
                    )
                new_action.clear_effects()
                for e in old_action.effects:
                    for ne in self._convert_effect(
                        e, problem, fluents_map, substituter, em, utf_remover
                    ):
                        new_action._add_effect_instance(ne)
                if new_action.simulated_effect is not None:
                    raise NotImplementedError
            elif isinstance(old_action, DurativeAction):
                assert isinstance(new_action, DurativeAction)
                new_action.clear_conditions()
                for i, cl in old_action.conditions.items():
                    for c in cl:
                        new_action.add_condition(
                            i, self._convert_to_value(c, em, utf_remover)
                        )
                new_action.clear_effects()
                for t, el in old_action.effects.items():
                    for e in el:
                        for ne in self._convert_effect(
                            e, problem, fluents_map, substituter, em, utf_remover
                        ):
                            new_action._add_effect_instance(t, ne)
                if new_action.simulated_effects:
                    raise NotImplementedError
            else:
                raise NotImplementedError  # Sensing Actions might be easy to implement
            new_to_old[new_action] = old_action
            old_to_new[old_action] = new_action

        new_problem.clear_timed_effects()
        for t, el in problem.timed_effects.items():
            for e in el:
                for ne in self._convert_effect(
                    e, problem, fluents_map, substituter, em, utf_remover
                ):
                    new_problem._add_effect_instance(t, ne)

        new_problem.clear_timed_goals()
        for i, cl in problem.timed_goals.items():
            for c in cl:
                new_problem.add_timed_goal(
                    i, self._convert_to_value(c, em, utf_remover)
                )

        new_problem.clear_quality_metrics()
        for qm in problem.quality_metrics:

            if isinstance(qm, MinimizeSequentialPlanLength) or isinstance(
                qm, MinimizeMakespan
            ):
                new_problem.add_quality_metric(qm)
            elif isinstance(qm, MinimizeExpressionOnFinalState):
                new_problem.add_quality_metric(
                    MinimizeExpressionOnFinalState(
                        self._convert_to_value(qm.expression, em, utf_remover)
                    )
                )
            elif isinstance(qm, MaximizeExpressionOnFinalState):
                new_problem.add_quality_metric(
                    MaximizeExpressionOnFinalState(
                        self._convert_to_value(qm.expression, em, utf_remover)
                    )
                )
            elif isinstance(qm, MinimizeActionCosts):
                new_costs = {}
                for a in problem.actions:
                    cost = qm.get_action_cost(a)
                    if cost is not None:
                        cost = self._convert_to_value(cost, em, utf_remover)
                    new_costs[old_to_new[a]] = cost
                new_problem.add_quality_metric(MinimizeActionCosts(new_costs))
            elif isinstance(qm, Oversubscription):
                new_goals = {
                    self._convert_to_value(g, em, utf_remover): v
                    for g, v in qm.goals.items()
                }
                new_problem.add_quality_metric(Oversubscription(new_goals))
            else:
                raise NotImplementedError

        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old), self.name
        )

    def _convert_to_value(
        self,
        expression: FNode,
        em: ExpressionManager,
        utf_remover: UsertypeFluentsWalker,
    ) -> FNode:
        new_exp, free_vars, added_fluents = utf_remover.remove_usertype_fluents(
            expression
        )
        if free_vars:
            assert added_fluents
            new_exp = em.Exists(em.And(new_exp, *added_fluents), *free_vars)
        else:
            assert not added_fluents
        return new_exp.simplify()

    def _convert_effect(
        self,
        effect: Effect,
        problem: Problem,
        fluents_map: Dict[Fluent, Fluent],
        substituter: Substituter,
        em: ExpressionManager,
        utf_remover: UsertypeFluentsWalker,
    ) -> Iterator[Effect]:
        (
            new_fluent,
            fluent_free_vars,
            fluent_added_fluents,
        ) = utf_remover.remove_usertype_fluents(effect.fluent)
        (
            new_value,
            value_free_vars,
            value_added_fluents,
        ) = utf_remover.remove_usertype_fluents(effect.value)
        if new_fluent.is_variable_exp():  # this effect's fluent is a user_type fluent
            assert effect.fluent.fluent() in fluents_map
            assert (
                not value_free_vars and not value_added_fluents
            ), "Error, this value type should be a UserType"
            fluent_var = new_fluent.variable()
            for f in fluent_added_fluents:
                assert f.is_fluent_exp()
                if f.arg(-1).variable() == fluent_var:
                    new_fluent = f
                    break
            fluent_added_fluents.remove(new_fluent)
            new_value = em.Equals(new_value, fluent_var)
        new_condition = em.And(
            self._convert_to_value(effect.condition, em, utf_remover),
            *fluent_added_fluents,
        )
        vars_list = list(fluent_free_vars)
        vars_list.extend(value_free_vars)
        for objects in product(*(problem.objects(v.type) for v in vars_list)):
            assert len(objects) == len(vars_list)
            objects = cast(Tuple[Object, ...], objects)
            subs: Dict[Expression, Expression] = dict(zip(vars_list, objects))
            subbed_cond = substituter.substitute(new_condition, subs).simplify()
            if not subbed_cond.is_constant() or subbed_cond.bool_constant_value():
                yield Effect(
                    substituter.substitute(new_fluent, subs).simplify(),
                    substituter.substitute(new_value, subs).simplify(),
                    subbed_cond,
                    effect.kind,
                )
