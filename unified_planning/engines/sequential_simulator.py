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


from enum import Enum, auto
from fractions import Fraction
from itertools import product
from warnings import warn
import unified_planning as up
from unified_planning.engines.compilers import Grounder, GrounderHelper
from unified_planning.engines.engine import Engine
from unified_planning.engines.mixins.sequential_simulator import (
    SequentialSimulatorMixin,
)
from unified_planning.model.fluent import get_all_fluent_exp
from unified_planning.model.problem_kind_versioning import LATEST_PROBLEM_KIND_VERSION
from unified_planning.exceptions import (
    UPUsageError,
    UPConflictingEffectsException,
    UPInvalidActionError,
    UPUnreachableCodeError,
    UPProblemDefinitionError,
)
from unified_planning.model import (
    Action,
    Fluent,
    FNode,
    ExpressionManager,
    UPState,
    Problem,
    MinimizeActionCosts,
    MinimizeExpressionOnFinalState,
    MaximizeExpressionOnFinalState,
    Oversubscription,
    Expression,
    Variable,
)
from unified_planning.model.types import _RealType
from unified_planning.model.walkers import StateEvaluator, ExpressionQuantifiersRemover
from typing import (
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    cast,
)


class InapplicabilityReasons(Enum):
    """
    Represents the possible reasons for an action being inapplicable after the
    ``SequentialSimulator.is_applicable`` method returns ``True`` but then the
    ``SequentialSimulator.apply_unsafe`` returns ``None``.

    Possible values:

    *   | ``VIOLATES_CONDITIONS``: The action's conditions don't evaluate to True in the given state;
        | Generally the most frequent and common cause of action's inapplicability.
    *   | ``CONFLICTING_EFFECTS``: The action applied in the given state creates conflicting effects;
        | This generally means that the action gives 2 different values to the same fluent instance.
    *   | ``VIOLATES_STATE_INVARIANTS``: The new state does not satisfy the state invariants of the problem.
        | State invariants are the ``Always`` expressions of the trajectory constraints or the bounded types.
    """

    VIOLATES_CONDITIONS = auto()
    CONFLICTING_EFFECTS = auto()
    VIOLATES_STATE_INVARIANTS = auto()


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
        SequentialSimulatorMixin.__init__(self, problem, error_on_failed_checks)
        pk = problem.kind
        if not Grounder.supports(pk):
            msg = f"The Grounder used in the {type(self).__name__} does not support the given problem"
            if self.error_on_failed_checks:
                raise UPUsageError(msg)
            else:
                warn(msg)
        assert isinstance(self._problem, up.model.Problem)
        self._grounder = GrounderHelper(problem)
        self._actions = set(self._problem.actions)
        self._se = StateEvaluator(self._problem)
        self._initial_state: Optional[UPState] = None
        self._grounded_actions: Optional[
            List[Tuple[Action, Tuple[FNode, ...], Optional[Action]]]
        ] = None

        # Add state invariants without quantifiers to get all the grounded
        # fluent instances that might modify the state invariants
        qrm = ExpressionQuantifiersRemover(self._problem.environment)
        self._state_invariants: List[FNode] = [
            qrm.remove_quantifiers(si, self._problem).simplify()
            for si in self._problem.state_invariants
        ]
        # Set of all the fluents appearing in the state_invariants. Used to skip checks
        # if None of this fluent is modified
        self._fluent_exps_in_state_invariants: Set[FNode] = set()
        for si in self._state_invariants:
            self._fluent_exps_in_state_invariants |= (
                si.environment.free_vars_extractor.get(si)
            )

        # Add bounded types as state invariants
        em = self._problem.environment.expression_manager
        for f in self._problem.fluents:
            lower_bound, upper_bound = None, None
            f_type = f.type
            if f_type.is_int_type() or f_type.is_real_type():
                f_type = cast(_RealType, f_type)
                lower_bound, upper_bound = f_type.lower_bound, f_type.upper_bound
            if lower_bound is not None:
                for f_e in get_all_fluent_exp(self._problem, f):
                    self._fluent_exps_in_state_invariants.add(f_e)
                    self._state_invariants.append(em.LE(lower_bound, f_e))
            if upper_bound is not None:
                for f_e in get_all_fluent_exp(self._problem, f):
                    self._fluent_exps_in_state_invariants.add(f_e)
                    self._state_invariants.append(em.LE(f_e, upper_bound))

        self._fluents_in_state_invariants: Set[Fluent] = set(
            (fe.fluent() for fe in self._fluent_exps_in_state_invariants)
        )

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
                f"The given action: {action.name} does not belong to the given problem."
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
        if self._initial_state is None:
            self._initial_state = UPState(
                self._problem.explicit_initial_values, self._problem
            )
            for si in self._state_invariants:
                if not self._se.evaluate(si, self._initial_state).bool_constant_value():
                    raise UPProblemDefinitionError(
                        "The initial state of the problem already violates the state invariants"
                    )
        assert self._initial_state is not None
        return self._initial_state

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
            _, reason = self.get_unsatisfied_conditions(
                state, action, parameters, early_termination=True, full_check=True
            )
            is_applicable = reason is None
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
        _, reason = self.get_unsatisfied_conditions(
            state, action, parameters, early_termination=True, full_check=False
        )
        if reason is not None:
            return None
        try:
            return self.apply_unsafe(state, action, parameters)
        except (UPInvalidActionError, UPConflictingEffectsException):
            return None

    def apply_unsafe(
        self,
        state: "up.model.State",
        action_or_action_instance: Union["up.model.Action", "up.plans.ActionInstance"],
        parameters: Optional[Sequence["up.model.Expression"]] = None,
    ) -> "up.model.State":
        """
        Returns a new `State`, which is a copy of the given `state` but the applicable `effects` of the
        `action` are applied; therefore some `fluent` values are updated.
        IMPORTANT NOTE: Assumes that `self.is_applicable(state, event)` returns `True`.

        :param state: The state in which the given action's conditions are checked and the effects evaluated.
        :param action_or_action_instance: The `ActionInstance` or the `Action` of which conditions are checked
            and effects evaluated.
        :param parameters: The parameters to ground the given `Action`. This param must be `None` if
            an `ActionInstance` is given instead.
        :return: The new `State` created by the given action.
        :raises UPConflictingEffectsException: If to the same fluent are assigned 2 different
            values.
        :raises UPInvalidActionError: If the action is invalid or if it violates some state invariants.
        """
        action, params = self._get_action_and_parameters(
            action_or_action_instance, parameters
        )
        if not isinstance(state, up.model.UPState):
            raise UPUsageError(
                f"The UPSequentialSimulator uses the UPState but {type(state).__name__} is given."
            )
        grounded_action = self._ground_action(action, params)
        if grounded_action is None:
            raise UPInvalidActionError("Apply_unsafe got an inapplicable action.")
        assert isinstance(action, up.model.InstantaneousAction)
        updated_values: Dict["up.model.FNode", "up.model.FNode"] = {}
        assigned_fluent: Set["up.model.FNode"] = set()
        em = self._problem.environment.expression_manager

        if grounded_action.simulated_effect is not None:
            for f, v in zip(
                grounded_action.simulated_effect.fluents,
                grounded_action.simulated_effect.function(self._problem, state, {}),
            ):
                updated_values[f] = v
                assigned_fluent.add(f)

        for e in grounded_action.effects:
            for effect in e.expand_effect(
                cast(up.model.mixins.ObjectsSetMixin, self._problem)
            ):
                fluent, value = self._evaluate_effect(
                    effect, state, updated_values, assigned_fluent, em
                )
                if fluent is not None:
                    assert value is not None
                    updated_values[fluent] = value

        new_state = state.make_child(updated_values)
        for si in self._state_invariants:
            if not self._se.evaluate(si, new_state).bool_constant_value():
                raise UPInvalidActionError(
                    "The given action is not applicable because it violates state invariants.",
                    "Bounded numeric types are checked as state invariants.",
                )
        return new_state

    def _evaluate_effect(
        self,
        effect: "up.model.Effect",
        state: "up.model.State",
        updated_values: Dict["up.model.FNode", "up.model.FNode"],
        assigned_fluent: Set["up.model.FNode"],
        em: ExpressionManager,
        evaluated_fluent: Optional[FNode] = None,
        evaluated_condition: Optional[bool] = None,
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
        :param evaluated_fluent: In case the fluent is already evaluated outside, pass it to
            avoid doing the same thing again.
        :param evaluated_condition: In case the condition is already evaluated outside, pass it to
            avoid doing the same thing again.
        :return: The Tuple[Fluent, Value], where the fluent is the one affected by the given
            effect and value is the new value assigned to the fluent.
        :raises UPConflictingEffectsException: If to the same fluent are assigned 2 different
            values.
        """
        evaluate: Callable[[FNode], FNode] = lambda exp: self._se.evaluate(exp, state)
        if evaluated_fluent is not None:
            fluent = evaluated_fluent
        else:
            fluent = effect.fluent.fluent()(*(map(evaluate, effect.fluent.args)))
        if evaluated_condition is None:
            evaluated_condition = (
                not effect.is_conditional() or evaluate(effect.condition).is_true()
            )
        if evaluated_condition:
            new_value = evaluate(effect.value)
            if effect.is_assignment():
                old_value = updated_values.get(fluent, None)
                if (
                    old_value is not None
                    and new_value.constant_value() != old_value.constant_value()
                ):
                    if not fluent.type.is_bool_type():
                        raise UPConflictingEffectsException(
                            f"The fluent {fluent} is modified by 2 different assignments in the same action."
                        )
                    # solve with add-after-delete logic
                    elif not old_value.bool_constant_value():
                        return fluent, new_value
                    else:
                        return None, None
                elif old_value is not None and fluent not in assigned_fluent:
                    raise UPConflictingEffectsException(
                        f"The fluent {fluent} is modified by 1 assignments and an increase/decrease in the same action."
                    )
                else:
                    assigned_fluent.add(fluent)
                    return fluent, new_value
            else:
                if fluent in assigned_fluent:
                    raise UPConflictingEffectsException(
                        f"The fluent {fluent} is modified by an assignment and an increase/decrease in the same action."
                    )
                # If the fluent is in updated_values, we take his modified value, (which was modified by another increase or decrease)
                # otherwise we take it's evaluation in the state as it's value.
                f_eval = updated_values.get(fluent, evaluate(fluent))
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
        if self._grounded_actions is None:
            self._grounded_actions = list(self._grounder.get_grounded_actions())
        for original_action, params, _ in self._grounded_actions:
            if self._is_applicable(state, original_action, params):
                yield (original_action, params)

    def get_unsatisfied_conditions(
        self,
        state: "up.model.State",
        action_or_action_instance: Union["up.model.Action", "up.plans.ActionInstance"],
        parameters: Optional[Sequence["up.model.Expression"]] = None,
        early_termination: bool = False,
        full_check: bool = False,
    ) -> Tuple[List["up.model.FNode"], Optional[InapplicabilityReasons]]:
        """
        Returns the list of ``unsatisfied action's conditions`` evaluated in the given ``state``, together with
        an Optional reason of why the action can't be applied to the given state. If the ``full_check``
        flag is set, the returned list can be empty but the action can't be applied in the given state,.
        To be sure that the action is applicable, the ``InapplicabilityReason`` returned must be ``None``.
        If the flag ``early_termination`` is set, the method ends and returns at the first ``unsatisfied condition``.
        Note that the returned list might also contain conditions that were not originally in the action, if this
        action violates some other semantic constraints (for example bounded types or state invariants).

        :param state: The state in which the given action's conditions are checked.
        :param action_or_action_instance: The `ActionInstance` or the `Action` of which conditions are checked.
        :param parameters: The parameters to ground the given `Action`. This param must be `None` if
            an `ActionInstance` is given instead.
        :param early_termination: When ``True``, the first error found is returned.
        :param full_check: When ``True``, fails also if the action applied creates any semantic problems; such as
            conflicting_effects or violates state_invariants.
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
        evaluate: Callable[[FNode], FNode] = lambda exp: self._se.evaluate(exp, state)
        reason: Optional[InapplicabilityReasons] = None
        unsatisfied_conditions = []
        for c in g_action.preconditions:
            evaluated_cond = evaluate(c)
            if (
                not evaluated_cond.is_bool_constant()
                or not evaluated_cond.bool_constant_value()
            ):
                unsatisfied_conditions.append(c)
                reason = InapplicabilityReasons.VIOLATES_CONDITIONS
                if early_termination:
                    return unsatisfied_conditions, reason

        updated_values: Dict["up.model.FNode", "up.model.FNode"] = {}
        assigned_fluent: Set["up.model.FNode"] = set()
        em = self._problem.environment.expression_manager

        if full_check:
            # Add simulated effects to updated_values and assigned_fluent before other effects
            sim_eff = g_action.simulated_effect
            if sim_eff is not None:
                for f, v in zip(
                    sim_eff.fluents,
                    sim_eff.function(self._problem, state, {}),
                ):
                    updated_values[f] = v
                    assigned_fluent.add(f)

            for effect in g_action.conditional_effects:
                for e in effect.expand_effect(
                    cast(up.model.mixins.ObjectsSetMixin, self._problem)
                ):
                    if not e.fluent.type.is_bool_type():
                        evaluated_condition = evaluate(
                            e.condition
                        ).bool_constant_value()
                        if evaluated_condition:
                            try:
                                fluent, value = self._evaluate_effect(
                                    e,
                                    state,
                                    updated_values,
                                    assigned_fluent,
                                    em,
                                    evaluated_condition=evaluated_condition,
                                )
                                assert fluent is not None and value is not None
                                updated_values[fluent] = value
                            except UPConflictingEffectsException:
                                reason = InapplicabilityReasons.CONFLICTING_EFFECTS
                                if early_termination:
                                    return unsatisfied_conditions, reason

            if updated_values:
                for effect in g_action.unconditional_effects:
                    for e in effect.expand_effect(
                        cast(up.model.mixins.ObjectsSetMixin, self._problem)
                    ):
                        ev_fluent = e.fluent.fluent()(*(map(evaluate, e.fluent.args)))
                        values = updated_values.get(ev_fluent, None)
                        if values is not None:
                            try:
                                fluent, value = self._evaluate_effect(
                                    e,
                                    state,
                                    updated_values,
                                    assigned_fluent,
                                    em,
                                    evaluated_fluent=ev_fluent,
                                    evaluated_condition=True,
                                )
                                assert fluent is not None and value is not None
                                updated_values[fluent] = value
                            except UPConflictingEffectsException:
                                reason = InapplicabilityReasons.CONFLICTING_EFFECTS
                                if early_termination:
                                    return unsatisfied_conditions, reason

            for effect in g_action.effects:
                for e in effect.expand_effect(
                    cast(up.model.mixins.ObjectsSetMixin, self._problem)
                ):
                    if e.fluent.fluent() in self._fluents_in_state_invariants:
                        ev_fluent = e.fluent.fluent()(*(map(evaluate, e.fluent.args)))
                        if ev_fluent in self._fluent_exps_in_state_invariants:
                            if ev_fluent not in updated_values:
                                try:
                                    fluent, value = self._evaluate_effect(
                                        e,
                                        state,
                                        updated_values,
                                        assigned_fluent,
                                        em,
                                        evaluated_fluent=ev_fluent,
                                    )
                                    assert fluent is not None and value is not None
                                    updated_values[fluent] = value
                                except UPConflictingEffectsException:
                                    raise UPUnreachableCodeError(
                                        "Conflicting effects should be caught above"
                                    )

            if not isinstance(state, up.model.UPState):
                raise UPUsageError(
                    f"The UPSequentialSimulator uses the UPState but {type(state).__name__} is given."
                )
            new_partial_state = state.make_child(updated_values)
            for si in self._state_invariants:
                if not self._se.evaluate(si, new_partial_state).bool_constant_value():
                    unsatisfied_conditions.append(si)
                    if reason is None:
                        reason = InapplicabilityReasons.VIOLATES_STATE_INVARIANTS
                    if early_termination:
                        break
        return unsatisfied_conditions, reason

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
        supported_kind = up.model.ProblemKind(version=LATEST_PROBLEM_KIND_VERSION)
        supported_kind.set_problem_class("ACTION_BASED")
        supported_kind.set_typing("FLAT_TYPING")
        supported_kind.set_typing("HIERARCHICAL_TYPING")
        supported_kind.set_parameters("BOOL_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_FLUENT_PARAMETERS")
        supported_kind.set_parameters("BOOL_ACTION_PARAMETERS")
        supported_kind.set_parameters("BOUNDED_INT_ACTION_PARAMETERS")
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
        supported_kind.set_conditions_kind("INTERPRETED_FUNCTIONS_IN_CONDITIONS")
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
        supported_kind.set_simulated_entities("SIMULATED_EFFECTS")
        supported_kind.set_constraints_kind("STATE_INVARIANTS")
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
    elif quality_metric.is_minimize_sequential_plan_length():
        return metric_value + 1
    elif (
        quality_metric.is_minimize_expression_on_final_state()
        or quality_metric.is_maximize_expression_on_final_state()
    ):
        assert isinstance(
            quality_metric,
            (MinimizeExpressionOnFinalState, MaximizeExpressionOnFinalState),
        )
        return se.evaluate(quality_metric.expression, next_state).constant_value()
    elif quality_metric.is_oversubscription():
        assert isinstance(quality_metric, Oversubscription)
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
    elif quality_metric.is_minimize_sequential_plan_length():
        return 0
    elif (
        quality_metric.is_minimize_expression_on_final_state()
        or quality_metric.is_maximize_expression_on_final_state()
    ):
        assert isinstance(
            quality_metric,
            (MinimizeExpressionOnFinalState, MaximizeExpressionOnFinalState),
        )
        return se.evaluate(quality_metric.expression, initial_state).constant_value()
    elif quality_metric.is_oversubscription():
        assert isinstance(quality_metric, Oversubscription)
        total_gain: Union[Fraction, int] = 0
        for goal, gain in quality_metric.goals.items():
            if se.evaluate(goal, initial_state).bool_constant_value():
                total_gain += gain
        return total_gain
    else:
        raise NotImplementedError(
            f"QualityMetric {quality_metric} not supported by the UPSequentialSimulator."
        )
