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
"""This module defines the negative preconditions remover class."""

import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.results import CompilerResult
from unified_planning.model import (
    Fluent,
    Problem,
    InstantaneousAction,
    DurativeAction,
    FNode,
    Action,
    Effect,
    ProblemKind,
    Oversubscription,
    TemporalOversubscription,
)
from unified_planning.model.walkers import OperatorsExtractor
from unified_planning.model.operators import OperatorKind
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.model.walkers.identitydag import IdentityDagWalker
from unified_planning.engines.compilers.utils import (
    get_fresh_name,
    replace_action,
    updated_minimize_action_costs,
)
from unified_planning.exceptions import (
    UPExpressionDefinitionError,
    UPProblemDefinitionError,
)
from typing import List, Dict, Union, Optional
from functools import partial


class NegativeFluentRemover(IdentityDagWalker):
    def __init__(self, problem, environment):
        self._env = environment
        IdentityDagWalker.__init__(self, self._env)
        self._fluent_mapping: Dict[Fluent, Fluent] = {}
        self._problem = problem

    def remove_negative_fluents(self, expression: FNode) -> FNode:
        return self.walk(expression)

    def walk_not(self, expression: FNode, args: List[FNode], **kwargs) -> FNode:
        # TODO check if "complex" expressions are compiled correctly e.g.:(Not(Or(bx, And(bx, Not(by))))), XOr, ...

        # print ("in walk not, exp:")
        # print (expression)
        assert len(args) == 1
        if args[0].is_fluent_exp():
            neg_fluent = self._fluent_mapping.get(args[0].fluent(), None)
            if neg_fluent is not None:
                return self._env.expression_manager.FluentExp(
                    neg_fluent, tuple(args[0].args)
                )
            f = args[0].fluent()
            if f in self._fluent_mapping.keys():
                nf = self._fluent_mapping[f]
            elif f in self._fluent_mapping.values():
                for k, v in self._fluent_mapping.items():
                    if v == f:
                        nf = k
                        break
            else:
                # make a new one
                nf = Fluent(
                    get_fresh_name(self._problem, f"not_{f.name}"),
                    f.type,
                    f.signature,
                    f._env,
                )
            self._fluent_mapping[f] = nf
            return self._env.expression_manager.FluentExp(nf, tuple(args[0].args))
        elif args[0].is_equals():
            assert args[0].args[0].is_fluent_exp()
            type_here = args[0].args[0].fluent().type
            assert not type_here.is_bool_type()
            for a in args[0].args:
                assert a.fluent().type == type_here
            if type_here.is_user_type():
                exps = []
                for arg_1_obj in self._problem.objects(type_here):
                    for arg_2_obj in self._problem.objects(type_here):
                        if arg_1_obj == arg_2_obj:
                            continue
                        temp_exp = self._env.expression_manager.And(
                            self._env.expression_manager.Equals(
                                args[0].args[0], arg_1_obj
                            ),
                            self._env.expression_manager.Equals(
                                args[0].args[1], arg_2_obj
                            ),
                        )
                        exps.append(temp_exp)
                return self._env.expression_manager.Or(exps)
            else:
                exp_1 = self._env.expression_manager.GT(*args[0].args)
                exp_2 = self._env.expression_manager.LT(*args[0].args)
                return self._env.expression_manager.Or(exp_1, exp_2)
        elif args[0].is_le():
            return self._env.expression_manager.GT(*args[0].args)
        elif args[0].is_lt():
            return self._env.expression_manager.GE(*args[0].args)
        elif args[0].is_iff():
            exp_1 = self._env.expression_manager.Iff(
                args[0].args[0], self._env.expression_manager.Not(args[0].args[1])
            )
            exp_2 = self._env.expression_manager.Iff(
                args[0].args[1], self._env.expression_manager.Not(args[0].args[0])
            )
            return self._env.expression_manager.Or(exp_1, exp_2)
        elif args[0].is_and():
            exp_t = self._env.expression_manager.Or(
                self._env.expression_manager.Not(args[0].args[0]),
                self._env.expression_manager.Not(args[0].args[1]),
            )
            return exp_t
        elif args[0].is_or():
            exp_t = self._env.expression_manager.And(
                self._env.expression_manager.Not(args[0].args[0]),
                self._env.expression_manager.Not(args[0].args[1]),
            )
            return exp_t
        else:
            raise UPExpressionDefinitionError(
                f"Expression: {expression} is not supported."
            )

    @property
    def fluent_mapping(self) -> Dict[Fluent, Fluent]:
        return self._fluent_mapping


class NegativeConditionsRemover(engines.engine.Engine, CompilerMixin):
    """
    Negative conditions remover class: this class offers the capability
    to transform a :class:`~unified_planning.model.Problem` with `negative conditions` into one without `negative conditions`.
    Negative conditions means that the `Not` operand appears in the `Problem`'s goal or
    :class:`Actions <unified_planning.model.Action>` `conditions <unified_planning.model.InstantaneousAction.preconditions>`.

    This is done by substituting every :class:`Fluent <unified_planning.model.Fluent>` that appears with a `Not` into the `conditions`
    with a different `Fluent` representing  his `negation`.
    Then, to every `Action` that modifies the original `Fluent`, is added an :class:`Effect <unified_planning.model.Effect>` that
    modifies the `negation Fluent` with the `negation` of the :func:`value <unified_planning.model.Effect.value>` given to `Fluent`.
    So, in every moment, the `negation Fluent` has the `inverse value` of the `original Fluent`.

    This `Compiler` supports only the the `NEGATIVE_CONDITIONS_REMOVING` :class:`~unified_planning.engines.CompilationKind`.
    """

    def __init__(self):
        engines.engine.Engine.__init__(self)
        CompilerMixin.__init__(self, CompilationKind.NEGATIVE_CONDITIONS_REMOVING)

    @property
    def name(self):
        return "ncrm"

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
        supported_kind.set_numbers("BOUNDED_TYPES")
        supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
        supported_kind.set_fluents_type("INT_FLUENTS")
        supported_kind.set_fluents_type("REAL_FLUENTS")
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
        supported_kind.set_effects_kind("STATIC_FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_BOOLEAN_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_NUMERIC_ASSIGNMENTS")
        supported_kind.set_effects_kind("FLUENTS_IN_OBJECT_ASSIGNMENTS")
        supported_kind.set_effects_kind("FORALL_EFFECTS")
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
        supported_kind.set_constraints_kind("STATE_INVARIANTS")
        supported_kind.set_constraints_kind("TRAJECTORY_CONSTRAINTS")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_actions_cost_kind("STATIC_FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("FLUENTS_IN_ACTIONS_COST")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("TEMPORAL_OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("MAKESPAN")
        supported_kind.set_quality_metrics("FINAL_VALUE")
        supported_kind.set_actions_cost_kind("INT_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_actions_cost_kind("REAL_NUMBERS_IN_ACTIONS_COST")
        supported_kind.set_oversubscription_kind("INT_NUMBERS_IN_OVERSUBSCRIPTION")
        supported_kind.set_oversubscription_kind("REAL_NUMBERS_IN_OVERSUBSCRIPTION")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= NegativeConditionsRemover.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == CompilationKind.NEGATIVE_CONDITIONS_REMOVING

    @staticmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: Optional[CompilationKind] = None
    ) -> ProblemKind:
        new_kind = problem_kind.clone()
        new_kind.unset_conditions_kind("NEGATIVE_CONDITIONS")
        return new_kind

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        """
        Takes an instance of a :class:`~unified_planning.model.Problem` and the `NEGATIVE_CONDITIONS_REMOVING` `CompilationKind`
        and returns a `CompilerResult` where the `Problem` does not have the `Not` operator as a `condition` or in the `goals`.

        :param problem: The instance of the `Problem` to compile.
        :param compilation_kind: The `CompilationKind` that must be applied on the given `problem`;
            only `NEGATIVE_CONDITIONS_REMOVING` is supported by this compiler
        :return: The resulting `CompilerResult`.
        """
        assert isinstance(problem, Problem)

        env = problem.environment
        simplifier = env.simplifier

        fluent_remover = NegativeFluentRemover(problem, env)

        op_extractor = OperatorsExtractor()

        new_to_old: Dict[Action, Optional[Action]] = {}

        new_problem = Problem(f"{self.name}_{problem.name}", env)
        for o in problem.all_objects:
            new_problem.add_object(o)

        name_action_map: Dict[str, Union[InstantaneousAction, DurativeAction]] = {}
        for action in problem.actions:
            if isinstance(action, InstantaneousAction):
                new_action = action.clone()
                new_action.name = get_fresh_name(new_problem, action.name)
                new_action.clear_preconditions()
                for p in action.preconditions:
                    np = p
                    while OperatorKind.NOT in op_extractor.get(np):
                        np = fluent_remover.remove_negative_fluents(np)
                    new_action.add_precondition(np)
                for ce in new_action.conditional_effects:
                    nc = ce.condition
                    while OperatorKind.NOT in op_extractor.get(nc):
                        nc = fluent_remover.remove_negative_fluents(nc)
                    ce.set_condition(nc)
                name_action_map[action.name] = new_action
            elif isinstance(action, DurativeAction):
                new_durative_action = action.clone()
                new_durative_action.name = get_fresh_name(new_problem, action.name)
                new_durative_action.clear_conditions()
                for i, cl in action.conditions.items():
                    for c in cl:
                        nc = c
                        while OperatorKind.NOT in op_extractor.get(nc):
                            nc = fluent_remover.remove_negative_fluents(nc)
                        new_durative_action.add_condition(i, nc)
                for t, cel in new_durative_action.conditional_effects.items():
                    for ce in cel:
                        nc = ce.condition
                        while OperatorKind.NOT in op_extractor.get(nc):
                            nc = fluent_remover.remove_negative_fluents(nc)
                        ce.set_condition(nc)
                name_action_map[action.name] = new_durative_action
            else:
                raise NotImplementedError

        for t, el in problem.timed_effects.items():
            for e in el:
                new_problem._add_effect_instance(t, e.clone())

        for t, el in new_problem.timed_effects.items():
            for e in el:
                if e.is_conditional():

                    nc = e.condition
                    while OperatorKind.NOT in op_extractor.get(nc):
                        nc = fluent_remover.remove_negative_fluents(nc)
                    e.set_condition(nc)

        for i, gl in problem.timed_goals.items():
            for g in gl:
                ng = g
                while OperatorKind.NOT in op_extractor.get(ng):
                    ng = fluent_remover.remove_negative_fluents(ng)
                new_problem.add_timed_goal(i, ng)

        for g in problem.goals:
            ng = g
            while OperatorKind.NOT in op_extractor.get(ng):
                ng = fluent_remover.remove_negative_fluents(ng)
            new_problem.add_goal(ng)

        for tc in problem.trajectory_constraints:

            ntc = tc
            while OperatorKind.NOT in op_extractor.get(ntc):
                ntc = fluent_remover.remove_negative_fluents(ntc)
            new_problem.add_trajectory_constraint(ntc)

        for qm in problem.quality_metrics:
            if qm.is_minimize_action_costs():
                new_problem.add_quality_metric(
                    updated_minimize_action_costs(
                        qm, new_to_old, new_problem.environment
                    )
                )
            elif qm.is_oversubscription():
                assert isinstance(qm, Oversubscription)
                os_dict = {}
                for g, v in qm.goals.items():
                    ng = g
                    while OperatorKind.NOT in op_extractor.get(ng):
                        ng = fluent_remover.remove_negative_fluents(ng)
                    os_dict[ng] = v
                new_problem.add_quality_metric(
                    Oversubscription(
                        os_dict,
                        environment=new_problem.environment,
                    )
                )
            elif qm.is_temporal_oversubscription():
                assert isinstance(qm, TemporalOversubscription)
                os_dict = {}
                for (t, g), v in qm.goals.items():
                    ng = g
                    while OperatorKind.NOT in op_extractor.get(ng):
                        ng = fluent_remover.remove_negative_fluents(ng)
                    os_dict[(t, ng)] = v
                new_problem.add_quality_metric(
                    TemporalOversubscription(
                        os_dict,
                        environment=new_problem.environment,
                    )
                )
            else:
                new_problem.add_quality_metric(qm)

        # fluent_mapping is the map between a fluent and it's negation, when the
        # negation is None it means the fluent is never found in a negation into
        # every condititon analized before; therefore it does not need to exist.
        fluent_mapping = fluent_remover.fluent_mapping
        for f in problem.fluents:
            new_problem.add_fluent(f)
            fneg = fluent_mapping.get(f, None)
            if fneg is not None:
                new_problem.add_fluent(fneg)

        for fl, v in problem.initial_values.items():
            fneg = fluent_mapping.get(fl.fluent(), None)
            new_problem.set_initial_value(fl, v)
            if fneg is not None:
                if v.bool_constant_value():
                    new_problem.set_initial_value(
                        env.expression_manager.FluentExp(fneg, tuple(fl.args)),
                        env.expression_manager.FALSE(),
                    )
                else:
                    new_problem.set_initial_value(
                        env.expression_manager.FluentExp(fneg, tuple(fl.args)),
                        env.expression_manager.TRUE(),
                    )

        for action in problem.actions:
            if isinstance(action, InstantaneousAction):
                new_action = name_action_map[action.name]
                new_effects: List[Effect] = []
                for e in new_action.effects:
                    fl, v = e.fluent, e.value
                    fneg = fluent_mapping.get(fl.fluent(), None)
                    if fneg is not None:
                        simplified_not_v = simplifier.simplify(
                            env.expression_manager.Not(v)
                        )
                        new_effects.append(
                            Effect(
                                env.expression_manager.FluentExp(fneg, tuple(fl.args)),
                                simplified_not_v,
                                e.condition,
                                e.kind,
                                e.forall,
                            )
                        )
                for ne in new_effects:
                    new_action._add_effect_instance(ne)
                new_problem.add_action(new_action)
                new_to_old[new_action] = action
            elif isinstance(action, DurativeAction):
                new_durative_action = name_action_map[action.name]
                new_durative_action.set_duration_constraint(action.duration)

                for t, el in new_durative_action.effects.items():
                    for e in el:
                        fl, v = e.fluent, e.value
                        fneg = fluent_mapping.get(fl.fluent(), None)
                        if fneg is not None:
                            simplified_not_v = simplifier.simplify(
                                env.expression_manager.Not(v)
                            )
                            new_durative_action._add_effect_instance(
                                t,
                                Effect(
                                    env.expression_manager.FluentExp(
                                        fneg, tuple(fl.args)
                                    ),
                                    simplified_not_v,
                                    e.condition,
                                    e.kind,
                                    e.forall,
                                ),
                            )
                new_problem.add_action(new_durative_action)
                new_to_old[new_durative_action] = action
            else:
                raise NotImplementedError

        for t, el in new_problem.timed_effects.items():
            for e in el:
                fl, v = e.fluent, e.value
                fneg = fluent_mapping.get(fl.fluent(), None)
                if fneg is not None:
                    simplified_not_v = simplifier.simplify(
                        env.expression_manager.Not(v)
                    )
                    new_problem._add_effect_instance(
                        t,
                        Effect(
                            env.expression_manager.FluentExp(fneg, tuple(fl.args)),
                            simplified_not_v,
                            e.condition,
                            e.kind,
                            e.forall,
                        ),
                    )

        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old), self.name
        )
