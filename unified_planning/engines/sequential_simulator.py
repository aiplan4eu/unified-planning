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


from fractions import Fraction
from warnings import warn
import unified_planning as up
from unified_planning.engines.compilers import Grounder, GrounderHelper
from unified_planning.engines.engine import Engine
from unified_planning.engines.mixins.sequential_simulator import (
    SequentialSimulatorMixin,
)
from unified_planning.exceptions import (
    UPUsageError,
    UPConflictingEffectsException,
    UPInvalidActionError,
)
from unified_planning.model import (
    FNode,
    Type,
    ExpressionManager,
    UPState,
    Problem,
    MinimizeActionCosts,
    MinimizeSequentialPlanLength,
    MinimizeExpressionOnFinalState,
    MaximizeExpressionOnFinalState,
    Oversubscription,
)
from unified_planning.model.types import _RealType
from unified_planning.model.walkers import StateEvaluator
from typing import Dict, Iterator, List, Optional, Sequence, Set, Tuple, Union, cast


class UPSequentialSimulator(Engine, SequentialSimulatorMixin):
    """
    Sequential SequentialSimulatorMixin implementation.

    This SequentialSimulator, when considering if a state is goal or not, ignores the
    quality metrics.
    """

    def __init__(
        self, problem: "up.model.Problem", error_on_failed_checks: bool = True, **kwargs
    ):
        Engine.__init__(self)
        self.error_on_failed_checks = error_on_failed_checks
        SequentialSimulatorMixin.__init__(self, problem)
        pk = problem.kind
        if not Grounder.supports(pk):
            msg = f"The Grounder used in the {type(self)} does not support the given problem"
            if self.error_on_failed_checks:
                raise UPUsageError(msg)
            else:
                warn(msg)
        assert isinstance(self._problem, up.model.Problem)
        self._grounder = GrounderHelper(problem)
        self._actions = set(self._problem.actions)
        self._se = StateEvaluator(self._problem)

    def _ground_action(
        self, action: "up.model.Action", params: Tuple["up.model.FNode", ...]
    ) -> Optional["up.model.InstantaneousAction"]:
        """
        Utility method to ground an action and do the basic checks.

        :param action: The action to ground.
        :param params: The parameters used to ground the action.
        :return: The grounded action. None if the action grounds to an
            invalid action.
        """
        if action not in self._actions:
            raise UPUsageError(
                f"The given action does not belong to the {type(self)} problem."
            )
        grounded_act = self._grounder.ground_action(action, params)
        assert (
            isinstance(grounded_act, up.model.InstantaneousAction)
            or grounded_act is None
        ), "Supported_kind not respected"
        return grounded_act

    def _get_initial_state(self) -> "up.model.State":
        """
        Returns the problem's initial state.

        NOTE: Every method that requires a state assumes that it's the same class
        of the state given here, therefore an up.model.UPState.
        """
        assert isinstance(self._problem, Problem), "supported_kind not respected"
        return UPState(self._problem.initial_values)

    def _is_applicable(
        self,
        state: "up.model.State",
        action: "up.model.Action",
        parameters: Tuple["up.model.FNode", ...],
    ) -> bool:
        """
        Returns `True` if the given `action conditions` are evaluated as `True` in the given `state`;
        returns `False` otherwise.

        :param state: The state in which the given action is checked for applicability.
        :param action_or_action_instance: The `ActionInstance` or the `Action` that must be checked
            for applicability.
        :param parameters: The parameters to ground the given `Action`. This param must be `None` if
            an `ActionInstance` is given instead.
        :return: Whether or not the action is applicable in the given `state`.
        """
        try:
            is_applicable = (
                len(
                    self.get_unsatisfied_conditions(
                        state, action, parameters, early_termination=True
                    )
                )
                == 0
            )
        except UPInvalidActionError:
            is_applicable = False
        return is_applicable

    def _apply(
        self,
        state: "up.model.State",
        action: "up.model.Action",
        parameters: Tuple["up.model.FNode", ...],
    ) -> Optional["up.model.State"]:
        """
        Returns `None` if the given `action` is not applicable in the given `state`, otherwise returns a new `State`,
        which is a copy of the given `state` where the `applicable effects` of the `action` are applied; therefore
        some `fluent values` are updated.

        :param state: The state in which the given action's conditions are checked and the effects evaluated.
        :param action_or_action_instance: The `ActionInstance` or the `Action` of which conditions are checked
            and effects evaluated.
        :param parameters: The parameters to ground the given `Action`. This param must be `None` if
            an `ActionInstance` is given instead.
        :return: `None` if the `action` is not applicable in the given `state`, the new State generated
            if the action is applicable.
        """
        if not self.is_applicable(state, action, parameters):
            return None
        else:
            return self.apply_unsafe(state, action, parameters)

    def apply_unsafe(
        self,
        state: "up.model.State",
        action_or_action_instance: Union["up.model.Action", "up.plans.ActionInstance"],
        parameters: Optional[Sequence["up.model.Expression"]] = None,
    ) -> Optional["up.model.State"]:
        """
        Returns a new `State`, which is a copy of the given `state` but the applicable `effects` of the
        `action` are applied; therefore some `fluent` values are updated.
        IMPORTANT NOTE: Assumes that `self.is_applicable(state, event)` returns `True`.

        :param state: The state in which the given action's conditions are checked and the effects evaluated.
        :param action_or_action_instance: The `ActionInstance` or the `Action` of which conditions are checked
            and effects evaluated.
        :param parameters: The parameters to ground the given `Action`. This param must be `None` if
            an `ActionInstance` is given instead.
        :return: The new `State` created by the given action; `None` if the evaluation of the effects
            creates conflicting effects.
        """
        action, params = self._get_action_and_parameters(
            action_or_action_instance, parameters
        )
        if not isinstance(state, up.model.UPState):
            raise UPUsageError(
                f"The UPSequentialSimulator uses the UPState but {type(state)} is given."
            )
        grounded_action = self._ground_action(action, params)
        if grounded_action is None:
            return None
        assert isinstance(action, up.model.InstantaneousAction)
        updated_values: Dict["up.model.FNode", "up.model.FNode"] = {}
        assigned_fluent: Set["up.model.FNode"] = set()
        em = self._problem.environment.expression_manager
        for effect in grounded_action.effects:
            try:
                fluent, value = self._evaluate_effect(
                    effect, state, updated_values, assigned_fluent, em
                )
            except UPConflictingEffectsException:
                return None
            if fluent is not None:
                assert value is not None
                updated_values[fluent] = value
        if grounded_action.simulated_effect is not None:
            for f, v in zip(
                grounded_action.simulated_effect.fluents,
                grounded_action.simulated_effect.function(self._problem, state, {}),
            ):
                old_value = updated_values.get(f, None)
                # If f was already modified and it was modified by an increase/decrease or with an assign
                # with a different value
                if old_value is not None and (
                    f not in assigned_fluent
                    or old_value.constant_value() != v.constant_value()
                ):
                    if not f.type.is_bool_type():
                        return None
                    # solve with add-after-delete logic
                    elif not old_value.bool_constant_value():
                        updated_values[f] = v
                else:
                    updated_values[f] = v
        return state.make_child(updated_values)

    def _evaluate_effect(
        self,
        effect: "up.model.Effect",
        state: "up.model.State",
        updated_values: Dict["up.model.FNode", "up.model.FNode"],
        assigned_fluent: Set["up.model.FNode"],
        em: ExpressionManager,
    ) -> Tuple[Optional[FNode], Optional[FNode]]:
        """
        Evaluates the given effect in the state, and returns the fluent affected
        by this effect and the new value that is assigned to the fluent.

        If the effect is conditional and the condition evaluates to False in the state,
        (None, None) is returned.

        :param effect: The effect to evaluate.
        :param state: The state in which the effect is evaluated.
        :param updated_values: Map from fluents to their value, used to correctly evaluate
            more than one increase/decrease effect on the same fluent.
        :param assigned_fluent: The set containing all the fluents already assigned in the
            event containing this effect.
        :param em: The current environment expression manager.
        :return: The Tuple[Fluent, Value], where the fluent is the one affected by the given
            effect and value is the new value assigned to the fluent.
        :raises UPConflictingEffectsException: If to the same fluent are assigned 2 different
            values.
        """
        evaluated_args = tuple(self._se.evaluate(a, state) for a in effect.fluent.args)
        fluent = self._problem.environment.expression_manager.FluentExp(
            effect.fluent.fluent(), evaluated_args
        )
        if (not effect.is_conditional()) or self._se.evaluate(
            effect.condition, state
        ).is_true():
            new_value = self._se.evaluate(effect.value, state)
            if effect.is_assignment():
                old_value = updated_values.get(fluent, None)
                if (
                    old_value is not None
                    and new_value.constant_value() != old_value.constant_value()
                ):
                    if not fluent.type.is_bool_type():
                        raise UPConflictingEffectsException(
                            f"The fluent {fluent} is modified by 2 different assignments in the same event."
                        )
                    # solve with add-after-delete logic
                    elif not old_value.bool_constant_value():
                        return fluent, new_value
                    else:
                        return None, None
                elif old_value is not None and fluent not in assigned_fluent:
                    raise UPConflictingEffectsException(
                        f"The fluent {fluent} is modified by 1 assignments and an increase/decrease in the same event."
                    )
                else:
                    assigned_fluent.add(fluent)
                    return fluent, new_value
            else:
                if fluent in assigned_fluent:
                    raise UPConflictingEffectsException(
                        f"The fluent {fluent} is modified by an assignment and an increase/decrease in the same event."
                    )
                # If the fluent is in updated_values, we take his modified value, (which was modified by another increase or decrease)
                # otherwise we take it's evaluation in the state as it's value.
                f_eval = updated_values.get(fluent, self._se.evaluate(fluent, state))
                if effect.is_increase():
                    return (
                        fluent,
                        em.auto_promote(
                            f_eval.constant_value() + new_value.constant_value()
                        )[0],
                    )
                elif effect.is_decrease():
                    return (
                        fluent,
                        em.auto_promote(
                            f_eval.constant_value() - new_value.constant_value()
                        )[0],
                    )
                else:
                    raise NotImplementedError
        else:
            return None, None

    def _get_applicable_actions(
        self, state: "up.model.State"
    ) -> Iterator[Tuple["up.model.Action", Tuple["up.model.FNode", ...]]]:
        """
        Returns a view over all the `action + parameters` that are applicable in the given `State`.

        :param state: the `state` where the formulas are evaluated.
        :return: an `Iterator` of applicable actions + parameters.
        """
        for original_action, params, _ in self._grounder.get_grounded_actions():
            if self._is_applicable(state, original_action, params):
                yield (original_action, params)

    def get_unsatisfied_conditions(
        self,
        state: "up.model.State",
        action_or_action_instance: Union["up.model.Action", "up.plans.ActionInstance"],
        parameters: Optional[Sequence["up.model.Expression"]] = None,
        early_termination: bool = False,
    ) -> List["up.model.FNode"]:
        """
        Returns the list of `unsatisfied action's conditions` evaluated in the given `state`.
        If the flag `early_termination` is set, the method ends and returns at the first `unsatisfied condition`.
        Note that the returned list might also contain conditions that were not originally in the action, if this
        action violates some other semantic bound (for example bounded types).

        :param state: The state in which the given action's conditions are checked.
        :param action_or_action_instance: The `ActionInstance` or the `Action` of which conditions are checked.
        :param parameters: The parameters to ground the given `Action`. This param must be `None` if
            an `ActionInstance` is given instead.
        :return: The list of all the `action's conditions` that evaluated to `False` or the list containing the first
            `condition` evaluated to `False` if the flag `early_termination` is set.
        """
        action, params = self._get_action_and_parameters(
            action_or_action_instance,
            parameters,
        )
        g_action = self._ground_action(action, params)
        if g_action is None:
            raise UPInvalidActionError(
                "The given action grounded with the given parameters does not create a valid action."
            )
        unsatisfied_conditions = []
        for c in g_action.preconditions:
            evaluated_cond = self._se.evaluate(c, state)
            if (
                not evaluated_cond.is_bool_constant()
                or not evaluated_cond.bool_constant_value()
            ):
                unsatisfied_conditions.append(c)
                if early_termination:
                    return unsatisfied_conditions

        # check that the assignments will respect the bound typing
        new_bounded_types_values: Dict["up.model.FNode", "up.model.FNode"] = {}
        assigned_fluent: Set["up.model.FNode"] = set()
        em = self._problem.environment.expression_manager
        for effect in g_action.effects:
            lower_bound, upper_bound = None, None
            f_type = effect.fluent.type
            if f_type.is_int_type() or f_type.is_real_type():
                f_type = cast(_RealType, effect.fluent.type)
                lower_bound, upper_bound = f_type.lower_bound, f_type.upper_bound
            if lower_bound is not None or upper_bound is not None:
                fluent, value = self._evaluate_effect(
                    effect, state, new_bounded_types_values, assigned_fluent, em
                )
                if fluent is not None:
                    assert value is not None
                    new_bounded_types_values[fluent] = value
                    if lower_bound is not None and lower_bound > cast(
                        Fraction, value.constant_value()
                    ):
                        unsatisfied_conditions.append(em.LE(lower_bound, fluent))
                        if early_termination:
                            return unsatisfied_conditions
                    if upper_bound is not None and upper_bound < cast(
                        Fraction, value.constant_value()
                    ):
                        unsatisfied_conditions.append(em.LE(fluent, upper_bound))
                        if early_termination:
                            return unsatisfied_conditions
        if g_action.simulated_effect is not None:
            to_check = False
            for f in g_action.simulated_effect.fluents:
                f_type = cast(_RealType, f.type)
                if (f_type.is_int_type() or f_type.is_real_type()) and (
                    f_type.lower_bound is not None or f_type.upper_bound is not None
                ):
                    to_check = True
                    break
            if to_check:
                for f, v in zip(
                    g_action.simulated_effect.fluents,
                    g_action.simulated_effect.function(self._problem, state, {}),
                ):
                    lower_bound, upper_bound = None, None
                    if f.type.is_int_type() or f.type.is_real_type():
                        f_type = cast(_RealType, f.type)
                        lower_bound, upper_bound = (
                            f_type.lower_bound,
                            f_type.upper_bound,
                        )
                    if lower_bound is not None or upper_bound is not None:
                        if (
                            lower_bound is not None
                            and cast(Fraction, v.constant_value()) < lower_bound
                        ):
                            unsatisfied_conditions.append(em.LE(lower_bound, f))
                            if early_termination:
                                break
                        if (
                            upper_bound is not None
                            and cast(Fraction, v.constant_value()) > upper_bound
                        ):
                            unsatisfied_conditions.append(em.LE(f, upper_bound))
                            if early_termination:
                                break
        return unsatisfied_conditions

    def get_unsatisfied_goals(
        self, state: "up.model.State", early_termination: bool = False
    ) -> List["up.model.FNode"]:
        """
        Returns the list of `unsatisfied goals` evaluated in the given `state`.
        If the flag `early_termination` is set, the method ends and returns the first `unsatisfied goal`.

        :param state: The `State` in which the `problem goals` are evaluated.
        :param early_termination: Flag deciding if the method ends and returns at the first `unsatisfied goal`.
        :return: The list of all the `goals` that evaluated to `False` or the list containing the first `goal` evaluated to `False` if the flag `early_termination` is set.
        """
        unsatisfied_goals = []
        for g in cast(up.model.Problem, self._problem).goals:
            g_eval = self._se.evaluate(g, state).bool_constant_value()
            if not g_eval:
                unsatisfied_goals.append(g)
                if early_termination:
                    break
        return unsatisfied_goals

    def _is_goal(self, state: "up.model.State") -> bool:
        """
        is_goal implementation
        """
        return len(self.get_unsatisfied_goals(state, early_termination=True)) == 0

    @property
    def name(self) -> str:
        return "sequential_simulator"

    @staticmethod
    def supported_kind() -> "up.model.ProblemKind":
        supported_kind = up.model.ProblemKind()
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_numbers("CONTINUOUS_NUMBERS")
        supported_kind.set_numbers("DISCRETE_NUMBERS")
        supported_kind.set_numbers("BOUNDED_TYPES")
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
        supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
        supported_kind.set_quality_metrics("ACTIONS_COST")
        supported_kind.set_quality_metrics("PLAN_LENGTH")
        supported_kind.set_quality_metrics("OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("TEMPORAL_OVERSUBSCRIPTION")
        supported_kind.set_quality_metrics("MAKESPAN")
        supported_kind.set_quality_metrics("FINAL_VALUE")
        return supported_kind

    @staticmethod
    def supports(problem_kind):
        return problem_kind <= UPSequentialSimulator.supported_kind()


def evaluate_quality_metric(
    simulator: SequentialSimulatorMixin,
    quality_metric: "up.model.PlanQualityMetric",
    metric_value: Union[Fraction, int],
    state: "up.model.State",
    action: "up.model.Action",
    parameters: Tuple["up.model.FNode", ...],
    next_state: "up.model.State",
) -> Union[Fraction, int]:
    """
    Evaluates the value of the given metric.

    :param simulator: A simulator, needed to evaluate the metric.
    :param quality_metric: The QualityMetric to evaluate.
    :param metric_value: The value of the metric before applying the given action.
    :param state: The State before applying the given action.
    :param action: The action applied.
    :param parameters: The parameters used to ground the action.
    :param next_state: The state after applying the given action.
    :return: The evaluation of the metric.
    """
    if not isinstance(simulator._problem, up.model.Problem):
        raise NotImplementedError(
            "Currently this method is implemented only for classical and numeric problems."
        )
    se = StateEvaluator(simulator._problem)
    if quality_metric.is_minimize_action_costs():
        assert isinstance(quality_metric, MinimizeActionCosts)
        action_cost = quality_metric.get_action_cost(action)
        if action_cost is None:
            raise UPUsageError(
                "Can't evaluate Action cost when the cost is not set.",
                "You can explicitly set a default in the MinimizeActionCost constructor.",
            )
        if len(action.parameters) != len(parameters):
            raise UPUsageError(
                "The parameters length is different than the action's parameters length."
            )
        action_cost = action_cost.substitute(dict(zip(action.parameters, parameters)))
        assert isinstance(action_cost, up.model.FNode)
        return se.evaluate(action_cost, state).constant_value() + metric_value
    elif isinstance(quality_metric, MinimizeSequentialPlanLength):
        return metric_value + 1
    elif isinstance(
        quality_metric,
        (MinimizeExpressionOnFinalState, MaximizeExpressionOnFinalState),
    ):
        return se.evaluate(quality_metric.expression, next_state).constant_value()
    elif isinstance(quality_metric, Oversubscription):
        total_gain: Union[Fraction, int] = 0
        for goal, gain in quality_metric.goals.items():
            if se.evaluate(goal, next_state).bool_constant_value():
                total_gain += gain
        return total_gain
    else:
        raise NotImplementedError(
            f"QualityMetric {quality_metric} not supported by the UPSequentialSimulator."
        )


def evaluate_quality_metric_in_initial_state(
    simulator: SequentialSimulatorMixin,
    quality_metric: "up.model.PlanQualityMetric",
) -> Union[Fraction, int]:
    """
    Returns the evaluation of the given metric in the initial state.

    :param simulator: The simulator used to evaluate the metric.
    :param quality_metric: The QUalityMetric tto evaluate.
    :return: The evaluation of the metric in the initial state.
    """
    if not isinstance(simulator._problem, up.model.Problem):
        raise NotImplementedError(
            "Currently this method is implemented only for classical and numeric problems."
        )
    se = StateEvaluator(simulator._problem)
    em = simulator._problem.environment.expression_manager
    initial_state = simulator.get_initial_state()
    if quality_metric.is_minimize_action_costs():
        return 0
    elif isinstance(quality_metric, MinimizeSequentialPlanLength):
        return 0
    elif isinstance(
        quality_metric,
        (MinimizeExpressionOnFinalState, MaximizeExpressionOnFinalState),
    ):
        return se.evaluate(quality_metric.expression, initial_state).constant_value()
    elif isinstance(quality_metric, Oversubscription):
        total_gain: Union[Fraction, int] = 0
        for goal, gain in quality_metric.goals.items():
            if se.evaluate(goal, initial_state).bool_constant_value():
                total_gain += gain
        return total_gain
    else:
        raise NotImplementedError(
            f"QualityMetric {quality_metric} not supported by the UPSequentialSimulator."
        )
