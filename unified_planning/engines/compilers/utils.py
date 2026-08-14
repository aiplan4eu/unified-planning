# Copyright 2021-2023 AIPlan4EU project
# Copyright 2024-2026 Unified Planning library and its maintainers
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
"""This module defines different utility functions for the compilers."""

import warnings
from fractions import Fraction
from typing import (
    Callable,
    Dict,
    List,
    Optional,
    OrderedDict,
    Sequence,
    Set,
    Tuple,
    Union,
    cast,
)

import unified_planning as up
from unified_planning.environment import Environment
from unified_planning.exceptions import (
    UPConflictingEffectsException,
    UPProblemDefinitionError,
    UPUsageError,
)
from unified_planning.model import (
    AbstractProblem,
    Action,
    BoolExpression,
    DurationInterval,
    DurativeAction,
    Effect,
    Expression,
    Fluent,
    FNode,
    InstantaneousAction,
    MaximizeExpressionOnFinalState,
    MinimizeActionCosts,
    MinimizeExpressionOnFinalState,
    NumericConstant,
    Oversubscription,
    Parameter,
    PlanQualityMetric,
    Problem,
    SimulatedEffect,
    TemporalOversubscription,
    TimeInterval,
    TimePointInterval,
)
from unified_planning.model.contingent import SensingAction
from unified_planning.plans import ActionInstance


def check_and_simplify_conditions(
    problem: AbstractProblem, action: DurativeAction, simplifier
) -> Tuple[bool, List[Tuple[TimeInterval, FNode]]]:
    """
    Simplifies conditions and if it is False (a contraddiction)
    returns False, otherwise returns True.
    If the simplification is True (a tautology) removes all conditions at the given timing.
    If the simplification is still an AND rewrites back every "arg" of the AND
    in the conditions
    If the simplification is not an AND sets the simplification as the only
    condition at the given timing.
    Then, the new conditions are returned as a List[Tuple[Timing, FNode]] and the user can
    decide how to use the new conditions.
    """
    # new action conditions
    nac: List[Tuple[TimeInterval, FNode]] = []
    # i = interval, lc = list condition
    for i, lc in action.conditions.items():
        # conditions (as an And FNode)
        c = problem.environment.expression_manager.And(lc)
        # conditions simplified
        cs = simplifier.simplify(c)
        if cs.is_bool_constant():
            if not cs.bool_constant_value():
                return (
                    False,
                    [],
                )
        else:
            if cs.is_and():
                nac.extend((i, new_cond) for new_cond in cs.args)
            else:
                nac.append((i, cs))
    return (True, nac)


def check_and_simplify_preconditions(
    problem: AbstractProblem, action: InstantaneousAction, simplifier
) -> Tuple[bool, List[FNode]]:
    """
    Simplifies preconditions and if it is False (a contraddiction)
    returns False, otherwise returns True.
    If the simplification is True (a tautology) removes all preconditions.
    If the simplification is still an AND rewrites back every "arg" of the AND
    in the preconditions
    If the simplification is not an AND sets the simplification as the only
    precondition.
    Then, the new preconditions are returned as a List[FNode] and the user can
    decide how to use the new preconditions.
    """
    # action preconditions
    ap = action.preconditions
    if len(ap) == 0:
        return (True, [])
    # preconditions (as an And FNode)
    p = problem.environment.expression_manager.And(ap)
    # preconditions simplified
    ps = simplifier.simplify(p)
    # new action preconditions
    nap: List[FNode] = []
    if ps.is_bool_constant():
        if not ps.bool_constant_value():
            return (False, [])
    else:
        if ps.is_and():
            nap.extend(ps.args)
        else:
            nap.append(ps)
    action._set_preconditions(nap)
    return (True, nap)


def create_effect_with_given_subs(
    problem: Problem,
    old_effect: Effect,
    simplifier,
    subs: Dict[Expression, Expression],
) -> Optional[Effect]:
    em = problem.environment.expression_manager
    new_fluent = old_effect.fluent.substitute(subs)
    if new_fluent.is_fluent_exp():
        new_fluent = em.FluentExp(
            new_fluent.fluent(),
            tuple(simplifier.simplify(a) for a in new_fluent.args),
        )
    new_value = simplifier.simplify(old_effect.value.substitute(subs))
    new_condition = simplifier.simplify(old_effect.condition.substitute(subs))
    if new_condition == em.FALSE():
        return None
    return Effect(
        new_fluent, new_value, new_condition, old_effect.kind, old_effect.forall
    )


def create_action_with_given_subs(
    problem: Problem,
    old_action: Action,
    simplifier,
    subs: Dict[Expression, Expression],
) -> Optional[Action]:
    """
    This method is used to instantiate the actions parameters to a constant.

    ``old_action`` is cloned first (preserving its exact subclass and any subclass-only
    data, e.g. a :class:`~unified_planning.model.contingent.SensingAction`'s
    ``observed_fluents``), then its preconditions/conditions, effects, and (for a `DurativeAction`)
    duration and continuous effects are rebuilt on the clone through the given substitution.

    When ``subs`` is empty (``old_action`` has no parameters), the action keeps its
    original name instead of going through :func:`get_fresh_name`: since ``old_action``
    is still registered in ``problem`` under that name, `get_fresh_name` would otherwise
    treat it as colliding with itself and rename it needlessly.
    """
    naming_list: List[str] = []
    for param, value in subs.items():
        assert isinstance(param, Parameter)
        assert isinstance(value, FNode)
        naming_list.append(str(value))
    c_subs = cast(Dict[Parameter, FNode], subs)
    if isinstance(old_action, InstantaneousAction):
        new_action = cast(InstantaneousAction, old_action.clone())
        new_action.name = (
            old_action.name
            if not subs
            else get_fresh_name(problem, old_action.name, naming_list)
        )
        new_action._parameters = OrderedDict()
        if isinstance(new_action, SensingAction):
            # observed_fluents is SensingAction-only, so create_effect_with_given_subs
            # (which only knows about preconditions/effects) can't substitute it; do it here.
            new_action._observed_fluents = [
                f.substitute(subs) for f in new_action.observed_fluents
            ]
        old_preconditions = new_action.preconditions
        new_action._set_preconditions([p.substitute(subs) for p in old_preconditions])

        old_effects = list(new_action.effects)
        old_simulated_effect = new_action.simulated_effect
        new_action.clear_effects()
        for e in old_effects:
            new_effect = create_effect_with_given_subs(problem, e, simplifier, subs)
            if new_effect is not None:
                # We try to add the new effect, but a compiler might generate conflicting effects,
                # so the action is just considered invalid
                try:
                    new_action._add_effect_instance(new_effect)
                except UPConflictingEffectsException:
                    return None
        if old_simulated_effect is not None:
            new_fluents = [f.substitute(subs) for f in old_simulated_effect.fluents]

            def fun(_problem, _state, _):
                assert old_simulated_effect is not None
                return old_simulated_effect.function(_problem, _state, c_subs)

            # this rebuilds a simulated effect the user already defined (and got
            # warned about), so the deprecation warning is silenced here
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                new_simulated_effect = SimulatedEffect(new_fluents, fun)
            # We try to add the new simulated effect, but a compiler might generate conflicting effects,
            # so the action is just considered invalid
            try:
                new_action.set_simulated_effect(new_simulated_effect)
            except UPConflictingEffectsException:
                return None
        is_feasible, new_preconditions = check_and_simplify_preconditions(
            problem, new_action, simplifier
        )
        if not is_feasible:
            return None
        new_action._set_preconditions(new_preconditions)
        return new_action
    if isinstance(old_action, DurativeAction):
        new_durative_action = cast(DurativeAction, old_action.clone())
        new_durative_action.name = (
            old_action.name
            if not subs
            else get_fresh_name(problem, old_action.name, naming_list)
        )
        new_durative_action._parameters = OrderedDict()
        old_duration = new_durative_action.duration
        new_duration = DurationInterval(
            simplifier.simplify(old_duration.lower.substitute(subs)),
            simplifier.simplify(old_duration.upper.substitute(subs)),
            old_duration.is_left_open(),
            old_duration.is_right_open(),
        )
        try:
            new_durative_action.set_duration_constraint(new_duration)
        except UPProblemDefinitionError:
            # the simplified interval is empty, so this grounding can never be applied
            return None

        old_conditions = {
            i: list(cl) for i, cl in new_durative_action.conditions.items()
        }
        new_durative_action.clear_conditions()
        for i, cl in old_conditions.items():
            for c in cl:
                new_durative_action.add_condition(i, c.substitute(subs))

        old_effects_by_timing = {
            t: list(el) for t, el in new_durative_action.effects.items()
        }
        old_simulated_effects = dict(new_durative_action.simulated_effects)
        old_continuous_effects = {
            i: list(el) for i, el in new_durative_action.continuous_effects.items()
        }
        new_durative_action.clear_effects()
        new_durative_action.clear_continuous_effects()
        for t, effects_list in old_effects_by_timing.items():
            for e in effects_list:
                new_effect = create_effect_with_given_subs(problem, e, simplifier, subs)
                if new_effect is not None:
                    # We try to add the new effect, but a compiler might generate conflicting effects,
                    # so the action is just considered invalid
                    try:
                        new_durative_action._add_effect_instance(t, new_effect)
                    except UPConflictingEffectsException:
                        return None
        for i, ce_list in old_continuous_effects.items():
            for ce in ce_list:
                new_continuous_effect = create_effect_with_given_subs(
                    problem, ce, simplifier, subs
                )
                if new_continuous_effect is not None:
                    new_durative_action._add_continuous_effect_instance(
                        i, new_continuous_effect
                    )
        for t, old_se in old_simulated_effects.items():
            new_fluents = []
            for f in old_se.fluents:
                new_fluents.append(f.substitute(subs))

            # _old_se bound as a default: the closure outlives the iteration, so capturing
            # the loop variable would make every timing call the last one's function.
            def durative_fun(_problem, _state, _, _old_se=old_se):
                return _old_se.function(_problem, _state, c_subs)

            # this rebuilds a simulated effect the user already defined (and got
            # warned about), so the deprecation warning is silenced here
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                new_simulated_effect = SimulatedEffect(new_fluents, durative_fun)
            # We try to add the new simulated effect, but a compiler might generate conflicting effects,
            # so the action is just considered invalid
            try:
                new_durative_action.set_simulated_effect(t, new_simulated_effect)
            except UPConflictingEffectsException:
                return None
        is_feasible, new_conditions = check_and_simplify_conditions(
            problem, new_durative_action, simplifier
        )
        if not is_feasible:
            return None
        new_durative_action.clear_conditions()
        for interval, c in new_conditions:
            new_durative_action.add_condition(interval, c)
        return new_durative_action
    raise NotImplementedError


def get_fresh_name(
    problem: AbstractProblem,
    original_name: str,
    parameters_names: Sequence[str] = (),
    trailing_info: Optional[str] = None,
) -> str:
    """This method returns a fresh name for the problem, given a name and an iterable of names in input."""
    name_list = [original_name]
    name_list.extend(parameters_names)
    if trailing_info:
        name_list.append(trailing_info)
    new_name = "_".join(name_list)
    base_name = new_name
    count = 0
    while problem.has_name(new_name):
        new_name = f"{base_name}_{count!s}"
        count += 1
    return new_name


def get_fresh_parameter_name(action: Action, name: str):
    """This method returns a fresh name for a parameter in the action, given a name and the action"""
    name_list: List[str] = [p.name for p in action.parameters]
    count = 0
    new_name = name
    while new_name in name_list:
        new_name = f"{name}_{count!s}"
        count += 1
    return new_name


def lift_action_instance(
    action_instance: ActionInstance,
    map: Dict["up.model.Action", Tuple["up.model.Action", List["up.model.FNode"]]],
) -> ActionInstance:
    """ "map" is a map from every action in the "grounded_problem" to the tuple
    (original_action, parameters).

    Where the grounded action is obtained by grounding
    the "original_action" with the specific "parameters"."""
    lifted_action, parameters = map[action_instance.action]
    return ActionInstance(lifted_action, tuple(parameters))


def replace_action(
    action_instance: ActionInstance,
    map: Dict["up.model.Action", Optional["up.model.Action"]],
) -> Optional[ActionInstance]:
    try:
        replaced_action = map[action_instance.action]
    except KeyError:
        raise UPUsageError(
            "The Action of the given ActionInstance does not have a valid replacement."
        ) from None
    if replaced_action is not None:
        return ActionInstance(
            replaced_action,
            action_instance.actual_parameters,
            action_instance.agent,
            action_instance.motion_paths,
        )
    return None


def add_invariant_condition_apply_function_to_problem_expressions(
    original_problem: Problem,
    new_problem: Problem,
    condition: Optional[FNode] = None,
    function: Optional[Callable[[FNode], FNode]] = None,
) -> Dict[Action, Optional[Action]]:
    """
    This function takes the original problem, the new problem and adds to the new problem
    all the fields that involve an expression, applying the given function (the identity if it is None)
    to all expressions in the problem and adding the condition as an invariant for the whole problem;
    adding it as a final goal and as a precondition for every action. For the temporal case,
    whenever there is the possibility that a point in time is relevant, the condition is also added there.

    NOTE: The new_problem field will be modified!

    :param original_problem: The Problem acting as a base that will be modified in the new problem.
    :param new_problem: The problem created from the original problem; outside of this function the name,
        the fluents and the objects must be manually added.
    :param condition: Optionally, the condition to add in every relevant point of the Problem, making
        it de-facto an invariant.
    :param function: Optionally, the function that will be called and that creates every expression of the
        new problem.
    :return: The mapping from the actions of the new problem to the actions of the original problem;
        every action is mapped to the action it was generated from.
    """
    env = new_problem.environment
    em = env.expression_manager
    if condition is None:
        condition = em.TRUE()
    assert condition is not None
    if function is None:

        def function(x):
            return x

    new_to_old: Dict[Action, Optional[Action]] = {}

    for constraint in original_problem.trajectory_constraints:
        new_problem.add_trajectory_constraint(function(constraint))

    for original_action in original_problem.actions:
        params = OrderedDict(((p.name, p.type) for p in original_action.parameters))
        if isinstance(original_action, InstantaneousAction):
            new_action: Union[InstantaneousAction, DurativeAction] = (
                InstantaneousAction(original_action.name, params, env)
            )
            assert isinstance(new_action, InstantaneousAction)
            new_cond = em.And(
                *map(function, original_action.preconditions), condition
            ).simplify()
            if new_cond.is_false():
                continue
            if new_cond.is_and():
                for arg in new_cond.args:
                    new_action.add_precondition(arg)
            else:
                new_action.add_precondition(new_cond)
            for effect in original_action.effects:
                new_action._add_effect_instance(
                    _apply_function_to_effect(effect, function)
                )
        elif isinstance(original_action, DurativeAction):
            new_action = DurativeAction(original_action.name, params, env)
            assert isinstance(new_action, DurativeAction)
            old_duration = original_action.duration
            new_duration = DurationInterval(
                function(old_duration.lower),
                function(old_duration.upper),
                old_duration.is_left_open(),
                old_duration.is_right_open(),
            )
            new_action.set_duration_constraint(new_duration)
            for interval, cond_list in original_action.conditions.items():
                new_cond = em.And(*map(function, cond_list), condition).simplify()
                if new_cond.is_false():
                    continue
                if new_cond.is_and():
                    for arg in new_cond.args:
                        new_action.add_condition(interval, arg)
                else:
                    new_action.add_condition(interval, new_cond)
            for timing, effects in original_action.effects.items():
                for effect in effects:
                    new_action._add_effect_instance(
                        timing, _apply_function_to_effect(effect, function)
                    )
                interval = TimePointInterval(timing)
                if interval not in new_action.conditions:
                    new_action.add_condition(interval, condition)
        else:
            raise NotImplementedError
        new_problem.add_action(new_action)
        new_to_old[new_action] = original_action

    for interval, goal_list in original_problem.timed_goals.items():
        new_goal = em.And(*map(function, goal_list), condition).simplify()
        if new_goal.is_and():
            for arg in new_goal.args:
                new_problem.add_timed_goal(interval, arg)
        else:
            new_problem.add_timed_goal(interval, new_goal)
    for timing, effects in original_problem.timed_effects.items():
        for effect in effects:
            new_problem._add_effect_instance(
                timing, _apply_function_to_effect(effect, function)
            )
        interval = TimePointInterval(timing)
        if interval not in new_problem.timed_goals:
            new_problem.add_timed_goal(interval, condition)

    new_goal = em.And(*map(function, original_problem.goals), condition).simplify()
    if new_goal.is_and():
        for arg in new_goal.args:
            new_problem.add_goal(arg)
    else:
        new_problem.add_goal(new_goal)

    for qm in original_problem.quality_metrics:
        if qm.is_minimize_action_costs():
            assert isinstance(qm, MinimizeActionCosts)
            new_costs: Dict["up.model.Action", "up.model.Expression"] = {}
            for new_a, old_a in new_to_old.items():
                if old_a is None:
                    continue
                cost = qm.get_action_cost(old_a)
                if cost is not None:
                    cost = function(cost)
                    new_costs[new_a] = cost
            new_qm: PlanQualityMetric = MinimizeActionCosts(
                new_costs, environment=new_problem.environment
            )
        elif qm.is_minimize_expression_on_final_state():
            assert isinstance(qm, MinimizeExpressionOnFinalState)
            new_qm = MinimizeExpressionOnFinalState(
                function(qm.expression), environment=new_problem.environment
            )
        elif qm.is_maximize_expression_on_final_state():
            assert isinstance(qm, MaximizeExpressionOnFinalState)
            new_qm = MaximizeExpressionOnFinalState(
                function(qm.expression), environment=new_problem.environment
            )
        elif qm.is_oversubscription():
            assert isinstance(qm, Oversubscription)
            new_goals: Dict[BoolExpression, NumericConstant] = {}
            for goal, gain in qm.goals.items():
                new_goal = function(em.And(goal, condition).simplify())
                new_goals[new_goal] = (
                    cast(Union[int, Fraction], new_goals.get(new_goal, 0)) + gain
                )
            new_qm = Oversubscription(new_goals, environment=new_problem.environment)
        elif qm.is_temporal_oversubscription():
            assert isinstance(qm, TemporalOversubscription)
            new_temporal_goals: Dict[
                Tuple["up.model.timing.TimeInterval", "up.model.BoolExpression"],
                NumericConstant,
            ] = {}
            for (interval, goal), gain in qm.goals.items():
                new_goal = function(em.And(goal, condition).simplify())
                new_temporal_goals[(interval, new_goal)] = (
                    cast(
                        Union[int, Fraction],
                        new_temporal_goals.get((interval, new_goal), 0),
                    )
                    + gain
                )
            new_qm = TemporalOversubscription(
                new_temporal_goals, environment=new_problem.environment
            )
        else:
            new_qm = qm
        new_problem.add_quality_metric(new_qm)

    for fluent, value in original_problem.initial_values.items():
        new_problem.set_initial_value(function(fluent), function(value))

    return new_to_old


def _apply_function_to_effect(
    effect: Effect, function: Callable[[FNode], FNode]
) -> Effect:
    auto_promote = effect.environment.expression_manager.auto_promote
    return Effect(
        function(effect.fluent),
        function(effect.value),
        function(effect.condition),
        effect.kind,
        tuple((exp.variable() for exp in auto_promote(effect.forall))),
    )


def updated_minimize_action_costs(
    quality_metric: PlanQualityMetric,
    new_to_old: Union[Dict[Action, Action], Dict[Action, Optional[Action]]],
    environment: Environment,
):
    """
    This method takes a `MinimizeActionCosts` `PlanQualityMetric`, a mapping from the new
    action introduced by the compiler to the old action of the problem (None if the
    new action) does not have a counterpart in the original problem) and returns the
    updated equivalent metric for the new problem. This simply changes the costs keys
    and does not alter the cost expression, so it does not cover use-cases like grounding.

    :param quality_metric: The `MinimizeActionCosts`metric to update.
    :param new_to_old: The action's mapping from the compiled problem to the original problem.
    :param environment: The environment of the new problem (therefore, also of the new actions).
    """
    assert isinstance(quality_metric, MinimizeActionCosts)
    new_costs: Dict["up.model.Action", "up.model.Expression"] = {}
    for new_act, old_act in new_to_old.items():
        if old_act is not None:
            new_cost = quality_metric.get_action_cost(old_act)
            if new_cost is not None:
                new_costs[new_act] = new_cost
        else:
            new_costs[new_act] = environment.expression_manager.Int(0)
    return MinimizeActionCosts(new_costs, environment=environment)


def remove_fluents(problem: Problem, fluents: Set[Fluent]) -> None:
    """
    Removes the given `fluents` from the given `problem`, together with their
    default values and all their `initial values`.

    This is meant to be used by a compiler on a problem it owns (typically a
    clone of the original one).

    :param problem: The `Problem` to remove the `fluents` from; modified in place.
    :param fluents: The `fluents` to remove; must all belong to the given `problem`.
    """
    for fluent in fluents:
        problem._fluents.remove(fluent)
        problem._fluents_defaults.pop(fluent, None)
    problem._initial_value = {
        fluent_exp: value
        for fluent_exp, value in problem._initial_value.items()
        if fluent_exp.fluent() not in fluents
    }


def split_all_ands(exp_list: List[FNode]) -> List[FNode]:
    """
    Helper function. Takes in input a List of FNodes and returns a list of FNodes that do not contain any AND operator as the first operator.

    :param exp_list: The List of FNodes that we want to remove AND operators from.
    :return: A list of FNodes not containing AND as the first operators such that AND(e for e in in_exp_list) is equivalent to AND(e for e in returned_list).
    """
    end_list = []
    start_list = exp_list.copy()
    while len(start_list) > 0:
        temp_list = []
        for exp in start_list:
            if exp.is_and():
                temp_list.extend(exp.args)
            else:
                end_list.append(exp)
        start_list = temp_list
    return end_list
