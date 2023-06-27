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
"""This module defines the dnf remover class."""


import unified_planning as up
import unified_planning.engines as engines
from unified_planning.engines.mixins.compiler import CompilationKind, CompilerMixin
from unified_planning.engines.compilers.utils import (
    get_fresh_name,
    replace_action,
    updated_minimize_action_costs,
)
from unified_planning.engines.results import CompilerResult
from unified_planning.model import (
    AbstractProblem,
    FNode,
    Problem,
    BoolExpression,
    NumericConstant,
    InstantaneousAction,
    DurativeAction,
    TimeInterval,
    Timing,
    Action,
    ProblemKind,
    Oversubscription,
    TemporalOversubscription,
)
from unified_planning.model.walkers import Dnf
from typing import Iterator, List, Optional, Tuple, Dict, cast
from itertools import product
from functools import partial


class DisjunctiveConditionsRemover(engines.engine.Engine, CompilerMixin):
    """
    DisjunctiveConditions remover class: this class offers the capability
    to transform a :class:`~unified_planning.model.Problem` with `DisjunctiveConditions` into a semantically equivalent `Problem`
    where the :class:`Actions <unified_planning.model.Action>` `conditions <unified_planning.model.InstantaneousAction.preconditions>` don't contain the `Or` operand.

    This is done by taking all the `Actions conditions` that are not in the `DNF` form (an `OR` of `ANDs`) and calculate the equivalent `DNF`.
    Then, the resulting `OR` is decomposed into multiple `subActions`; every `subAction` has the same :func:`Effects <unified_planning.model.InstantaneousAction.effects>`
    of the original `Action`, and as condition an element of the decomposed `Or`. So, for every element of the `Or`, an `Action` is created.

    For this `Compiler`, only the `DISJUNCTIVE_CONDITIONS_REMOVING` :class:`~unified_planning.engines.CompilationKind` is supported.
    """

    def __init__(self):
        engines.engine.Engine.__init__(self)
        CompilerMixin.__init__(self, CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING)

    @property
    def name(self):
        return "dcrm"

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
        return problem_kind <= DisjunctiveConditionsRemover.supported_kind()

    @staticmethod
    def supports_compilation(compilation_kind: CompilationKind) -> bool:
        return compilation_kind == CompilationKind.DISJUNCTIVE_CONDITIONS_REMOVING

    @staticmethod
    def resulting_problem_kind(
        problem_kind: ProblemKind, compilation_kind: Optional[CompilationKind] = None
    ) -> ProblemKind:
        new_kind = ProblemKind(problem_kind.features)
        new_kind.unset_conditions_kind("DISJUNCTIVE_CONDITIONS")
        return new_kind

    def _compile(
        self,
        problem: "up.model.AbstractProblem",
        compilation_kind: "up.engines.CompilationKind",
    ) -> CompilerResult:
        """
        Takes an instance of a :class:`~unified_planning.model.Problem` and the `DISJUNCTIVE_CONDITIONS_REMOVING` `~unified_planning.engines.CompilationKind`
        and returns a `CompilerResult` where the `Problem` does not have `Actions` with disjunctive conditions.

        :param problem: The instance of the `Problem` that must be returned without disjunctive conditions.
        :param compilation_kind: The `CompilationKind` that must be applied on the given problem;
            only `DISJUNCTIVE_CONDITIONS_REMOVING` is supported by this compiler
        :return: The resulting `CompilerResult` data structure.
        """
        assert isinstance(problem, Problem)

        env = problem.environment

        new_to_old: Dict[Action, Optional[Action]] = {}
        new_fluents: List["up.model.Fluent"] = []

        new_problem = problem.clone()
        new_problem.name = f"{self.name}_{problem.name}"
        new_problem.clear_actions()
        new_problem.clear_goals()
        new_problem.clear_timed_goals()
        new_problem.clear_quality_metrics()

        dnf = Dnf(env)
        for a in problem.actions:
            for na in self._create_non_disjunctive_actions(a, new_problem, dnf):
                new_to_old[na] = a
                new_problem.add_action(na)

        # Meaningful action is the list of the actions that modify fluents; those actions are not
        # added just to remove the disjunction from goals
        meaningful_actions: List["up.model.Action"] = new_problem.actions[:]

        goal_to_add = self._goals_without_disjunctions_adding_new_elements(
            dnf,
            new_problem,
            new_to_old,
            new_fluents,
            problem.goals,
        )
        new_problem.add_goal(goal_to_add)

        for t, gl in problem.timed_goals.items():
            goal_to_add = self._goals_without_disjunctions_adding_new_elements(
                dnf,
                new_problem,
                new_to_old,
                new_fluents,
                gl,
                t,
            )
            new_problem.add_timed_goal(t, goal_to_add)

        # Every meaningful action must set to False every new fluent added.
        # For the DurativeActions this must happen every time the action modifies something
        em = env.expression_manager
        # new_effects is the List of effects that must be added to every meaningful action
        new_effects: List["up.model.Effect"] = [
            up.model.Effect(em.FluentExp(f), em.FALSE(), em.TRUE()) for f in new_fluents
        ]
        for a in meaningful_actions:
            # Since we modify the action that is a key in the Dict, we must update the mapping
            old_action = new_to_old.pop(a)
            if isinstance(a, InstantaneousAction):
                for e in new_effects:
                    a._add_effect_instance(e)
            elif isinstance(a, DurativeAction):
                for tim in a.effects:
                    for e in new_effects:
                        a._add_effect_instance(tim, e)
            else:
                raise NotImplementedError
            new_to_old[a] = old_action

        for qm in problem.quality_metrics:
            if qm.is_minimize_action_costs():
                new_problem.add_quality_metric(
                    updated_minimize_action_costs(
                        qm, new_to_old, new_problem.environment
                    )
                )
            elif qm.is_oversubscription():
                assert isinstance(qm, Oversubscription)
                new_oversubscription: Dict[BoolExpression, NumericConstant] = {}
                for g, v in qm.goals.items():
                    new_goal = self._goals_without_disjunctions_adding_new_elements(
                        dnf, new_problem, new_to_old, new_fluents, [g]
                    )
                    new_oversubscription[new_goal] = v
                new_problem.add_quality_metric(
                    Oversubscription(
                        new_oversubscription, environment=new_problem.environment
                    )
                )
            elif qm.is_temporal_oversubscription():
                assert isinstance(qm, TemporalOversubscription)
                new_temporal_oversubscription: Dict[
                    Tuple["up.model.timing.TimeInterval", "up.model.BoolExpression"],
                    NumericConstant,
                ] = {}
                for (t, g), v in qm.goals.items():
                    new_goal = self._goals_without_disjunctions_adding_new_elements(
                        dnf, new_problem, new_to_old, new_fluents, [g]
                    )
                    new_temporal_oversubscription[(t, new_goal)] = v
                new_problem.add_quality_metric(
                    TemporalOversubscription(
                        new_temporal_oversubscription,
                        environment=new_problem.environment,
                    )
                )
            else:
                new_problem.add_quality_metric(qm)

        return CompilerResult(
            new_problem, partial(replace_action, map=new_to_old), self.name
        )

    def _goals_without_disjunctions_adding_new_elements(
        self,
        dnf: Dnf,
        new_problem: "up.model.Problem",
        new_to_old: Dict[Action, Optional[Action]],
        new_fluents: List["up.model.Fluent"],
        goals: List["up.model.FNode"],
        timing: Optional["up.model.timing.TimeInterval"] = None,
    ) -> "up.model.FNode":
        env = new_problem.environment
        new_goal = dnf.get_dnf_expression(env.expression_manager.And(goals))
        if new_goal.is_or():
            new_name = self.name if timing is None else f"{self.name}_timed"
            fake_fluent = up.model.Fluent(
                get_fresh_name(new_problem, f"{new_name}_fake_goal")
            )
            fake_action = InstantaneousAction(f"{new_name}_fake_action", _env=env)
            fake_action.add_effect(fake_fluent, True)
            for and_exp in new_goal.args:
                na = self._create_new_action_with_given_precond(
                    new_problem, and_exp, fake_action, dnf
                )
                if na is not None:
                    new_to_old[na] = None
                    new_problem.add_action(na)
            new_problem.add_fluent(fake_fluent, default_initial_value=False)
            new_fluents.append(fake_fluent)
            return env.expression_manager.FluentExp(fake_fluent)
        else:
            return new_goal

    def _create_new_durative_action_with_given_conds_at_given_times(
        self,
        new_problem: "up.model.AbstractProblem",
        interval_list: List[TimeInterval],
        cond_list: List[FNode],
        original_action: DurativeAction,
        dnf: Dnf,
    ) -> Optional[DurativeAction]:
        new_action = original_action.clone()
        new_action.name = get_fresh_name(new_problem, original_action.name)
        new_action.clear_conditions()
        for i, c in zip(interval_list, cond_list):
            c = c.simplify()
            if c.is_false():
                return None
            elif c.is_and():
                for co in c.args:
                    new_action.add_condition(i, co)
            else:
                new_action.add_condition(i, c)
        new_action.clear_effects()
        for t, el in original_action.effects.items():
            for e in el:
                if e.is_conditional():
                    new_cond = dnf.get_dnf_expression(e.condition).simplify()
                    if new_cond.is_or():
                        for and_exp in new_cond.args:
                            new_e = e.clone()
                            new_e.set_condition(and_exp)
                            new_action._add_effect_instance(t, new_e)
                    elif not new_cond.is_false():
                        new_e = e.clone()
                        new_e.set_condition(new_cond)
                        new_action._add_effect_instance(t, new_e)
                else:
                    new_action._add_effect_instance(t, e)
        if len(new_action.effects) == 0:
            return None
        return new_action

    def _create_new_action_with_given_precond(
        self,
        new_problem: "up.model.AbstractProblem",
        precond: FNode,
        original_action: InstantaneousAction,
        dnf: Dnf,
    ) -> Optional[InstantaneousAction]:
        new_action = original_action.clone()
        new_action.name = get_fresh_name(new_problem, original_action.name)
        new_action.clear_preconditions()
        precond = precond.simplify()
        if precond.is_false():
            return None
        if precond.is_and():
            for leaf in precond.args:
                new_action.add_precondition(leaf)
        else:
            new_action.add_precondition(precond)
        new_action.clear_effects()
        for e in original_action.effects:
            if e.is_conditional():
                new_cond = dnf.get_dnf_expression(e.condition).simplify()
                if new_cond.is_or():
                    for and_exp in new_cond.args:
                        new_e = e.clone()
                        new_e.set_condition(and_exp)
                        new_action._add_effect_instance(new_e)
                elif not new_cond.is_false():
                    new_e = e.clone()
                    new_e.set_condition(new_cond)
                    new_action._add_effect_instance(new_e)
            else:
                new_action._add_effect_instance(e)
        if len(new_action.effects) == 0:
            return None
        return new_action

    def _create_non_disjunctive_actions(
        self, action: Action, new_problem: AbstractProblem, dnf: Dnf
    ) -> Iterator[Action]:
        env = new_problem.environment
        if isinstance(action, InstantaneousAction):
            new_precond = dnf.get_dnf_expression(
                env.expression_manager.And(action.preconditions)
            )
            if new_precond.is_or():
                for and_exp in new_precond.args:
                    na = self._create_new_action_with_given_precond(
                        new_problem, and_exp, action, dnf
                    )
                    if na is not None:
                        yield na
            else:
                na = self._create_new_action_with_given_precond(
                    new_problem, new_precond, action, dnf
                )
                if na is not None:
                    yield na
        elif isinstance(action, DurativeAction):
            interval_list: List[TimeInterval] = []
            conditions: List[List[FNode]] = []
            # save the timing, calculate the dnf of the and of all the conditions at the same time
            # and then save it in conditions.
            # conditions contains lists of Fnodes, where [a,b,c] means a or b or c
            for i, cl in action.conditions.items():
                interval_list.append(i)
                new_cond = dnf.get_dnf_expression(env.expression_manager.And(cl))
                if new_cond.is_or():
                    conditions.append(new_cond.args)
                else:
                    conditions.append([new_cond])
            conditions_tuple = cast(Tuple[List[FNode], ...], product(*conditions))
            for cond_list in conditions_tuple:
                nda = self._create_new_durative_action_with_given_conds_at_given_times(
                    new_problem, interval_list, cond_list, action, dnf
                )
                if nda is not None:
                    yield nda
        else:
            raise NotImplementedError
